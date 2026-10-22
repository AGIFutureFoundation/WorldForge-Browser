import { Hono } from "hono";
import { cors } from "hono/cors";
import { paymentMiddleware } from "x402-hono";
import { registerCatalogRoutes } from "./routes/catalog";
import { registerDataRoutes } from "./routes/data";
import { registerStatsRoutes } from "./routes/stats";
import { registerX402Info } from "./routes/x402";

const app = new Hono();

// CORS for agents and browsers
app.use("/*", cors({ origin: "*", allowMethods: ["GET", "POST", "OPTIONS"], allowHeaders: ["*", "X-PAYMENT", "X-PAYMENT-REQUIREMENTS"], exposeHeaders: ["X-PAYMENT-REQUIREMENTS"] }));

// Payment middleware for protected routes
const PAY_TO = "0xD1D5965dB771d95725C08d9Eaf0083Ed0b7D9CDC";
app.use("/*", paymentMiddleware(
  PAY_TO as `0x${string}`,
  {
    "/v1/episodes/*": { price: "$0.01", network: "base-sepolia", config: { description: "Single episode download (.jsonl/.parquet)" } },
    "/v1/streams/*": { price: "$0.01", network: "base-sepolia", config: { description: "Data stream slice" } },
    "/v1/packs/*": { price: "$2.00", network: "base-sepolia", config: { description: "Region pack download" } },
    "/v1/packs/dental": { price: "$10.00", network: "base-sepolia", config: { description: "Unspoken Smiles dental training pack" } },
  },
  { url: "https://x402.org/facilitator" },
));

// Register route groups
registerCatalogRoutes(app);
registerDataRoutes(app);
registerStatsRoutes(app);
registerX402Info(app);

// Health check
app.get("/health", (c) => c.json({ status: "ok", ts: Date.now() }));

// 404
app.notFound((c) => c.json({ error: "not_found", hint: "GET /v1/catalog to see available datasets" }, 404));

export default app;