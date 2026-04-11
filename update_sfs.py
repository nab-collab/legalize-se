"""
update_sfs.py — Uppdaterar Legalize-SE-repot med nya, ändrade och upphävda SFS-författningar.

Logik per körning:
  1. Läs manifest.json → beteckning → uppdateradDateTime (versionsstämpel per dok.)
  2. Fråga Rättsbaser-API:et år för år → hämta beteckning + uppdateradDateTime + fulltext.
  3. Klassificera varje post:
       NYA      — beteckning saknas i manifest (inte hämtad förut)
       ÄNDRADE  — beteckning finns men uppdateradDateTime är nyare i API
       UPPHÄVDA — beteckning finns i manifest men saknas i API (ej längre gällande)
  4. Hämta och spara/uppdatera markdown för NYA + ÄNDRADE.
  5. Ta bort markdown för UPPHÄVDA.
  6. Skriv om sfs_lista.txt och manifest.json.
  7. Skriv sammanfattning till update_log.txt.

Körs av GitHub Actions (weekly-update.yml) varje måndag.
"""

import urllib.request
import urllib.error
import json
import re
import time
import os
import sys
from datetime import date

# ── Config ─────────────────────────────────────────────────────────────────────
BASE       = "https://beta.rkrattsbaser.gov.se"
ENDPOINT   = BASE + "/elasticsearch/SearchEsByRawJson"
START_YEAR = 1600
PAGE_SIZE  = 50
DELAY_S    = 0.5
MD_DIR     = "md"
LIST_FILE  = "sfs_lista.txt"
MANIFEST_F = "manifest.json"   # beteckning → uppdateradDateTime
LOG_FILE   = "update_log.txt"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "sv,en;q=0.9",
    "Origin": BASE,
    "Referer": BASE + "/",
    "User-Agent": "Mozilla/5.0 (compatible; legalize-se-updater/1.0; +https://github.com/nab-collab/legalize-se)",
    "Cookie": "rattsdatabaser_kakinfo=cookieConsent%3D1",
}

# ── HTTP med retry ─────────────────────────────────────────────────────────────
def post(payload: dict, retries: int = 5) -> dict:
    data = json.dumps(payload).encode("utf-8")
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(ENDPOINT, data=data, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 403) and attempt < retries:
                wait = 10 * attempt
                print(f"    [HTTP {e.code}] Väntar {wait}s...", flush=True)
                time.sleep(wait)
            else:
                raise
        except Exception:
            if attempt < retries:
                time.sleep(5 * attempt)
            else:
                raise


# ── Hämta alla gällande SFS-poster för ett år ──────────────────────────────────
def fetch_year(year: int) -> list[dict]:
    hits, offset, total = [], 0, None
    while True:
        payload = {
            "searchIndexes": ["Sfs"],
            "api": "search",
            "json": {
                "track_total_hits": True,
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"publicerad": True}},
                            {"term": {"publiceringsar": year}},
                        ]
                    }
                },
                "post_filter": {
                    "bool": {
                        "must": [
                            {"bool": {"should": [
                                {"range": {"upphavdDateTime": {"gt": "now"}}},
                                {"bool": {"must_not": {"exists": {"field": "upphavdDateTime"}}}},
                            ]}},
                            {"bool": {"should": [
                                {"range": {"tidsbegransadDateTime": {"gt": "now"}}},
                                {"bool": {"must_not": {"exists": {"field": "tidsbegransadDateTime"}}}},
                            ]}},
                        ]
                    }
                },
                "size": PAGE_SIZE,
                "from": offset,
                "_source": [
                    "beteckning",
                    "rubrik",
                    "organisation",
                    "forfattningstypNamn",
                    "ikraftDateTime",
                    "uppdateradDateTime",   # ← versionsstämpel för ändringsdetektering
                    "fulltext",
                ],
            },
        }
        result = post(payload)
        page = result["hits"]["hits"]
        if total is None:
            total = result["hits"]["total"]["value"]
        hits.extend(h["_source"] for h in page)
        if not page or len(hits) >= total:
            break
        offset += PAGE_SIZE
        time.sleep(DELAY_S)
    return hits


# ── Filnamn och markdown ───────────────────────────────────────────────────────
def safe_filename(beteckning: str) -> str:
    return "SFS_" + re.sub(r"[^\w]", "_", beteckning) + ".md"

