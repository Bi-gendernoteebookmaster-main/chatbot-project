# main.py
import os
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
from dotenv import load_dotenv

from database import init_db, save_message


# Загрузка переменных окружения
load_dotenv()


# Получение настроек из .env
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN must be set in .env")


# Создание приложения FastAPI
app = FastAPI(title="Telegram Chatbot", version="1.0")


@app.on_event("startup")
async def on_startup():
    """Инициализация базы данных при запуске."""
    await init_db()
    async with httpx.AsyncClient() as client:
        webhook_response = await client.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
            json={"url": WEBHOOK_URL}
        )
        if not webhook_response.json().get("ok"):
            print("⚠️ Не удалось установить Telegram webhook")


@app.get("/")
async def root():
    """Базовый маршрут для проверки работоспособности."""
    return {"message": "Telegram chatbot is running!"}


@app.get("/health")
async def health_check():
    """Эндпоинт для проверки здоровья сервиса."""
    return {"status": "ok"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Обработка входящих обновлений от Telegram."""
    try:
        payload: Dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if "message" not in payload:
        return JSONResponse(content={"status": "ignored"}, status_code=200)

    message = payload["message"]
    user_id = message["from"]["id"]
    username = message["from"].get("username", "Unknown")
    message_text = message.get("text", "")

    if not message_text:
        return JSONResponse(content={"status": "no_text"}, status_code=200)

    # Сохранение сообщения в БД
    await save_message(user_id, username, message_text)

    # Отправка ответа пользователю
    response_text = f"Echo: {message_text}"
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": user_id, "text": response_text}
        )

    return JSONResponse(content={"status": "ok"}, status_code=200)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
