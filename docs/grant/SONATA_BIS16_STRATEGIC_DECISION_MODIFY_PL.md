# SONATA BIS 16 - decyzja strategiczna po analizie wariantu szerszego

Data decyzji: 2026-08-21  
Decyzja: **MODIFY**  
Status pilota: bez zmian; protokół i wyniki pozostają zamrożone

## 1. Decyzja w jednym zdaniu

Nie przebudowujemy projektu w ogólną teorię reprezentacji dla dowolnych danych.
Przesuwamy natomiast punkt ciężkości z samej nazwy TRPP na jedno prostsze
pytanie: **kiedy informację o wartościach należy zachować, kiedy mogą ją
zastąpić relacje wewnątrz próbki, a kiedy potrzebne jest połączenie obu, aby
grupowanie omiczne było stabilne i przenośne?**

TRPP pozostaje główną rodziną metod i biomedycznym rezultatem projektu, ale nie
jest już przedstawiane jako odpowiedź założona z góry.

## 2. Dlaczego nie wybieramy skrajnego wariantu A ani B

| Kryterium | Wariant A: projekt wyłącznie TRPP | Wariant B: ogólne absolute/relational/hybrid | Decyzja MODIFY |
| --- | --- | --- | --- |
| Jasność pytania | konkretna metoda, ale nazwa wyprzedza dowód | intuicyjne pytanie, lecz zbyt szerokie | jedno pytanie ograniczone do przenośnego grupowania omicznego |
| Wsparcie pilota | direct regions nie były testowane | Gate B bezpośrednio wspiera różne domeny kompetencji | wykorzystuje Gate B, a Gate C traktuje jako otwartą lukę |
| Nowość | relacyjne profile są charakterystyczne | sam wybór lub łączenie reprezentacji jest zatłoczoną dziedziną | nowość wynika z audytu source-only, abstention, regionów i frozen transfer |
| Ryzyko zakresu | umiarkowane | wysokie: wiele danych, relacji i shiftów | omika jest jedynym głównym testbedem; cztery WP |
| Zrozumiałość | wymaga natychmiastowego wyjaśnienia TRPP | łatwe hasło, trudny do ograniczenia program | problem -> intuicja -> przykład -> hipotezy -> metoda |
| Zespół SONATA BIS | dobry temat algorytmiczno-biomedyczny | grozi rozproszonym zespołem „AI do wszystkiego” | spójne role: metoda, doktorat, niezależna walidacja |

Wniosek jest więc **modyfikacją**, a nie zmianą dyscypliny ani dodaniem nowych
rodzin algorytmów.

## 3. Centralne pytanie badawcze

> Under which source-observable conditions should magnitude information be
> retained, replaced by within-sample relational information, or combined with
> it to obtain stable and transportable clustering in high-dimensional omics
> data?

Prostym językiem: zanim pogrupujemy pacjentów, sprawdzamy, jaki sposób ich
porównywania jest uzasadniony przez kohortę źródłową. Dopiero potem uczymy
krótki profil grupy i sprawdzamy go bez dostrajania na nowych kohortach.

## 4. Hipotezy falsyfikowalne

1. **H1 - mierzalne domeny kompetencji.** VALUE, RELATIONAL i HYBRID mają
   odmienne, powtarzalne domeny kompetencji wyznaczane przez rodzaj sygnału,
   szumu, braków cech i przesunięcia między kohortami.
2. **H2 - ocena source-only i wstrzymanie.** Diagnostyki obliczone bez etykiet i
   bez danych target pozwalają uzyskać niski regret względem retrospektywnego
   oracle albo jawnie zwrócić `NO_STABLE_STRUCTURE`; nie muszą zawsze trafiać w
   dokładną rodzinę.
3. **H3 - bezpośrednie regiony relacyjne.** `RR_DIRECT` przewyższa
   `RR_POSTHOC` co najmniej jednym z prerejestrowanych efektów: wynikiem
   zewnętrznym, stabilnością profilu albo kompresją bez istotnej straty.
4. **H4 - przenośność ma granice.** Zamrożone profile zachowują użyteczne
   przypisania tylko wewnątrz jawnej domeny pokrycia, marginesu i shiftu; poza
   nią poprawnym wynikiem jest `UNASSIGNED` albo negatywny transfer.

## 5. Architektura projektu - cztery pakiety robocze

