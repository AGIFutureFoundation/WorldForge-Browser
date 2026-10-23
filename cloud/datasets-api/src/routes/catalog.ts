import type { Hono } from "hono";

export function registerCatalogRoutes(app: Hono) {
  app.get("/v1/catalog", async (c) => {
    const r2 = (c.env as any).R2;
    const obj = await r2.get("manifest.json");
    if (!obj) return c.json({ error: "manifest_unavailable" }, 503);
    const manifest = await obj.json() as any;
    return c.json({
      name: "WorldForge ROS Training Datasets",
      description: "Synthetic ROS 2 data from robot runs across 544 live worlds",
      formats: [".jsonl", ".parquet"],
      total_runs: manifest.total_runs,
      pricing: manifest.pricing,
      regions: [...new Set(manifest.runs.map((r: any) => r.region))],
      robots: [...new Set(manifest.runs.map((r: any) => r.robot))],
      runs: manifest.runs.map((r: any) => ({ id: r.run_id, robot: r.robot, world: r.world, region: r.region, duration_sec: r.duration_sec, messages: r.message_count, price_usd: r.price_usd, tier: r.tier, description: r.description, tags: r.tags || [] })),
    });
  });
  app.get("/v1/manifest", async (c) => {
    const r2 = (c.env as any).R2;
    const obj = await r2.get("manifest.json");
    if (!obj) return c.json({ error: "manifest_unavailable" }, 503);
    return c.body(await obj.text(), { headers: { "content-type": "application/json" } });
  });
  app.get("/v1/sample/:file", async (c) => {
    const file = c.req.param("file");
    const r2 = (c.env as any).R2;
    const obj = await r2.get(`samples/${file}`);
    if (!obj) return c.json({ error: "sample_not_found", file }, 404);
    const body = await obj.arrayBuffer();
    const ct = file.endsWith(".jsonl") ? "application/x-ndjson" : file.endsWith(".parquet") ? "application/octet-stream" : "application/json";
    return c.body(body, { headers: { "content-type": ct } });
  });
}