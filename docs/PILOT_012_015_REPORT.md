# Raport wykonawczy PILOT-012--015 oraz Gate B/C

Data: 2026-08-17

Protokół: `SONATA BIS PILOT PROTOCOL v1.0`

SHA-256 protokołu: `5104901b66403ab29bbad24f7fdc48dda10121b1a584740ec47af02790d6a704`

Bazowy commit PILOT-001--011: `0cc2d042168ac2aceec5816e63fd4137aec56779`

## Co się dzieje — prostymi słowami

Pierwotna intuicja była poprawna:

1. Najpierw, wyłącznie na source, sprawdzamy, czy pacjentów lepiej porównują
   poziomy ekspresji, układ rang/relacji, czy połączenie obu widoków.
2. Każdy widok dostaje dokładnie ten sam PAM. Centrum grupy jest medoidem,
   czyli rzeczywistym pacjentem source, nie średnią sztuczną.
3. Wybrany sposób porównywania, preprocessing, relacje, skale, medoidy i progi
   odrzucenia są zamrażane.
4. Każdy pacjent target jest niezależnie przypisywany do najbliższego medoidu;
   target nie jest ponownie klasteryzowany ani normalizowany na sobie.
5. Dopiero po zapisaniu przypisań moduł ewaluacji otwiera etykiety.
6. Planowane obszary reguł (`gen_A > gen_B`, itd.) miały być późniejszym,
   interpretowalnym opisem grupy. Nie zostały teraz uruchomione, ponieważ
   zewnętrzna Gate C zakończyła się STOP.

## Wynik wykonawczy

- PILOT-012: **wykonany**;
- PILOT-013: **wykonany**;
- pełna Gate B, 630 par: **GO**;
- PILOT-014, GSE10072→GSE19804: **wykonany**;
- PILOT-015, GSE19804→GSE10072: **wykonany**;
- Gate C: **STOP** — jeden limit regret przekroczony o `0.005284`;
- PILOT-016, direct regions i anchory: **nie rozpoczęte**.

## PILOT-012 — adapter repozytorium feasibility

### Wykonane zmiany

- dodano read-only adapter dla Golub, Colon i DLBCL;
- adapter wymaga commita
  `dc97680a1e944e74924b5e7b151e0c27d5655f22`;
- każda macierz X ma zamrożony rozmiar i SHA-256;
- etykiety nie występują w manifeście fittingowym;
- Golub/Colon zachowują źródłowe ID próbek, a DLBCL dostaje stabilne ID wierszy.

### Pliki

- `src/rep_audit/data/adapters/{base,feasibility}.py`;
- `data/manifests/feasibility_datasets.json`;
- `data/manifests/evaluation_labels.json` — dostępny tylko ewaluacji;
- `tests/integration/test_reference_adapters.py`;
- `tests/unit/test_repository_adapter_firewall.py`.

### Testy i wynik

Załadowano trzy macierze: Golub `72×7129`, Colon `62×2000`, DLBCL
`194×2294`. Sprawdzono commit, rozmiar, SHA, orientację, unikalność ID i brak
pola `y` w `DatasetBundle`.

### Ryzyko i odstępstwa

Brak zmiany kryterium. Nie wykonano jeszcze pełnych opisowych audytów
within-dataset na tych trzech zbiorach; PILOT-012 obejmował adapter.

### Dokładne następne zadanie po etapie

PILOT-013: adapter wszystkich ośmiu zbiorów AIR.

## PILOT-013 — adapter AIR

### Wykonane zmiany

- dodano adapter ośmiu macierzy features×samples z transpozycją do kontraktu
  samples×features;
- wymagany jest commit
  `2dee739f6ee5e001ef1be76df2eb753ca389adb3` i osiem dokładnych SHA;
- `verify_all()` sprawdza komplet danych bez otwierania y;
- potwierdzono 22,277 wspólnych sond GSE10072/GSE19804;
- fittingowe i ewaluacyjne manifesty są fizycznie rozdzielone.

### Pliki

- `src/rep_audit/data/adapters/air.py`;
- `data/manifests/air_datasets.json`;
- `configs/datasets.example.yml`;
- wspólne testy adapterów i firewall.

### Testy i wynik

Osiem sum X przeszło; dwie macierze płucne załadowano jako `107×22283` i
`120×54675`. Test AST potwierdził, że namespace adapterów danych nie importuje
`rep_audit.evaluation`.

