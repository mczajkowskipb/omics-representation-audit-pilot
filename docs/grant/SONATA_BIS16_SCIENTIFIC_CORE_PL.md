# SONATA BIS 16 — rdzeń naukowy po pilotażu

Status: wersja robocza do redakcji wniosku, oparta na zamrożonym pilotażu z 17.08.2026  
Repozytorium pilota: commit `9adae889601486ffb5e9e29f29afe16cc1e1e698`  
Protokół: SHA-256 `5104901b66403ab29bbad24f7fdc48dda10121b1a584740ec47af02790d6a704`

## 1. Decyzja strategiczna

Decyzja po porównaniu dwóch skrajnych wariantów brzmi **MODIFY**. Projekt nie
powinien być ani wyłącznie projektem o TRPP, ani ogólną teorią wyboru
reprezentacji dla dowolnych danych. Powinien odpowiadać na jedno ograniczone
pytanie: kiedy w przenośnym grupowaniu danych omicznych zachować informację o
wartościach, kiedy zastąpić ją relacjami wewnątrz próbki, kiedy połączyć oba
widoki, a kiedy wstrzymać grupowanie.

Pilot daje mocny dowód kontrolowany, że reprezentacje wartościowe,
rankingowo-relacyjne i hybrydowe mają różne domeny kompetencji. Nie daje
natomiast podstaw do stwierdzenia, że selektor został już szeroko potwierdzony
między niezależnymi kohortami ani że direct regions są skuteczne.

Representation Audit powinien pełnić w projekcie rolę pierwszej, jawnej bramki: ma wskazać, czy dane source uzasadniają dalsze uczenie profili wartościowych, relacyjnych lub hybrydowych, albo czy należy wstrzymać grupowanie. Główną nowością metodologiczną pozostaje uczenie krótkich relacyjnych obszarów, które opisują grupę regułami wewnątrz pacjenta i mogą być zastosowane do nowej kohorty bez jej ponownego grupowania.

## 2. Proponowany tytuł i akronim

**Tytuł polski:** Adekwatność reprezentacji i przenośne profile relacyjne w grupowaniu danych omicznych

**Tytuł angielski:** Representation Adequacy and Transportable Relational Profiles in Omics Clustering

**Nazwa metody:** TRPP — Transportable Relational Patient Profiles

Tytuł celowo nie obiecuje, że relacje zawsze wygrają. TRPP pozostaje konkretną
rodziną metod rozwijaną w WP2-WP3, a nie akronimem narzucającym wynik WP1.

## 3. Problem naukowy

Grupowanie pacjentów w danych omicznych zwykle rozpoczyna się od arbitralnego wyboru geometrii danych: odległości euklidesowej na wartościach, korelacji, rang albo innego przekształcenia. Ten wybór jest często ukrytym założeniem, mimo że decyduje, które różnice między pacjentami uznaje się za biologicznie istotne. Stabilny klaster w jednej reprezentacji nie musi być stabilny w innej, a stabilność wewnątrz pojedynczej kohorty nie gwarantuje przenośności ani zgodności z klinicznie interesującym fenotypem.

Reprezentacje oparte na relacjach wewnątrz próbki, takich jak `gene_A > gene_B`, są atrakcyjne, ponieważ mogą być mniej zależne od skali pomiaru i mają bezpośrednią interpretację regułową. Nie są jednak uniwersalnie odporne: szum, przesunięcia genowo-specyficzne, remapowanie platform i niepełne pokrycie cech mogą odwracać relacje. Potrzebne są zatem dwie powiązane, lecz odrębne metody:

1. source-only mechanizm oceny, czy dana reprezentacja ma wystarczająco stabilną strukturę;
2. metoda ucząca bezpośrednio krótkie, przenośne obszary relacyjne zamiast jedynie opisywać klastry po fakcie.

## 4. Główna hipoteza

