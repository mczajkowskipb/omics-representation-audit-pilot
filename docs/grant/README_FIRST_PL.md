# SONATA BIS 16 - od czego zacząć

## Decyzja strategiczna z 21.08.2026

Po krytycznym porównaniu wariantu TRPP-centred z szerokim projektem
absolute/relational/hybrid przyjęto **MODIFY**. Centralne pytanie dotyczy teraz
tego, kiedy zachować wartości, kiedy użyć relacji wewnątrz próbki, kiedy obu
widoków, a kiedy wstrzymać grupowanie - zawsze w przenośnym grupowaniu danych
omicznych. TRPP pozostaje główną rodziną metod i rezultatem biomedycznym, ale
nie odpowiedzią założoną z góry.

Pełne uzasadnienie znajduje się w
`SONATA_BIS16_STRATEGIC_DECISION_MODIFY_PL.md`. Ta zmiana dotyczy narracji
wniosku. Nie zmienia protokołu, wyników ani bramek pilota.

## Co tu się dzieje, prostymi słowami

Projekt ma trzy kolejne poziomy:

1. **Najpierw sprawdzamy, jak w ogóle warto porównywać pacjentów.** Ten sam
   deterministyczny algorytm PAM grupuje trzy wersje danych: wartości, relacje
   rankingowe oraz ich połączenie. Audit korzysta wyłącznie z kohorty źródłowej
   i może odpowiedzieć „brak stabilnej struktury”.
2. **Potem grupujemy i opisujemy grupy.** W pilocie centralnym reprezentantem
   grupy jest medoid, czyli rzeczywisty pacjent najbardziej centralny w danej
   grupie. W projekcie badawczym powstaną krótkie obszary relacyjne: zestawy
   reguł typu „gen A > gen B”, które mają definiować profil grupy czytelniej niż
   sam medoid.
3. **Na końcu sprawdzamy przenośność.** Cały model z kohorty źródłowej jest
   zamrażany i stosowany do nowego pacjenta lub nowej kohorty bez ponownego
   grupowania, bez wspólnej normalizacji i bez dostrajania do etykiet target.
   Niepewny pacjent może pozostać `UNASSIGNED`.

Czyli pierwotna intuicja była prawidłowa: najpierw ocena, czy geometria
rankingowo-relacyjna ma sens dla danych; potem grupowanie; następnie utworzenie
regułowego obszaru opisującego pacjenta/grupę; na końcu uczciwy test na nowych
kohortach.

## Co jest już zakończone

- Pilot techniczny i eksperymentalny jest zamrożony.
- Gate B: GO - kontrolowane symulacje wspierają Representation Audit.
- Gate C: STOP - jeden kierunek transferu przekroczył limit regret o 0,005284.
- Progu nie rozluźniono i nie dostrajano niczego na target.
- direct regions: NOT TESTED.
- anchors: NOT TESTED.
- PILOT-016-018 nie zostały uruchomione, zgodnie z protokołem.
- W samodzielnym środowisku tej paczki przechodzi 150 testów; trzy oczekiwane
  testy są pomijane, ponieważ zewnętrzne repozytoria referencyjne nie są
  kopiowane do paczki, a etykiety realne pozostają fizycznie zamknięte. Testy
  poprawności, deterministyczności i braku leakage przechodzą.
- Gotowe są: opis skrócony EN, opis szczegółowy EN, streszczenie popularne PL,
  streszczenie popularne EN, rdzeń naukowy PL, wyniki wstępne, audyt kohort i
  komplet raportów pilota.

## Gdzie są najważniejsze pliki

- `output/pdf/SONATA_BIS16_SHORT_DESCRIPTION_EN_DRAFT.pdf` - opis skrócony;
- `output/pdf/SONATA_BIS16_DETAILED_DESCRIPTION_EN_DRAFT.pdf` - opis
  szczegółowy;
- `output/pdf/SONATA_BIS16_POPULAR_SUMMARY_PL.pdf` - streszczenie PL;
- `output/pdf/SONATA_BIS16_POPULAR_SUMMARY_EN.pdf` - streszczenie EN;
- `output/pdf/SONATA_BIS_PILOT_CLOSEOUT_REPORT.pdf` - końcowy raport pilota;
- `docs/grant/SONATA_BIS16_DEFAULTS_FROZEN.md` - zatwierdzone ustawienia
  robocze;
- `docs/grant/SONATA_BIS16_STRATEGIC_DECISION_MODIFY_PL.md` - decyzja
  `MODIFY`, granice zakresu i prosty argument dla recenzenta;
- `docs/grant/SONATA_BIS16_DATASET_AUDIT.md` - kohorty lung/CRC i ryzyka;
- `docs/grant/SONATA_BIS16_CLAIM_BOUNDARIES.md` - czego nie wolno nadmiernie
  twierdzić;
- `docs/SONATA_BIS16_COMPLETION_REPORT.md` - raport z ostatniego bloku.
- `docs/SONATA_BIS16_NARRATIVE_UPDATE_REPORT.md` - raport decyzji `MODIFY`,
  zmian narracji i ich walidacji.

## Co trzeba jeszcze zrobić przed wysłaniem wniosku

Nie są to kolejne eksperymenty. Potrzebne są dane, których nie można uczciwie
wymyślić:

1. wpisać zweryfikowane osoby i ich role oraz sprawdzić kwalifikowalność;
2. przygotować budżet, wynagrodzenia i uzasadnienia kosztów;
3. uzupełnić osiągnięcia PI, publikacje i rozdzielenie względem innych projektów;
4. potwierdzić współpracę z Gironą, jeśli ma być wymieniona;
5. uzupełnić dane jednostki, etykę, DMP, oświadczenia i wewnętrzny termin;
6. przenieść zatwierdzoną treść do aktualnego formularza OSF i wykonać końcową
   kontrolę limitów oraz zgodności formalnej.

Najbliższe właściwe zadanie to zatem **finalizacja administracyjna i budżetowa
wniosku**, a nie dalsze „ratowanie” pilota. Nowe eksperymenty direct regions są
treścią proponowanego projektu i pozostają jawnie niewykonane na etapie wniosku.
