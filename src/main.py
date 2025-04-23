from fastapi import FastAPI
from dotenv import load_dotenv
import httpx
import os

# Load dari .env (kalau lo pakai)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://nimmziebqmbzxexlpbpm.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")

app = FastAPI()

@app.get("/data/{table_name}")
async def get_table_data(table_name: str):
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": f"Gagal ambil data: {response.text}"}

    return response.json()
