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

## Warteschlange für Alexa (seit 10.11.2026)

- `einplanen.py` vergibt jeder neuen Meldung ihren Freischalt-Zeitpunkt: mittwochs starten 3, danach kommt jeden Morgen um 5 Uhr eine dazu (bei 9 Meldungen bis Dienstag).
- Alexa spielt die 5 neuesten der laufenden Woche, die neueste zuerst. Mittwoch beginnt eine neue Woche.
- Ansage: „K I Stadt Sicherheits-News im <Monat> <Jahr>.“, dann wechselnde Überleitungen zwischen den Meldungen, am Ende einmal „Hör bald wieder rein.“ (`alexa_text.py`).
- Einmal raus ist raus: Eine Meldung, die schon im Fach liegt, wird nicht noch einmal eingeplant.
- Die News-Seite zeigt eine Meldung ab ihrem Freischalt-Tag.

`build.py` prüft jede Meldung (Pflichtfelder, Quellen, Schlusssatz der Hör-Fassung) und bricht ab, wenn etwas fehlt. So geht nie etwas Kaputtes online.

© 2026 Evelyn Störzner. Alle Rechte vorbehalten. Die Texte dürfen nicht ohne Erlaubnis übernommen werden.