**H0-projektowa:** nie istnieje jedna reprezentacja właściwa dla wszystkich kohort omicznych, a stabilność wewnątrz jednej kohorty sama nie wystarcza do uzasadnienia biologicznego grupowania.

**Hipoteza główna:** mierzalne właściwości sygnału i przesunięcia między
kohortami wyznaczają, czy przenośne grupowanie powinno zachować wartości,
użyć relacji wewnątrz próbki, połączyć oba widoki albo zostać wstrzymane;
wewnątrz domeny relacyjnej biologicznie użyteczne podgrupy można opisać jako
rzadkie, zamrożone profile reguł.

Hipotezy szczegółowe:

- **H1 — adekwatność reprezentacji:** source-only diagnostyki stabilności,
  prediction strength, odporności na perturbacje oraz jawne własności
  invariance pozwalają rozróżniać domeny kompetencji VALUE, RELATIONAL i
  HYBRID oraz wykrywać brak stabilnej struktury;
- **H2 — regiony bezpośrednie:** bezpośrednia indukcja rzadkich regionów relacyjnych daje profile co najmniej równie przenośne jak relacyjny PAM z ekstrakcją post-hoc, przy większej stabilności lub krótszym opisie;
- **H3 — transfer bez refittingu:** profile zamrożone na source zachowują użyteczne przypisania i kalibrowane odrzucanie w niezależnych kohortach, bez dostrajania na target;
- **H4 — granice stosowalności:** rodzaj przesunięcia technicznego i biologicznego wyznacza przewidywalne warunki, w których relacje pomagają, są neutralne albo zawodzą.

Anchory nie powinny być osobną hipotezą główną. Mogą pozostać warunkową hipotezą obliczeniową uruchamianą dopiero po wykazaniu wartości direct regions.

## 5. Cele naukowe

### Cel 1. Mapa adekwatności reprezentacji

Opracować i zwalidować source-only Representation Audit dla VALUE, RELATIONAL, HYBRID i `NO_STABLE_STRUCTURE`, oddzielając wybór reprezentacji od oceny zgodności z etykietami.

### Cel 2. Bezpośrednie rzadkie regiony relacyjne

Opracować deterministyczny algorytm, który jednocześnie uczy przypisań i krótkich profili relacyjnych z rozróżnieniem reguł core/optional, kontrolą redundancji i możliwością pozostawienia próbki jako `UNASSIGNED`.

### Cel 3. Przenośne profile pacjentów

Zamrażać pełny artefakt source — cechy, preprocessing, relacje, stany, wagi, progi, profile i regułę przypisania — oraz oceniać go na niezależnych kohortach bez ponownego grupowania target.

### Cel 4. Empiryczne granice stosowalności

Wyznaczyć, które typy sygnału, szumu, braków cech i przesunięć platformowych sprzyjają wartościom, relacjom lub hybrydom, i sformułować zasady wstrzymania analizy, gdy stabilna interpretowalna struktura nie jest wsparta przez dane.

## 6. Wyniki wstępne — interpretacja bez nadinterpretacji

Pilot zrealizował deterministyczny, Python-first audit z jednym algorytmem PAM dla wszystkich reprezentacji oraz z fizycznym oddzieleniem etykiet. W pełnej siatce 630 par source-target poprawna rodzina reprezentacji została wskazana w 93,3% replikacji; mediana target-ARI regret wyniosła 0,000, false-structure rate w NULL 6,7%, fałszywy wybór HYBRID w czystych reżimach 0%, a korelacja Spearmana między różnicą source-only Q i różnicą zachowania target wyniosła 0,854. Wszystkie zamrożone kryteria Gate B zostały spełnione.

W 11 rzeczywistych zbiorach within-dataset audit wybrał RELATIONAL w 8 przypadkach, VALUE w 2 i HYBRID w 1. Wybór znajdował się w granicy 0,05 ARI od retrospektywnego oracle w 9/11 przypadków, a mediana regret wyniosła 0,011. Mediana ARI wybranej reprezentacji względem dostępnej etykiety wyniosła jednak tylko 0,065. Wynik pokazuje, że adekwatność geometrii niesuperwizowanej i zgodność z pojedynczą etykietą kliniczną są różnymi pytaniami.

