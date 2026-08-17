# Publikacja repozytorium i uruchomienie na serwerze

Ten dokument dotyczy wyłącznie publikacji i odtwarzalności zamkniętego pilota.
Nie zmienia protokołu, metod, progów ani wyników.

## 1. Zamrożony stan naukowy

- Gate B: **GO**.
- Gate C: **STOP**.
- direct regions: **NOT TESTED**.
- anchors: **NOT TESTED**.
- PILOT-016--018: **NOT RUN**, zablokowane wynikiem Gate C.
- brak target tuning i brak retrospektywnego rozluźniania progów.

Publikacja kodu lub ponowne sprawdzenie środowiska nie może zmienić tych
decyzji. Nowy przebieg obliczeniowy musi używać nowego katalogu wynikowego.

## 2. Planowane repozytorium GitHub

Docelowa nazwa:

```text
omics-representation-audit-pilot
```

Docelowy adres właściciela projektu:

```text
https://github.com/mczajkowskipb/omics-representation-audit-pilot
```

Najbezpieczniej utworzyć najpierw puste repozytorium prywatne. Nie należy
inicjalizować go dodatkowym README, `.gitignore` ani LICENSE, ponieważ te pliki
już znajdują się w historii projektu.

### Publikacja z Git bundle

W katalogu rozpakowanej paczki all-in-one:

```bash
git clone \
  05_ARCHIVES/omics-representation-audit-pilot-history-<COMMIT7>.bundle \
  omics-representation-audit-pilot

cd omics-representation-audit-pilot
git status --short --branch
git rev-parse HEAD

git remote set-url origin \
  https://github.com/mczajkowskipb/omics-representation-audit-pilot.git

git push -u origin main
```

`<COMMIT7>` należy zastąpić dokładnym sufiksem podanym w
`01_START_HERE/RELEASE_FILES_EXACT_PL.md` w danej paczce.

Po sprawdzeniu commita można utworzyć tag zamknięcia:

```bash
git tag -a pilot-closeout-2026-08-17 -m \
  "SONATA BIS pilot: Gate B GO, Gate C STOP"
git push origin pilot-closeout-2026-08-17
```

Paczki all-in-one i ciężkiego drzewa wyników nie należy dodawać do zwykłej
historii Git. Należy dołączyć paczkę all-in-one jako asset GitHub Release albo
zachować ją w repozytorium danych/OSF.

## 3. Minimalne wymagania serwera

- Linux x86-64;
- Python co najmniej 3.11;
- Git;
- kilka GB wolnego miejsca;
- CPU; CUDA nie jest używana;
- fonty DejaVu w `/usr/share/fonts/truetype/dejavu`, jeżeli mają być
  regenerowane PDF-y.

Zalecana konfiguracja odtwarzająca przebieg pilota to osiem procesów roboczych,
po jednym wątku numerycznym na proces.

## 4. Instalacja

```bash
git clone \
  https://github.com/mczajkowskipb/omics-representation-audit-pilot.git
cd omics-representation-audit-pilot

python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install -r requirements-grant.lock
.venv/bin/python -m pip install --no-deps -e .
```

Kontrola kodu bez rzeczywistych repozytoriów referencyjnych:

```bash
PYTHON_BIN=.venv/bin/python bash scripts/01_verify_core.sh
```

Testy adapterów rzeczywistych danych będą wtedy pominięte. Nie należy
przedstawiać takiego przebiegu jako pełnego serwerowego testu akceptacyjnego.

## 5. Oddzielne migawki repozytoriów referencyjnych

Nie należy używać ani modyfikować roboczych kopii tych projektów. Na serwerze
trzeba utworzyć nowe, odłączone migawki tylko do odczytu:

