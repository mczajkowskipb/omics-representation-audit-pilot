# Pliki i paczki, które należy zachować

Ten wykaz rozdziela artefakty niezbędne od kopii wygodnych. Dokładne nazwy
plików zależne od bieżącego commita są dodatkowo generowane w każdej paczce jako
`01_START_HERE/RELEASE_FILES_EXACT_PL.md`.

## 1. Minimalny komplet archiwalny

Najważniejszy jest jeden plik:

```text
SONATA_BIS16_TRPP_ALL_IN_ONE-<COMMIT7>.zip
```

Zawiera repozytorium, historię Git, wyniki, raporty, protokół, dokumenty wniosku,
sumy SHA-256 i instrukcję serwerową. Jeżeli ten plik oraz jego suma SHA-256 są
zachowane, pozostałe paczki można z niego odzyskać.

## 2. Pliki potrzebne do GitHub

Preferowany plik zachowujący pełną historię:

```text
05_ARCHIVES/omics-representation-audit-pilot-history-<COMMIT7>.bundle
```

Alternatywny czysty snapshot bez katalogu `.git`:

```text
05_ARCHIVES/omics-representation-audit-pilot-<COMMIT7>.zip
```

Do pierwszej publikacji należy użyć Git bundle. ZIP jest kopią do przeglądania
lub awaryjnego odtworzenia samych źródeł.

## 3. Pełne wyniki eksperymentów

Nazwa jest zamrożona, ponieważ wyniki nie są ponownie liczone:

```text
05_ARCHIVES/omics-representation-audit-pilot-results-9adae88.tar.gz
```

SHA-256:

```text
58f3cf8f52001f18af547301289304ee74f8988d1c761c6e9fb3c8208dffe0da
```

Archiwum obejmuje:

- `results/full630_primary/`;
- `results/real_lung_primary/`;
- `results/real_within_primary/`.

## 4. Raporty i dowody

Zbiorcze archiwum:

```text
05_ARCHIVES/SONATA_BIS16_EVIDENCE_AND_REPORTS-<COMMIT7>.zip
```

Najważniejszy pojedynczy raport:

```text
03_PILOT_REPORT/SONATA_BIS_PILOT_CLOSEOUT_REPORT.pdf
```

Najważniejsze pliki tekstowe w repozytorium:

```text
docs/PILOT_FINAL_REPORT.md
docs/PILOT_012_015_REPORT.md
docs/DECISION_LOG.md
docs/REUSE_AUDIT.md
docs/evidence/PILOT_019_VALIDATION.json
docs/tables/gate_b_summary.csv
docs/tables/external_transfer_results.csv
docs/tables/real_within_results.csv
```

## 5. Protokół nadrzędny

```text
06_PROTOCOL/SONATA_BIS_PILOT_PROTOCOL_v1.md
```

Odpowiednik w repozytorium:

```text
docs/SONATA_BIS_PILOT_PROTOCOL_v1.md
```

Zamrożona suma SHA-256 protokołu:

```text
5104901b66403ab29bbad24f7fdc48dda10121b1a584740ec47af02790d6a704
```

## 6. Dokumenty wniosku zachowane archiwalnie

PDF-y:

```text
02_GRANT_PDFS/SONATA_BIS16_SHORT_DESCRIPTION_EN_DRAFT.pdf
02_GRANT_PDFS/SONATA_BIS16_DETAILED_DESCRIPTION_EN_DRAFT.pdf
02_GRANT_PDFS/SONATA_BIS16_POPULAR_SUMMARY_PL.pdf
02_GRANT_PDFS/SONATA_BIS16_POPULAR_SUMMARY_EN.pdf
```

Edytowalne źródła znajdują się w `04_GRANT_SOURCES/`. Są zachowane jako stan
z dnia zamknięcia pakietu; publikacja repozytorium nie zmienia ich treści.

## 7. Pliki potrzebne na serwerze

Po sklonowaniu repozytorium kluczowe są:

```text
requirements.lock
requirements-grant.lock
pyproject.toml
configs/pilot.yml
configs/full630.yml
configs/real_lung.yml
configs/real_within.yml
configs/datasets.example.yml
data/manifests/feasibility_datasets.json
data/manifests/air_datasets.json
data/manifests/evaluation_labels.json
```

Lokalnie trzeba utworzyć, ale nie commitować:

```text
configs/datasets.local.yml
```

## 8. Zewnętrzne repozytoria danych

Nie są kopiowane do paczki all-in-one. Potrzebne są osobne, tylko do odczytu
migawki:

```text
rank-relational-clustering-feasibility
commit dc97680a1e944e74924b5e7b151e0c27d5655f22

AIR-relational-benchmark
commit 2dee739f6ee5e001ef1be76df2eb753ca389adb3
```

## 9. Pliki kontrolne paczki

```text
README_FIRST.md
CONTENTS.txt
CHECKSUMS.sha256
01_START_HERE/RELEASE_FILES_EXACT_PL.md
01_START_HERE/GITHUB_SERVER_GUIDE_PL.md
```

`CHECKSUMS.sha256` służy do sprawdzenia wszystkich plików wewnętrznych. Dla
zewnętrznego ZIP-a generowany jest również sąsiedni plik `.sha256`.
