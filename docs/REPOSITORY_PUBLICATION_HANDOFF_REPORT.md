# Raport domknięcia publikacyjnego repozytorium

Data: 2026-08-17  
Zakres: dokumentacja GitHub/serwer, manifest artefaktów i deterministyczna paczka
wydaniowa  
Status protokołu: bez zmian, nadrzędny i wiążący

## Wykonane zmiany

- uzupełniono instalację o zależności wymagane przez pełny zestaw testów i PDF-y;
- dodano dokładną instrukcję publikacji repozytorium na GitHubie;
- dodano konfigurację dwóch odłączonych repozytoriów referencyjnych na
  zamrożonych commitach;
- rozdzielono szybki test kodu, pełny test adapterów, walidację zaakceptowanych
  wyników oraz opcjonalne przeliczenie od zera;
- dodano wykaz plików i paczek, które należy zachować;
- dodano deterministyczny builder all-in-one z kontrolą czystego worktree,
  protokołu oraz SHA-256 zamrożonego archiwum wyników;
- wymuszono jednowątkowe pakowanie Git bundle po wykryciu, że domyślny
  wielowątkowy `pack-objects` nie dawał identycznych bajtów między buildami;
- dodano testy chroniące kolejność `prelabel`/`evaluate` i zamrożony status
  Gate B/Gate C/direct regions/anchors.

## Pliki utworzone

- `docs/GITHUB_SERVER_GUIDE_PL.md`;
- `docs/FILES_AND_ARCHIVES_MANIFEST_PL.md`;
- `docs/REPOSITORY_PUBLICATION_HANDOFF_REPORT.md`;
- `scripts/12_build_handoff_package.py`;
- `tests/unit/test_repository_handoff.py`.

## Pliki zmienione

- `README.md`;
- `docs/package/ALL_IN_ONE_README_PL.md`.

## Testy akceptacyjne

- pełny `pytest` z obiema migawkami referencyjnymi: **151 passed, 0 failed**;
- sześć nowych testów dokumentacji i buildera: **6 passed, 0 failed**;
- ścisła kontrola środowiska: **PASS**;
- kompilacja `src`, `scripts` i `tests`: **PASS**;
- `pip check`: **No broken requirements found**;
- walidacja pakietu grantowego: **PASS**, 11 dokumentów, zero
  niedozwolonych twierdzeń;
- walidacja rozpakowanego pełnego drzewa wyników: **PASS** dla 630/630 zadań,
  11/11 analiz realnych i 2/2 transferów;
- status odtworzony bez zmian: Gate B **GO**, Gate C **STOP**;
- dwukrotne zbudowanie paczki z czystego commita: **byte-identical PASS**;
- test głównego ZIP-a, źródłowego ZIP-a i archiwum dowodowego: **PASS**;
- wszystkie wewnętrzne `CHECKSUMS.sha256`: **PASS**;
- odtworzenie repozytorium z Git bundle i zgodność `HEAD`: **PASS**;
- archiwum wyników: 7957 wpisów, w tym 6410 plików, test `tar`: **PASS**.

## Ryzyka

- publikacja na zewnętrznym GitHubie wymaga uwierzytelnionego konta właściciela;
- uruchomienie na docelowym serwerze wymaga dostępu do maszyny i osobnych
  migawek obu repozytoriów danych;
- repozytorium zawiera archiwalne teksty wniosku, dlatego zalecany jest najpierw
  tryb prywatny;
- migawka AIR zawiera jeden zastany nieśledzony plik tymczasowy; adapter go
  wyklucza, a pliki śledzone repozytorium pozostają czyste;
- nowa dokumentacja nie jest nową walidacją naukową i nie zmienia Gate C STOP.

## Odstępstwa od protokołu

Brak. Nie zmieniono danych, metod, parametrów, progów, etykiet, wyników ani
dokumentów naukowych. PILOT-016--018 pozostają niewykonane.

## Dokładne następne zadanie

Po przejściu testów: utworzyć commit dokumentacyjno-wydaniowy, zbudować nową
paczę all-in-one, zapisać ją trwale i przekazać użytkownikowi dokładne nazwy
plików. Publikacja GitHub i walidacja na serwerze są następnymi czynnościami
zewnętrznymi.
