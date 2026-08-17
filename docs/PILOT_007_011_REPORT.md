# Raport akceptacyjny PILOT-007--011

Data: 2026-08-17

Protokół: `SONATA BIS PILOT PROTOCOL v1.0`

SHA-256 protokołu: `5104901b66403ab29bbad24f7fdc48dda10121b1a584740ec47af02790d6a704`

Bazowy commit PILOT-001--006: `eb9dc9adfd343aee6aa7a2a3f90cbbdd96f48da1`

## Status w prostych słowach

Ten blok implementuje wcześniejszą ocenę, **jakiego rodzaju porównanie
pacjentów ma sens**, zanim spojrzymy na etykiety lub kohortę target:

1. z danych source budowane są reprezentacje VALUE, RELATIONAL i HYBRID;
2. każda jest grupowana dokładnie tym samym deterministycznym PAM;
3. audit sprawdza, czy grupy odtwarzają się po podziale danych, podpróbkowaniu
   i realistycznych zaburzeniach;
4. progi z symulacji NULL odrzucają strukturę, która może powstać przypadkiem;
5. wynik to VALUE, RELATIONAL, HYBRID albo jawne
   `NO_STABLE_STRUCTURE`.

W PAM centrum klastra jest **medoidem**, czyli rzeczywistym pacjentem source
najbardziej centralnym według wybranej odległości. Obszar reguł typu
`gene_A > gene_B` nie jest jeszcze zaimplementowany. Taki profil będzie
późniejszym, interpretowalnym odpowiednikiem centroidu grupy w PILOT-016.
Pełne direct regions (PILOT-017) i anchory pozostają poza tym blokiem.

Status tego zakresu: **GO dla PILOT-007--011 i smoke gate**. Nie oznacza to
jeszcze pełnego Gate B ani gotowości biologicznej: nie wykonano pełnej siatki
630 par, target ARI regret, korelacji audit--target ani realnego transferu.

## PILOT-007 — generatory VALUE/RELATIONAL/HYBRID/NULL

### Wykonane zmiany

- dodano cztery deterministyczne mechanizmy symulacyjne;
- source i target mają niezależne strumienie losowe;
- prawda symulacyjna i etykiety są fizycznie odrębnymi obiektami w module
  `evaluation`, a oba `DatasetBundle` nie mają pola etykiet;
- VALUE koduje zmiany poziomów bez istotnych inwersji rang;
- RELATIONAL koduje klasowo zależne odwrócenia par;
- HYBRID używa rozłącznych bloków wartościowego i relacyjnego;
- NULL ma zmienne relacje, ale nie ma klasowo zależnego sygnału generatora.

### Pliki

- `src/rep_audit/simulation/generators.py`;
- `src/rep_audit/simulation/__init__.py`;
- `src/rep_audit/evaluation/simulation_truth.py`;
- `src/rep_audit/evaluation/simulation_metrics.py`;
- `tests/unit/test_simulation_generators.py`;
- `tests/determinism/test_simulation_determinism.py`.

### Testy akceptacyjne

`15/15` testów generatorów i deterministyczności. Sprawdzono m.in. niezależne
kohorty, brak etykiet w bundle, odwrócenia relacji, prawie niezmienione rangi
VALUE i bajtową powtarzalność.

### Ryzyka

- generatory są przypadkami kontrolnymi mechanizmu, nie modelami konkretnej
  biologii;
- poprawna rodzina w syntetycznym zbiorze nie gwarantuje poprawnej rodziny w
  danych rzeczywistych;
- czysty source VALUE ma stałe tło nieinformatywne, aby techniczny mnożnik
  próbki nie stał się zamierzonym klastrem; stres techniczny pozostaje po
  stronie target.

### Odstępstwa

Brak zmiany kryterium. Korekta generatora VALUE doprowadziła go do definicji
protokołu: klaster ma pochodzić ze zmian poziomów genów informatywnych, a nie z
ukrytego mnożnika technicznego source.

### Następne zadanie po etapie

PILOT-008: zaburzenia oraz kontrola niezależności source--target.

## PILOT-008 — perturbacje i source--target

### Wykonane zmiany

- dodano transformacje monotoniczne próbki, offsety genowe, szum addytywny,
  dropout cech/wartości i kwantyzację/remisy;
- poziomy `small`, `moderate` i `strong` mają zamrożone parametry;
- losowe perturbacje są deterministyczne także po zmianie kolejności wierszy
  i kolumn;