W dwukierunkowym transferze GSE10072/GSE19804 jeden kierunek osiągnął ARI 0,926 i regret 0,000, natomiast drugi ARI 0,559 przy oracle 0,664, czyli regret 0,105284. Zamrożony limit odwrotnego kierunku wynosił 0,10. Formalna bramka zewnętrzna pozostała STOP; progu nie rozluźniono i nie wykonano strojenia po etykietach.

Ten mieszany wynik jest argumentem za projektem, jeśli zostanie przedstawiony jako wykryta luka: kontrolowane warunki są obiecujące, lecz transfer wymaga jawnego modelu obszaru stosowalności, wielu niezależnych kohort i profili uczonych bezpośrednio pod kątem stabilności, a nie retrospektywnego ratowania jednego selektora.

## 7. Koncepcja projektu i pakiety robocze

Rekomendowany czas realizacji: **48 miesięcy**. Jest wystarczający do utworzenia zespołu, opracowania metody, wielokohortowej walidacji i jednej kontrolowanej iteracji ulepszeń. Wariant 60-miesięczny ma sens tylko przy dołączeniu nowych danych generowanych w projekcie; dla badań opartych głównie na danych publicznych może wyglądać na nadmierny.

### WP1 — Representation adequacy and abstention, miesiące 1–12

- operacyjna analiza informacji zachowanej i traconej przez wartości, rangi,
  ternarne relacje i prostą hybrydę;
- taksonomia transformacji, wobec których każda reprezentacja jest niezmienna
  albo podatna, przełożona na falsyfikowalne reżimy symulacyjne;
- zamrożenie benchmarku, kohort i metadanych przed oceną;
- rozszerzenie controlled regimes o techniczne confoundery, niepełne mapowanie i unknown-K;
- kalibracja source-only diagnostyk oraz `NO_STABLE_STRUCTURE`;
- porównanie reprezentacji przy wspólnym deterministycznym silniku grupowania;
- rezultat: mapa kompetencji i prerejestrowany protokół dalszej walidacji.

**Bramka WP1:** dalsze uczenie profili jest dopuszczone tylko dla przypadków z niedegeneracyjną, ponad-NULL strukturą. Brak przejścia nie jest błędem algorytmu, lecz wynikiem naukowym.

### WP2 — Direct sparse relational regions, miesiące 7–24

- implementacja `RR_POSTHOC` jako jawnej bazy;
- implementacja `RR_DIRECT` z pełnym trace, deterministycznym rozwiązywaniem remisów i ochroną pustych klastrów;
- profile o rozmiarach 10, 25 i 50 relacji, z kontrolą relacji odwrotnych, redundancji i nadmiernego użycia jednego genu;
- core/optional relations oraz kalibrowane odrzucanie próbki;
- bootstrapowa ocena stabilności profili i porównanie z PAM.

**Bramka WP2:** `RR_DIRECT` musi względem `RR_POSTHOC` poprawić zewnętrzne ARI/NMI o co najmniej 0,05, zwiększyć bootstrap Jaccard o co najmniej 0,10 albo zachować wynik w granicy 0,03 przy istotnie krótszym profilu. W przeciwnym razie projekt pozostaje przy metodzie post-hoc i raportuje wynik negatywny.

### WP3 — Frozen multi-cohort TRPP transfer, miesiące 18–38

- wybór co najmniej dwóch modułów chorobowych, każdy z co najmniej trzema porównywalnymi kohortami;
- discovery wyłącznie w pierwszej kohorcie, zamrożenie artefaktu i niezależna aplikacja w kolejnych;
- kierunki A→B, A→C oraz kontrolne zamiany źródła tam, gdzie są biologicznie uzasadnione;
- porównanie z value PAM, relational PAM, hybrydą, klasycznym cluster-then-classify i `RR_POSTHOC`;
- ocena coverage, `UNASSIGNED`, retencji profilu, flip rate relacji oraz zgodności biologicznej po zamrożeniu wyników.

