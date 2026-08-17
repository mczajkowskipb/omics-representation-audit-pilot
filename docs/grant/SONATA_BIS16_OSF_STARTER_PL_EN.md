# SONATA BIS 16 — pakiet startowy do OSF

Status: roboczy, do potwierdzenia danych administracyjnych i zespołu  
Aktualność wymogów: sprawdzono 17.08.2026 na podstawie [ogłoszenia SONATA BIS 16](https://www.ncn.gov.pl/ogloszenia/konkursy/sonata-bis16) i [wzoru formularza](https://www.ncn.gov.pl/sites/default/files/pliki/formularze/sonatabis16_wzor_formularza_wniosku.pdf).

## 1. Dane podstawowe — rekomendacja

| Pole | Wartość robocza |
|---|---|
| Czas realizacji | 48 miesięcy |
| Tytuł PL | Przenośne relacyjne profile pacjentów do interpretowalnego grupowania danych omicznych |
| Title EN | Transportable Relational Patient Profiles for Interpretable Clustering of Omics Data |
| Akronim | TRPP |
| Obszar | ST |
| Panel główny | ST6 — Informatyka i technologie informacyjne |
| Określenia pomocnicze | ST6_11, ST6_13; opcjonalnie ST6_07 |
| Planowany charakter | badania podstawowe, metodologia uczenia niesuperwizowanego i bioinformatyka |

Słowa kluczowe PL:

`interpretowalne uczenie maszynowe; grupowanie; dane omiczne; relacje wewnątrz próbki; rangi; transfer między kohortami; stabilność klastrów; profile pacjentów`

Keywords EN:

`interpretable machine learning; clustering; omics data; within-sample relations; ranks; cross-cohort transfer; cluster stability; patient profiles`

## 2. Abstract — wersja angielska

High-dimensional omics clustering usually starts with an implicit and rarely tested decision: how should two patients be compared? Distances computed from scaled measurements, within-sample ranks, and pairwise ordering relations encode different biological and technical assumptions. A stable partition under one representation may disappear under another, and stability within a discovery cohort does not guarantee transfer to an independent cohort. This project will develop Transportable Relational Patient Profiles (TRPP), an interpretable framework in which representation adequacy is evaluated using source data only, sparse cluster profiles are learned as within-patient ordering rules, and the complete model is frozen before application to independent cohorts.

The project has four objectives. First, it will establish a representation-adequacy map for value, relational and hybrid geometries, including an explicit NO_STABLE_STRUCTURE outcome. Second, it will develop deterministic direct sparse relational regions and compare them with ordinary relational clustering followed by post-hoc profile extraction. Third, it will test frozen profiles across independent omics cohorts without target refitting, joint normalisation or target-driven feature selection. Fourth, it will identify the signal, noise, missing-feature and platform-shift conditions under which relational information is useful, neutral or misleading.

Preliminary experiments implemented a leakage-controlled, deterministic Python pipeline using the same PAM clustering engine for all representations. Across 630 controlled source-target pairs, the source-only audit identified the generating representation family in 93.3% of replicates, with median target ARI regret of 0.000 and a source-to-target Spearman association of 0.854. Results on eleven real datasets were more cautious: the selected representation was usually close to the retrospective within-dataset oracle, but median agreement with available labels was low. In bidirectional transfer between GSE10072 and GSE19804, one direction was strong whereas the reverse direction narrowly exceeded the preregistered regret limit. This mixed result motivates, rather than resolves, the proposed research: robust patient profiles require explicit applicability limits, multiple independent cohorts and direct profile learning.

The expected outcome is a falsifiable theory and open reference implementation for deciding when relational patient profiles should be learned, how they can be transferred without reclustering target data, and when clustering should be withheld. The project will advance interpretable unsupervised learning by treating representation choice, abstention and cross-cohort transportability as first-class scientific problems.

## 3. Streszczenie popularnonaukowe — PL

Badania omiczne mierzą jednocześnie aktywność tysięcy genów lub innych cząsteczek u każdego pacjenta. Jednym z głównych celów analizy jest odnalezienie grup pacjentów o podobnych mechanizmach choroby. Wynik takiego grupowania zależy jednak od sposobu porównywania osób. Możemy porównywać bezpośrednie wartości pomiarów albo pytać, które geny mają u danego pacjenta wyższą aktywność niż inne. Drugi sposób prowadzi do prostych reguł, na przykład „gen A jest bardziej aktywny niż gen B”, które mogą być łatwiejsze do interpretacji i mniej zależne od skali laboratoryjnej. Nie zawsze są jednak lepsze.

Celem projektu jest opracowanie przenośnych relacyjnych profili pacjentów. Najpierw program, korzystając wyłącznie z kohorty źródłowej, sprawdzi, czy dane uzasadniają porównywanie wartości, rang lub obu rodzajów informacji. Gdy żadna reprezentacja nie daje wiarygodnej struktury, program będzie mógł wstrzymać grupowanie. Następnie dla stabilnych grup utworzy krótkie profile złożone z relacji między cechami. Pełny profil zostanie zamrożony i zastosowany do pacjentów z niezależnej kohorty bez ponownego grupowania tej kohorty i bez dostrajania modelu do jej wyników.

Badania obejmą kontrolowane symulacje i wiele niezależnych zbiorów omicznych. Porównamy profile relacyjne z klasycznym grupowaniem wartościowym, rankingowym i hybrydowym. Ocenimy nie tylko zgodność z dostępnymi etykietami, lecz także stabilność profili, ich długość, pokrycie cech, odporność na różnice platform laboratoryjnych i zdolność do pozostawienia niepewnego pacjenta bez przypisania.

Wyniki wstępne pokazują, że różne sposoby reprezentacji rzeczywiście działają najlepiej w różnych warunkach, ale także że stabilna struktura nie musi odpowiadać konkretnej etykiecie klinicznej. Projekt nie zakłada więc, że relacje zawsze wygrywają. Jego wynikiem będzie zestaw metod i jawnych zasad określających, kiedy relacyjne profile pacjentów są wiarygodne, kiedy należy wybrać inną reprezentację, a kiedy uczciwym wynikiem jest rezygnacja z grupowania.

## 4. Abstract for the general public — EN

Omics studies measure thousands of genes or other molecular features in every patient. A common goal is to identify patient groups that may reflect different disease mechanisms. However, the resulting groups depend strongly on how patients are compared. We may compare measurement values directly, or ask which features are higher than others within the same patient. The latter approach creates readable rules such as “gene A is more active than gene B” and may be less sensitive to laboratory scale differences, but it is not universally superior.

This project will develop Transportable Relational Patient Profiles. Using only a discovery cohort, the method will first determine whether value, rank-based or combined comparisons are supported by stable structure. It will also be allowed to report that no stable structure is present. For supported cases, it will learn short profiles made of ordering relations. The complete profile will then be frozen and applied to patients from independent cohorts without regrouping those cohorts or tuning the method to their outcomes.

The research will combine controlled simulations with multiple independent omics datasets. Relational profiles will be compared with standard value-based, rank-based and hybrid clustering. Evaluation will cover profile stability, interpretability, missing-feature coverage, resistance to laboratory and platform shifts, agreement with external biological information, and the ability to leave uncertain patients unassigned.

Preliminary findings show both promise and an important limitation: different representations work best under different conditions, but a stable data structure does not necessarily match a particular clinical label. The project therefore does not assume that relational methods always win. Its outcome will be a set of transparent methods and rules defining when relational patient profiles are credible, when another representation is preferable, and when clustering should be withheld.

## 5. Plan badań — nazwy zadań PL/EN

Nazwy są sformułowane jako zadania badawcze, a nie zakupy, wyjazdy lub przygotowanie publikacji.

| Nr | Nazwa PL | Name EN | Miesiące |
|---:|---|---|---:|
| 1 | Ocena adekwatności reprezentacji i kalibracja wstrzymania grupowania | Representation adequacy assessment and clustering-abstention calibration | 1–12 |
| 2 | Bezpośrednie uczenie rzadkich relacyjnych obszarów pacjentów | Direct learning of sparse relational patient regions | 7–24 |
| 3 | Zamrożony transfer profili relacyjnych między niezależnymi kohortami | Frozen transfer of relational profiles across independent cohorts | 18–38 |
| 4 | Wyznaczenie granic stosowalności i uogólnienie profili TRPP | Applicability-boundary mapping and generalisation of TRPP profiles | 31–48 |

## 6. Wyniki wstępne — skrót do pola/sekcji

The pilot established a deterministic source-only Representation Audit with physical separation of labels and a shared PAM engine across value, relational and hybrid representations. In 630 controlled source-target pairs, all frozen simulation criteria passed: exact family identification was 0.933, median target ARI regret was 0.000, the NULL false-structure rate was 0.067, HYBRID was never selected in pure regimes, and the source-audit/target-performance Spearman association was 0.854. In eleven real within-dataset audits, the selected representation was within 0.05 ARI of the retrospective oracle in 9/11 cases, but the median selected ARI against available labels was only 0.065. Bidirectional GSE10072/GSE19804 transfer produced one strong direction (ARI 0.926, regret 0.000) and one weaker direction (ARI 0.559 versus oracle 0.664; regret 0.105), narrowly failing the frozen 0.10 reverse-direction limit. No threshold was relaxed and target labels were not used for tuning. Direct relational regions and anchors were therefore not evaluated in the pilot and remain prospective research tasks.

## 7. Uzasadnienie nowego zespołu — rdzeń

The project requires a new team because it combines three workloads that cannot be credibly delivered as a single-investigator extension of existing code: development and formal testing of a new direct relational clustering family; independent multi-cohort bioinformatics and metadata harmonisation; and leakage-controlled, reproducible evaluation across simulations and real datasets. The PI contributes established expertise in interpretable relational learning and omics analysis. A doctoral researcher will develop and analyse direct relational regions as a coherent dissertation topic, while a competitively recruited post-doctoral researcher or specialist analyst will lead cross-cohort benchmarking and independent reproducibility checks. The separation of method development from validation is deliberate and reduces confirmation bias.

Tekst trzeba dostosować po wyborze rodzaju stanowiska i sprawdzeniu, czy kandydaci spełniają warunki konkursowe dotyczące nowego zespołu.

## 8. Checklista formalna do potwierdzenia

Według dokumentacji konkursowej aktualnej 17.08.2026:

- termin wysłania: **15.09.2026, godz. 14:00 CEST**;
- opis skrócony: po angielsku, maksymalnie 5 stron A4 plus literatura;
- opis szczegółowy: po angielsku, maksymalnie 15 stron A4 plus literatura;
- oba opisy muszą samodzielnie zawierać wszystkie wymagane informacje, ponieważ są czytane na różnych etapach;
- popularnonaukowe streszczenia PL i EN: dwa osobne pliki, każde maksymalnie 1 strona A4;
- czas projektu: 36, 48 albo 60 miesięcy;
- zaangażowanie doktoranta/doktorantów przez łącznie co najmniej 36 miesięcy jest obowiązkowe;
- PI: doktorat w latach 2014–2021 dla tej edycji; doktorat z 2015 r. mieści się w tym zakresie, ale dane OSF trzeba sprawdzić;
- PI musi być zatrudniony w jednostce realizującej co najmniej na 1/2 etatu przez cały projekt i spełniać wymóg dyspozycyjności w Polsce;
- trzeba zweryfikować limit kierowanych projektów/wniosków oraz zależność od ewentualnego OPUS;
- trzeba wykazać publikacje retraktowane albo jawnie wskazać brak, zgodnie z nowym polem konkursu;
- wszystkie osoby wymienione z nazwiska w dowolnej części muszą znaleźć się w sekcji „Osoby wskazane we wniosku” i zostać poinformowane;
- należy sprawdzić wewnętrzny termin Politechniki Białostockiej, podpisy i dane jednostki — termin uczelniany będzie wcześniejszy niż NCN;
- wybór panelu jest nieodwracalny po wysłaniu; ST6 jest rekomendacją, nie zatwierdzoną decyzją;
- wykorzystanie AI do redakcji jest przez NCN dopuszczalne, lecz PI odpowiada za treść, źródła, prawa autorskie i rzetelność naukową.

## 9. Brakujące dane przed wersją do wysłania

- ostateczny tytuł i 3 pomocnicze określenia identyfikujące;
- decyzja 48/60 miesięcy;
- dane i model zatrudnienia doktoranta oraz post-doc/specjalisty;
- lista wcześniejszych wspólnych projektów członków zespołu;
- budżet oraz uzasadnienia kosztów;
- konkretne kohorty w dwóch modułach chorobowych;
- deklaracja współpracy międzynarodowej, osoby i korzyści;
- plan zarządzania danymi, kwestie etyczne i dual-use;
- 5–10 osiągnięć PI, 1–3 załączone publikacje oraz potwierdzenie przyjęcia pracy accepted, jeśli nie ma jeszcze wersji opublikowanej;
- wykaz zbliżonych zadań badawczych i rozdzielenie względem zakończonego OPUS 17 oraz planowanego OPUS 32.
