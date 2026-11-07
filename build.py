#!/usr/bin/env python3
"""Baut aus data/meldungen.json die News-Seite und die Nachrichten-Datei fuer Alexa.

KiStadt Sicherheits-News von Evelyn Störzner, kischild.de
Copyright (c) 2026 Evelyn Störzner. Alle Rechte vorbehalten.

Ausgabe im Ordner site/:
  feed.json       Nachrichten-Datei fuer den Alexa-Nachrichten-Skill (Flash Briefing)
  aussprache.json Testdatei fuer den Aussprache-Test (nur zum Testen im Skill)
  index.html      Die News-Seite (news.kischild.de)

Nur Python-Standardbibliothek. Bricht mit Fehler ab, wenn eine Meldung
unvollstaendig oder fehlerhaft ist, damit nie etwas Kaputtes online geht.
"""
import datetime as dt
import hashlib
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SITE = ROOT / "site"

NEWS_URL = "https://news.kischild.de/"
NEWSLETTER_URL = "https://kischild.de/newsletter/"
SCHLUSSSATZ = "Hör bald wieder rein."
PLATZHALTER = ("Heute gibt es keine neue Meldung aus den K I Stadt Sicherheits-News. "
               "Hör bald wieder rein.")
MAX_TAGE_ALEXA = 6          # Alexa spielt nichts, was aelter als 7 Tage ist
MAX_MELDUNGEN_ALEXA = 5
MAX_HOER = 800              # Zeichen, Sicherheitsgrenze (Ziel: 600)

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,120}$")
DATUM_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class Fehler(Exception):
    pass


def text_pruefen(wert, feld, mid, max_len=None, leer_ok=False):
    if not isinstance(wert, str):
        raise Fehler(f"{mid}: Feld '{feld}' fehlt oder ist kein Text")
    wert = wert.strip()
    if not wert and not leer_ok:
        raise Fehler(f"{mid}: Feld '{feld}' ist leer")
    if any(ord(c) < 32 and c not in "\n\t" for c in wert):
        raise Fehler(f"{mid}: Feld '{feld}' enthaelt Steuerzeichen")
    if max_len and len(wert) > max_len:
        raise Fehler(f"{mid}: Feld '{feld}' ist zu lang ({len(wert)} > {max_len})")
    return wert


def zeit_lesen(wert, mid):
    try:
        t = dt.datetime.fromisoformat(wert)
    except (TypeError, ValueError):
        raise Fehler(f"{mid}: 'veroeffentlicht' ist kein gueltiger Zeitpunkt")
    if t.tzinfo is None:
        raise Fehler(f"{mid}: 'veroeffentlicht' braucht eine Zeitzone, z. B. +01:00")
    return t.astimezone(dt.timezone.utc)


def meldungen_laden():
    roh = json.loads((DATA / "meldungen.json").read_text(encoding="utf-8"))
    if not isinstance(roh, list):
        raise Fehler("data/meldungen.json muss eine Liste sein")
    gesehen, ergebnis = set(), []
    for m in roh:
        mid = m.get("id", "?") if isinstance(m, dict) else "?"
        if not isinstance(m, dict) or not isinstance(mid, str) or not ID_RE.match(mid):
            raise Fehler(f"Ungueltige id: {mid!r}")
        if mid in gesehen:
            raise Fehler(f"{mid}: id doppelt")
        gesehen.add(mid)
        datum = text_pruefen(m.get("datum"), "datum", mid)
        if not DATUM_RE.match(datum):
            raise Fehler(f"{mid}: 'datum' muss JJJJ-MM-TT sein")
        hoer = text_pruefen(m.get("hoerfassung"), "hoerfassung", mid, MAX_HOER)
        if not hoer.endswith(SCHLUSSSATZ):
            raise Fehler(f"{mid}: Hör-Fassung endet nicht mit dem festen Schlusssatz")
        if "http" in hoer.lower() or "www." in hoer.lower():
            raise Fehler(f"{mid}: Hör-Fassung darf keine Links enthalten")
        if re.search(r"kischild|k i schild|punkt de\b|\.de\b", hoer.lower()):
            raise Fehler(f"{mid}: Hör-Fassung darf keine Webseite nennen, Alexa liest Adressen falsch vor")
        if "kistadt" in hoer.lower() or "ki-stadt" in hoer.lower():
            raise Fehler(f"{mid}: In der Hör-Fassung 'K I Stadt' schreiben, damit Alexa es richtig ausspricht")
        quellen = m.get("quellen")
        if not isinstance(quellen, list) or not quellen:
            raise Fehler(f"{mid}: mindestens eine Quelle ist Pflicht")
        q_ok = []
        for q in quellen:
            name = text_pruefen(q.get("name") if isinstance(q, dict) else None, "quellen.name", mid, 200)
            url = text_pruefen(q.get("url"), "quellen.url", mid, 500)
            if not url.startswith("https://"):
                raise Fehler(f"{mid}: Quellen-Link muss mit https:// beginnen")
            q_ok.append({"name": name, "url": url})
        ergebnis.append({
            "id": mid,
            "datum": datum,
            "veroeffentlicht": zeit_lesen(m.get("veroeffentlicht"), mid),
            "titel": text_pruefen(m.get("titel"), "titel", mid, 120),
            "titelLang": text_pruefen(m.get("titelLang", m.get("titel")), "titelLang", mid, 200),
            "text": text_pruefen(m.get("text"), "text", mid, 3000),
            "hoerfassung": hoer,
            "akut": bool(m.get("akut", False)),
            "quellen": q_ok,
        })
    ergebnis.sort(key=lambda x: (x["veroeffentlicht"], x["datum"]), reverse=True)
    return ergebnis


