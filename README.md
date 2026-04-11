# Legalize SE — Svensk Författningssamling (SFS)

Samtliga **gällande** författningar ur Svensk Författningssamling (SFS), hämtade från [Rättsbaser](https://beta.rkrattsbaser.gov.se/) via öppet API.

## Innehåll

| Fil/Katalog | Beskrivning |
|---|---|
| `sfs_lista.txt` | Tab-separerad förteckning över alla gällande SFS-författningar (SFS-nr + rubrik) |
| `manifest.json` | JSON-objekt med beteckning → uppdateradDateTime (versionsstämpel per dokument) |
| `md/` | En markdown-fil per författning med fulltext (>7K filer) |
| `update_sfs.py` | Skript som hämtar och uppdaterar data från Rättsbaser-API:et |
| `update_log.txt` | Logg över automatiska uppdateringar |

### Markdown-format (`md/`)

Varje fil i `md/`-katalogen är namngiven `SFS_<nr>.md` och innehåller:

- Rubrik (lagens namn)
- SFS-nummer
- Typ (lag, förordning, etc.)
- Myndighet/Departement
- Ikraftträdandedatum
- Senast uppdaterad i Rättsbaser
- Fullständig författningstext

## Automatisk uppdatering

Repot uppdateras automatiskt varje **måndag kl. 03:00 UTC** via GitHub Actions (se `.github/workflows/weekly-update-sfs.yml`).

Uppdateringsskriptet:
1. Läser `manifest.json` för att se vilka SFS-nr som redan finns i repot och deras versionsstämplar (uppdateradDateTime)
2. Frågar Rättsbaser-API:et efter **alla** gällande SFS-dokument (år för år, fr.o.m. 1800)
3. Klassificerar varje post som ny, ändrad eller upphävd
4. Laddar ner och sparar/uppdaterar markdown-filer för nya och ändrade författningar
5. Tar bort markdown-filer för upphävda författningar
6. Uppdaterar `sfs_lista.txt` och `manifest.json` och loggar förändringarna i `update_log.txt`

## Datakälla

**Rättsbaser** / Regeringskansliets rättsdatabaser  
API: `https://beta.rkrattsbaser.gov.se/elasticsearch/SearchEsByRawJson`  
Senast hämtad: 2026-04-11

## Användning

Klona repot och bläddra bland markdown-filerna, eller använd `sfs_lista.txt` som index:

```bash
# Hitta alla lagar som innehåller ett visst ord
grep -rl "personuppgift" md/

# Sök i listan efter rubrik
grep -i "dataskydd" sfs_lista.txt
```


## Licens

- **Kod** (t.ex. `update_sfs.py`, GitHub Actions-workflows) licensieras under **MIT** (se `LICENSE`).
- **Data/innehåll** (t.ex. `md/`, `sfs_lista.txt`) licensieras under **Creative Commons Erkännande 4.0 Internationell** (**CC BY 4.0**) (se `LICENSE-DATA`).

Observera: Underliggande SFS-texter är officiella författningstexter och kan omfattas av separata villkor för vidareutnyttjande; CC BY 4.0 avser denna sammanställning/metadata/formattering.
