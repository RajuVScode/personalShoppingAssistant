import type { Express, Request } from "express";
import { createServer, type Server } from "http";
import { createProxyMiddleware } from "http-proxy-middleware";
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
      pathRewrite: {
        "^/api": "/api",
      },
      on: {
        proxyReq: (proxyReq, req) => {
          const expressReq = req as Request;
          if (expressReq.body && Object.keys(expressReq.body).length > 0) {
            const bodyData = JSON.stringify(expressReq.body);
            proxyReq.setHeader("Content-Type", "application/json");
            proxyReq.setHeader("Content-Length", Buffer.byteLength(bodyData));
            proxyReq.write(bodyData);
          }
        },
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
