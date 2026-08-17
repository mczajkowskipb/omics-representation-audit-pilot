# Raport wykonawczy — blok grant-ready po zamknięciu pilota

Data: 2026-08-17  
Stan bazowy: commit `9adae889601486ffb5e9e29f29afe16cc1e1e698`  
Protokół SHA-256: `5104901b66403ab29bbad24f7fdc48dda10121b1a584740ec47af02790d6a704`

## Wynik

Przygotowano pierwszy kompletny pakiet redakcyjny SONATA BIS 16 oparty na
zamrożonych wynikach pilota. Pakiet obejmuje rdzeń naukowy po polsku, gotowe
pola startowe PL/EN do OSF, angielską sekcję wyników wstępnych, plan czterech
zadań badawczych oraz jawne granice dopuszczalnych twierdzeń.

Pilot nie został ponownie otwarty. Gate B pozostaje GO, Gate C pozostaje STOP,
a PILOT-016--018 pozostają niewykonane.

## Wykonane zmiany

1. Odtworzono lokalne repozytorium do kompletnego stanu końcowego
   `9adae88` z walidowanego Git bundle.
2. Zweryfikowano aktualne wymagania SONATA BIS 16: termin, strukturę opisów,
   limity stron, plan badań, panel, obowiązek doktoranta i reguły zespołu.
3. Zdefiniowano strategię wniosku skoncentrowaną na TRPP, z Representation
   Audit jako bramką i direct sparse relational regions jako prospektywną
   hipotezą metodologiczną.
4. Przygotowano tytuły, słowa kluczowe, abstrakt, streszczenia
   popularnonaukowe PL/EN, zadania PL/EN, hipotezy, cele, metody, ryzyka i
   rekomendowany harmonogram 48 miesięcy.
5. Dodano maszynowy manifest twierdzeń oraz walidator, który porównuje liczby
   grantowe z pierwotnym artefaktem PILOT-019 i odrzuca niedozwolone
   nadinterpretacje.

## Pliki utworzone

- `docs/grant/README.md`;
- `docs/grant/CLAIMS_EVIDENCE.json`;
- `docs/grant/SONATA_BIS16_SCIENTIFIC_CORE_PL.md`;
- `docs/grant/SONATA_BIS16_OSF_STARTER_PL_EN.md`;
- `docs/grant/SONATA_BIS16_PRELIMINARY_RESULTS_EN.md`;
- `docs/grant/SONATA_BIS16_CLAIM_BOUNDARIES.md`;
- `src/rep_audit/reporting/__init__.py`;
- `src/rep_audit/reporting/grant_package.py`;
- `scripts/10_validate_grant_package.py`;
- `tests/unit/test_grant_package.py`;
- `docs/evidence/GRANT_PACKAGE_VALIDATION.json`;
- `docs/POST_PILOT_GRANT_BLOCK_REPORT.md`.

## Pliki zmienione

- `README.md`;
- `docs/DECISION_LOG.md`.

## Testy i wyniki

- testy nowego walidatora: `4 passed`;
- pełny pytest z dwoma zamrożonymi repozytoriami referencyjnymi i jawnie
  odblokowanym testem evaluation-only: `142 passed`, `0 failed`, `0 skipped`;
- `compileall`: passed;
- `pip check`: `No broken requirements found.`;
- `git diff --check`: passed;
- dwie niezależne generacje walidacji grantowej: byte-identical;
- liczba wykrytych niedozwolonych twierdzeń: `0`;
- sprawdzony status: Gate B `GO`, Gate C `STOP`, direct regions `NOT_TESTED`,
  anchors `NOT_TESTED`.

## Ryzyka

1. Pakiet nie jest jeszcze finalnym 5- i 15-stronicowym opisem angielskim.
   Brakuje ostatecznej literatury, danych zespołu, budżetu i konkretnych
   wielokohortowych modułów chorobowych.
2. Największe ryzyko naukowe pozostaje niezmienione: stabilny nuisance może
   wyglądać jak struktura biologiczna.
3. Jedna para zewnętrzna nie wystarcza do szerokiej generalizacji; wniosek musi
   wskazać co najmniej trzy kohorty na moduł chorobowy.
4. Skład zespołu musi być sprawdzony pod kątem szczególnych ograniczeń SONATA
   BIS 16, zwłaszcza wcześniejszej wspólnej realizacji projektów konkursowych.
5. Planowany OPUS wymaga osobnej kontroli limitów i braku nakładania zadań.

## Odstępstwa od protokołu

Brak odstępstw eksperymentalnych. Nie uruchomiono nowych obliczeń naukowych,
nie zmieniono progów, danych, reprezentacji ani reguł selekcji. Nowe pliki są
wyłącznie warstwą redakcyjną i kontrolą spójności nad zamrożonym dowodem.

## Dokładne następne zadanie

Przygotować pełny angielski opis skrócony do 5 stron i szkielet opisu
szczegółowego do 15 stron. Przed jego zamrożeniem trzeba rozstrzygnąć siedem
elementów: tytuł, 48/60 miesięcy, skład zespołu, dwa moduły chorobowe z trzema
kohortami każdy, formalną współpracę międzynarodową, budżet oraz ostateczne
określenia panelowe. Rekomendowane ustawienia startowe są zapisane w
`docs/grant/SONATA_BIS16_SCIENTIFIC_CORE_PL.md`.