def alexa_zeit(t):
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.0Z")


def feed_bauen(meldungen, jetzt):
    grenze = jetzt - dt.timedelta(days=MAX_TAGE_ALEXA)
    aktuell = [m for m in meldungen if grenze <= m["veroeffentlicht"] <= jetzt][:MAX_MELDUNGEN_ALEXA]
    if aktuell:
        return [{
            "uid": f"urn:kistadt-sicherheits-news:{m['id']}",
            "updateDate": alexa_zeit(m["veroeffentlicht"]),
            "titleText": m["titel"],
            "mainText": m["hoerfassung"],
            "redirectionUrl": NEWS_URL,
        } for m in aktuell]
    heute = jetzt.replace(hour=5, minute=0, second=0, microsecond=0)
    return [{
        "uid": f"urn:kistadt-sicherheits-news:platzhalter-{jetzt:%Y-%m-%d}-{hashlib.sha256(PLATZHALTER.encode()).hexdigest()[:8]}",
        "updateDate": alexa_zeit(heute if heute <= jetzt else jetzt),
        "titleText": "KiStadt Sicherheits-News",
        "mainText": PLATZHALTER,
        "redirectionUrl": NEWS_URL,
    }]


def aussprache_bauen(jetzt):
    datei = DATA / "aussprache.json"
    if not datei.exists():
        return []
    saetze = json.loads(datei.read_text(encoding="utf-8"))
    text = " ".join(text_pruefen(s, "aussprache", "aussprache", 300) for s in saetze)
    return [{
        "uid": f"urn:kistadt-sicherheits-news:aussprache-{jetzt:%Y-%m-%d}-{hashlib.sha256(text.encode()).hexdigest()[:8]}",
        "updateDate": alexa_zeit(jetzt),
        "titleText": "Aussprache-Test",
        "mainText": text,
        "redirectionUrl": NEWS_URL,
    }]


def e(s):
    return html.escape(s, quote=True)


def absaetze(text):
    return "".join(f"<p>{e(teil)}</p>" for teil in text.split("\n") if teil.strip())


def datum_deutsch(datum):
    j, m, t = datum.split("-")
    return f"{t}.{m}.{j}"


