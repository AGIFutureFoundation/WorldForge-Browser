-- Migration 001: Create payments table
CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tx_hash TEXT NOT NULL,
  buyer TEXT NOT NULL,
  amount_usd REAL NOT NULL,
  item_id TEXT NOT NULL,
  item_type TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_payments_item ON payments(item_type, item_id);
CREATE INDEX IF NOT EXISTS idx_payments_buyer ON payments(buyer);
CREATE INDEX IF NOT EXISTS idx_payments_created ON payments(created_at);