### WP1. Representation adequacy, invariance and abstention

- operacyjna analiza informacji zachowanej i traconej przez wartości, rangi,
  ternarne relacje i hybrydę;
- jawna taksonomia transformacji: wspólne transformacje monotoniczne,
  przesunięcia cechowe, szum, kwantyzacja, braki i mapping platform;
- source-only Representation Audit, NULL i `NO_STABLE_STRUCTURE`;
- jeden deterministyczny PAM w podstawowym porównaniu.

Nie obiecujemy kompletnej teorii informacji dla wszystkich reprezentacji.
Formalizacja ma prowadzić do testowalnych przewidywań dla z góry ustalonej
rodziny reprezentacji i zakłóceń.

### WP2. Direct sparse relational regions

- najpierw mocna baza `RR_POSTHOC`;
- następnie deterministyczny `RR_DIRECT` z krótkimi regułami core/optional;
- jawne progi pokrycia i możliwość pozostawienia próbki bez przypisania;
- bramka zatrzymująca metodę, jeżeli nie poprawia wyniku, stabilności ani
  długości profilu.

### WP3. Frozen multi-cohort transfer

- omika jako główny i jedyny podstawowy testbed;
- co najmniej trzy kohorty na moduł chorobowy;
- pełny artefakt uczony na source i stosowany do target bez refittingu,
  wspólnej normalizacji ani target tuning;
- raportowanie wszystkich zarejestrowanych kierunków, także negatywnych.

### WP4. Applicability map and reproducible release

- mapa warunków, w których wartość, relacja, hybryda lub abstention są
  uzasadnione;
- synteza symulacji i walidacji wielokohortowej;
- otwarta implementacja referencyjna i audytowalne artefakty;
- wyłącznie warunkowy eksperyment single-anchor po przejściu bramki WP2.

## 6. Granice zakresu

### Wchodzi

- high-dimensional numerical omics data;
- VALUE, rank/Footrule, ternary pair relations i prosty HYBRID;
- deterministyczne PAM, source-only audit, NULL i abstention;
- post-hoc i direct sparse relational regions;
- frozen cross-cohort transfer w dwóch modułach chorobowych;
- analiza jawnie zdefiniowanych invariance i failure modes.

### Nie wchodzi

- ogólny meta-learner wybierający algorytmy dla setek dziedzin;
- defence/PYTHIA, finance, IoT, social data, GNN i Hawkes processes;
- dodatkowy podstawowy testbed EEG przed zamknięciem głównej walidacji
  omicznej;
- deep learning, fuzzy clustering, algorytmy ewolucyjne, federated learning,
  CUDA i portal;
- nieograniczona rodzina differences/ratios/group relations w jednym grancie;
- anchor sets i pełny direct hybrid-region optimiser jako zadania podstawowe.

## 7. Rola omiki i TRPP

**Omika jest częścią problemu badawczego, a nie tylko demonstratorem.** To w
niej jednocześnie występują low-n/high-p, batch effects, niezgodność platform,
braki mapowania oraz potrzeba zastosowania modelu do pojedynczej nowej próbki.

**TRPP jest głównym rezultatem metodycznym WP2-WP3.** Nazwa oznacza rodzinę
zamrożonych, interpretowalnych profili pacjentów. Nie oznacza, że relacje są
zawsze wybierane; WP1 może wskazać VALUE, HYBRID albo brak podstaw do
grupowania.

## 8. Co pilot już wspiera, a czego nie wspiera

- Gate B: **GO** - 630 kontrolowanych par wspiera istnienie różnych domen
  kompetencji i source-only ocenę ich adekwatności.
- Jedenaście analiz realnych jest opisowych: wybór był często bliski oracle,
  lecz mediana zgodności z etykietą była niska.
- Gate C: **STOP** - jeden kierunek przekroczył zamrożony limit regret o
  `0.005284`; nie wolno przedstawiać selektora jako potwierdzonego zewnętrznie.
- direct regions: **NOT TESTED**.
- anchors: **NOT TESTED**.

Nie jest potrzebny nowy eksperyment przed zmianą narracji. Istniejący pilot już
jest minimalnym eksperymentem VALUE/RELATIONAL/HYBRID pod kontrolowanymi
perturbacjami. Dalsze liczenie po ujawnieniu wyników nie może zmienić bramek.

## 9. Ryzyko nowości - czego nie wolno twierdzić

