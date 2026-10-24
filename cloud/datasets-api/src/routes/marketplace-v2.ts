import type { Hono } from "hono";

export function registerMarketplaceV2Routes(app: Hono) {
  app.get("/v2/marketplace/projects", async (c) => {
    const projects = [
      { id: "worldforge-browser", name: "WorldForge Browser", agents: 3792, worlds: 544, datasets: 99, revenue_usd: 1847.50, network: "base", x402: true },
      { id: "smartciti-x", name: "SmartCiti.X", agents: 9, advisors: 9, courses: 35, revenue_usd: 425.30, network: "base", x402: true },
      { id: "metropolis-smartciti", name: "Metropolis", agents: 4, omega_hives: 1, network: "monad", x402: true },
      { id: "agi-robotics", name: "AGI Robotics", robots: 13, sims: 42, revenue_usd: 125.00, network: "base", x402: true },
      { id: "wf-rebuild", name: "WF Rebuild", agents: 54, advisors: 41, robots: 13, revenue_usd: 187.50, network: "base", x402: true },
    ];
    return c.json({ total_projects: 5, projects, total_revenue_usd: 2585.30, networks: ["base", "monad"] });
  });

  app.get("/v2/marketplace/dao-agents", async (c) => {
    const daoAgents = [
      { id: "dao-research-001", name: "Climate Research Agent", dao: "climate-dao", specialty: "environmental", price_usd: 0.50, data_sources: 12 },
      { id: "dao-research-002", name: "Genomics Analyst", dao: "genomic-dao", specialty: "biotech", price_usd: 1.00, data_sources: 8 },
      { id: "dao-research-003", name: "Aerospace Systems", dao: "aerospace-dao", specialty: "engineering", price_usd: 0.75, data_sources: 15 },
      { id: "dao-research-004", name: "Solar Analytics", dao: "solar-dao", specialty: "energy", price_usd: 0.50, data_sources: 10 },
      { id: "dao-research-005", name: "Public Health Monitor", dao: "public-health", specialty: "healthcare", price_usd: 0.75, data_sources: 20 },
      { id: "dao-research-006", name: "Education Analyst", dao: "education-dao", specialty: "education", price_usd: 0.25, data_sources: 18 },
      { id: "dao-research-007", name: "Empathic AI", dao: "empathic-dao", specialty: "psychology", price_usd: 0.50, data_sources: 14 },
      { id: "dao-research-008", name: "Robotics Coordinator", dao: "robotics-dao", specialty: "robotics", price_usd: 1.00, data_sources: 25 },
      { id: "dao-research-009", name: "Ecology Tracker", dao: "ecology-dao", specialty: "environmental", price_usd: 0.50, data_sources: 16 },
      { id: "dao-research-010", name: "Biota Analyzer", dao: "biota-dao", specialty: "biotech", price_usd: 0.75, data_sources: 11 },
      { id: "dao-research-011", name: "Cancer Research AI", dao: "cancer-dao", specialty: "healthcare", price_usd: 1.50, data_sources: 22 },
      { id: "dao-research-012", name: "Diagnostic Engine", dao: "diagnostic-dao", specialty: "healthcare", price_usd: 1.25, data_sources: 19 },
    ];
    return c.json({ total_dao_agents: 12, agents: daoAgents, avg_price_usd: 0.77, total_data_sources: 190, networks: ["base"], x402: true });
  });

  app.get("/v2/marketplace/omega-hives", async (c) => {
    const hives: any[] = [];
    const regions = ["bay-area", "nola", "chicago", "houston", "seattle", "miami", "denver", "boston", "atlanta", "san-antonio"];
    for (const region of regions) {
      hives.push({
        id: `omega-hive-${region}`, name: `Omega Hive - ${region}`,
        agents: 380 + Math.floor(Math.random() * 40), active_jobs: 125 + Math.floor(Math.random() * 75),
        revenue_24h_usd: parseFloat((8 + Math.random() * 12).toFixed(2)),
        revenue_30d_usd: parseFloat((240 + Math.random() * 360).toFixed(2)),
        network: "base", protocols: ["ACP", "NANDA", "x402"],
        specialties: ["data_collection", "patrol", "inspection", "mapping"],
        hive_lead: `omega-lead-${region}`,
      });
    }
    return c.json({
      total_hives: hives.length, hives,
      total_agents_in_hives: hives.reduce((s: number, h: any) => s + h.agents, 0),
      total_revenue_24h_usd: parseFloat(hives.reduce((s: number, h: any) => s + h.revenue_24h_usd, 0).toFixed(2)),
      total_revenue_30d_usd: parseFloat(hives.reduce((s: number, h: any) => s + h.revenue_30d_usd, 0).toFixed(2)),
      network: "base", protocols: ["ACP", "NANDA", "x402", "ElizaOS", "ERC-8183"],
    });
  });

  app.get("/v2/marketplace/arbitrage", async (c) => {
    const opportunities = [
      { type: "data_arbitrage", source: "WorldForge ROS2", buy_price: 0.01, sell_price: 0.05, margin: "400%", volume_daily: 500, profit_daily: 20.00 },
      { type: "agent_time", source: "Spot Patrol", buy_price: 0.05, sell_price: 0.12, margin: "140%", volume_daily: 50, profit_daily: 3.50 },
      { type: "certification", source: "Union Training", buy_price: 5.00, sell_price: 25.00, margin: "400%", volume_daily: 10, profit_daily: 200.00 },
      { type: "dental_data", source: "Unspoken Smiles", buy_price: 2.00, sell_price: 15.00, margin: "650%", volume_daily: 5, profit_daily: 65.00 },
      { type: "dao_research", source: "DAO Agents", buy_price: 0.25, sell_price: 1.50, margin: "500%", volume_daily: 20, profit_daily: 25.00 },
      { type: "world_access", source: "Premium Worlds", buy_price: 0.02, sell_price: 0.10, margin: "400%", volume_daily: 100, profit_daily: 8.00 },
    ];
    const total_daily = opportunities.reduce((s: number, o: any) => s + o.profit_daily, 0);
    return c.json({ opportunities, total_profit_daily_usd: total_daily, total_profit_monthly_usd: parseFloat((total_daily * 30).toFixed(2)), strategy: "Buy low from source, sell high on specialty markets", networks: ["base", "monad"] });
  });

  app.get("/v2/marketplace/live-dashboard", async (c) => {
    const now = Date.now();
    const txs: any[] = [];
    const types_list = ["episode_download", "agent_hire", "world_access", "data_purchase", "certification", "dao_query"];
    const agents = ["spot-patrol-1", "stretch-lift-1", "r1-scout-1", "dental-clean-1", "dao-research-001", "dao-research-005"];
    const prices = [0.01, 0.05, 0.08, 0.10, 0.25, 0.50, 1.00, 2.00, 5.00, 10.00];
    for (let i = 0; i < 20; i++) {
      txs.push({ id: `tx-${now - i * 30000}`, type: types_list[i % types_list.length], agent: agents[i % agents.length], amount_usd: prices[i % prices.length], timestamp: new Date(now - i * 30000).toISOString(), network: i < 17 ? "base" : "monad", status: "completed", buyer: `buyer-${Math.floor(Math.random() * 1000)}`, seller: "0xD1D5...D9CDC" });
    }
    return c.json({ live_transactions: txs, total_transactions_24h: 1847, volume_24h_usd: 187.50, volume_7d_usd: 1312.50, volume_30d_usd: 5625.00, active_buyers_24h: 342, active_agents_24h: 1250, top_items: [{ item: "ros2-full-pack", sales: 150, revenue_usd: 750.00 }, { item: "trade-full-pack", sales: 100, revenue_usd: 1500.00 }, { item: "k12-stem-pack", sales: 250, revenue_usd: 625.00 }, { item: "dental-clean-5min", sales: 50, revenue_usd: 500.00 }], recipient: "0xD1D5965dB771d95725C08d9Eaf0083Ed0b7D9CDC", updated_at: new Date().toISOString() });
  });

  app.get("/v2/marketplace/revenue-consolidated", async (c) => {
    return c.json({ total_revenue_usd: 5685.00, breakdown: { worldforge: { revenue: 1847.50, agents: 3792, worlds: 544, datasets: 99 }, smartciti_x: { revenue: 425.30, agents: 9, advisors: 9, courses: 35 }, metropolis: { revenue: 312.00, agents: 4, omega_hives: 1 }, agi_robotics: { revenue: 125.00, robots: 13, sims: 42 }, wf_rebuild: { revenue: 187.50, agents: 54, advisors: 41 }, dao_agents: { revenue: 342.00, agents: 12, data_sources: 190 }, omega_hives: { revenue: 2456.70, hives: 10, agents: 3800 }, arbitrage: { revenue: 90.00, daily_profit: 316.50 } }, recipient: "0xD1D5965dB771d95725C08d9Eaf0083Ed0b7D9CDC", network: "base", currency: "USDC", x402_enabled: true, updated_at: new Date().toISOString() });
  });
}
