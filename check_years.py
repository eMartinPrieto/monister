#!/usr/bin/env python3
import re, time, json, urllib.parse, urllib.request

SONGS_FILE = "songs.js"
OUT_FILE   = "informe_anos.md"
TOLERANCE  = 1  # margen de años antes de marcar como sospechosa
UA = "paraelpan@gmail.com"  # pon aquí tu usuario o email

def load_songs(path):
    raw = open(path, encoding="utf-8").read()
    pat = re.compile(r'\{\s*artist:\s*"((?:[^"\\]|\\.)*)",\s*title:\s*"((?:[^"\\]|\\.)*)",\s*year:\s*(\d+)\s*\}')
    return [{"artist": m.group(1).replace('\\"','"'),
             "title":  m.group(2).replace('\\"','"'),
             "year":   int(m.group(3))} for m in pat.finditer(raw)]

def mb_year(artist, title):
    q = 'artist:"%s" AND recording:"%s"' % (artist.replace('"',''), title.replace('"',''))
    url = "https://musicbrainz.org/ws/2/recording/?query=%s&fmt=json&limit=5" % urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except Exception as e:
        return None, "error: %s" % e
    recs = data.get("recordings", [])
    if not recs:
        return None, "sin resultados"
    best = recs[0]  # mejor coincidencia
    d = best.get("first-release-date", "")
    if d[:4].isdigit():
        return int(d[:4]), "ok"
    years = [int(rel["date"][:4]) for rel in best.get("releases", []) if rel.get("date","")[:4].isdigit()]
    return (min(years), "ok") if years else (None, "sin fecha")

def main():
    songs = load_songs(SONGS_FILE)
    print("Canciones a comprobar:", len(songs))
    sospechosas, sin_datos = [], []
    for i, s in enumerate(songs, 1):
        mb, status = mb_year(s["artist"], s["title"])
        if mb is None:
            sin_datos.append((s, status))
        elif abs(mb - s["year"]) > TOLERANCE:
            sospechosas.append((s, mb))
        if i % 25 == 0:
            print("  %d/%d..." % (i, len(songs)))
        time.sleep(1.1)  # límite de MusicBrainz: 1 petición/segundo

    L = ["# Informe de años – Monister", "",
         "Comprobadas: **%d** · Sospechosas: **%d** · Sin datos: **%d**" % (len(songs), len(sospechosas), len(sin_datos)),
         "", "## Posibles años mal (MusicBrainz dice otra cosa)", "",
         "| Artista | Título | Tu año | MusicBrainz |", "|---|---|---|---|"]
    for s, mb in sorted(sospechosas, key=lambda x: x[0]["artist"].lower()):
        L.append("| %s | %s | %d | **%d** |" % (s["artist"], s["title"], s["year"], mb))
    L += ["", "## Sin datos fiables (revisar a mano)"]
    for s, status in sin_datos:
        L.append("- %s, %s (%d) — %s" % (s["title"], s["artist"], s["year"], status))
    open(OUT_FILE, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("Informe escrito en", OUT_FILE)

if __name__ == "__main__":
    main()
