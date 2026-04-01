"use strict";

const { contextBridge } = require("electron");

// Expose a minimal, safe API to the renderer process.
// Add IPC handlers here as the app needs them (e.g. open file dialogs, etc.)
contextBridge.exposeInMainWorld("electron", {
  platform: process.platform,
});
