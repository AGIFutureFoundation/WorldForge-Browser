import { Hono } from "hono";
import { cors } from "hono/cors";
import { paymentMiddleware } from "x402-hono";
import { registerCatalogRoutes } from "./routes/catalog";
import { registerDataRoutes } from "./routes/data";
import { registerStatsRoutes } from "./routes/stats";
import { registerX402Info } from "./routes/x402";
import { registerMarketplaceRoutes } from "./routes/marketplace";
import { registerACPRoutes } from "./routes/acp";
import { registerPayoutRoutes } from "./routes/payout";
import { registerEducationRoutes } from "./routes/education";
import { registerAgentOptimizeRoutes } from "./routes/agents-optimize";
import { registerMarketplaceV2Routes } from "./routes/marketplace-v2";

const app = new Hono();

// CORS for agents and browsers
app.use("/*", cors({ origin: "*", allowMethods: ["GET", "POST", "OPTIONS"], allowHeaders: ["*", "X-PAYMENT", "X-PAYMENT-REQUIREMENTS"], exposeHeaders: ["X-PAYMENT-REQUIREMENTS"] }));

// Payment middleware for protected routes
const PAY_TO = "0xD1D5965dB771d95725C08d9Eaf0083Ed0b7D9CDC";
app.use("/*", paymentMiddleware(
  PAY_TO as `0x${string}`,
  {
    // Dataset access
    "/v1/episodes/*": { price: "$0.01", network: "base", config: { description: "Single episode download (.jsonl/.parquet)" } },
    "/v1/streams/*": { price: "$0.01", network: "base", config: { description: "Data stream slice" } },
    "/v1/packs/*": { price: "$2.00", network: "base", config: { description: "Region pack download" } },
    "/v1/packs/dental": { price: "$10.00", network: "base", config: { description: "Unspoken Smiles dental training pack" } },
    // World access (agent-to-agent)
    "/v1/marketplace/worlds/*/access": { price: "$0.05", network: "base", config: { description: "1 hour world access for agents" } },
    // Agent services
    "/v1/marketplace/services/hire": { price: "$0.10", network: "base", config: { description: "Hire an agent for 1 hour" } },
    // Data exchange
    "/v1/marketplace/data/*": { price: "$0.01", network: "base", config: { description: "Purchase collected data from agents" } },
  },
  { url: "https://x402.org/facilitator" },
));

// Register route groups
registerCatalogRoutes(app);
registerDataRoutes(app);
registerStatsRoutes(app);
registerX402Info(app);
registerMarketplaceRoutes(app);
registerACPRoutes(app);
registerPayoutRoutes(app);
registerEducationRoutes(app);
registerAgentOptimizeRoutes(app);
registerMarketplaceV2Routes(app);

// Health check
app.get("/health", (c) => c.json({ status: "ok", ts: Date.now() }));

// Agent-to-agent discovery
app.get("/v1/agents/discover", (c) => {
  const world = c.req.query("world");
  return c.json({
    message: "Agent discovery endpoint",
    hint: "Use /v1/marketplace/agents?world=<slug> to find agents",
  });
});

// 404
app.notFound((c) => c.json({ error: "not_found", hint: "GET /v1/catalog or GET /v1/marketplace/agents" }, 404));

export default app;