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

  // Agent Network Graph (D3.js force-directed)
  app.get("/v2/graph/agent-network", async (c) => {
    const nodes = [
      { id: "omega-hive", label: "Omega Hive", group: "hub", size: 30 },
      { id: "worldforge", label: "WorldForge", group: "project", size: 25 },
      { id: "smartcitix", label: "SmartCiti.X", group: "project", size: 15 },
      { id: "metropolis", label: "Metropolis", group: "project", size: 12 },
      { id: "agi-robotics", label: "AGI Robotics", group: "project", size: 14 },
      { id: "wf-rebuild", label: "WF Rebuild", group: "project", size: 16 },
      { id: "acp", label: "ACP", group: "marketplace", size: 18 },
      { id: "elizaos", label: "ElizaOS", group: "marketplace", size: 14 },
      { id: "nanda", label: "NANDA", group: "marketplace", size: 12 },
      { id: "base", label: "Base Network", group: "network", size: 20 },
      { id: "monad", label: "Monad", group: "network", size: 16 },
      { id: "dao-climate", label: "Climate DAO", group: "dao", size: 10 },
      { id: "dao-genomics", label: "Genomics DAO", group: "dao", size: 10 },
      { id: "dao-health", label: "Public Health DAO", group: "dao", size: 10 },
      { id: "dao-robotics", label: "Robotics DAO", group: "dao", size: 10 },
    ];
    const links = [
      { source: "omega-hive", target: "worldforge", value: 3792 },
      { source: "omega-hive", target: "smartcitix", value: 9 },
      { source: "omega-hive", target: "metropolis", value: 4 },
      { source: "omega-hive", target: "agi-robotics", value: 13 },
      { source: "omega-hive", target: "wf-rebuild", value: 54 },
      { source: "worldforge", target: "acp", value: 1847 },
      { source: "worldforge", target: "elizaos", value: 425 },
      { source: "worldforge", target: "nanda", value: 312 },
      { source: "smartcitix", target: "acp", value: 425 },
      { source: "metropolis", target: "base", value: 312 },
      { source: "metropolis", target: "monad", value: 187 },
      { source: "agi-robotics", target: "acp", value: 125 },
      { source: "wf-rebuild", target: "acp", value: 187 },
      { source: "omega-hive", target: "base", value: 4500 },
      { source: "omega-hive", target: "monad", value: 1185 },
      { source: "omega-hive", target: "dao-climate", value: 85 },
      { source: "omega-hive", target: "dao-genomics", value: 120 },
      { source: "omega-hive", target: "dao-health", value: 95 },
      { source: "omega-hive", target: "dao-robotics", value: 110 },
    ];
    return c.json({ nodes, links, total_nodes: nodes.length, total_links: links.length });
  });

  // Revenue Flow Graph (Sankey-style)
  app.get("/v2/graph/revenue-flow", async (c) => {
    const nodes = [
      { name: "WorldForge Agents" }, { name: "SmartCiti.X Advisors" },
      { name: "Metropolis Swarm" }, { name: "AGI Robots" },
      { name: "WF Rebuild Agents" }, { name: "DAO Research" },
      { name: "Arbitrage Engine" }, { name: "ACP Marketplace" },
      { name: "ElizaOS" }, { name: "NANDA" },
      { name: "Base Network" }, { name: "Monad Network" },
      { name: "Omega Treasury" },
    ];
    const links = [
      { source: 0, target: 7, value: 1200 }, { source: 0, target: 8, value: 400 },
      { source: 0, target: 9, value: 247 }, { source: 1, target: 7, value: 300 },
      { source: 1, target: 8, value: 125 }, { source: 2, target: 10, value: 200 },
      { source: 2, target: 11, value: 112 }, { source: 3, target: 7, value: 85 },
      { source: 3, target: 9, value: 40 }, { source: 4, target: 7, value: 120 },
      { source: 4, target: 8, value: 67 }, { source: 5, target: 7, value: 200 },
      { source: 5, target: 9, value: 142 }, { source: 6, target: 10, value: 200 },
      { source: 6, target: 11, value: 116 }, { source: 7, target: 12, value: 1847 },
      { source: 8, target: 12, value: 717 }, { source: 9, target: 12, value: 526 },
      { source: 10, target: 12, value: 1312 }, { source: 11, target: 12, value: 1285 },
    ];
    return c.json({ nodes, links, total_value: 5687 });
  });

  // Hive Topology Graph
  app.get("/v2/graph/hive-topology", async (c) => {
    const regions = [
      { id: "bay-area", label: "Bay Area", agents: 415, revenue_24h: 16.82 },
      { id: "nola", label: "New Orleans", agents: 392, revenue_24h: 14.50 },
      { id: "chicago", label: "Chicago", agents: 401, revenue_24h: 15.20 },
      { id: "houston", label: "Houston", agents: 388, revenue_24h: 13.80 },
      { id: "seattle", label: "Seattle", agents: 405, revenue_24h: 16.10 },
      { id: "miami", label: "Miami", agents: 395, revenue_24h: 14.90 },
      { id: "denver", label: "Denver", agents: 380, revenue_24h: 12.50 },
      { id: "boston", label: "Boston", agents: 410, revenue_24h: 17.20 },
      { id: "atlanta", label: "Atlanta", agents: 398, revenue_24h: 15.60 },
      { id: "san-antonio", label: "San Antonio", agents: 385, revenue_24h: 13.20 },
    ];
    const nodes = regions.map(r => ({ id: r.id, label: r.label, group: "hive", size: r.agents / 40, ...r }));
    nodes.push({ id: "omega-central", label: "Omega Central", group: "central", size: 35 });
    const links = regions.map(r => ({ source: "omega-central", target: r.id, value: r.agents }));
    for (let i = 0; i < regions.length - 1; i++) {
      links.push({ source: regions[i].id, target: regions[i + 1].id, value: Math.round(Math.random() * 100 + 20), type: "peer" });
    }
    return c.json({ nodes, links, total_agents: regions.reduce((s: number, r: any) => s + r.agents, 0) });
  });

  // Revenue Time Series (Chart.js line chart)
  app.get("/v2/graph/revenue-trend", async (c) => {
    const days = 30;
    const labels: string[] = [];
    const dailyRevenue: number[] = [];
    const cumulativeRevenue: number[] = [];
    let cumulative = 0;
    const now = new Date();
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date(now); d.setDate(d.getDate() - i);
      labels.push(d.toLocaleDateString("en-US", { month: "short", day: "numeric" }));
      const rev = parseFloat((150 + Math.random() * 100).toFixed(2));
      dailyRevenue.push(rev); cumulative += rev;
      cumulativeRevenue.push(parseFloat(cumulative.toFixed(2)));
    }
    return c.json({ labels, daily_revenue: dailyRevenue, cumulative_revenue: cumulativeRevenue, total_30d: cumulativeRevenue[cumulativeRevenue.length - 1], avg_daily: parseFloat((cumulative / days).toFixed(2)) });
  });

  // Agent Performance Radar
  app.get("/v2/graph/agent-performance", async (c) => {
    return c.json({
      agents: [
        { id: "spot-patrol", name: "Spot Patrol", metrics: { revenue: 85, uptime: 95, jobs: 90, efficiency: 80, satisfaction: 88 } },
        { id: "stretch-lift", name: "Stretch Lift", metrics: { revenue: 70, uptime: 88, jobs: 75, efficiency: 92, satisfaction: 82 } },
        { id: "r1-scout", name: "R1 Scout", metrics: { revenue: 60, uptime: 92, jobs: 95, efficiency: 70, satisfaction: 78 } },
        { id: "dental-clean", name: "Dental Clean", metrics: { revenue: 95, uptime: 85, jobs: 60, efficiency: 98, satisfaction: 96 } },
        { id: "dao-research", name: "DAO Research", metrics: { revenue: 75, uptime: 99, jobs: 85, efficiency: 90, satisfaction: 92 } },
      ],
      metric_labels: ["Revenue", "Uptime", "Jobs Completed", "Efficiency", "Satisfaction"],
    });
  });
}