### Ryzyko i odstępstwa

Zastany roboczy checkout AIR miał wcześniej skrócone pliki GSE17920 i
GSE27272. Nie został zmodyfikowany ani użyty. Obliczenia wykonała czysta,
odłączona migawka wskazanego commita. Dwa platform_id, których upstream nie
zamrażał w prostym manifeście, mają opisowe identyfikatory liczby cech; nie
wpływa to na macierz ani transfer płucny.

### Dokładne następne zadanie po etapie

Pełna Gate B przed odblokowaniem realnych target labels.

## Pełna Gate B — obowiązkowa bramka przed transferem realnym

### Wykonane zmiany

- dodano dokładną siatkę 630 par: 540 sygnałowych i 90 NULL;
- użyto `n_source=n_target=180`, `p=200`, `K=3`, 30 cech informatywnych,
  `B=20`, `M=2000`, α `0.25/0.50/0.75`, margin `0.00`;
- trzy poziomy shift są sparowane z jednym source: 210 audytów source i 630
  osobnych transferów;
- proces pre-label zapisuje wszystkie kandydackie przypisania, a ewaluator
  odmawia pracy bez kompletu 630 markerów i SHA;
- ARI/regret używa wymuszonego przypisania wszystkich próbek; coverage używa
  zamrożonej reguły `UNASSIGNED`;
- runner jest równoległy, atomowy, walidowany i wznawialny.

### Pliki

- `configs/full630.yml`;
- `src/rep_audit/experiments/{grid,full_runner}.py`;
- `scripts/05_run_full630.py`;
- `src/rep_audit/transfer/{artifact,assign}.py`;
- `tests/integration/{test_frozen_transfer,test_primary_prelabel_boundary}.py`.

### Wynik

| Kryterium | Wynik | Próg | Status |
|---|---:|---:|---|
| Kompletność | 630/630 | 630/630 | PASS |
| Trafność rodziny | 0.9333 | ≥0.70 | PASS |
| Mediana target ARI regret | 0.0000 | ≤0.05 | PASS |
| Fałszywa struktura NULL | 0.0667 | ≤0.10 | PASS |
| HYBRID na czystych reżimach | 0.0000 | ≤0.20 | PASS |
| Spearman audit–target | 0.8537 | ≥0.40 | PASS |

Gate B: **GO**.

Pierwszy przebieg pre-label trwał `624.93 s` na 8 procesach. Rerun zweryfikował
210 istniejących grup bez refitowania. Zbiorczy hash 3150 naukowych plików
pre-label (runtime wyłączony) był identyczny: `6f84a699...e6667`.

### Ryzyka i odstępstwa

- Protokół wymienia margin `0.00` i `0.02`, ale jego dokładna liczba 630 nie
  zawiera osi margin. Zamrożono `0.00`; nie uruchomiono `0.02` po etykietach.
- Spearman to trzy podpisane kontrasty par rodzin na parę sygnałową, z
  maksimum Q i ARI w rodzinie; definicja jest zapisana w artefakcie.
- Przy ewaluacji pierwszy kolektor zatrzymał się na raporcie NULL bez rodziny
  relacyjnej. Poprawiono wyłącznie obsługę jawnego braku (`null`) i wznowiono;
  żaden audyt, model, próg ani assignment nie został zmieniony.

### Dokładne następne zadanie po etapie

Po GO: zamrozić oba kierunki płucne przed oceną ich target labels.

## PILOT-014 — GSE10072→GSE19804

### Wykonane zmiany

- K=2, wspólny universe 22,277 sond, source MAD wybiera 200;
- kalibracja NULL: 30 źródeł o `n=107`, K=2, B=20, M=2000;
- source audit wybrał `VALUE`, metodę `V_COR_PAM`;
- przed ewaluacją zapisano audit, selection, common universe, preprocessing,
  relacje, skale, wszystkie medoidy, progi i przypisania siedmiu metod.

### Wynik po odblokowaniu etykiet

- wybrana metoda: ARI `0.558876`, NMI `0.483484`;
- retrospektywny oracle `H_EUC_PAIR_A025_PAM`: ARI `0.664161`;
- regret `0.105284`;
- coverage `0.833333`;
- najmniejszy zaakceptowany klaster / cały target `0.333333`;
- ARI na zaakceptowanym podzbiorze `0.844774` (raportowane pomocniczo, nie
  zastępuje gate ARI na wszystkich próbkach).