Łączenie wielu widoków danych ma rozbudowaną literaturę multi-view i
multiple-kernel clustering. Istnieją także metody wspólnie uczące klastry i
regułowe lub drzewiaste wyjaśnienia. W transkryptomice porównywano już
single-sample reguły genowe z centroidami. Dlatego nowością nie może być samo
hasło „hybrid”, „rules” ani „ranks are robust”.

Pozycja projektu jest węższa: **source-only adequacy + jawne abstention +
within-sample relational regions + frozen multi-cohort transfer + fizyczna
bariera etykiet**. Literatura pokazuje też, że relacje nie są bezwarunkowo
odporne: w analizie REO około 20% stabilnych relacji wspólnych dla dwóch
platform miało niezgodny kierunek z powodu konstrukcji sond. To wzmacnia rolę
mapy stosowalności zamiast obietnicy uniwersalnej invariance.

Wybrane punkty odniesienia:

- Kumar A, Rai P, Daume H. Co-regularized Multi-view Spectral Clustering.
  *NeurIPS 24*, 2011. <https://proceedings.neurips.cc/paper/2011/hash/31839b036f63806cba3f47b93af8ccb5-Abstract.html>
- Bertsimas D, Orfanoudaki A, Wiberg H. Interpretable clustering: an
  optimization approach. *Machine Learning* 110, 89-138, 2021.
  <https://doi.org/10.1007/s10994-020-05896-2>
- Carrizosa E, Kurishchenko K, Marin A, Romero Morales D. On clustering and
  interpreting with rules by means of mathematical optimization. *Computers &
  Operations Research* 154, 106180, 2023.
  <https://doi.org/10.1016/j.cor.2023.106180>
- Eriksson P et al. A comparison of rule-based and centroid single-sample
  multiclass predictors for transcriptomic classification. *Bioinformatics*
  38, 1022-1029, 2022. <https://doi.org/10.1093/bioinformatics/btab763>
- Guan Q et al. Differential expression analysis for individual cancer samples
  based on robust within-sample relative gene expression orderings across
  multiple profiling platforms. *Oncotarget* 7, 68909-68920, 2016.
  <https://doi.org/10.18632/oncotarget.11996>

## 10. Naturalne strumienie publikacyjne

1. Representation adequacy, invariance taxonomy and abstention benchmark.
2. Direct sparse relational regions versus post-hoc explanation.
3. Frozen multi-cohort transfer in lung omics.
4. Frozen multi-cohort transfer in colorectal omics.
5. Cross-module applicability map and negative transfer analysis.

To pięć różnych pytań badawczych, a nie dzielenie jednego benchmarku na małe
publikacje.

## 11. Minimalny zespół

- PI: metodologia, reprezentacje relacyjne, bramki i synteza;
- doktorant: `RR_DIRECT`, testy poprawności i stabilność profili;
- post-doc lub specjalista: niezależna kuracja kohort, mapping i walidacja;
- konsultacje biomedyczne tylko dla interpretacji i kwalifikacji kohort.

## 12. Tytuł

Rekomendowany:

- **PL:** Adekwatność reprezentacji i przenośne profile relacyjne w grupowaniu
  danych omicznych
- **EN:** Representation Adequacy and Transportable Relational Profiles in
  Omics Clustering

TRPP pozostaje nazwą rodziny metod, nie musi być akronimem całego projektu.

Alternatywy rezerwowe:

1. When Are Relational Representations Adequate for Transportable Omics
   Clustering?
2. Source-only Representation Adequacy for Transportable Omics Clustering
3. Value, Relational and Hybrid Geometries in Cross-cohort Omics Clustering
4. Applicability Boundaries of Relational Representations in Omics Clustering
5. From Representation Audit to Transportable Relational Patient Profiles

## 13. Lekcja z poprzedniego OPUS

W krótkim opisie należy konsekwentnie utrzymać kolejność:

`PROBLEM -> INTUICJA -> PROSTY PRZYKLAD -> HIPOTEZY -> METODA -> BRAMKI`

Nie zaczynamy od nazw algorytmów, list relacji ani infrastruktury. Recenzent ma
najpierw zrozumieć, że jedna kohorta może wyglądać inaczej zależnie od sposobu
porównywania pacjentów, a projekt ma ustalić, który sposób jest uzasadniony i
czy przenosi się do nowych kohort.
