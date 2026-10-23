import type { Hono } from "hono";

export function registerX402Info(app: Hono) {
  app.get("/.well-known/x402", (c) => c.json({
    version: "2.0.0",
    recipient: "0xD1D5965dB771d95725C08d9Eaf0083Ed0b7D9CDC",
    network: "base",
    facilitator: "https://x402.org/facilitator",
    pricing: {
      // Dataset access
      "/v1/episodes/*": { price: "$0.01", description: "Single episode download" },
      "/v1/streams/*": { price: "$0.01", description: "Data stream slice" },
      "/v1/packs/*": { price: "$2.00", description: "Region pack" },
      "/v1/packs/dental": { price: "$10.00", description: "Unspoken Smiles dental pack" },
      // Agent-to-agent marketplace
      "/v1/marketplace/worlds/*/access": { price: "$0.05", description: "World access (1 hour)" },
      "/v1/marketplace/services/hire": { price: "$0.10", description: "Hire agent (1 hour)" },
      "/v1/marketplace/data/*": { price: "$0.01", description: "Purchase agent data" },
    },
    free_routes: ["/v1/catalog", "/v1/manifest", "/v1/sample/*", "/v1/stats", "/v1/marketplace/*", "/v1/agents/discover", "/health"],
    docs: "https://x402.org",
    agent_economy: {
      description: "Agent-to-agent monetization for world access, services, and data",
      revenue_share_pct: 15,
      payout_currency: "USDC",
      payout_network: "base",
    },
  }));
}