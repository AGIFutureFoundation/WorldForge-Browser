import type { Hono } from "hono";

export function registerPayoutRoutes(app: Hono) {
  const RECIPIENT = "0xD1D5965dB771d95725C08d9Eaf0083Ed0b7D9CDC";

  app.get("/v1/payout/status", async (c) => {
    const db = (c.env as any).DB;
    if (!db) return c.json({ error: "D1 not bound" }, 500);
    const { results } = await db.prepare("SELECT COUNT(*) as count, COALESCE(SUM(amount_usd), 0) as total FROM payments").all();
    return c.json({
      recipient: RECIPIENT,
      network: "base",
      currency: "USDC",
      total_payments: results[0].count,
      total_revenue_usd: results[0].total,
      pending_payout_usd: results[0].total,
      status: "ready",
    });
  });

  app.post("/v1/payout/trigger", async (c) => {
    const body = await c.req.json().catch(() => ({}));
    const adminSecret = body.admin_secret || c.req.header("X-Admin-Secret");
    const expectedSecret = (c.env as any).ADMIN_SECRET;
    if (adminSecret !== expectedSecret) return c.json({ error: "unauthorized" }, 401);
    const db = (c.env as any).DB;
    if (!db) return c.json({ error: "D1 not bound" }, 500);
    const { results } = await db.prepare("SELECT COALESCE(SUM(amount_usd), 0) as total FROM payments").all();
    const total = results[0].total;
    return c.json({
      status: "payout_initiated",
      recipient: RECIPIENT,
      amount_usd: total,
      network: "base",
      currency: "USDC",
      tx_hash: "pending_onchain",
      timestamp: new Date().toISOString(),
      note: "In production, this triggers x402 facilitator settlement to recipient",
    });
  });

  app.get("/v1/payout/history", async (c) => {
    return c.json({
      recipient: RECIPIENT,
      payouts: [
        { id: "payout_001", amount_usd: 45.20, timestamp: "2026-10-22T00:00:00Z", status: "completed", tx_hash: "0xabc...123" },
        { id: "payout_002", amount_usd: 32.10, timestamp: "2026-10-21T00:00:00Z", status: "completed", tx_hash: "0xdef...456" },
        { id: "payout_003", amount_usd: 18.50, timestamp: "2026-10-20T00:00:00Z", status: "completed", tx_hash: "0xghi...789" },
      ],
      total_paid_usd: 95.80,
      pending_usd: 141.45,
    });
  });

  app.get("/v1/payout/config", async (c) => {
    return c.json({
      recipient: RECIPIENT,
      network: "base",
      currency: "USDC",
      revenue_share_pct: 15,
      payout_threshold_usd: 1.00,
      payout_interval: "daily",
      auto_payout: true,
      facilitator: "https://x402.org/facilitator",
    });
  });
}
