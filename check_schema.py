import sqlite3, os, sys

# Load DB_PATH from web/backend/.env if present
env_path = os.path.join(os.path.dirname(__file__), "web", "backend", ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("DB_PATH="):
                os.environ["DB_PATH"] = line.split("=", 1)[1]

db_path = os.getenv("DB_PATH", "OnDemand_subscriptions.db")
print(f"Checking: {os.path.abspath(db_path)}")
print(f"File exists: {os.path.exists(db_path)}")

if not os.path.exists(db_path):
    print("ERROR: database file not found at that path")
    sys.exit(1)

c = sqlite3.connect(db_path).cursor()
print("subscriptions:", [r[1] for r in c.execute("PRAGMA table_info(subscriptions)")])
print("billing_history:", [r[1] for r in c.execute("PRAGMA table_info(billing_history)")])
