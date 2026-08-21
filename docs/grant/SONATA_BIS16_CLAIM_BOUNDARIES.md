# Granice twierdzeń wynikających z pilota

Ten dokument jest blokadą redakcyjną. Nie zmienia protokołu ani wyników i nie tworzy nowej bramki.

## Zamrożony status

- Gate A: GO — poprawność, deterministyczność i bariery leakage potwierdzone.
- Gate B: GO — wszystkie pięć kryteriów pełnej siatki symulacyjnej spełnione.
- Gate C: STOP — jeden kierunek przekroczył dopuszczalny regret o `0.00528419284859625`.
- direct regions: NOT TESTED.
- anchors: NOT TESTED.
- jedenaście analiz within-dataset: wynik opisowy, nie zewnętrzna walidacja.

## Bezpieczne twierdzenia po polsku

1. W kontrolowanych warunkach audyt rozróżniał domeny kompetencji reprezentacji wartościowej, relacyjnej i hybrydowej oraz poprawnie wstrzymywał część analiz NULL.
2. W symulacjach source-only wynik audytu był silnie związany z późniejszym zachowaniem target, a regret wybranej reprezentacji był niski.
3. W większości rzeczywistych analiz within-dataset wybór reprezentacji był bliski najlepszemu wariantowi dostępnemu retrospektywnie, lecz same klastry często słabo odpowiadały etykietom.
4. Jedna z dwóch walidacji zewnętrznych była bardzo dobra, a drugi kierunek nie spełnił zamrożonego kryterium o niewielki margines.
5. Pilot uzasadnia badanie mapy adekwatności, mechanizmu wstrzymania i bezpośrednich profili relacyjnych, ale nie przesądza ich skuteczności.
6. Brak uruchomienia regionów i anchorów pokazuje respektowanie prerejestrowanej bramki, a nie brak technicznej możliwości dopasowania wyniku.

## Safe claims in English

1. Controlled experiments support distinct domains of competence for value, relational and hybrid representations.
2. The source-only audit achieved low selection regret and a strong association with target behaviour under controlled shifts.
3. Within-dataset stability and agreement with a particular clinical label were empirically distinct.
4. Bidirectional external transfer produced one strong and one threshold-failing direction; the mixed result motivates multi-cohort validation.
5. Direct relational regions and anchor restrictions remain prospective hypotheses.
6. The labels were used only after all source-only decisions and assignments had been frozen.

## Twierdzenia, których nie należy formułować

- że projekt tworzy uniwersalną teorię wyboru reprezentacji dla dowolnych
  danych albo meta-learner dla wielu dziedzin;
- że samo połączenie VALUE i RELATIONAL, użycie rang albo regułowy opis
  klastrów stanowi nowość;
- że znana invariance na wspólną transformację monotoniczną oznacza odporność
  na przesunięcia cechowe, zmianę sond, mapping platform lub każdy batch effect;
- że automatyczny selektor jest już uniwersalnym rozwiązaniem dla nowych kohort;
- że dwa kierunki transferu łącznie spełniły zamrożoną bramkę;
- że 11 analiz within-dataset zastępuje niezależną replikację;
- że stabilność niesuperwizowana dowodzi biologicznej albo klinicznej trafności grup;
- że relacje są z definicji odporne na każdy batch effect lub zmianę platformy;
- że regiony bezpośrednie, core/optional rules lub anchory mają już wyniki pilotażowe;
- że przekroczenie progu o 0,005 jest statystycznie nieistotne i może zostać zignorowane;
- że retrospektywny oracle jest metodą możliwą do zastosowania w praktyce bez etykiet target.

## Jak opisać wąskie niepowodzenie Gate C

Najlepsze sformułowanie:

> One transfer direction matched the retrospective oracle, whereas the reverse direction exceeded the preregistered ARI-regret allowance by 0.0053. We retained the formal STOP decision and performed no target-driven rescue. This result narrows the proposed claim from universal automatic selection to explicit representation-adequacy mapping and multi-cohort validation.

Nie należy nazywać wyniku „praktycznie zaliczonym”. Zamrożona bramka jest binarna. Można natomiast uczciwie wskazać, że skala przekroczenia jest mała i dlatego wynik wspiera dalsze, prerejestrowane badania zamiast porzucenia pytania naukowego.

## Co jest wynikiem, a co planem

| Element | Pilot | Wniosek |
|---|---|---|
| deterministyczny PAM i reprezentacje | wykonane i przetestowane | infrastruktura startowa |
| source-only Representation Audit | wykonany; Gate B pozytywny, Gate C mieszany | rozwinięcie i walidacja wielokohortowa |
| `NO_STABLE_STRUCTURE` | wykonane w symulacjach | pełnoprawny outcome projektu |
| post-hoc relational profiles | niewykonane po STOP | baza porównawcza do opracowania |
| direct sparse relational regions | niewykonane po STOP | główna hipoteza metodologiczna |
| single-anchor restriction | niewykonane po STOP | eksperyment warunkowy |
| anchor sets | poza podstawowym zakresem | nie wpisywać jako centralnego zadania |

## Granica narracji po decyzji MODIFY

Centralnym pytaniem jest adekwatność VALUE, RELATIONAL, HYBRID albo abstention
w przenośnym grupowaniu omicznym. Omika pozostaje jedynym podstawowym
testbedem, a TRPP główną rodziną metod rozwijaną dopiero dla przypadków, w
których reprezentacja relacyjna jest wsparta przez dane. Zmiana tytułu i
hipotezy głównej nie otwiera pilota, nie zmienia Gate C i nie tworzy wyniku dla
direct regions lub anchorów.

## Źródła dowodowe

- `docs/evidence/PILOT_019_VALIDATION.json` — pierwotne wartości i statusy;
- `docs/tables/gate_b_summary.csv` — pięć kryteriów Gate B;
- `docs/tables/external_transfer_results.csv` — dwa kierunki Gate C;
- `docs/tables/real_within_results.csv` — jedenaście analiz opisowych;
- `docs/PILOT_FINAL_REPORT.md` — interpretacja końcowa;
- `docs/DECISION_LOG.md` — zamrożone decyzje i zakaz retrospektywnego ratowania.
