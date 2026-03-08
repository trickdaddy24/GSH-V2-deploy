import sqlite3, os
db_path = os.getenv("DB_PATH", "OnDemand_subscriptions.db")
c = sqlite3.connect(db_path).cursor()
print("subscriptions:", [r[1] for r in c.execute("PRAGMA table_info(subscriptions)")])
print("billing_history:", [r[1] for r in c.execute("PRAGMA table_info(billing_history)")])
