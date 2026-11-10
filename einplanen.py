#!/usr/bin/env python3
"""Plant freigegebene Meldungen in die Alexa-Warteschlange ein.

KiStadt Sicherheits-News von Evelyn Störzner, kischild.de
Copyright (c) 2026 Evelyn Störzner. Alle Rechte vorbehalten.

Aufruf:  python3 einplanen.py neue.json [--jetzt 2026-11-11T07:07:00+01:00]

neue.json: Liste von Meldungen im Format von data/meldungen.json, aber ohne
"veroeffentlicht". Das Skript vergibt den Freischalt-Zeitpunkt:

- Die ersten 3 Meldungen der Woche (ab Mittwoch 0 Uhr) starten sofort.
- Jede weitere kommt am naechsten Morgen um 5 Uhr dazu, eine pro Tag.
- Reihenfolge: Akut zuerst, dann die neuesten Meldungen.

Regel "einmal raus ist raus": Eine id, die schon in data/meldungen.json steht,
wird nicht noch einmal eingeplant (Ausnahme nur auf Evelyns ausdrücklichen
Wunsch im Chat: dann --nochmal <id> angeben).
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from alexa_text import BERLIN, rundenstart

ROOT = Path(__file__).resolve().parent
DATEI = ROOT / "data" / "meldungen.json"
START_ANZAHL = 3
UHRZEIT = 5          # 5 Uhr morgens; der Bau auf GitHub laeuft um 5:17 Uhr


def zeit(wert):
    t = dt.datetime.fromisoformat(wert)
    if t.tzinfo is None:
        raise SystemExit(f"FEHLER: Zeit ohne Zeitzone: {wert}")
    return t


def morgen_um_fuenf(tag):
    return dt.datetime(tag.year, tag.month, tag.day, UHRZEIT, tzinfo=BERLIN)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("neue")
    ap.add_argument("--jetzt")
    ap.add_argument("--nochmal", action="append", default=[])
    a = ap.parse_args()

    jetzt = zeit(a.jetzt) if a.jetzt else dt.datetime.now(BERLIN)
    jetzt = jetzt.astimezone(BERLIN).replace(microsecond=0)
    bestand = json.loads(DATEI.read_text(encoding="utf-8"))
    neue = json.loads(Path(a.neue).read_text(encoding="utf-8"))
    vorhanden = {m["id"] for m in bestand}

    schon_raus, einplanen = [], []
    for m in neue:
        if m["id"] in vorhanden and m["id"] not in a.nochmal:
            schon_raus.append(m["id"])
        else:
            einplanen.append(m)
    # Akut zuerst, dann die neuesten Meldungen
    einplanen.sort(key=lambda m: m["datum"], reverse=True)
    einplanen.sort(key=lambda m: not m.get("akut", False))
    if a.nochmal:
        bestand = [m for m in bestand if m["id"] not in a.nochmal]

    start = rundenstart(jetzt)
    diese_woche = [zeit(m["veroeffentlicht"]) for m in bestand if zeit(m["veroeffentlicht"]) >= start]
    plan = []
    for m in einplanen:
        anzahl = len(diese_woche)
        if anzahl < START_ANZAHL:
            t = jetzt - dt.timedelta(seconds=anzahl)            # sofort, feste Reihenfolge
        else:
            letzter_tag = max(diese_woche).astimezone(BERLIN).date()
            tag = max(letzter_tag, jetzt.date()) + dt.timedelta(days=1)
            t = morgen_um_fuenf(tag)
        diese_woche.append(t)
        eintrag = dict(m)
        eintrag["veroeffentlicht"] = t.isoformat()
        bestand.append(eintrag)
        plan.append((t, m["id"]))

    DATEI.write_text(json.dumps(bestand, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    for t, mid in plan:
        lokal = t.astimezone(BERLIN)
        print(f"EINGEPLANT {tage[lokal.weekday()]} {lokal:%d.%m. %H:%M} Uhr  {mid}")
    for mid in schon_raus:
        print(f"SCHON RAUS (nicht nochmal) {mid}")
    print(f"OK: {len(plan)} eingeplant, {len(schon_raus)} schon raus.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
