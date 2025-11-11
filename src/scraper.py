import asyncio
import re
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os

load_dotenv()

# --- Hilfsfunktionen ---------------------------------------------------------


def clean_text(text):
    """Entfernt unnötige Leerzeichen und HTML-Elemente."""
    return re.sub(r"\s+", " ", text).strip()


def extract_contact_info(text):
    """Extrahiert Telefonnummern und E-Mail-Adressen aus Text."""
    phones = re.findall(r"\+?\d[\d\s/-]{6,}\d", text)
    emails = re.findall(r"[\w\.-]+@[\w\.-]+", text)
    return {"phones": phones, "emails": emails}


import json

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def save_listing(listing):
    """Speichert Einträge in der Supabase-Tabelle."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️ Supabase-Umgebungsvariablen fehlen! Bitte .env prüfen.")
        return

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "title": listing["title"],
        "url": listing["url"],
        "contact_name": listing["contact_name"],
        "phone": listing["phone"],
        "email": listing["email"],
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/listings",
        headers=headers,
        data=json.dumps(data),
    )

    if response.status_code in [200, 201]:
        print(f"✅ Gespeichert in Supabase: {listing['title']}")
    else:
        print(
            f"⚠️ Fehler beim Speichern in Supabase: {response.status_code} {response.text}"
        )


# --- Hauptfunktion -----------------------------------------------------------


async def scrape_ebay_kleinanzeigen():
    """Scraped Inserate und extrahiert Kontaktdaten."""
    base_url = "https://www.kleinanzeigen.de/s-hotel/apartments/k0"

    # Erste Seite abrufen
    print("🔍 Lade Inserate...")
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Beispiel: Extrahiere die ersten paar Links
    links = []
    for a in soup.select("a[href]"):
        href = a["href"]
        if href.startswith("/s-anzeige/"):
            links.append("https://www.kleinanzeigen.de" + href)

    print(f"➡️ {len(links)} Inserate gefunden. Starte Scraping...")

    # Durch Seiten mit Playwright gehen
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for link in links[:5]:  # Nur erste 5 für Testzwecke
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
                    "title": title,
                    "url": link,
                    "contact_name": contact_name,
                    "phone": phone,
                    "email": email,
                }

                save_listing(listing)

            except Exception as e:
                print(f"⚠️ Fehler bei {link}: {e}")

        await browser.close()


# --- Startpunkt --------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(scrape_ebay_kleinanzeigen())
