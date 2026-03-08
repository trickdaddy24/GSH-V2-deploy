import sqlite3, os, sys

# Load DB_PATH from web/backend/.env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "backend", ".env")
db_path = None

if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("DB_PATH="):
                db_path = stripped.split("=", 1)[1].strip()
                break

if not db_path:
    db_path = "OnDemand_subscriptions.db"
    print(f"WARNING: DB_PATH not found in .env — using default: {db_path}")
else:
    print(f"DB_PATH from .env: {db_path}")

print(f"Absolute path:    {os.path.abspath(db_path)}")
print(f"File exists:      {os.path.exists(db_path)}")

if not os.path.exists(db_path):
    print("ERROR: file not found")
    sys.exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("\n--- Schema ---")
print("subscriptions:", [r[1] for r in c.execute("PRAGMA table_info(subscriptions)")])
print("billing_history:", [r[1] for r in c.execute("PRAGMA table_info(billing_history)")])

print("\n--- Row counts ---")
print("Total rows:     ", c.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0])
print("is_active = 1:  ", c.execute("SELECT COUNT(*) FROM subscriptions WHERE is_active = 1").fetchone()[0])
print("is_active = 0:  ", c.execute("SELECT COUNT(*) FROM subscriptions WHERE is_active = 0").fetchone()[0])
print("is_active NULL: ", c.execute("SELECT COUNT(*) FROM subscriptions WHERE is_active IS NULL").fetchone()[0])

print("\n--- First 3 subscribers ---")
for row in c.execute("SELECT id, username, package, price, is_active FROM subscriptions LIMIT 3"):
    print(dict(row))

conn.close()