```bash
mkdir -p ../reference_snapshots

git clone \
  https://github.com/mczajkowskipb/rank-relational-clustering-feasibility \
  ../reference_snapshots/rank-relational-clustering-feasibility-dc97680
git -C ../reference_snapshots/rank-relational-clustering-feasibility-dc97680 \
  checkout --detach dc97680a1e944e74924b5e7b151e0c27d5655f22

git clone \
  https://github.com/mczajkowskipb/AIR-relational-benchmark \
  ../reference_snapshots/AIR-relational-benchmark-2dee739
git -C ../reference_snapshots/AIR-relational-benchmark-2dee739 \
  checkout --detach 2dee739f6ee5e001ef1be76df2eb753ca389adb3
```

Następnie:

```bash
cp configs/datasets.example.yml configs/datasets.local.yml
```

W `configs/datasets.local.yml` należy wpisać bezwzględne ścieżki do obu nowych
migawek. Plik jest lokalny i celowo ignorowany przez Git.

## 6. Pełny test akceptacyjny z adapterami

```bash
export PILOT_FEASIBILITY_ROOT=/absolute/path/to/rank-relational-clustering-feasibility-dc97680
export PILOT_AIR_ROOT=/absolute/path/to/AIR-relational-benchmark-2dee739
export PILOT_ALLOW_REAL_LABEL_TEST=1

PYTHON_BIN=.venv/bin/python bash scripts/01_verify_core.sh
```

Flaga otwierająca etykiety jest dozwolona tylko w końcowym module ewaluacji i
teście zgodności adaptera. Nie może być ustawiana jako sposób wyboru metody,
cech, relacji, progów ani liczby klastrów.

## 7. Odtworzenie i sprawdzenie zaakceptowanych wyników

Pełne wyniki są dostarczone jako:

```text
omics-representation-audit-pilot-results-9adae88.tar.gz
```

Ich zamrożona suma SHA-256:

```text
58f3cf8f52001f18af547301289304ee74f8988d1c761c6e9fb3c8208dffe0da
```

Odtworzenie:

```bash
tar -xzf /absolute/path/to/omics-representation-audit-pilot-results-9adae88.tar.gz \
  -C .
```

Walidacja bez nadpisywania śledzonego raportu:

```bash
.venv/bin/python scripts/08_validate_and_collect.py \
  --run-tests \
  --output results/server_revalidation.json
```

Oczekiwany stan naukowy pozostaje Gate B GO i Gate C STOP. Inny wynik oznacza
problem odtwarzalności lub środowiska, a nie zgodę na zmianę bramki.

## 8. Pełne przeliczenie od zera - tylko opcjonalnie

Do archiwizacji i wniosku nie jest potrzebne ponowne liczenie. Jeżeli ma być
wykonana niezależna reprodukcja, należy użyć nowych katalogów i zachować fizyczną
granicę `prelabel` przed `evaluate`:

```bash
.venv/bin/python scripts/05_run_full630.py \
  --phase prelabel --max-workers 8 --output results/repro_full630
.venv/bin/python scripts/05_run_full630.py \
  --phase evaluate --output results/repro_full630

.venv/bin/python scripts/06_run_real_lung.py \
  --phase prelabel --max-workers 8 \
  --gate-b results/repro_full630/gate_b_summary.json \
  --output results/repro_real_lung
.venv/bin/python scripts/06_run_real_lung.py \
  --phase evaluate --output results/repro_real_lung

.venv/bin/python scripts/07_run_real_within.py \
  --phase prelabel --max-workers 8 \
  --gate-b results/repro_full630/gate_b_summary.json \
  --output results/repro_real_within
.venv/bin/python scripts/07_run_real_within.py \
  --phase evaluate --output results/repro_real_within
```

Nie wolno kierować nowego przebiegu do zaakceptowanych katalogów
`results/full630_primary`, `results/real_lung_primary` ani
`results/real_within_primary`.

## 9. Co przesłać innej osobie

Najprostsza opcja to jeden plik:

```text
SONATA_BIS16_TRPP_ALL_IN_ONE-<COMMIT7>.zip
```

Wewnątrz znajduje się dokładny manifest plików, źródła repozytorium, Git bundle,
pełne wyniki, raporty, protokół i dokumenty. Osobie, która potrzebuje tylko
kodu, wystarczy adres GitHub albo źródłowy ZIP z `05_ARCHIVES/`.
