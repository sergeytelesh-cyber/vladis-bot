import os
import json
import logging
import httpx
import asyncio
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

SYSTEM_PROMPT = """Ты помощник агентства недвижимости Владис в Сыктывкаре. Работаем с 2007 года. Телефон: +7 (912) 861-11-00. Отвечай на русском, вежливо и профессионально."""

user_histories = {}

async def send_message(chat_id, text):
    async with httpx.AsyncClient() as c:
        await c.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text})

async def process_update(update):
    if "message" not in update:
        return
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    if not text:
        return
    if text == "/start":
        await send_message(chat_id, "Добро пожаловать в Владис! Задайте вопрос по недвижимости.\n📞 +7 (912) 861-11-00")
        return
    if chat_id not in user_histories:
        user_histories[chat_id] = []
    user_histories[chat_id].append({"role": "user", "content": text})
    if len(user_histories[chat_id]) > 20:
        user_histories[chat_id] = user_histories[chat_id][-20:]
    try:
        response = client.messages.create(model="claude-sonnet-4-6", max_tokens=1000, system=SYSTEM_PROMPT, messages=user_histories[chat_id])
        reply = response.content[0].text
        user_histories[chat_id].append({"role": "assistant", "content": reply})
        await send_message(chat_id, reply)
    except Exception as e:
        logger.error(f"Error: {e}")
        await send_message(chat_id, "Ошибка. Позвоните: +7 (912) 861-11-00")

async def main():
    offset = 0
    logger.info("Бот Владис запущен!")
    while True:
        try:
            async with httpx.AsyncClient(timeout=35) as c:
                r = await c.get(f"{BASE_URL}/getUpdates", params={"offset": offset, "timeout": 30})
                updates = r.json().get("result", [])
                for u in updates:
                    offset = u["update_id"] + 1
                    await process_update(u)
        except Exception as e:
            logger.error(f"Poll error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
