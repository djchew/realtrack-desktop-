"use strict";

const { app, BrowserWindow, shell } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const http = require("http");

const isDev = !app.isPackaged;

const FRONTEND_PORT = 3000;
const BACKEND_PORT  = 8000;

let backendProcess  = null;
let frontendProcess = null;
let mainWindow      = null;

// ── Process launchers ─────────────────────────────────────────────────────────

function startBackend() {
  const dbPath = path.join(app.getPath("userData"), "realtrack.db");

  if (isDev) {
    // Dev: run uvicorn directly from the backend source folder
    backendProcess = spawn(
      "python",
      ["-m", "uvicorn", "main:app", "--port", String(BACKEND_PORT), "--no-access-log"],
      {
        cwd: path.join(__dirname, "..", "backend"),
        stdio: "inherit",
        env: { ...process.env, DB_PATH: dbPath },
      }
    );
  } else {
    // Production: run the PyInstaller-bundled executable
    const exePath = path.join(process.resourcesPath, "backend", "main.exe");
    backendProcess = spawn(exePath, [], {
      cwd: path.dirname(exePath),
      stdio: "inherit",
      env: { ...process.env, DB_PATH: dbPath },
    });
  }

  backendProcess.on("error", (err) =>
    console.error("[backend] process error:", err.message)
  );
  backendProcess.on("exit", (code) =>
    console.log(`[backend] exited with code ${code}`)
  );
}

function startFrontend() {
  if (isDev) return; // dev server is started separately via `npm run dev`

  // Production: run the Next.js standalone server bundled in resources
  const serverPath = path.join(process.resourcesPath, "frontend", "server.js");
  frontendProcess = spawn(process.execPath, [serverPath], {
    cwd: path.dirname(serverPath),
    stdio: "inherit",
    env: {
      ...process.env,
      PORT:                   String(FRONTEND_PORT),
      HOSTNAME:               "localhost",
      NEXT_PUBLIC_API_URL:    `http://localhost:${BACKEND_PORT}/api`,
    },
  });

  frontendProcess.on("error", (err) =>
    console.error("[frontend] process error:", err.message)
  );
  frontendProcess.on("exit", (code) =>
    console.log(`[frontend] exited with code ${code}`)
  );
}

// ── Port readiness check ──────────────────────────────────────────────────────

function waitForPort(port, retries = 40, delayMs = 500) {
  return new Promise((resolve, reject) => {
    const attempt = (remaining) => {
      const req = http
        .get(`http://localhost:${port}`, () => resolve())
        .on("error", () => {
          if (remaining <= 0) return reject(new Error(`Port ${port} never became ready`));
          setTimeout(() => attempt(remaining - 1), delayMs);
        });
      req.setTimeout(300, () => req.destroy());
    };
    attempt(retries);
  });
}

// ── Window ────────────────────────────────────────────────────────────────────

function createWindow() {
  mainWindow = new BrowserWindow({
    width:  1400,
    height: 900,
    minWidth:  1024,
    minHeight: 700,
    title: "RealTrack",
    show: false,
    webPreferences: {
      preload:          path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration:  false,
    },
  });

  mainWindow.loadURL(`http://localhost:${FRONTEND_PORT}`);

  // Show once the page has painted (avoids white flash)
  mainWindow.once("ready-to-show", () => mainWindow.show());

  // Open all <a target="_blank"> links in the system browser, not Electron
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  mainWindow.on("closed", () => { mainWindow = null; });
}

// ── App lifecycle ─────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  startBackend();
  startFrontend();

  console.log("Waiting for services to start…");
  try {
    await Promise.all([
      waitForPort(FRONTEND_PORT),
      waitForPort(BACKEND_PORT),
    ]);
    console.log("Services ready");
  } catch (err) {
    console.error("Services failed to start:", err.message);
    // Open anyway — the page will show a useful error
  }

  createWindow();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

app.on("will-quit", () => {
  if (backendProcess)  backendProcess.kill();
  if (frontendProcess) frontendProcess.kill();
});