- zmiana wyłącznie target shift nie zmienia ani jednego bajtu source ani
  artefaktu preprocessingu.

### Pliki

- `src/rep_audit/simulation/perturbations.py`;
- `tests/unit/test_perturbations.py`;
- `tests/integration/test_simulation_source_target_leakage.py`.

### Testy akceptacyjne

`11/11` testów perturbacji, deterministyczności i leakage.

### Ryzyka

- brakujące geny target są generowane, lecz zachowanie pokrycia i
  `UNASSIGNED` w realnym transferze należy do następnego bloku;
- offsety genowe i szum celowo mogą zniszczyć relacje — metoda relacyjna nie
  ma być automatycznie odporna na każdy shift.

### Odstępstwa

Brak.

### Następne zadanie po etapie

PILOT-009: source-only relation screen i diagnostyki auditu.

## PILOT-009 — Representation Audit

### Wykonane zmiany

- generowane są wszystkie kanoniczne nieuporządkowane pary w zamrożonym
  source-selected universe;
- relation screen wymaga coverage `>0.90`, entropii `>=0.05`, stabilności
  `>=0.80` i niezmienności stanu; remisy rozstrzyga `relation_id`;
- zaimplementowano `PS`, `STAB`, `INV`, `ND`, `REP` i complexity;
- jakość jest dokładnie `Q = min(PS, STAB, INV)` z osobnym warunkiem
  non-degeneracy;
- wszystkie metody VALUE, RELATIONAL i HYBRID używają jednego PAM;
- preprocessing, relacje, wagi i skale hybrid są fitowane wyłącznie na source
  i zapisywane w manifeście auditu.

### Pliki

- `src/rep_audit/representations/relation_screen.py`;
- `src/rep_audit/audit/config.py`;
- `src/rep_audit/audit/distances.py`;
- `src/rep_audit/audit/diagnostics.py`;
- `src/rep_audit/audit/report.py`;
- `tests/unit/test_relation_screen.py`;
- `tests/unit/test_audit_diagnostics.py`;
- `tests/integration/test_audit_no_leakage.py`.

### Testy akceptacyjne

`9/9` bezpośrednich testów auditu i leakage oraz testy współdzielone z
PILOT-004--008. Zmiana wartości target nie zmieniła bajtów raportu source.
Sygnatura `run_source_audit(source, config)` nie przyjmuje target ani etykiet.

### Ryzyka

- wewnętrzne splity PS zamrażają reprezentację dopasowaną na całym source i
  rozdzielają część klasteryzacyjną; to jest source-only, ale może dawać mniej
  konserwatywną ocenę niż refit preprocessingu w każdym splicie;
- `B=5` w smoke ma dużą dyskretyzację. Protokół wymaga `B=20` w głównym
  eksperymencie;
- stabilny nuisance może wyglądać jak stabilna biologia bez informacji batch.

### Odstępstwa

W smoke użyto dozwolonej czułości `M=500`, a nie głównego `M=2000`.
Formuła screen score została zamrożona przed jakimikolwiek realnymi etykietami.

### Następne zadanie po etapie

PILOT-010: konserwatywny selektor kalibrowany przez NULL.

## PILOT-010 — null-kalibrowany selektor

### Wykonane zmiany

- każda metoda ma osobny górny kwantyl NULL (`q=0.90`, metoda `higher`);
- możliwość wyboru jednej z wielu metod kontroluje dodatkowy margines:
  90. percentyl krzyżowo estymowanego maksimum
  `Q - próg_własnej_metody`;
- HYBRID musi pokonać oba najlepsze czyste endpointy o
  `delta_hybrid=max(0.02, kwantyl_NULL)`;
- przy różnicy do `0.02` wybierana jest prostsza reprezentacja czysta;
- głosowanie po zewnętrznych resamplach oznacza `UNCERTAIN` poniżej częstości
  `0.60`;
- selektor nie importuje i nie przyjmuje etykiet.

### Pliki

- `src/rep_audit/audit/selector.py`;
- `tests/unit/test_selector.py`;
- `docs/evidence/PILOT_010_NULL_CALIBRATION.json`.

### Testy akceptacyjne

`11/11` testów reguł selekcji. Końcowy artefakt dla `n=90`, `K=3` ma:

- `multiple_testing_margin = 0.03930882824326365`;
- `delta_hybrid = 0.14035087719298245`;
- po 10 obserwacji NULL dla każdej z 7 metod.

### Ryzyka

