import type { Express, Request } from "express";
import { createServer, type Server } from "http";
import { createProxyMiddleware, fixRequestBody } from "http-proxy-middleware";
import { storage } from "./storage";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  const pythonBackendUrl = process.env.PYTHON_BACKEND_URL || "http://localhost:8000";
  
  app.use(
    "/api",
    createProxyMiddleware({
      target: pythonBackendUrl,
      changeOrigin: true,
      pathRewrite: (path) => `/api${path}`,
      on: {
        proxyReq: fixRequestBody,
        error: (err, _req, res) => {
          console.error("Proxy error:", err.message);
          if (res && typeof (res as any).status === "function") {
            (res as any).status(502).json({ 
              error: "Python backend unavailable",
              message: "Please ensure the Python backend is running on port 8000"
            });
          }
        },
      },
    })
  );

  return httpServer;
}
