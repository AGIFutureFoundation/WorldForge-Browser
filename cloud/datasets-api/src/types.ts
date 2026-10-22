export interface Env {
  DB: D1Database;
  R2: R2Bucket;
  PAY_TO: string;
  NETWORK: string;
  FACILITATOR_URL: string;
  ADMIN_SECRET: string;
}

export interface RunEntry {
  run_id: string;
  robot: string;
  world: string;
  region: string;
  duration_sec: number;
  message_count: number;
  jsonl_size: number;
  parquet_size: number;
  sha256: string;
  price_usd: number;
  tier: string;
  description: string;
  tags?: string[];
  files: Record<string, string>;
}

export interface Manifest {
  version: string;
  generated_at: string;
  total_runs: number;
  total_size_bytes: number;
  pricing: Record<string, { price_usd: number }>;
  runs: RunEntry[];
}

export interface PaymentRecord {
  id: number;
  tx_hash: string;
  buyer: string;
  amount_usd: number;
  item_id: string;
  item_type: string;
  created_at: string;
}