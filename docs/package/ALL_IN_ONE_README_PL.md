# SONATA BIS 16 - paczka kompletna

Ta paczka zbiera w jednym miejscu aktualny kod, historię Git, pełne wyniki
pilota, dowody, raporty i dokumenty wniosku. Najwygodniej zacząć od katalogu
`01_START_HERE`, a następnie otworzyć cztery PDF-y w `02_GRANT_PDFS`.

## Zawartość

- `01_START_HERE/README_FIRST_PL.md` - proste wyjaśnienie projektu, aktualny
  status i dokładne następne kroki;
- `01_START_HERE/STRATEGIC_DECISION_MODIFY_PL.md` - krytyczna decyzja
  strategiczna: representation adequacy jako pytanie centralne, TRPP jako
  główna rodzina metod, bez rozszerzania projektu na „AI do wszystkiego”;
- `01_START_HERE/SONATA_BIS16_NARRATIVE_UPDATE_REPORT.md` - raport zmian,
  testów, ryzyk i braku odstępstw po aktualizacji narracji;
- `01_START_HERE/SONATA_BIS16_COMPLETION_REPORT.md` - raport wykonanych zmian,
  testów, ryzyk i odstępstw;
- `01_START_HERE/GITHUB_SERVER_GUIDE_PL.md` - dokładna instrukcja publikacji
  repozytorium, instalacji, konfiguracji danych i walidacji na serwerze;
- `01_START_HERE/RELEASE_FILES_EXACT_PL.md` - dokładne nazwy, rozmiary i sumy
  SHA-256 plików danej wersji;
- `01_START_HERE/FILES_AND_ARCHIVES_MANIFEST_PL.md` - wykaz artefaktów, które
  należy zachować;
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

Nazwa technicznej paczki nadal zawiera `TRPP`, aby zachować zgodność z
wcześniejszymi wydaniami. Nie oznacza to, że TRPP jest odpowiedzią założoną z
góry w zmodyfikowanej narracji grantowej.

## Najbliższe zadanie

Pilot nie wymaga kolejnego „ratowania”. Po zamknięciu dokumentów naukowych
pozostają czynności operacyjne: publikacja repozytorium, dołączenie paczki jako
GitHub Release lub archiwum OSF oraz niezależna walidacja środowiska na serwerze.
Nie są one nowymi eksperymentami i nie zmieniają żadnej bramki.
