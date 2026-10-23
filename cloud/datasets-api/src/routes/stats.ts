import type { Hono } from "hono";

export function registerStatsRoutes(app: Hono) {
  app.get("/v1/stats", async (c) => {
    const db = (c.env as any).DB;
    if (!db) return c.json({ total_payments: 0, total_usd: 0, note: "D1 not bound" });
    const { results } = await db.prepare("SELECT COUNT(*) as count, COALESCE(SUM(amount_usd), 0) as total FROM payments").all();
    return c.json({ total_payments: results[0].count, total_usd: results[0].total, network: "base", currency: "USDC", revenue_share_pct: 15 });
  });
}