"""Bausteine fuer die Alexa-Fassung der KiStadt Sicherheits-News.

KiStadt Sicherheits-News von Evelyn Störzner, kischild.de
Copyright (c) 2026 Evelyn Störzner. Alle Rechte vorbehalten.

Festgelegt mit Evelyn am 10.11.2026:
- Ansage: "K I Stadt Sicherheits-News im <Monat> <Jahr in Worten>."
- Zwischen den Meldungen wechselnde Ueberleitungen statt Zaehlung:
  eine fuer den Anfang, wechselnde fuer die Mitte, eine fuer die letzte Meldung.
- Am Ende einmal "Hör bald wieder rein."
- Die Woche (Runde) beginnt mittwochs um 0 Uhr (Berlin).
"""
import datetime as dt
import re
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")

MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
          "August", "September", "Oktober", "November", "Dezember"]

FLOSKELN_ANFANG = [
    "Den Anfang macht:",
    "Zuerst:",
    "Ganz oben auf der Liste:",
    "Beginnen wir mit:",
]
FLOSKELN_MITTE = [
    "Außerdem wurde bekannt:",
    "Ebenfalls aktuell:",
    "Auch das ist wichtig:",
    "Weiter geht es mit:",
    "Daneben gemeldet:",
    "Eine weitere Meldung:",
    "Ein anderes Thema:",
    "Auch hier lohnt sich ein genauer Blick:",
    "Ebenfalls neu:",
    "Dazu kommt:",
    "Ein weiterer Hinweis:",
    "Und noch etwas:",
    "Ebenfalls gemeldet:",
    "Wechseln wir das Thema:",
    "Auch das solltest du wissen:",
]
FLOSKELN_ENDE = [
    "Und zum Schluss:",
    "Als letzte Meldung:",
    "Zum Abschluss noch:",
    "Bleibt noch eine Meldung:",
]

_EINER = ["", "ein", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun"]
_ZEHN_BIS_19 = ["zehn", "elf", "zwölf", "dreizehn", "vierzehn", "fünfzehn",
                "sechzehn", "siebzehn", "achtzehn", "neunzehn"]
_ZEHNER = ["", "", "zwanzig", "dreißig", "vierzig", "fünfzig",
           "sechzig", "siebzig", "achtzig", "neunzig"]


def _unter_hundert(n):
    if n == 0:
        return ""
    if n == 1:
        return "eins"
    if n < 10:
        return _EINER[n]
    if n < 20:
        return _ZEHN_BIS_19[n - 10]
    z, e = divmod(n, 10)
    return (_EINER[e] + "und" if e else "") + _ZEHNER[z]


def jahr_in_worten(jahr):
    """2026 -> zweitausendsechsundzwanzig (fuer Jahre 2000 bis 2999)."""
    if not 2000 <= jahr <= 2999:
        raise ValueError("Jahr ausserhalb 2000-2999")
    rest = jahr - 2000
    h, r = divmod(rest, 100)
    teil = (_EINER[h] + "hundert" if h else "") + _unter_hundert(r)
    return "zweitausend" + teil


def ansage(jetzt):
    lokal = jetzt.astimezone(BERLIN)
    return f"K I Stadt Sicherheits-News im {MONATE[lokal.month - 1]} {jahr_in_worten(lokal.year)}."


def rundenstart(jetzt):
    """Beginn der laufenden Woche: letzter Mittwoch 0 Uhr Berlin (als UTC)."""
    lokal = jetzt.astimezone(BERLIN)
    tage = (lokal.weekday() - 2) % 7          # Montag=0, Mittwoch=2
    tag = (lokal - dt.timedelta(days=tage)).date()
    return dt.datetime(tag.year, tag.month, tag.day, tzinfo=BERLIN).astimezone(dt.timezone.utc)


# Zeichen, bei denen die Vorlesestimme laut Amazon unberechenbar wird
_ERSETZEN = [
    (re.compile(r"\s[–—-]\s"), ", "),        # Gedankenstrich als Pause -> Komma
    (re.compile(r"[–—]"), "-"),
    (re.compile(r"…|\.\.\."), "."),
    (re.compile(r"[„“”\"«»‚‘’]"), ""),
    (re.compile(r"\s*&\s*"), " und "),
    (re.compile(r"\s*%"), " Prozent"),
    (re.compile(r"[()\[\]{}*#_|<>]"), " "),
    (re.compile(r"\s+"), " "),
]


def saeubern(text):
    for muster, ersatz in _ERSETZEN:
        text = muster.sub(ersatz, text)
    text = re.sub(r"\s+([,.!?:;])", r"\1", text)
    return text.strip()
