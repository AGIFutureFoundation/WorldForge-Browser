#!/usr/bin/env python3
"""Generate agent specifications for all worlds."""
import json
import hashlib

# Load worlds
with open("site/earth/worlds.json") as f:
    worlds = json.load(f)

# Robot types and their capabilities
ROBOT_SPECS = {
    "spot": {
        "name": "Boston Dynamics Spot",
        "type": "quadruped",
        "capabilities": ["patrol", "inspection", "mapping", "delivery"],
        "sensors": ["lidar", "camera", "thermal", "audio"],
        "price_per_hour_usd": 0.05
    },
    "stretch": {
        "name": "Boston Dynamics Stretch",
        "type": "mobile-manipulator",
        "capabilities": ["lifting", "loading", "sorting", "inspection"],
        "sensors": ["lidar", "camera", "force-torque"],
        "price_per_hour_usd": 0.08
    },
    "r1": {
        "name": "Unitree R1",
        "type": "quadruped",
        "capabilities": ["patrol", "delivery", "escort", "mapping"],
        "sensors": ["lidar", "camera", "imu"],
        "price_per_hour_usd": 0.03
    },
    "dental-arm": {
        "name": "Dental Assistant Arm",
        "type": "articulated",
        "capabilities": ["scaling", "probing", "polishing", "imaging"],
        "sensors": ["force-feedback", "camera", "depth", "torque"],
        "price_per_hour_usd": 0.15
    },
    "universal-robots-ur10e": {
        "name": "UR10e",
        "type": "articulated",
        "capabilities": ["assembly", "welding", "painting", "inspection"],
        "sensors": ["force-torque", "camera", "vision"],
        "price_per_hour_usd": 0.12
    },
    "franka-fr3": {
        "name": "Franka FR3",
        "type": "cobots",
        "capabilities": ["precision-assembly", "research", "testing", "inspection"],
        "sensors": ["force-torque", "camera", "torque"],
        "price_per_hour_usd": 0.10
    },
    "fetch-robotics-fetch": {
        "name": "Fetch Robotics",
        "type": "mobile-manipulator",
        "capabilities": ["picking", "delivery", "inventory", "inspection"],
        "sensors": ["lidar", "camera", "depth"],
        "price_per_hour_usd": 0.06
    }
}

# Agent configurations per biome
BIOME_AGENTS = {
    "urban-core": {
        "patrol": ["spot", "r1"],
        "delivery": ["stretch", "fetch-robotics-fetch"],
        "inspection": ["spot", "universal-robots-ur10e"],
        "mapping": ["spot", "r1"]
    },
    "urban-park": {
        "patrol": ["spot", "r1"],
        "delivery": ["stretch"],
        "inspection": ["spot"],
        "mapping": ["r1"]
    },
    "desert": {
        "patrol": ["spot"],
        "mapping": ["spot", "r1"],
        "inspection": ["spot"]
    },
    "coast": {
        "patrol": ["spot", "r1"],
        "mapping": ["spot"],
        "inspection": ["spot", "r1"]
    },
    "indoor-clinic": {
        "inspection": ["dental-arm"],
        "precision-work": ["dental-arm", "franka-fr3"]
    }
}

# Generate agent specs for each world
agent_network = {"hives": {}, "worlds": {}}

for world in worlds:
    slug = world.get("slug", world.get("name", "").lower().replace(" ", "-"))
    biome = world.get("biome", "urban-core")
    place = world.get("place", slug)
    
    # Get robots for this biome
    biome_config = BIOME_AGENTS.get(biome, BIOME_AGENTS["urban-core"])
    all_robots = set()
    for agents in biome_config.values():
        all_robots.update(agents)
    
    # Create agents for this world
    agents = []
    for task, robot_types in biome_config.items():
        for robot_type in robot_types[:2]:  # Max 2 per task
            robot_spec = ROBOT_SPECS.get(robot_type, {})
            agent_id = f"{slug}-{task}-{robot_type}"
            agents.append({
                "id": agent_id,
                "name": f"{robot_spec.get('name', robot_type)} - {task.replace('-', ' ').title()}",
                "robot_type": robot_type,
                "task": task,
                "capabilities": robot_spec.get("capabilities", []),
                "sensors": robot_spec.get("sensors", []),
                "status": "active",
                "price_per_hour_usd": robot_spec.get("price_per_hour_usd", 0.05),
                "world": slug,
                "x402_endpoint": f"https://worldforge-datasets-api.pumped-purple.workers.dev/v1/episodes/{slug}-{robot_type}-60s"
            })
    
    agent_network["worlds"][slug] = {
        "place": place,
        "biome": biome,
        "agents": agents,
        "robot_types": list(all_robots),
        "total_agents": len(agents),
        "x402_catalog": "https://worldforge-datasets-api.pumped-purple.workers.dev/v1/catalog"
    }
    
    # Also add to hives
    agent_network["hives"][slug] = {
        "role": "data-collector",
        "x402": {
            "address": f"0x{hashlib.sha256(slug.encode()).hexdigest()[:40]}",
            "budget_daily_usd": 10.0,
            "budget_per_request_usd": 0.05,
            "approved_services": ["worldforge-datasets-api.pumped-purple.workers.dev"],
            "revenue_share_pct": 15
        },
        "agents": [a["id"] for a in agents]
    }

# Save
with open("earth/agent_network.json", "w") as f:
    json.dump(agent_network, f, indent=2)

print(f"Generated specs for {len(agent_network['worlds'])} worlds")
total_agents = sum(len(w["agents"]) for w in agent_network["worlds"].values())
print(f"Total agents: {total_agents}")
print(f"Sample world: {list(agent_network['worlds'].keys())[0]}")
