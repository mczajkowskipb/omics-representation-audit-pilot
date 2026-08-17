# SONATA BIS 16 / TRPP - paczka kompletna

Ta paczka zbiera w jednym miejscu aktualny kod, historię Git, pełne wyniki
pilota, dowody, raporty i dokumenty wniosku. Najwygodniej zacząć od katalogu
`01_START_HERE`, a następnie otworzyć cztery PDF-y w `02_GRANT_PDFS`.

## Zawartość

- `01_START_HERE/README_FIRST_PL.md` - proste wyjaśnienie projektu, aktualny
  status i dokładne następne kroki;
- `01_START_HERE/SONATA_BIS16_COMPLETION_REPORT.md` - raport wykonanych zmian,
  testów, ryzyk i odstępstw;
- `02_GRANT_PDFS/` - opis skrócony EN, opis szczegółowy EN, streszczenie
  popularnonaukowe PL i EN;
- `03_PILOT_REPORT/` - końcowy raport pilota w PDF;
- `04_GRANT_SOURCES/` - edytowalne źródła Markdown wniosku i audyt kohort;
- `05_ARCHIVES/omics-representation-audit-pilot-*.zip` - czyste źródła aktualnego
  repozytorium z bieżącego commita;
- `05_ARCHIVES/omics-representation-audit-pilot-history-*.bundle` - kompletna
  historia Git do odtworzenia poleceniem `git clone plik.bundle katalog`;
- `05_ARCHIVES/SONATA_BIS16_EVIDENCE_AND_REPORTS-*.zip` - dowody, tabele,
  figury i raporty;
- `05_ARCHIVES/omics-representation-audit-pilot-results-9adae88.tar.gz` - pełne
  ciężkie wyniki obliczeniowe zamkniętego pilota;
- `06_PROTOCOL/` - nadrzędny protokół projektu;
- `CHECKSUMS.sha256` - sumy SHA-256 wszystkich plików wewnątrz paczki;
- `CONTENTS.txt` - lista plików i rozmiarów.

## Status naukowy, którego nie wolno zmieniać

- Gate B: GO.
- Gate C: STOP.
- direct regions: NOT TESTED.
- anchors: NOT TESTED.
- PILOT-016-018: niewykonane, zablokowane wynikiem Gate C.
- Brak target tuning i brak retrospektywnego rozluźniania progów.

## Najbliższe zadanie

Pilot nie wymaga kolejnego „ratowania”. Następnym blokiem jest uzupełnienie
wniosku o prawdziwe dane osób, budżet, osiągnięcia PI, dane jednostki, DMP,
etykę i potwierdzoną współpracę, a następnie kontrola zgodności z aktualnym
formularzem OSF.

