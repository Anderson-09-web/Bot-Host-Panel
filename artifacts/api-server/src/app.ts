import express, { type Express } from "express";
import cors from "cors";
import pinoHttp from "pino-http";
import { createProxyMiddleware } from "http-proxy-middleware";
import router from "./routes";
import { logger } from "./lib/logger";

const app: Express = express();

app.use(
  pinoHttp({
    logger,
    serializers: {
      req(req) {
        return {
          id: req.id,
          method: req.method,
          url: req.url?.split("?")[0],
        };
      },
      res(res) {
        return {
          statusCode: res.statusCode,
        };
      },
    },
  }),
);
app.use(cors());

// IMPORTANTE: NO poner body parsers globales aquí.
// El proxy reenvía el body stream crudo a Flask; si Express lo
// consume primero, Flask recibe JSON vacío y falla.
// Los parsers se aplican sólo dentro de las rutas que Express maneja.
app.use("/api", router);

// Proxy todo lo demás al panel Flask (puerto 5000)
app.use(
  "/",
  createProxyMiddleware({
    target: "http://127.0.0.1:5000",
    changeOrigin: true,
    ws: true,
    on: {
      error: (err, _req, res: any) => {
        logger.error({ err }, "Proxy error hacia Flask panel");
        res.status?.(502).send("Panel no disponible — asegúrate de que Bot Panel esté corriendo.");
      },
    },
  }),
);

export default app;
