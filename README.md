# KiStadt Sicherheits-News

Meldungen zur KI-Sicherheit von Evelyn Störzner, [kischild.de](https://kischild.de/).

Dieses Fach enthält nur freigegebene, öffentliche Meldungen. Keine Zugangsdaten, nichts Privates.

## So funktioniert es

1. Neue Meldungen kommen als Vorschlag (Pull Request) in `data/meldungen.json`.
2. Evelyn liest sie und gibt frei (Merge). Nur sie darf freigeben.
3. Danach baut GitHub automatisch:
   - die News-Seite (erreichbar über news.kischild.de)
   - `feed.json`, die Nachrichten-Datei für den Alexa-Skill „KiStadt Sicherheits-News“
4. Gibt es in den letzten Tagen keine Meldung, liest Alexa eine Platzhalter-Meldung vor.

## Ablauf für Alexa (festgelegt mit Evelyn, zuletzt 26.11.2026)

- Mittwochs gibt Evelyn 9 Meldungen frei.
- Am Mittwoch liest Alexa 3 davon vor. Donnerstag bis Dienstag kommt jeden Morgen um 5 Uhr eine dazu.
- Die neueste steht immer oben. Alexa spielt höchstens 5 Meldungen, die älteste fällt weg.
- Alles bleibt in der eigenen Woche, nichts rutscht in die nächste Woche (`einplanen.py`).
- Die Meldungen lassen sich jederzeit wieder anhören: Die Kennungen wechseln jede Stunde.
- Der Bau läuft nach jeder Freigabe, jede Stunde und zusätzlich jeden Morgen kurz nach 5 Uhr über eine geplante Aufgabe.
- Alexa bekommt alle Meldungen in einem einzigen Eintrag, damit die Reihenfolge immer stimmt: akut zuerst, dann die aktuellste Meldung oben (nach Datum, wie im Dashboard). Eingeplant wird von alt nach neu, so ist die täglich neue Meldung auch die aktuellste.
- Ansage: „Ka Ih Stadt Sicherheits-News im <Monat> <Jahr>.“, wechselnde Überleitungen, am Ende einmal „Alle genannten Marken gehören ihren Herstellern. Hör bald wieder rein.“ (`alexa_text.py`, `build.py`).
- Die Hör-Fassung nennt die betroffene App, den Dienst oder die Firma und die Behörde mit Namen. Keine Medien, keine Webadressen.
- Quellen nur: Behörden, Gesetze, Studien, Forscher, die betroffene Firma selbst und The Hacker News.
- Die News-Seite trägt unten denselben Marken-Satz.
- Einmal raus ist raus: Eine Meldung, die schon im Fach liegt, wird nicht noch einmal eingeplant.
- Die News-Seite zeigt alle freigegebenen Meldungen sofort, nach Datum sortiert, die neueste oben.

`build.py` prüft jede Meldung (Pflichtfelder, Quellen, Schlusssatz der Hör-Fassung) und bricht ab, wenn etwas fehlt. So geht nie etwas Kaputtes online.

© 2026 Evelyn Störzner. Alle Rechte vorbehalten. Die Texte dürfen nicht ohne Erlaubnis übernommen werden.
