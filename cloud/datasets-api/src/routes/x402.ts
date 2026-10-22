import type { Hono } from "hono";

export function registerX402Info(app: Hono) {
  app.get("/.well-known/x402", (c) => c.json({
    version: "1.0.0",
    recipient: "0xD1D5965dB771d95725C08d9Eaf0083Ed0b7D9CDC",
    network: "base-sepolia",
    facilitator: "https://x402.org/facilitator",
    pricing: {
      "/v1/episodes/*": { price: "$0.01", description: "Single episode download" },
      "/v1/streams/*": { price: "$0.01", description: "Data stream slice" },
      "/v1/packs/*": { price: "$2.00", description: "Region pack" },
      "/v1/packs/dental": { price: "$10.00", description: "Unspoken Smiles dental pack" },
    },
    free_routes: ["/v1/catalog", "/v1/manifest", "/v1/sample/*", "/v1/stats", "/health"],
    docs: "https://x402.org",
  }));
}