def seite_bauen(meldungen):
    karten = []
    for m in meldungen:
        quellen = "".join(
            f'<li><a href="{e(q["url"])}" rel="noopener noreferrer">{e(q["name"])}</a></li>'
            for q in m["quellen"])
        akut = '<span class="marke akut">Akut</span>' if m["akut"] else ""
        karten.append(f"""
    <article class="meldung" id="{e(m['id'])}">
      <div class="kopf"><time datetime="{e(m['datum'])}">{datum_deutsch(m['datum'])}</time>{akut}</div>
      <h2>{e(m['titelLang'])}</h2>
      {absaetze(m['text'])}
      <div class="tun">
        <strong>Was du jetzt tun kannst</strong>
        <p>Die konkreten Schritte bekommst du in den KiStadt Sicherheits-News per E-Mail.</p>
        <a class="btn" href="{NEWSLETTER_URL}">Kostenlos eintragen</a>
      </div>
      <h3>Quellen</h3>
      <ul class="quellen">{quellen}</ul>
    </article>""")
    inhalt = "".join(karten) if karten else """
    <p class="leer">Hier erscheinen bald die ersten Meldungen.</p>"""
    stand = dt.datetime.now(dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=1)))
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>KiStadt Sicherheits-News · KI-Schild</title>
<meta name="description" content="Aktuelle Meldungen zur KI-Sicherheit mit Quellen, verständlich erklärt von Evelyn Störzner, kischild.de.">
<meta name="theme-color" content="#0F1B2D">
<meta name="robots" content="index,follow">
<style>
:root{{--gold:#F2B84B;--gold-hell:#F7D08A;--nacht:#0F1B2D;--karte:#182A43;--linie:#2A3E5C;--text:#EEF2F8;--leise:#A9B6CA;--rot:#E0655A;--rund:18px;
--schrift:"Inter KI-Schild","Inter","Segoe UI",-apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif}}
*{{box-sizing:border-box}}
body{{margin:0;background:#0B1524;color:var(--text);font-family:var(--schrift);font-size:17px;line-height:1.6}}
a{{color:var(--gold-hell)}}
a:focus-visible{{outline:3px solid var(--gold);outline-offset:2px}}
.wrap{{max-width:760px;margin:0 auto;padding:32px 16px 56px}}
header{{border-bottom:1px solid var(--linie);padding-bottom:20px;margin-bottom:28px}}
.zurueck{{font-size:.95rem;text-decoration:none}}
h1{{font-size:2rem;line-height:1.15;margin:14px 0 8px}}
h1 span{{color:var(--gold)}}
.unter{{color:var(--leise);margin:0}}
.anmelden{{margin-top:16px}}
.meldung{{background:var(--karte);border:1px solid var(--linie);border-radius:var(--rund);padding:20px;margin-bottom:18px}}
.kopf{{display:flex;gap:10px;align-items:center;color:var(--leise);font-size:.9rem}}
.marke{{font-weight:700;border-radius:999px;padding:2px 10px;font-size:.8rem}}
.akut{{background:rgba(224,101,90,.18);color:var(--rot)}}
h2{{font-size:1.3rem;line-height:1.3;margin:8px 0 10px}}
h3{{font-size:.85rem;letter-spacing:.08em;text-transform:uppercase;color:var(--leise);margin:16px 0 6px}}
.tun{{background:rgba(242,184,75,.12);border:1px solid rgba(242,184,75,.35);border-radius:14px;padding:14px;margin-top:14px}}
.tun p{{margin:4px 0 10px}}
.btn{{display:inline-block;background:var(--gold);color:var(--nacht);font-weight:700;text-decoration:none;border-radius:999px;padding:10px 18px}}
.btn:hover{{background:var(--gold-hell)}}
.quellen{{margin:0;padding-left:1.2em;overflow-wrap:anywhere}}
.leer{{color:var(--leise)}}
footer{{border-top:1px solid var(--linie);margin-top:36px;padding-top:18px;color:var(--leise);font-size:.9rem;display:flex;flex-wrap:wrap;gap:8px 18px}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <a class="zurueck" href="https://kischild.de/index.html">← Zur Startseite von KI-Schild</a>
    <h1>KiStadt <span>Sicherheits-News</span></h1>
    <p class="unter">Aktuelle Meldungen zur KI-Sicherheit, verständlich erklärt, mit Quellen zum Nachlesen. Das Neueste steht oben.</p>
    <p class="anmelden"><a class="btn" href="{NEWSLETTER_URL}">Sicherheits-News per E-Mail bekommen</a></p>
  </header>
  <main>{inhalt}
  </main>
  <footer>
    <span>© {stand:%Y} Evelyn Störzner · kischild.de</span>
    <a href="https://kischild.de/impressum.html">Impressum</a>
    <a href="https://kischild.de/datenschutz.html">Datenschutz</a>
    <a href="https://kischild.de/index.html">Startseite</a>
  </footer>
</div>
</body>
</html>
"""


def main():
    jetzt = dt.datetime.now(dt.timezone.utc)
    try:
        meldungen = meldungen_laden()
        aussprache = aussprache_bauen(jetzt)
    except Fehler as f:
        print(f"FEHLER: {f}", file=sys.stderr)
        return 1
    SITE.mkdir(exist_ok=True)
    (SITE / "feed.json").write_text(json.dumps(feed_bauen(meldungen, jetzt), ensure_ascii=False, indent=2), encoding="utf-8")
    if aussprache:
        (SITE / "aussprache.json").write_text(json.dumps(aussprache, ensure_ascii=False, indent=2), encoding="utf-8")
    (SITE / "index.html").write_text(seite_bauen(meldungen), encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    print(f"OK: {len(meldungen)} Meldungen, Nachrichten-Datei und News-Seite gebaut.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
