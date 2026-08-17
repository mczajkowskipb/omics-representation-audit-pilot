# Raport wykonawczy zamknięcia: real within, PILOT-019 i PILOT-020

Data: 2026-08-17

Protokół SHA-256: `5104901b66403ab29bbad24f7fdc48dda10121b1a584740ec47af02790d6a704`

## Wynik

- wymagane 11 audytów within-dataset: wykonane i zamrożone przed etykietami;
- PILOT-019: zakończony, wszystkie kontrole integralności przeszły;
- PILOT-020: zakończony, 5 tabel, 6 figur, raport Markdown, tekst do
  wniosku i ośmiostronicowy PDF;
- PILOT-016--018: `NOT_RUN_BLOCKED_BY_GATE_C_STOP`;
- Gate B pozostaje GO, Gate C pozostaje STOP.

## Wykonane zmiany

1. Dodano dokładnie 11 źródłowych audytów realnych wymaganych protokołem.
2. Dla każdego z 11 rozmiarów próby wykonano po 30 kalibracji NULL przy K=2.
3. Zapisano oddzielne, hashowane artefakty `prelabel` z audytem, selekcją i
   przypisaniami. Dopiero walidacja kompletu 11 markerów odblokowała moduł
   ewaluacji.
4. Dodano walidację cache NULL pod kątem pełnej konfiguracji i liczby próbek.
5. Dodano kolektor PILOT-019, który odtwarza Gate B/C i wynik within z
   artefaktów składowych, sprawdza rewizje referencyjne, markery i hashe.
6. Dodano deterministyczny generator raportów PILOT-020 oraz wizualną kontrolę
   PDF po renderowaniu wszystkich stron.

## Najważniejsze pliki utworzone lub zmienione

- `configs/real_within.yml`;
- `src/rep_audit/experiments/real_within.py`;
- `src/rep_audit/experiments/closeout_validation.py`;
- `src/rep_audit/experiments/real_lung.py`;
- `scripts/07_run_real_within.py`;
- `scripts/08_validate_and_collect.py`;
- `scripts/09_generate_closeout_report.py`;
- `tests/unit/test_real_within.py`;
- `tests/unit/test_closeout_validation.py`;
- `tests/integration/test_real_within_boundary.py`;
- `docs/evidence/PILOT_019_VALIDATION.json`;
- `docs/evidence/PILOT_020_DELIVERABLES.json`;
- `docs/PILOT_FINAL_REPORT.md`;
- `docs/SONATA_BIS_PILOT_TEXT_PL.md`;
- `docs/tables/*.csv`, `docs/figures/*.png`;
- `output/pdf/SONATA_BIS_PILOT_CLOSEOUT_REPORT.pdf`.

## Uruchomione testy i wyniki

- pełny pytest z obiema rewizjami referencyjnymi i jawnie odblokowanym testem
  evaluation-only: `138 passed`, `0 failed`;
- `compileall`: passed;
- `pip check`: `No broken requirements found.`;
- ponowny pełny przebieg within-dataset: hash drzewa przed i po identyczny,
  `47ce572d4db1ff6cf77fd60b8202e04c6eadcfc895a5a2a5c3454ea17e1801af`;
- dwie niezależne generacje 15 artefaktów PILOT-020: 0 różnic;
- finalny PDF: 8 stron A4, poprawny odczyt tekstu, brak szyfrowania i
  JavaScript, wszystkie strony wyrenderowane i sprawdzone wizualnie.

## Wyniki naukowe nowego bloku

- decyzje within: RELATIONAL 8, VALUE 2, HYBRID 1;
- odrzucenia `NO_STABLE_STRUCTURE`: 0;
- wybrana metoda w granicy 0,05 ARI od oracle: 9/11 (`0.818182`);
- mediana within-dataset ARI regret: `0.010589`;
- mediana wybranego ARI: `0.065165`.

Ostatni punkt jest kluczowym ograniczeniem: stabilność source-only nie
gwarantuje zgodności z dostępną etykietą kliniczną. Wynik within jest opisowy i
nie zmienia formalnej Gate C.

## Wykryte ryzyka

1. Stabilna struktura może odpowiadać biologii innej niż etykieta ewaluacyjna
   albo czynnikowi technicznemu.
2. Jedna para zewnętrzna nie daje podstaw do szerokiego twierdzenia o
   generalizacji selektora.
3. Snapshot AIR zawiera zastany, nieśledzony częściowy plik tymczasowy
   `data/final/GSE19804/.X_features_x_samples.csv.Bceve0`. Nie został usunięty
   ani odczytany. Wszystkie pliki śledzone są czyste, a właściwa macierz została
   zaakceptowana wyłącznie po zgodności rozmiaru i SHA-256 z manifestem.
4. Regiony post-hoc, direct regions i anchory nie mają wyniku pilotażowego.

## Odstępstwa od protokołu

Nie zmieniono danych, progów, alpha, margin, coverage, selektora ani polityki
przypisań po odczycie etykiet. PILOT-016--018 nie wykonano z powodu zamrożonego
Gate C STOP. Jest to jawna decyzja zakresowa zgodna z wcześniejszym decision
logiem, a nie retrospektywna zmiana kryterium.

## Dokładne następne zadanie

Blok implementacyjny pilota jest zamknięty. Następne zadanie to redakcja
wniosku na podstawie `SONATA_BIS_PILOT_TEXT_PL.md` i
`PILOT_FINAL_REPORT.md`, z zachowaniem sformułowań Gate B GO / Gate C STOP oraz
bez deklarowania, że direct regions lub anchory zostały już zwalidowane.
