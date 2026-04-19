"""
heartbeat.py — Sends a Telegram "still alive" message at a random time every 24 hours.
Runs as an asyncio background task started from main.py lifespan.
"""
import asyncio
import random
import logging
from notify import notify_telegram

logger = logging.getLogger("gsh.heartbeat")

MESSAGES = [
    "💚 GuardianStreams is alive and running.",
    "✅ GSH heartbeat — all systems operational.",
    "🛡️ GuardianStreams is up and watching.",
    "📡 GSH check-in — running normally.",
]


async def run_heartbeat() -> None:
    """Ping Telegram at a random time every 24 hours."""
    initial = random.randint(0, 28800)  # 0–8h before first ping
    logger.info("Heartbeat scheduled: first ping in %.1fh", initial / 3600)
    await asyncio.sleep(initial)

    while True:
        try:
            msg = random.choice(MESSAGES)
            sent = await asyncio.to_thread(notify_telegram, msg)
            logger.info("Heartbeat sent: %s", "ok" if sent else "skipped (not configured)")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Heartbeat error — will retry after delay")
        delay = random.randint(72000, 100800)  # 20–28h until next ping
        logger.info("Next heartbeat in %.1fh", delay / 3600)
        await asyncio.sleep(delay)
