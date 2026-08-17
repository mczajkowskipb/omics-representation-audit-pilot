# Przenośne relacyjne profile pacjentów

Badania omiczne mierzą jednocześnie aktywność tysięcy genów lub innych
cząsteczek u każdego pacjenta. Jednym z głównych celów analizy jest odnalezienie
grup osób o podobnych mechanizmach choroby. Wynik takiego grupowania silnie
zależy jednak od sposobu porównywania pacjentów. Możemy porównywać bezpośrednie
wartości pomiarów albo pytać, które geny mają u danego pacjenta wyższą aktywność
niż inne. Drugi sposób prowadzi do prostych reguł, na przykład „gen A jest
bardziej aktywny niż gen B”. Takie reguły mogą być łatwiejsze do interpretacji i
mniej zależne od skali laboratoryjnej, ale nie zawsze są lepsze.

Celem projektu jest opracowanie przenośnych relacyjnych profili pacjentów.
Najpierw program, korzystając wyłącznie z jednej kohorty źródłowej, sprawdzi, czy
dane uzasadniają porównywanie wartości, rang, relacji między genami lub połączenie
tych informacji. Jeżeli żadna reprezentacja nie daje wiarygodnej struktury,
program będzie mógł uczciwie wstrzymać grupowanie. Dla stabilnych grup utworzy
krótkie profile złożone z relacji między cechami. Taki profil będzie pełnił rolę
czytelnego opisu grupy, zamiast sztucznego „średniego pacjenta”.

Pełny profil zostanie następnie zamrożony i zastosowany do pacjentów z
niezależnych kohort. Dane nowych pacjentów nie będą służyły do ponownego uczenia,
wspólnej normalizacji ani poprawiania progów. Pacjent zostanie przypisany tylko
wtedy, gdy wystarczająco wiele reguł będzie można sprawdzić, a wynik będzie
jednoznaczny. W przeciwnym razie pozostanie bez przypisania. To ważna cecha:
niepewność nie będzie ukrywana przez wymuszenie decyzji.

Badania obejmą kontrolowane symulacje oraz niezależne kohorty raka płuca i raka
jelita grubego. We wszystkich podstawowych porównaniach różne sposoby opisu
pacjentów będą korzystały z tego samego deterministycznego algorytmu grupowania.
Ocenimy stabilność, długość i czytelność profili, pokrycie genów między
platformami, odporność na zakłócenia oraz zgodność zamrożonych grup z informacją
biologiczną i kliniczną. Etykiety choroby i wyniki kliniczne będą używane dopiero
na końcu, wyłącznie do oceny.

Wyniki wstępne pokazują, że różne reprezentacje rzeczywiście działają najlepiej
w różnych warunkach. Pokazały też ważne ograniczenie: stabilna struktura nie
musi odpowiadać konkretnej etykiecie klinicznej, a jeden z dwóch kierunków
transferu między kohortami nie spełnił z góry ustalonego kryterium. Projekt nie
zakłada więc, że relacje zawsze wygrają. Jego wynikiem będą metody i jawne zasady
określające, kiedy relacyjne profile pacjentów są wiarygodne, kiedy należy
zachować informacje o wartościach, a kiedy uczciwym wynikiem jest rezygnacja z
grupowania.