- 10 zbiorów NULL to mała kalibracja; progi mają zostać ponownie ocenione dla
  głównego `n=180` bez użycia etykiet target;
- kwantyl `higher` przy małej próbie jest celowo dyskretny i konserwatywny;
- obecna kalibracja jest ważna dla zamrożonego `K=3`, `n=90`, `B=5`, a nie
  automatycznie dla innych rozmiarów i K.

### Odstępstwa

Protokół wymaga progów właściwych dla metody/K/rozmiaru, lecz nie podaje
kontroli wielokrotnego wyboru. Dodany cross-fitted excess margin jest
konserwatywnym zabezpieczeniem przed siedmioma równoległymi kandydatami; nie
obniża żadnego progu i został zamrożony przed danymi realnymi.

### Następne zadanie po etapie

PILOT-011: kanoniczna siatka oraz atomowe i walidowane wyniki.

## PILOT-011 — siatka smoke i atomowy runner

### Wykonane zmiany

- zamrożono osiem komórek po pięć replik: po dwa poziomy VALUE, RELATIONAL i
  HYBRID oraz dwa warianty NULL;
- każda specyfikacja ma pełny 64-znakowy deterministyczny job ID;
- job zapisuje do katalogu tymczasowego, waliduje kompletność, schematy,
  checksumy i gzip, a następnie publikuje jednym `rename`;
- poprawny istniejący job nie jest nadpisywany, a niekompletny jest odrzucany;
- NULL jest oceniany z kalibracją leave-one-out;
- etykiety są odsłaniane wyłącznie w `evaluation` po utworzeniu niezmiennego
  obiektu wyboru; etykiety target nie są używane;
- czas i rzeczywisty high-water RSS procesu są zapisane oddzielnie od
  deterministycznych artefaktów.

### Pliki

- `configs/smoke.yml`;
- `src/rep_audit/experiments/job_spec.py`;
- `src/rep_audit/experiments/grid.py`;
- `src/rep_audit/experiments/runner.py`;
- `scripts/02_run_smoke_grid.py`;
- `scripts/03_verify_pilot_007_011.sh`;
- `scripts/04_compare_smoke_artifacts.py`;
- `tests/unit/test_job_spec_grid.py`;
- `tests/integration/test_atomic_job_runner.py`;
- `docs/evidence/PILOT_011_SMOKE_SUMMARY.json`;
- `docs/evidence/PILOT_011_DETERMINISM.txt`.

### Testy i wynik smoke

`6/6` testów specyfikacji, atomowego zapisu i walidatora.

Końcowa siatka:

| Wskaźnik | Wynik | Bramka |
|---|---:|---:|
| Ukończone joby | 40/40 | 40/40 |
| Trafność rodziny, sygnały | 93.33% | >=70% |
| Fałszywa struktura NULL | 0.00% | <=10% |
| HYBRID w czystym VALUE/RELATIONAL | 0.00% | <=20% |

Rozbicie: VALUE `10/10`, RELATIONAL `10/10`, HYBRID `8/10`, NULL `10/10`.
W HYBRID jeden wynik był RELATIONAL, a jeden `NO_STABLE_STRUCTURE`.
Końcowy moduł ewaluacji, uruchomiony dopiero po wyborze, wykazał medianę source
ARI `1.0` dla wybranych przypadków VALUE, RELATIONAL i HYBRID; minimum w
dziewięciu przypisanych HYBRID wyniosło `0.5281`. Source ARI nie było użyte do
fitowania, auditu, kalibracji ani wyboru.

Sekwencyjny przebieg 40 jobów w tym kontenerze: suma czasu jobów `58.53 s`,
mediana `1.56 s`, maksimum `1.74 s`, maksymalny high-water RSS procesu
`199.14 MiB`. Nie jest to benchmark docelowego serwera.

Dwa niezależne przebiegi porównały 242 kluczowe pliki: `0` różnic bajtowych.
Wspólny aggregate tree SHA-256:
`437f5132701483365834e1bcc5bd01e068e59927485a84ca328202717b86a010`.
`runtime.json` jest celowo wyłączony z porównania.

### Ryzyka

- runner jest obecnie sekwencyjny; równoległość 20--28 CPU dotyczy pełnego
  uruchomienia serwerowego i wymaga osobnego benchmarku;
- job ID zgodnie z protokołem nie zawiera commitu kodu, dlatego każde
  właściwe uruchomienie musi zapisać/freeze'ować commit i użyć nowego rootu;
- smoke nie wykonuje target assignment ani metryk transferu.

### Odstępstwa

