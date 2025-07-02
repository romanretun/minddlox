import os
import logging
import tempfile
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
import nest_asyncio
import asyncio

# Получаем токены из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Инициализация клиента OpenAI с ключом
client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли мне аудиофайл, я его расшифрую.")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = None
    if update.message.voice:
        file = await update.message.voice.get_file()
    elif update.message.audio:
        file = await update.message.audio.get_file()
    else:
        await update.message.reply_text("Пожалуйста, отправь аудиофайл или голосовое сообщение.")
        return

    with tempfile.NamedTemporaryFile(suffix=".ogg") as tmp_file:
        await file.download_to_drive(tmp_file.name)

        await update.message.reply_text("Обрабатываю аудио...")

        try:
            with open(tmp_file.name, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-1",
                    language="ru"  # укажи язык, если нужно
                )
            text = transcript.text
            await update.message.reply_text(f"Расшифровка:\n\n{text}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка при расшифровке: {e}")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio))

    print("Бот запущен")
    await app.run_polling(close_loop=False)

if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(main())