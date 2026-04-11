# Legalize SE

### Svensk lagstiftning konsoliderad i Markdown, versionerad med Git.

Varje lag är en fil. Varje reform är en commit.

**7 277 författningar** · **Daglig uppdatering**

> **Early stage** — This repository is under active development. File structure, commit history, and content may undergo significant changes, including full regeneration.

## Snabbstart

```bash
# Klona den svenska lagstiftningen
git clone https://github.com/nab-collab/legalize-se.git

# Vad säger 1 kap. 2 § i Regeringsformen?
grep -A 5 "1 kap" md/SFS_1974_152.md

# Hur många gånger har Brottsbalken reformerats?
git log --oneline -- md/SFS_1962_700.md

# Visa exakt diff av en reform
git show <commit> -- md/SFS_1962_700.md
```

## Struktur

```
md/                          ← samtliga SFS-författningar (7 277 st)
  SFS_1974_152.md            — Regeringsformen
  SFS_1962_700.md            — Brottsbalken
  SFS_1942_740.md            — Rättegångsbalken
  SFS_1949_381.md            — Föräldrabalken
  ...
```

Författningens typ (lag, förordning, kungörelse, etc.) anges i varje fils metadata, inte i katalogstrukturen.

## Format

Varje fil innehåller:

- **Metadata** — SFS-nummer, typ, myndighet/departement, ikraftträdandedatum
- **Markdown-brödtext** — konsoliderad författningstext med hierarkisk struktur (kapitel, paragrafer)

Commits använder det historiska datumet för officiell publicering i SFS. Varje commit möjliggör rekonstruktion av det fullständiga lagstiftningshistoriken med `git log`.

## Datakälla

Data hämtad från <a href="https://beta.rkrattsbaser.gov.se/">Rättsbaser</a>, Regeringskansliets rättsdatabaser, publicerade av Regeringskansliet som öppen data.

## Licens

Lagtexter är offentlig information. Strukturering och formatering är licensierade under <a>MIT</a>.

---

Skapat av <a href="https://enriquelopez.eu">Enrique Lopez</a>