Smoke używa dozwolonych ustawień testowych: `n=90` (czułość), `B=5`, `M=500`,
margin `0.00`. Główne `n=180`, `B=20`, `M=2000`, margin `0.00/0.02` nie zostały
zastąpione ani uznane za wykonane. Siatkę uruchomiono sekwencyjnie, ponieważ
celem tego etapu była poprawność i deterministyczność, nie throughput serwera.

### Następne zadanie po etapie

PILOT-012: read-only adapter danych z repozytorium feasibility.

## Historia nieudanych testów i korekt

Nie ukrywano nieudanych przebiegów:

1. Pierwszy smoke: trafność sygnałów `50%`, NULL false structure `10%`, STOP.
   NULL nie dostarczał dostatecznej zmienności relacji do kalibracji hybrid.
2. Drugi smoke po naprawie NULL: trafność `76.67%`, NULL `20%`, STOP.
   Osobne progi siedmiu metod tworzyły problem wielokrotnego wyboru.
3. Trzeci smoke z jednym surowym progiem globalnego Q: trafność `63.33%`,
   NULL `0%`, STOP. Próg mieszał nieporównywalne rozkłady Q i odrzucał VALUE.
4. Końcowa reguła używa progów właściwych dla metody plus cross-fitted margin,
   a generator VALUE usuwa niezamierzony source batch factor. Wynik: `GO`.

W testach technicznych wykryto również traktowanie niezacytowanego `NULL` w
YAML jako wartości pustej, walidację tymczasowego katalogu pod jego roboczą
nazwą, starą straż zakresu PILOT-001--006 oraz niewiarygodny odczyt RSS przez
`psutil` w kontenerze. Każdy problem ma test regresyjny lub pełną walidację po
korekcie. Żadna bramka nie została obniżona.

## Skonsolidowana walidacja

Polecenia:

```bash
PYTHON_BIN=.venv/bin/python bash scripts/01_verify_core.sh
.venv/bin/python -m pip check
.venv/bin/python -m compileall -q src tests scripts
.venv/bin/python scripts/04_compare_smoke_artifacts.py RUN_A RUN_B
```

Wynik końcowy, dwa niezależne przebiegi pełnego zestawu:

```text
run 1: 117 passed in 1.55 s
run 2: 117 passed in 1.62 s
skipped/xfail: 0
pip check: no broken requirements
compileall: no errors
git diff --check: no errors
```

Testy obejmują poprawność, deterministyczność, leakage, golden optimum PAM,
selekcję i atomowe zbieranie wyników. Ścisła kontrola środowiska miała wszystkie
flagi `true`; SHA protokołu był zgodny.

## Wykryte ryzyka przekrojowe

1. Smoke był etapem rozwojowym; wyniku 93.33% nie wolno przedstawiać jako
   niezależnej estymacji generalizacji.
2. Pełny Gate B nadal wymaga target ARI regret `<=0.05` i korelacji różnic
   audit--target Spearmana `>=0.40`.
3. Źródłowo stabilny nuisance nadal może być stabilny statystycznie, mimo że
   nie jest biologiczny.
4. Nie ma jeszcze realnych adapterów, target assignment, kontroli pokrycia ani
   `UNASSIGNED`.
5. Nie ma regionów reguł, direct regions ani anchor sets.

## Dokładne następne zadanie

Rekomendowany następny większy blok to **PILOT-012--015**:

1. read-only adapter feasibility i adapter AIR bez modyfikowania repozytoriów;
2. testy manifestów, identyfikatorów próbek/genów i brak leakage;
3. przed odsłonięciem jakichkolwiek realnych etykiet target: zbudowanie i
   uruchomienie wymaganej głównej siatki 630 par na serwerze (`n=180`, `B=20`,
   `M=2000`) oraz zamrożenie progów, konfiguracji i commitu;
4. zamrożony source artifact oraz niezależne, pojedynczo zgodne target
   assignment z zachowaniem `UNASSIGNED`;
5. GSE10072->GSE19804 i kierunek odwrotny, z zapisaniem decyzji i przypisań
   przed odsłonięciem target labels.

Blok powinien być realizowany po jednym zatwierdzeniu, z wewnętrznymi bramkami,
aby ograniczyć liczbę interakcji. PILOT-016 (post-hoc profile/region reguł jako
odpowiednik centroidu) należy rozpocząć dopiero po wskazaniu realnego przypadku
RELATIONAL; PILOT-017 i anchory pozostają warunkowe.
