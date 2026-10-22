import type { Hono } from "hono";

export function registerDataRoutes(app: Hono) {
  app.get("/v1/episodes/:id", async (c) => {
    const id = c.req.param("id");
    const fmt = c.req.query("format") || "jsonl";
    const res = await fetch("https://raw.githubusercontent.com/tempgithubhelp/WorldForge-Browser/main/datasets/worldforge-ros-training/manifest.json");
    if (!res.ok) return c.json({ error: "manifest_unavailable" }, 503);
    const manifest = await res.json() as any;
    const entry = manifest.runs.find((r: any) => r.run_id === id);
    if (!entry) return c.json({ error: "episode_not_found", id }, 404);
    const fname = entry.files?.[fmt === "parquet" ? "parquet" : "jsonl"];
    if (!fname) return c.json({ error: "format_not_found", fmt }, 400);
    const ghRes = await fetch(`https://raw.githubusercontent.com/tempgithubhelp/WorldForge-Browser/main/datasets/worldforge-ros-training/samples/${fname}`);
    if (!ghRes.ok) return c.json({ error: "file_not_found", file: fname }, 404);
    const body = await ghRes.arrayBuffer();
    const ct = fmt === "parquet" ? "application/octet-stream" : "application/x-ndjson";
    return c.body(body, { headers: { "content-type": ct } });
  });

  app.get("/v1/streams/:id", async (c) => {
    const id = c.req.param("id");
    const minutes = parseInt(c.req.query("minutes") || "1");
    const topic = c.req.query("topic") || "";
    return c.json({ run_id: id, minutes, topic, price_estimate: `$${(0.01 * minutes).toFixed(3)}` });
  });

  app.get("/v1/packs/:region", async (c) => {
    return c.json({ pack: c.req.param("region"), note: "Signed R2 URL after payment" });
  });

  app.get("/v1/packs/dental", async (c) => {
    return c.json({ pack: "unspoken-smiles-dental", description: "Scaler force, probe depth, tool position (5 min)", price_usd: 10.0 });
  });
}