Nie wolno używać kohort B/C do doboru cech, relacji, wag, liczby klastrów, progów odrzucania ani wariantu metody.

### WP4 — Generalisation map and conditional efficiency, miesiące 31–48

- synteza wyników symulacyjnych i wielokohortowych w mapę domen kompetencji;
- analiza negatywnych i granicznych przypadków, w tym struktur stabilnych, lecz niezgodnych z etykietą;
- pojedynczy, warunkowy eksperyment anchor-to-feature tylko po przejściu bramki WP2;
- przygotowanie otwartej implementacji referencyjnej, manifestów i odtwarzalnych benchmarków.

Anchor sets nie wchodzą do zakresu podstawowego. Mogą być badaniem następczym dopiero po wykazaniu, że ograniczenie single-anchor daje co najmniej pięciokrotną redukcję kosztu bez straty ARI większej niż 0,03 i bez istotnego spadku coverage/stabilności.

## 8. Zasady metodyczne, których nie wolno osłabić

1. Preprocessing, wybór cech, screening relacji, dobór reprezentacji i progów odbywa się wyłącznie na source/train.
2. Etykiety są fizycznie odseparowane od modułów fit/audit i trafiają wyłącznie do końcowego modułu ewaluacji.
3. Target nie może być użyty do refittingu, normalizacji wspólnej, korekty batch ani dostrajania hiperparametrów w analizie podstawowej.
4. Matched comparison używa tego samego deterministycznego PAM; dodatkowe algorytmy są jedynie secondary baselines.
5. `NO_STABLE_STRUCTURE` i `UNASSIGNED` są pełnoprawnymi wynikami, a nie błędami do usunięcia.
6. Każdy wynik naukowy ma immutable prelabel artifact, manifest, hash i osobny etap evaluation-only.
7. Podstawowa implementacja pozostaje Python-first, CPU i deterministyczna; fuzzy clustering, algorytmy ewolucyjne, deep learning, federated learning, CUDA i portal są poza zakresem.

## 9. Ewaluacja

### Kontrolowane dane

- trafność decyzji VALUE/RELATIONAL/HYBRID/NO_STABLE_STRUCTURE;
- target ARI/NMI oraz regret względem retrospektywnego oracle;
- specificity pod NULL i odporność na nuisance;
- korelacja source-only diagnostyk z zachowaniem target;
- częstość nieuzasadnionego HYBRID.

### Kohorty rzeczywiste

- frozen-transfer ARI/NMI odczytywane dopiero po zamrożeniu;
- coverage, udział `UNASSIGNED`, minimalna liczebność grup;
- profile-state retention, relation flip rate i assignment margin;
- długość profilu, liczba genów, bootstrap Jaccard;
- analiza biologiczna jako ewaluacja wtórna, nigdy jako selektor metody.

### Testy techniczne

- golden optimum i deterministyczność PAM;
- invariance rang na przekształcenia monotoniczne oraz prawidłowe ties/missingness;
- niezmienność artefaktów source po zmianie wartości lub etykiet target;
- identyczność przypisania próbki target ocenianej osobno i w batchu;
- odrzucenie niekompletnych, niespójnych lub niezgodnych ze schematem zadań.

## 10. Ryzyka i reakcje

