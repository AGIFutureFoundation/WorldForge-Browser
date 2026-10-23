#!/usr/bin/env python3
"""Expand agent network with monetization capabilities."""
import json
import hashlib

# Load existing agent network
with open("earth/agent_network.json") as f:
    agent_net = json.load(f)

# Update each world's agents with monetization
for world_slug, world_data in agent_net["worlds"].items():
    for agent in world_data.get("agents", []):
        # Add monetization fields
        agent_id = agent["id"]
        agent["monetization"] = {
            "x402_enabled": True,
            "wallet_address": f"0x{hashlib.sha256((agent_id + '-wallet').encode()).hexdigest()[:40]}",
            "price_per_hour_usd": agent.get("price_per_hour_usd", 0.05),
            "revenue_share_pct": 15,
            "accepted_currencies": ["USDC"],
            "network": "base",
        }
        agent["services"] = [
            {"type": agent["task"], "price_per_hour_usd": agent.get("price_per_hour_usd", 0.05)},
            {"type": "data_sale", "price_per_message_usd": 0.0001},
            {"type": "world_access", "price_per_hour_usd": 0.05},
        ]

# Update hives with monetization
for hive_slug, hive_data in agent_net["hives"].items():
    hive_data["monetization"] = {
        "x402_enabled": True,
        "wallet_address": hive_data["x402"]["address"],
        "budget_daily_usd": hive_data["x402"]["budget_daily_usd"],
        "budget_per_request_usd": hive_data["x402"]["budget_per_request_usd"],
        "revenue_share_pct": hive_data["x402"]["revenue_share_pct"],
        "approved_services": hive_data["x402"]["approved_services"],
    }
    hive_data["economy"] = {
        "total_agents": len(hive_data.get("agents", [])),
        "active_agents": len(hive_data.get("agents", [])),
        "daily_revenue_usd": 0.0,
        "monthly_revenue_usd": 0.0,
    }

# Add global economy config
agent_net["economy"] = {
    "version": "2.0.0",
    "network": "base",
    "currency": "USDC",
    "facilitator": "https://x402.org/facilitator",
    "recipient": "0xD1D5965dB771d95725C08d9Eaf0083Ed0b7D9CDC",
    "pricing": {
        "world_access_1h": 0.05,
        "world_access_24h": 0.50,
        "world_access_7d": 2.00,
        "world_access_30d": 5.00,
        "agent_service_per_hour": 0.10,
        "data_per_message": 0.0001,
        "data_per_episode": 0.01,
        "data_per_hour": 0.50,
    },
    "revenue_share_pct": 15,
    "payout_threshold_usd": 1.00,
    "payout_interval": "daily",
}

# Save
with open("earth/agent_network.json", "w") as f:
    json.dump(agent_net, f, indent=2)

print(f"Updated {len(agent_net['worlds'])} worlds with monetization")
print(f"Economy config: {agent_net['economy']['pricing']}")
