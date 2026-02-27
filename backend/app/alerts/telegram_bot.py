# backend/app/alerts/telegram_bot.py
import os
import asyncio
import json
import logging
from telegram import Bot
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

async def start_alert_bot():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

    if not token or not chat_id:
        logger.error("Telegram credentials missing")
        return

    bot = Bot(token=token)
    redis = await aioredis.from_url(redis_url)
    pubsub = redis.pubsub()
    await pubsub.subscribe("anza:alerts")

    logger.info("Alert Bot Worker started...")
    async for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                alert = json.loads(message['data'])
                text = f"🚨 *ANZA ALERT*: {alert.get('symbol')} - {alert.get('message')}"
                await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Alert Error: {e}")

if __name__ == "__main__":
    asyncio.run(start_alert_bot())
