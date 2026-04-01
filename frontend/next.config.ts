import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a self-contained build for Electron packaging.
  // `next dev` ignores this — only affects `next build`.
  output: "standalone",
  // Tell Next.js the monorepo root for standalone file tracing.
  outputFileTracingRoot: path.join(__dirname, ".."),
  webpack: (config) => {
    // @sentry/node bundles a Prisma integration which uses dynamic requires
    // in @opentelemetry/instrumentation. We don't use Prisma — suppress the noise.
    config.ignoreWarnings = [
      ...(config.ignoreWarnings ?? []),
      { module: /@opentelemetry\/instrumentation/ },
    ];
    return config;
  },
};

export default nextConfig;
