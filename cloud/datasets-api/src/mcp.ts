import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { withX402, type X402Config } from "agents/x402";
import { z } from "zod";

const X402_CONFIG: X402Config = {
  network: "base",
  recipient: "0xD1D5965dB771d95725C08d9Eaf0083Ed0b7D9CDC",
  facilitator: { url: "https://x402.org/facilitator" },
};

const MANIFEST_URL = "https://raw.githubusercontent.com/AGIFutureFoundation/WorldForge-Browser/main/datasets/worldforge-ros-training/manifest.json";

export function createMcpServer(): McpServer {
  const server = withX402(new McpServer({ name: "WorldForgeDatasets", version: "1.0.0" }), X402_CONFIG);

  // Free: search episodes
  server.tool("search_episodes", "Search available training episodes", {
    robot: z.string().optional().describe("Robot type: spot, stretch, r1, dental-arm"),
    world: z.string().optional().describe("World slug"),
    region: z.string().optional().describe("Region: bay-area, nola, dental"),
  }, async ({ robot, world, region }) => {
    const res = await fetch(MANIFEST_URL);
    if (!res.ok) return { content: [{ type: "text", text: "Manifest unavailable" }] };
    const manifest = await res.json() as any;
    let runs = manifest.runs;
    if (robot) runs = runs.filter((r: any) => r.robot === robot);
    if (world) runs = runs.filter((r: any) => r.world === world);
    if (region) runs = runs.filter((r: any) => r.region === region);
    return { content: [{ type: "text", text: JSON.stringify(runs.map((r: any) => ({ id: r.run_id, robot: r.robot, world: r.world, price: r.price_usd })), null, 2) }] };
  });

  // Free: dataset card
  server.tool("dataset_card", "Get dataset overview and pricing", {}, async () => {
    const res = await fetch(MANIFEST_URL);
    if (!res.ok) return { content: [{ type: "text", text: "Manifest unavailable" }] };
    const m = await res.json() as any;
    return { content: [{ type: "text", text: `Total runs: ${m.total_runs}\nSize: ${m.total_size_bytes} bytes\nPricing: ${JSON.stringify(m.pricing)}` }] };
  });

  // Paid: get episode ($0.01)
  server.paidTool("get_episode", "Download a single training episode", 0.01, {
    run_id: z.string().describe("Episode run_id from search_episodes"),
    format: z.enum(["jsonl", "parquet"]).default("jsonl"),
  }, {}, async ({ run_id, format }) => {
    const res = await fetch(MANIFEST_URL);
    if (!res.ok) return { content: [{ type: "text", text: "Manifest unavailable" }] };
    const manifest = await res.json() as any;
    const entry = manifest.runs.find((r: any) => r.run_id === run_id);
    if (!entry) return { content: [{ type: "text", text: `Episode not found: ${run_id}` }] };
    return { content: [{ type: "text", text: `Episode: ${run_id}\nRobot: ${entry.robot}\nMessages: ${entry.message_count}\nFile: ${entry.files[format]}\nDownload: /v1/episodes/${run_id}?format=${format}` }] };
  });

  // Paid: get stream slice ($0.002)
  server.paidTool("get_stream_slice", "Get a filtered slice of a data stream", 0.002, {
    run_id: z.string(),
    topic: z.string().describe("ROS topic to filter"),
    minutes: z.number().default(1),
  }, {}, async ({ run_id, topic, minutes }) => {
    return { content: [{ type: "text", text: `Stream slice for ${run_id}, topic=${topic}, ${minutes}min\nAccess: /v1/streams/${run_id}?topic=${topic}&minutes=${minutes}` }] };
  });

  // Paid: generate episode ($0.25)
  server.paidTool("generate_episode", "Generate custom synthetic training data", 0.25, {
    robot: z.string().describe("Robot type"),
    world: z.string().describe("World slug"),
    duration_sec: z.number().default(60),
  }, {}, async ({ robot, world, duration_sec }) => {
    return { content: [{ type: "text", text: `Custom generation queued: ${robot} in ${world} for ${duration_sec}s\nStatus: /v1/generate/status (poll)` }] };
  });

  return server;
}