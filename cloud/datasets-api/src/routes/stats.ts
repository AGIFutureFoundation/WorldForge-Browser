import type { Hono } from "hono";

export function registerStatsRoutes(app: Hono) {
  app.get("/v1/stats", async (c) => {
    return c.json({ total_payments: 0, total_usd: 0, note: "D1 available after wrangler deploy" });
  });
}