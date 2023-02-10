# Doplňkové testy k projektu do IPP 2021/2022
* Autor: Zbyněk Křivka, krivka@fit.vut.cz
* Verze: 2022-02-14
  
Testy jsou ve formátu, který odpovídá vstupům skriptu `test.php`. Při nalezení chyby prosím kontaktujte autora. V případě, že budete odevzdávat testy (nejlépe v podadresáři `tests` v archivu vámi vypracované úlohy), které jste nevypracovávali sami, tak prosím uveďte též jejich zdroj či autora například ve speciálním README souboru uloženém u testů.
Některé testovací soubory/data byly po vygenerování ručně pozměněny, aby lépe otestovaly schopnost vašich skriptů a upozornily na alternativní možnosti ve výstupech (např. zkrácený zápis prázdných značek XML). Použitá adresářová struktura je pouze ilustrační a v hodnotících testech bude zcela odlišná.

## Obsažené adresáře
 * `both` - adresář s testy pro kompletní zpracování skriptem `test.php` bez nutnosti dodatečných parametrů
 * `parse-only` - testy pro `test.php` s parametrem `--parse-only` (výstup ve formátu XML je třeba porovnávat nástrojem *JExamXML* a ne nástrojem `diff`), vstupem jsou soubory s příponou `src`, očekávaný výstup najdete v souborech s příponou `out` a očekávané návratové kódy v souborech s příponou `rc`
 * `int-only` - testy pro `test.php` s parametrem `--int-only` (výstup se porovnává nástrojem `diff`), vstup `*.src`, očekávaný výstup `*.out` a očekávaný návratový kód `*.rc`
  
## Příklady použití testů na serveru Merlin

Ručně a jednotlivě pro testy skriptu `parse.php` bez použití `test.php` (předpokládejme jméno testu například `read_test`): 
```bash
php8.1 parse.php < read_test.src > read_test.your_out
echo $? > read_test.your_rc 
```
Následně musíte zjistit, zda jsou obsahy rovné těm referenčním v `read_test.rc` a `read_test.out`. Rovnost `read_test.out` a `read_test.your_out` je třeba ověřovat nástrojem *JExamXML* (viz níže).

Ručně a jednotlivě pro testy skriptu `interpret.py` (předpokládejme jméno testu například `write_test`): 
```bash
python3.8 interpret.py --source=write_test.src < write_test.in > write_test.your_out
echo $? > write_test.your_rc 
```
Pomocí nástroje `diff` zbývá zjistit, zda referenční výstupy odpovídají těm získaným v souborech s příponou `your_out` a `your_rc`.

Máte-li již implementován skript `test.php`, tak lze spouštět všechny testy v zadaném adresáři (např. `tests`) následovně (za předpokladu, že skripty `parse.php` a `interpret.py` jsou k dispozici v aktuálním adresáři):
```bash
php8.1 test.php --directory=tests > report.html 
```

Porovnání XML souborů např. `test.out` a `test.your_out` (s využitím *JExamXML* umístěného ve sdíleném adresáři na serveru Merlin):
```bash
java -jar /pub/courses/ipp/jexamxml/jexamxml.jar test.out test.your_out diffs.xml  /D /pub/courses/ipp/jexamxml/options
NAVRATOVA_HODNOTA="$?"
```
V případě, že bude nástrojem *JExaxmXML* detekována odlišnost zadaných XML souborů, tak bude návratová hodnota (viz proměnná `$NAVRATOVA_HODNOTA`) 1 a zadaný soubor `diffs.xml` bude obsahovat popis rozdílů. V případě, že jsou si oba soubory rovné vzhledem k nastavení porovnávání souborem `options`, tak bude návratová hodnota 0.
