import type { Hono } from "hono";

const MANIFEST_URL = "https://raw.githubusercontent.com/AGIFutureFoundation/WorldForge-Browser/main/datasets/worldforge-ros-training/manifest.json";

export function registerCatalogRoutes(app: Hono) {
  app.get("/v1/catalog", async (c) => {
    const res = await fetch(MANIFEST_URL);
    if (!res.ok) return c.json({ error: "manifest_unavailable" }, 503);
    const manifest = await res.json() as any;
    return c.json({
      name: "WorldForge ROS Training Datasets",
      description: "Synthetic ROS 2 data from robot runs across 80+ live worlds",
      formats: [".jsonl", ".parquet"],
      total_runs: manifest.total_runs,
      pricing: manifest.pricing,
      regions: [...new Set(manifest.runs.map((r: any) => r.region))],
      robots: [...new Set(manifest.runs.map((r: any) => r.robot))],
      runs: manifest.runs.map((r: any) => ({ id: r.run_id, robot: r.robot, world: r.world, region: r.region, duration_sec: r.duration_sec, messages: r.message_count, price_usd: r.price_usd, tier: r.tier, description: r.description, tags: r.tags || [] })),
    });
  });
  app.get("/v1/manifest", async (c) => {
    const res = await fetch(MANIFEST_URL);
    if (!res.ok) return c.json({ error: "manifest_unavailable" }, 503);
    return c.body(await res.text(), { headers: { "content-type": "application/json" } });
  });
  app.get("/v1/sample/:file", async (c) => {
    const file = c.req.param("file");
    const res = await fetch(`https://raw.githubusercontent.com/AGIFutureFoundation/WorldForge-Browser/main/datasets/worldforge-ros-training/samples/${file}`);
    if (!res.ok) return c.json({ error: "sample_not_found", file }, 404);
    const body = await res.arrayBuffer();
    const ct = file.endsWith(".jsonl") ? "application/x-ndjson" : file.endsWith(".parquet") ? "application/octet-stream" : "application/json";
    return c.body(body, { headers: { "content-type": ct } });
  });
}