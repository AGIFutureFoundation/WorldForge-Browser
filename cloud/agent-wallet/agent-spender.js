/**
 * WorldForge Agent x402 Spending Client
 *
 * Each hive agent gets a budget, per-request cap, and approved service list.
 * Payments over approval_threshold_usd require human sign-off.
 *
 * Usage:
 *   import { createAgentFetcher } from "./agent-spender.js";
 *   const fetch = createAgentFetcher("bay-area-training", agentNetwork, signer);
 *   const res = await fetch("https://datasets-api.worldforge.workers.dev/v1/episodes/...");
 */
import { x402Fetch } from "@x402/fetch";

const DEFAULT_BASE = "https://datasets-api.worldforge.workers.dev";

export function createAgentFetcher(hiveId, agentNetwork, signer) {
  const hive = agentNetwork.hives[hiveId];
  if (!hive) throw new Error(`Unknown hive: ${hiveId}`);
  const cfg = hive.x402;

  let spentToday = 0;
  const spentLog = [];

  async function agentFetch(url, opts = {}) {
    const parsed = new URL(url, DEFAULT_BASE);
    const price = estimatePrice(parsed.pathname);

    if (spentToday + price > cfg.budget_daily_usd) {
      throw new Error(`Daily budget exceeded: $${spentToday.toFixed(3)} + $${price.toFixed(3)} > $${cfg.budget_daily_usd}`);
    }
    if (price > cfg.budget_per_request_usd) {
      throw new Error(`Per-request cap exceeded: $${price.toFixed(3)} > $${cfg.budget_per_request_usd}`);
    }
    if (!cfg.approved_services.some((s) => parsed.hostname.includes(s))) {
      throw new Error(`Service not approved: ${parsed.hostname}`);
    }
    if (price > (agentNetwork.approval_threshold_usd || 1.0)) {
      throw new Error(`Human approval required for $${price.toFixed(2)}`);
    }

    const res = await x402Fetch(url, { ...opts, signer, maxPrice: `$${price.toFixed(3)}` });
    spentToday += price;
    spentLog.push({ url: parsed.pathname, price, ts: Date.now() });
    return res;
  }

  return {
    fetch: agentFetch,
    get spentToday() { return spentToday; },
    get log() { return [...spentLog]; },
    resetDaily() { spentToday = 0; spentLog.length = 0; },
    config: cfg,
  };
}

function estimatePrice(pathname) {
  if (pathname.startsWith("/v1/episodes/")) return 0.01;
  if (pathname.startsWith("/v1/streams/")) return 0.01;
  if (pathname === "/v1/packs/dental") return 10.0;
  if (pathname.startsWith("/v1/packs/")) return 2.0;
  return 0.0;
}