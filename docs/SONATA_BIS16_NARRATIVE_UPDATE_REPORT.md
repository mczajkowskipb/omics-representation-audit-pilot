# SONATA BIS 16 - raport aktualizacji narracji po decyzji MODIFY

Data: 2026-08-21  
Zakres: krytyczna ocena wariantu zaproponowanego przez drugi chat i aktualizacja
pakietu wniosku  
Status protokołu: bez zmian; nadrzędny protokół pilota pozostaje wiążący

## Wynik w prostych słowach

Z propozycji wykorzystano najlepszy element: projekt powinien zaczynać się od
pytania, **jak należy porównywać pacjentów przed ich grupowaniem**. Wartości,
relacje rankingowe i prosta hybryda są porównywane uczciwie tym samym PAM.
Dopiero po tej ocenie powstaje medoid, a w planowanym projekcie także krótki
obszar reguł opisujący grupę. Zamrożony model jest następnie sprawdzany na nowej
kohorcie bez dostrajania.

Decyzja to **MODIFY**, nie pełne przyjęcie wariantu szerokiego. Omika pozostaje
jedynym głównym obszarem zastosowania, a TRPP główną rodziną metod. Nie dodano
EEG, ogólnego meta-learningu, nowych rodzin relacji ani kolejnych algorytmów.

## Wykonane zmiany

- przeniesiono centralny akcent z nazwy TRPP na falsyfikowalne pytanie o
  adekwatność reprezentacji VALUE, RELATIONAL i HYBRID;
- zachowano `NO_STABLE_STRUCTURE`, fizyczne oddzielenie etykiet, source-only
  preprocessing i brak target tuning;
- uporządkowano projekt w cztery pakiety: adequacy i abstention, direct sparse
  relational regions, frozen multi-cohort transfer oraz applicability map;
- jawnie oddzielono to, co pilot potwierdza, od direct regions i anchors, które
  pozostają `NOT TESTED`;
- dodano granicę nowości wobec multi-view clustering, interpretable clustering
  i istniejących reguł genowych;
- uproszczono streszczenia i opisy według kolejności: problem, intuicja, prosty
  przykład, hipotezy, metoda i bramki;
- zachowano techniczną nazwę paczki zawierającą `TRPP` dla zgodności z
  poprzednimi wydaniami.

## Pliki utworzone

- `.gitattributes` - traktuje generowane PDF-y jako pliki binarne w Git;
- `docs/grant/SONATA_BIS16_STRATEGIC_DECISION_MODIFY_PL.md`;
- `docs/SONATA_BIS16_NARRATIVE_UPDATE_REPORT.md`.

## Pliki zmienione

- `README.md`;
- `docs/DECISION_LOG.md`;
- `docs/FILES_AND_ARCHIVES_MANIFEST_PL.md`;
- `docs/SONATA_BIS16_COMPLETION_REPORT.md`;
- `docs/grant/CLAIMS_EVIDENCE.json`;
- `docs/grant/README.md`;
- `docs/grant/README_FIRST_PL.md`;
- `docs/grant/SONATA_BIS16_CLAIM_BOUNDARIES.md`;
- `docs/grant/SONATA_BIS16_DEFAULTS_FROZEN.md`;
- `docs/grant/SONATA_BIS16_DETAILED_DESCRIPTION_EN_DRAFT.md`;
- `docs/grant/SONATA_BIS16_OSF_STARTER_PL_EN.md`;
- `docs/grant/SONATA_BIS16_POPULAR_SUMMARY_EN.md`;
- `docs/grant/SONATA_BIS16_POPULAR_SUMMARY_PL.md`;
- `docs/grant/SONATA_BIS16_SCIENTIFIC_CORE_PL.md`;
- `docs/grant/SONATA_BIS16_SHORT_DESCRIPTION_EN.md`;
- `docs/package/ALL_IN_ONE_README_PL.md`;
- `scripts/11_generate_grant_pdfs.py`;
- `scripts/12_build_handoff_package.py`;
- `tests/unit/test_grant_package.py`;
- `tests/unit/test_grant_pdfs.py`;
- `tests/unit/test_repository_handoff.py`;
- cztery wygenerowane PDF-y w `output/pdf/` oraz ich dwa raporty walidacyjne w
  `docs/evidence/`.

Nie zmieniono kodu naukowego w `src/`, konfiguracji eksperymentalnych, danych,
zamrożonych wyników ani protokołu.

## Uruchomione testy i wyniki

- testy skupione na narracji, PDF-ach i paczce: **15 passed**;
- pełny lokalny zestaw: **150 passed, 3 skipped, 0 failed**;
- pominięcia są oczekiwane: dwa wymagają osobnych, niekopiowanych repozytoriów
  referencyjnych, a jedno pozostawia etykiety realne zamknięte do jawnie
  autoryzowanej fazy ewaluacji;
- walidacja twierdzeń: **12 dokumentów, 0 zabronionych nadinterpretacji**;
- statusy dowodów zachowane: Gate B `GO`, Gate C `STOP`, direct regions i
  anchors `NOT_TESTED`;
- kompilacja `src`, `scripts` i `tests`: bez błędów;
- kontrola zależności: bez konfliktów;
- cztery PDF-y wygenerowane dwukrotnie: identyczne bajtowo, odpowiednio
  **6, 15, 1 i 1 stron**;
- wszystkie 23 strony wyrenderowano do obrazów i skontrolowano wizualnie: brak
  obcięcia tekstu, nakładania elementów i uszkodzonych znaków.

Testy braku leakage obejmują między innymi brak kanału etykiet w
`DatasetBundle`, brak parametrów target/labels w interfejsach fit i audit,
niezmienność artefaktu source po zmianie target oraz fizyczną kolejność
prelabel przed evaluation.

## Wykryte ryzyka

- Gate C pozostaje `STOP`; wynik przekraczający próg o `0.005284` nie może być
  przedstawiany jako potwierdzona walidacja zewnętrzna selektora.
- Samo połączenie wielu reprezentacji, użycie rang lub reguł nie wystarcza jako
  nowość. Teza musi pozostać przy source-only adequacy, abstention, regionach
  wewnątrz próbki i zamrożonym transferze.
- Relacje genowe nie są automatycznie odporne na każdą zmianę platformy;
  potrzebne są coverage, `UNASSIGNED` i jawna mapa stosowalności.
- Direct regions mogą nie przewyższyć mocnej bazy post-hoc. Projekt zawiera
  bramkę zatrzymania zamiast obietnicy sukcesu.
- Zbyt szeroka narracja ponownie utrudniłaby ocenę. EEG i inne dziedziny nie
  powinny trafiać do głównego planu.
- Dane zespołu, dorobku PI, budżetu, instytucji i współpracy nie mogą być
  uzupełnione bez zweryfikowanych informacji użytkownika.

## Odstępstwa od protokołu

**Brak.** Zmiana dotyczy wyłącznie narracji przyszłego wniosku. Nie zmieniono
progów, reprezentacji w pilocie, PAM, podziału source/target, zasad użycia
etykiet ani decyzji GO/STOP. Nie uruchomiono PILOT-016--018 i nie zmodyfikowano
repozytoriów referencyjnych.

## Dokładne następne zadanie

Nie należy wykonywać kolejnego ratunkowego eksperymentu. Następny blok to
finalizacja wniosku z danymi, których nie można zgadnąć: osoby i role, dorobek
PI, budżet, kwalifikowalność, współpraca, etyka/DMP, dane jednostki i aktualny
formularz OSF. Po ich otrzymaniu trzeba wykonać jedną końcową kontrolę
formalną, limitów i spójności tekstu.
