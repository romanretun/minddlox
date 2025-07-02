import os
import logging
import tempfile
import asyncio
import nest_asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from openai import OpenAI

# Настройка ключей
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Настройка логов
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Инициализация OpenAI клиента
client = OpenAI(api_key=OPENAI_API_KEY)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли мне аудиофайл или голосовое сообщение, и я его расшифрую.")

# Обработка аудио
async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    print(f"Получено сообщение: {message}")  # Отладка

    file = None
    if message.voice:
        print("Тип: voice")
        file = await message.voice.get_file()
    elif message.audio:
        print("Тип: audio")
        file = await message.audio.get_file()
    elif message.document and message.document.mime_type.startswith("audio/"):
        print("Тип: document с аудио")
        file = await message.document.get_file()
    else:
        await message.reply_text("Пожалуйста, отправь голосовое, аудио или аудиодокумент.")
        return

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_file:
        await file.download_to_drive(tmp_file.name)
        await message.reply_text("Обрабатываю аудио...")

        try:
            with open(tmp_file.name, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            await message.reply_text(f"Расшифровка:\n\n{transcript.text}")
        except Exception as e:
            logging.exception("Ошибка при расшифровке:")
            await message.reply_text(f"Ошибка при расшифровке:\n\n{e}")

# Запуск бота
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_audio))  # ловим всё

    print("Бот запущен")
    await app.run_polling(close_loop=False)

# Точка входа
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
