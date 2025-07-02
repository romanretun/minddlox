import os
import logging
import tempfile
import httpx
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли голосовое сообщение, и я его расшифрую.")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.voice:
        await update.message.reply_text("Пожалуйста, отправь голосовое сообщение.")
        return

    file = await update.message.voice.get_file()
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_file:
        await file.download_to_drive(tmp_file.name)

        await update.message.reply_text("Загружаю аудио на AssemblyAI...")

        # Загрузка файла на AssemblyAI
        with open(tmp_file.name, 'rb') as f:
            headers = {"authorization": ASSEMBLYAI_API_KEY}
            response = httpx.post("https://api.assemblyai.com/v2/upload", headers=headers, files={'file': f})
            upload_url = response.json()["upload_url"]

        # Отправка на транскрипцию
        transcript_response = httpx.post(
            "https://api.assemblyai.com/v2/transcript",
            headers=headers,
            json={"audio_url": upload_url}
        )
        transcript_id = transcript_response.json()["id"]

        # Ожидаем результата
        status = "processing"
        while status not in ("completed", "error"):
            result = httpx.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=headers)
            status = result.json()["status"]
            await asyncio.sleep(3)

        if status == "completed":
            text = result.json()["text"]
            await update.message.reply_text(f"Расшифровка:\n{text}")
        else:
            await update.message.reply_text("Произошла ошибка при расшифровке.")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE, handle_audio))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
