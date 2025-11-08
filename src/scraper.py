import os
import time
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import psycopg2
from psycopg2.extras import RealDictCursor
from helpers import extract_contact_info, clean_text
import requests

# ----------------------------------------------------------
# 1️⃣ .env laden
# ----------------------------------------------------------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ----------------------------------------------------------
# 2️⃣ Supabase / Postgres-Verbindung
# ----------------------------------------------------------
def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def save_listing(listing):
    conn = get_connection()
    cur = conn.cursor()

    # Tabelle anlegen, falls sie nicht existiert
    cur.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id SERIAL PRIMARY KEY,
            title TEXT,
            url TEXT UNIQUE,
            contact_name TEXT,
            phone TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # Eintrag speichern (nur wenn noch nicht vorhanden)
    cur.execute("""
        INSERT INTO listings (title, url, contact_name, phone, email)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (url) DO NOTHING
    """, (listing["title"], listing["url"], listing["contact_name"], listing["phone"], listing["email"]))

    conn.commit()
    cur.close()
    conn.close()

# ----------------------------------------------------------
# 3️⃣ Telegram-Benachrichtigung
# ----------------------------------------------------------
def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram nicht konfiguriert.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=data)

# ----------------------------------------------------------
# 4️⃣ Scraper-Logik (Beispiel: eBay Kleinanzeigen)
# ----------------------------------------------------------
async def scrape_ebay_kleinanzeigen():
    base_url = "https://www.kleinanzeigen.de"
    search_url = (
        "https://www.kleinanzeigen.de/s-wohnung-mieten/aparthotel/k0"
    )

    print("🔍 Starte eBay Kleinanzeigen-Scraper...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(search_url)
        await page.wait_for_timeout(4000)

        # Alle Inserate auf der Suchseite holen
        links = await page.eval_on_selector_all(
            "a.ellipsis",
            "elements => elements.map(el => el.href)"
        )

        print(f"✅ {len(links)} Inserate gefunden")

        for link in links[:10]:  # Begrenzung für Testzwecke
            try:
                await page.goto(link)
                await page.wait_for_timeout(2000)

                title = await page.title()
                html = await page.content()
                text = clean_text(html)
                contact_info = extract_contact_info(text)

                contact_name = None
                phone = contact_info["phones"][0] if contact_info["phones"] else None
                email = contact_info["emails"][0] if contact_info["emails"] else None

                listing = {
                    "title": title[:200],
                    "url": link,
                    "contact_name": contact_name,
                    "phone": phone,
                    "em
