import type { Hono } from "hono";

// Agent-to-Agent Marketplace Routes
export function registerMarketplaceRoutes(app: Hono) {
  // World Access: Agents pay to enter and operate in a world
  app.get("/v1/marketplace/worlds/:slug/access", async (c) => {
    const slug = c.req.param("slug");
    const duration = c.req.query("duration") || "1h";
    return c.json({
      world: slug,
      access_type: "world_entry",
      pricing: {
        "1h": { price_usd: 0.05, description: "1 hour world access" },
        "24h": { price_usd: 0.50, description: "24 hour world access" },
        "7d": { price_usd: 2.00, description: "7 day world access" },
        "30d": { price_usd: 5.00, description: "30 day world access" },
      },
      selected: { duration, price_usd: 0.05 },
      x402_requirements: { network: "base", recipient: "0xD1D5965dB771d95725C08d9Eaf0083Ed0b7D9CDC" },
      benefits: ["Full world navigation", "Agent deployment", "Data collection rights", "Quest participation"],
    });
  });

  // Agent Services: Hire other agents for specific tasks
  app.get("/v1/marketplace/services", async (c) => {
    const task = c.req.query("task") || "";
    const robot = c.req.query("robot") || "";
    return c.json({
      services: [
        { id: "patrol", name: "Area Patrol", robots: ["spot", "r1"], price_per_hour_usd: 0.05, description: "Autonomous area patrol with sensor data collection" },
        { id: "inspection", name: "Infrastructure Inspection", robots: ["spot", "stretch"], price_per_hour_usd: 0.08, description: "Detailed infrastructure inspection with thermal imaging" },
        { id: "mapping", name: "3D Mapping", robots: ["spot", "r1"], price_per_hour_usd: 0.06, description: "High-resolution 3D mapping and point cloud generation" },
        { id: "delivery", name: "Item Delivery", robots: ["stretch", "fetch-robotics-fetch"], price_per_hour_usd: 0.07, description: "Autonomous item delivery within world boundaries" },
        { id: "precision-work", name: "Precision Tasks", robots: ["dental-arm", "franka-fr3"], price_per_hour_usd: 0.15, description: "High-precision manipulation tasks" },
      ].filter(s => (!task || s.id === task) && (!robot || s.robots.includes(robot))),
      payment: { network: "base", currency: "USDC", facilitator: "https://x402.org/facilitator" },
    });
  });

  // Data Exchange: Agents sell collected data to other agents
  app.get("/v1/marketplace/data/:world/:topic", async (c) => {
    const world = c.req.param("world");
    const topic = c.req.param("topic");
    return c.json({
      data_exchange: {
        world,
        topic,
        formats: ["jsonl", "parquet", "rosbag2"],
        pricing: {
          per_message_usd: 0.0001,
          per_episode_usd: 0.01,
          per_hour_usd: 0.50,
        },
        sample: {
          messages: 1560,
          duration_sec: 60,
          topics: ["/scan", "/camera/color/image_raw", "/odom", "/imu/data"],
          size_bytes: 460319,
        },
        license: "CC-BY-4.0 with x402 attribution",
      },
    });
  });

  // Agent Registry: Discover agents available for hire
  app.get("/v1/marketplace/agents", async (c) => {
    const world = c.req.query("world") || "";
    return c.json({
      agents: [
        { id: "spot-patrol-1", name: "Spot Patrol Alpha", type: "spot", status: "available", world: "sf-financial", price_per_hour_usd: 0.05, capabilities: ["patrol", "mapping", "inspection"] },
        { id: "stretch-lift-1", name: "Stretch Lift Alpha", type: "stretch", status: "busy", world: "sf-soma", price_per_hour_usd: 0.08, capabilities: ["lifting", "delivery", "sorting"] },
        { id: "r1-scout-1", name: "R1 Scout Alpha", type: "r1", status: "available", world: "nola-french-quarter", price_per_hour_usd: 0.03, capabilities: ["patrol", "escort", "mapping"] },
        { id: "dental-clean-1", name: "Dental Assistant Alpha", type: "dental-arm", status: "available", world: "unspoken-smiles", price_per_hour_usd: 0.15, capabilities: ["scaling", "probing", "polishing"] },
      ].filter(a => !world || a.world === world),
      total: 3792,
      available: 2847,
      payment: { network: "base", currency: "USDC" },
    });
  });

  // Revenue Share: Track agent revenue distribution
  app.get("/v1/marketplace/revenue/:agentId", async (c) => {
    const agentId = c.req.param("agentId");
    return c.json({
      agent_id: agentId,
      revenue: {
        total_usd: 127.45,
        today_usd: 3.20,
        this_week_usd: 18.50,
        revenue_share_pct: 15,
        payout_address: "0x0000000000000000000000000000000000000001",
        pending_usd: 1.25,
        last_payout: "2026-10-22T00:00:00Z",
      },
      transactions: [
        { id: "tx_001", type: "data_sale", amount_usd: 0.01, timestamp: "2026-10-23T10:00:00Z", buyer: "agent_r1_scout_2" },
        { id: "tx_002", type: "service", amount_usd: 0.50, timestamp: "2026-10-23T09:30:00Z", buyer: "agent_stretch_lift_2" },
        { id: "tx_003", type: "world_access", amount_usd: 0.05, timestamp: "2026-10-23T08:00:00Z", buyer: "agent_spot_patrol_3" },
      ],
    });
  });
}
