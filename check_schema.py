import sqlite3, os, sys

def check_db(path):
    if not os.path.exists(path):
        return
    try:
        c = sqlite3.connect(path).cursor()
        count = c.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0]
        if count > 0:
            rows = c.execute("SELECT id, username, package, price FROM subscriptions LIMIT 2").fetchall()
            print(f"\n*** FOUND DATA ({count} subscribers): {os.path.abspath(path)}")
            for r in rows:
                print("   ", dict(zip(["id","username","package","price"], r)))
        else:
            print(f"  empty: {os.path.abspath(path)}")
    except Exception as e:
        print(f"  error ({e}): {path}")

# Load DB_PATH from web/backend/.env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "backend", ".env")
db_from_env = None
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("DB_PATH="):
                db_from_env = stripped.split("=", 1)[1].strip()
                break

print(f"DB_PATH in .env: {db_from_env}")
print("\nScanning all GSH-related databases...\n")

candidates = [
    db_from_env,
    "OnDemand_subscriptions.db",
    r"C:\Users\stunna\Documents\GSH\OnDemand_subscriptions.db",
    r"C:\Users\stunna\Documents\GSH\db\OnDemand_subscriptions.db",
    r"C:\Users\stunna\Documents\GSH\db\OnDemand_subscriptions_backup.db",
    r"C:\Users\stunna\Documents\Guardian Hosting 4.0\OnDemand_subscriptions.db",
]

# Also scan GSH directory tree
base = r"C:\Users\stunna\Documents\GSH"
if os.path.exists(base):
    for root, dirs, files in os.walk(base):
        for f in files:
            if f.endswith(".db"):
                candidates.append(os.path.join(root, f))

seen = set()
for path in candidates:
    if path and path not in seen:
        seen.add(path)
        check_db(path)
