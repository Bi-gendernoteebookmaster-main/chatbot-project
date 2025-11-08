# main.py - Telegram Bot with Google Sheets
import os
import asyncio
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN must be set in .env")

app = FastAPI(title="Telegram Chatbot", version="1.0")

# Google Sheets setup
def get_sheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "credentials.json", scope)
        client = gspread.authorize(creds)
        # Open your Google Sheet by name
        sheet = client.open("Telegram Messages").sheet1
        return sheet
    except Exception as e:
        print(f"Error accessing Google Sheet: {e}")
        return None

@app.get("/")
async def root():
    return {"message": "Telegram Bot with Google Sheets is running!"}

@app.post(f"/webhook/{TELEGRAM_BOT_TOKEN}")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook updates"""
    try:
        data = await request.json()
        message = data.get("message")
        
        if not message:
            return {"ok": True}
        
        user_id = message["from"]["id"]
        username = message["from"].get("username", "Unknown")
        text = message.get("text", "")
        
        # Save to Google Sheets
        sheet = get_sheet()
        if sheet:
            sheet.append_row([user_id, username, text])
            
        return {"ok": True}
    except Exception as e:
        print(f"Error: {e}")
        return {"ok": False}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
