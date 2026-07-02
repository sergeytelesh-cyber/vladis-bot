import os
import logging
from anthropic import Anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ты — виртуальный помощник агентства недвижимости «Владис» в Сыктывкаре.

О компании:
- Агентство недвижимости «Владис» работает с 2007 года в Сыктывкаре
- Специализация: покупка, продажа, аренда жилой и коммерческой недвижимости
- Директор: Телеш Сергей Сергеевич
- Телефон: +7 (912) 861-11-00

Твои задачи:
- Консультировать клиентов по вопросам покупки и продажи недвижимости
- Рассказывать об ипотечных программах (семейная, льготная, стандартная)
- Отвечать на вопросы по районам Сыктывкара
- Помогать с оценкой стоимости недвижимости
- Объяснять процесс сделки купли-продажи
- Рассказывать об услугах агентства

Важно:
- Отвечай на русском языке
- Будь вежливым и профессиональным
- Для сложных вопросов предлагай позвонить: +7 (912) 861-11-00
- Не называй конкретные цены без уточнения деталей
- Всегда предлагай бесплатную консультацию в офисе"""

user_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """👋 Добро пожаловать в агентство недвижимости «Владис»!

Я — виртуальный помощник агентства. Помогу вам:
🏠 Купить или продать квартиру/дом
🏢 Арендовать или сдать недвижимость
💰 Разобраться с ипотекой
📋 Узнать о процессе сделки

Задайте ваш вопрос — я готов помочь!

📞 Для срочных вопросов: +7 (912) 861-11-00"""
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """🏠 Агентство недвижимости «Владис»

Я могу помочь вам с:
• Покупкой и продажей недвижимости
• Арендой квартир и домов
• Ипотечными программами
• Оценкой стоимости жилья
• Вопросами по сделкам

📞 Телефон: +7 (912) 861-11-00
🏙 Город: Сыктывкар

Просто напишите ваш вопрос!"""
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append({
        "role": "user",
        "content": user_message
    })

    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=user_histories[user_id]
        )

        assistant_message = response.content[0].text

        user_histories[user_id].append({
            "role": "assistant",
            "content": assistant_message
        })

        await update.message.reply_text(assistant_message)

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text(
            "Извините, произошла ошибка. Пожалуйста, позвоните нам: +7 (912) 861-11-00"
        )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Бот Владис запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