| Ryzyko | Znaczenie | Reakcja bez ratowania wyniku |
|---|---|---|
| Stabilny nuisance udaje biologię | wysokie | jawne perturbacje, metadane techniczne jako evaluation-only/diagnostic audit, wielokohortowa replikacja, ostrożna interpretacja |
| Selektor ma niski exact hit, lecz niski regret | średnie | zmiana tezy na adequacy ranking zamiast automatycznego rekomendowania jednej rodziny |
| Direct regions nie przewyższają post-hoc | wysokie | zatrzymanie RR_DIRECT; zachowanie post-hoc TRPP jako wyniku i publikacja granicy metody |
| Niskie pokrycie relacji między platformami | wysokie | zamrożony próg coverage i `UNASSIGNED`; bez target-driven wymiany relacji |
| Profile stabilne, lecz słabo zgodne z etykietą | wysokie | rozdzielenie stabilności struktury od zgodności fenotypowej; brak retrospektywnego label-guided tuningu |
| Koszt wszystkich par relacji | średnie | budżet M i redukcja redundancji; anchor restriction tylko po pozytywnej bramce bez anchor sets |
| Jedna para kohort daje przypadkowy rezultat | wysokie | co najmniej trzy kohorty na moduł chorobowy i raportowanie każdego kierunku, nie tylko najlepszego |

## 11. Nowatorstwo

Nowością nie jest samo użycie rang, PAM, wielu widoków ani regułowego opisu
klastrów. Multi-view clustering łączy reprezentacje, a istniejące metody
interpretable clustering uczą drzewa lub reguły. Nowość wynika z ich
specyficznego, rygorystycznego połączenia dla relacji wewnątrz próbki i
przenośności między kohortami:

- source-only wybór geometrii przed uczeniem profilu;
- jawne wstrzymanie przy braku stabilnej struktury;
- bezpośrednie uczenie rzadkich obszarów relacyjnych zamiast wyłącznie post-hoc opisu klastra;
- zamrożony transfer profilu do nowych pacjentów bez reclusteringu kohorty target;
- empiryczna mapa warunków, w których wartości, relacje lub hybrydy są właściwe;
- artefakty umożliwiające audyt leakage i odtworzenie każdej decyzji.

## 12. Zespół i wykonalność

Rekomendowany minimalny skład:

- PI: metodologia, architektura badań, reprezentacje relacyjne, nadzór i synteza;
- doktorant przez co najmniej wymagane 36 miesięcy: implementacja RR_DIRECT, eksperymenty i analiza stabilności;
- post-doc lub specjalista analityczny: benchmarki wielokohortowe, harmonizacja metadanych i niezależna walidacja;
- krótkie konsultacje dziedzinowe bez przenoszenia do nich odpowiedzialności za metodę.

Skład personalny trzeba zweryfikować względem szczególnych ograniczeń SONATA BIS 16: nowy zespół, zakaz części kategorii seniorów poza PI oraz ograniczenia dotyczące wcześniejszej wspólnej realizacji projektów konkursowych. Nazwisk nie należy wpisywać do tekstu, zanim ta kontrola nie zostanie zakończona.

Wykonalność wspierają: gotowy deterministyczny rdzeń Python z testami
poprawności, deterministyczności i braku leakage, pełny benchmark 630 par,
adaptery do 11 zbiorów, zamrożony transfer dwóch kohort i publiczne repozytoria
referencyjne. Niewykonane direct regions są planowanym przedmiotem badań, a nie
ukrytym brakującym rezultatem.

## 13. Co wymaga decyzji użytkownika przed wersją finalną

1. Czas projektu: rekomendowane 48 miesięcy.
2. Skład i role zespołu po kontroli formalnej SONATA BIS.
3. Dwa konkretne moduły chorobowe i trzecia kohorta w każdym module.
4. Czy współpraca Girona ma być formalnie opisana i czy obejmuje osobę wymienioną z nazwiska.
5. Wysokość budżetu, post-doc versus specjalista oraz model stypendium doktoranta.
6. Ostateczny panel i słowa pomocnicze; rekomendacja robocza: ST6, ST6_11, ST6_13, ewentualnie ST6_07.

Do czasu tych decyzji tekst jest kompletnym rdzeniem naukowym, ale nie finalnym wnioskiem OSF.
