import re
import phonenumbers

def extract_emails(text):
    """Findet alle E-Mail-Adressen in einem Text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    return list(set(emails))  # Duplikate entfernen

def extract_phone_numbers(text, region="DE"):
    """Findet alle Telefonnummern in einem Text."""
    phones = []
    for match in phonenumbers.PhoneNumberMatcher(text, region):
        phones.append(phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
    return list(set(phones))

def extract_contact_info(text):
    """Kombiniert E-Mail und Telefonnummern-Suche."""
    emails = extract_emails(text)
    phones = extract_phone_numbers(text)
    return {
        "emails": emails,
        "phones": phones
    }

def clean_text(text):
    """Entfernt HTML, überflüssige Leerzeichen usw."""
    text = re.sub(r"<.*?>", "", text)  # HTML-Tags löschen
    text = re.sub(r"\s+", " ", text)   # Mehrere Leerzeichen zusammenfassen
    return text.strip()