def to_markdown(src: dict) -> str:
    b    = src.get("beteckning", "")
    rubr = src.get("rubrik", "(ingen rubrik)").replace("\n", " ")
    org  = src.get("organisation", {}) or {}
    typ  = src.get("forfattningstypNamn", "")
    ikt  = (src.get("ikraftDateTime", "") or "")[:10] or "okänd"
    upd  = (src.get("uppdateradDateTime", "") or "")[:10] or "okänd"
    ft   = src.get("fulltext", {}) or {}
    text = ft.get("forfattningstext", "(ingen text tillgänglig)") or "(ingen text tillgänglig)"
    return "\n".join([
        f"# {rubr}", "",
        f"**SFS-nummer:** {b}  ",
        f"**Typ:** {typ}  ",
        f"**Myndighet/Departement:** {org.get('namnOchEnhet', '')}  ",
        f"**Ikraftträdande:** {ikt}  ",
        f"**Senast uppdaterad i Rättsbaser:** {upd}  ",
        "", "---", "", "## Författningstext", "", text,
    ])


# ── Läs/skriv manifest ─────────────────────────────────────────────────────────
def load_manifest() -> dict[str, str]:
    """Returnerar dict: beteckning → uppdateradDateTime (sträng)."""
    if not os.path.exists(MANIFEST_F):
        return {}
    with open(MANIFEST_F, encoding="utf-8") as f:
        return json.load(f)

def save_manifest(manifest: dict[str, str]):
    with open(MANIFEST_F, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)


# ── Huvudfunktion ──────────────────────────────────────────────────────────────
def main():
    os.makedirs(MD_DIR, exist_ok=True)

    print(f"=== Legalize-SE uppdatering {date.today()} ===\n")

    # 1. Läs befintligt manifest (versionsstämplar)
    manifest = load_manifest()
    print(f"Manifest: {len(manifest)} poster sedan tidigare")

    # 2. Hämta ALLA gällande poster från API:et (år för år)
    current_year = date.today().year
    api_data: dict[str, dict] = {}   # beteckning → _source

    for year in range(START_YEAR, current_year + 1):
        hits = fetch_year(year)
        for src in hits:
            b = src.get("beteckning", "").strip()
            if b:
                api_data[b] = src
        if hits:
            print(f"  {year}: {len(hits)} st", flush=True)
        if hits:
            time.sleep(DELAY_S)

    print(f"\nAPI returnerade: {len(api_data)} gällande poster")

    # 3. Klassificera
    api_set   = set(api_data.keys())
    mani_set  = set(manifest.keys())

    new_entries     = []   # beteckning saknas i manifest
    changed_entries = []   # beteckning finns men timestamp är nyare
    gone_entries    = []   # beteckning försvunnit från API

    for b in api_set:
        src = api_data[b]
        api_ts   = (src.get("uppdateradDateTime") or "")[:19]   # "YYYY-MM-DDTHH:MM:SS"
        mani_ts  = manifest.get(b, "")

        if b not in mani_set:
            new_entries.append(b)
        elif api_ts > mani_ts:
            changed_entries.append(b)

    for b in mani_set:
        if b not in api_set:
            gone_entries.append(b)

    print(f"  Nya:      {len(new_entries)}")
    print(f"  Ändrade:  {len(changed_entries)}")
    print(f"  Upphävda: {len(gone_entries)}")

    if not new_entries and not changed_entries and not gone_entries:
        print("\nInget att uppdatera.")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{date.today()}: Ingen förändring ({len(api_data)} poster).\n")
        sys.exit(0)

    # 4. Spara/uppdatera markdown för NYA och ÄNDRADE
    for b in sorted(new_entries):
        src   = api_data[b]
        fpath = os.path.join(MD_DIR, safe_filename(b))
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(to_markdown(src))
        manifest[b] = (src.get("uppdateradDateTime") or "")[:19]
        print(f"  + {b}")

    for b in sorted(changed_entries):
        src   = api_data[b]
        fpath = os.path.join(MD_DIR, safe_filename(b))
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(to_markdown(src))
        manifest[b] = (src.get("uppdateradDateTime") or "")[:19]
        print(f"  ~ {b}  (uppdaterad)")

    # 5. Ta bort upphävda markdown-filer
    for b in sorted(gone_entries):
        fpath = os.path.join(MD_DIR, safe_filename(b))
        if os.path.exists(fpath):
            os.remove(fpath)
        del manifest[b]
        print(f"  - {b}  (upphävd)")

    # 6. Skriv om manifest och sfs_lista.txt
    save_manifest(manifest)

    all_rows = []
    for b in sorted(api_data.keys()):
        rubr = (api_data[b].get("rubrik", "") or "").replace("\n", " ").strip()
        all_rows.append(f"{b}\t{rubr}")
    with open(LIST_FILE, "w", encoding="utf-8") as f:
        f.write("SFS-nr\tRubrik\n")
        f.write("\n".join(all_rows) + "\n")

    # 7. Logg
    log_line = (
        f"{date.today()}: "
        f"+{len(new_entries)} nya, "
        f"~{len(changed_entries)} ändrade, "
        f"-{len(gone_entries)} upphävda. "
        f"Totalt {len(api_data)} poster.\n"
    )
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

    print(f"\nUppdatering klar: {log_line.strip()}")


if __name__ == "__main__":
    main()
