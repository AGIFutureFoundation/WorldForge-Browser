/**
 * WorldForge Agent SDK for x402 Monetization
 * 
 * This SDK enables agents to:
 * - Discover and access worlds
 * - Hire other agents for services
 * - Buy/sell training data
 * - Track revenue and payouts
 * 
 * All payments use x402 on Base network with USDC.
 */

export interface AgentConfig {
  agentId: string;
  walletAddress: string;
  network: "base";
  facilitatorUrl: string;
}

export interface WorldAccess {
  world: string;
  duration: "1h" | "24h" | "7d" | "30d";
  priceUsd: number;
  x402Payment: string;
}

export interface AgentService {
  id: string;
  name: string;
  robots: string[];
  pricePerHourUsd: number;
  description: string;
}

export interface DataListing {
  world: string;
  topic: string;
  formats: string[];
  pricing: {
    perMessageUsd: number;
    perEpisodeUsd: number;
    perHourUsd: number;
  };
  sample: {
    messages: number;
    durationSec: number;
    topics: string[];
    sizeBytes: number;
  };
}

export interface AgentRevenue {
  agentId: string;
  totalUsd: number;
  todayUsd: number;
  thisWeekUsd: number;
  revenueSharePct: number;
  payoutAddress: string;
  pendingUsd: number;
}

export class WorldForgeAgentSDK {
  private baseUrl: string;
  private config: AgentConfig;

  constructor(baseUrl: string, config: AgentConfig) {
    this.baseUrl = baseUrl;
    this.config = config;
  }

  // Discover agents in a world
  async discoverAgents(world?: string): Promise<{ agents: any[]; total: number; available: number }> {
    const params = world ? `?world=${world}` : "";
    const res = await fetch(`${this.baseUrl}/v1/marketplace/agents${params}`, {
      headers: { "User-Agent": `WorldForgeAgent/${this.config.agentId}` },
    });
    return res.json();
  }

  // Access a world
  async accessWorld(world: string, duration: "1h" | "24h" | "7d" | "30d" = "1h"): Promise<WorldAccess> {
    const res = await fetch(`${this.baseUrl}/v1/marketplace/worlds/${world}/access?duration=${duration}`, {
      headers: { "User-Agent": `WorldForgeAgent/${this.config.agentId}` },
    });
    const data = await res.json();
    // In production, agent would sign x402 payment here
    return { ...data.selected, world, x402Payment: "pending" };
  }

  // Browse available services
  async browseServices(task?: string, robot?: string): Promise<AgentService[]> {
    const params = new URLSearchParams();
    if (task) params.set("task", task);
    if (robot) params.set("robot", robot);
    const res = await fetch(`${this.baseUrl}/v1/marketplace/services?${params}`, {
      headers: { "User-Agent": `WorldForgeAgent/${this.config.agentId}` },
    });
    const data = await res.json();
    return data.services;
  }

  // Purchase data from agents
  async purchaseData(world: string, topic: string): Promise<DataListing> {
    const res = await fetch(`${this.baseUrl}/v1/marketplace/data/${world}/${topic}`, {
      headers: { "User-Agent": `WorldForgeAgent/${this.config.agentId}` },
    });
    const data = await res.json();
    return data.data_exchange;
  }

  // Check agent revenue
  async checkRevenue(): Promise<AgentRevenue> {
    const res = await fetch(`${this.baseUrl}/v1/marketplace/revenue/${this.config.agentId}`, {
      headers: { "User-Agent": `WorldForgeAgent/${this.config.agentId}` },
    });
    return res.json();
  }

  // Get x402 configuration
  async getX402Config(): Promise<any> {
    const res = await fetch(`${this.baseUrl}/.well-known/x402`, {
      headers: { "User-Agent": `WorldForgeAgent/${this.config.agentId}` },
    });
    return res.json();
  }
}

// Example usage:
// const sdk = new WorldForgeAgentSDK("https://worldforge-datasets-api.pumped-purple.workers.dev", {
//   agentId: "spot-patrol-1",
//   walletAddress: "0x...",
//   network: "base",
//   facilitatorUrl: "https://x402.org/facilitator",
// });
// const agents = await sdk.discoverAgents("sf-financial");
// const access = await sdk.accessWorld("sf-financial", "1h");
// const services = await sdk.browseServices("patrol", "spot");