### Ryzyko

Source Q kilku metod osiąga `1.0`, więc reguła prostoty wybiera czystą metodę,
choć oracle target jest hybrid. To dokładnie przypadek, który mierzy regret;
po wyniku nie wolno zmieniać reguły.

### Odstępstwa

Brak dostrajania target. Regret przekracza limit `0.10` o `0.005284`.

### Dokładne następne zadanie po etapie

PILOT-015: niezależnie zamrożony transfer odwrotny.

## PILOT-015 — GSE19804→GSE10072

### Wykonane zmiany

- osobna kalibracja NULL: 30 źródeł o `n=120`, K=2, B=20, M=2000;
- source audit wybrał `RELATIONAL`, metodę `R_PAIR_PAM`;
- zastosowano identyczny dwuetapowy freeze/evaluation boundary.

### Wynik

- wybrana metoda: ARI `0.925940`, NMI `0.883635`;
- oracle target ma to samo ARI `0.925940` (remis obejmuje `R_PAIR_PAM`);
- regret `0.000000`;
- coverage `0.925234`;
- najmniejszy zaakceptowany klaster / cały target `0.401869`;
- accepted-subset ARI `1.0`.

### Ryzyko i odstępstwa

Brak odstępstwa. Bardzo dobry kierunek odwrotny nie może unieważnić
przekroczenia progu w pierwszym kierunku.

### Dokładne następne zadanie po etapie

Wydać Gate C bez zmiany kryteriów.

## Gate C

| Kryterium | Wynik | Status |
|---|---:|---|
| Regret ≤0.05 w jednym i ≤0.10 w drugim kierunku | 0.0000 / 0.1053 | FAIL |
| Obie decyzje zapisane przed oceną performance | tak | PASS |
| Coverage obu kierunków ≥0.80 | 0.8333 / 0.9252 | PASS |
| Każdy przypisany klaster ≥0.10 target | 0.3333 / 0.4019 | PASS |

Gate C: **STOP**.

Nie obniżono progu do `0.11`, nie zmieniono α, margin, selektora, coverage ani
metody po zobaczeniu etykiet. Nie rozpoczęto PILOT-016.

## Uwaga proceduralna o zaślepieniu

Podczas tworzenia adaptera, przed zamrożeniem transferu, pierwotna wersja testu
integracyjnego otworzyła plik y GSE10072 wyłącznie w module ewaluacyjnym, aby
sprawdzić zgodność sample ID i dwóch nazw klas. Nie policzono ARI/NMI, nie
wybrano metody i etykiety nie trafiły do fitowania; nazwy klas były już jawne w
protokole i upstreamowym manifeście. Test został następnie domyślnie
zapieczętowany i wymaga flagi uruchamianej dopiero po freeze.

Najściślejsza interpretacja clean-room powinna odnotować, że operator technicznie
odczytał y przed freeze, choć pierwsza **ocena performance** nastąpiła dopiero po
walidacji obu markerów. Ponieważ Gate C i tak jest STOP, raport nie wykorzystuje
tego zastrzeżenia do deklaracji sukcesu.

## Skonsolidowane testy

Po zamrożeniu obu kierunków:

```text
129 passed in 13.16 s
failed: 0
skipped: 0
```

Zakres obejmuje poprawność, deterministyczność, integralność SHA, source-only
fit, brak label imports w adapterach, target-value leakage, singleton-vs-batch
assignment, dokładne 630 komórek, atomowy pre-label boundary i golden PAM.

## Pliki wynikowe i dowody

- `docs/evidence/PILOT_012_015_SUMMARY.json`;
- `docs/evidence/PILOT_012_015_DETERMINISM.txt`;
- pełne wyniki lokalne: `results/full630_primary/` i
  `results/real_lung_primary/`;
- Gate B SHA: `dedd2af3...842603f`;
- Gate C SHA: `f6f380cc...9bccd`.

## Dokładne następne zadanie

Nie przechodzić automatycznie do PILOT-016. Najbezpieczniejszy następny blok to
zamknięcie i grant-ready raportowanie PILOT-019/020 z wynikiem „silne Gate B,
jednokierunkowo silny transfer, formalny Gate C STOP”. Alternatywnie potrzebna
jest jawna, prospektywna zmiana protokołu i niezależna nowa kohorta; obecnego
target nie wolno użyć do strojenia ani do retrospektywnego ratowania Gate C.
