# **Spēles "Dalīšana ar 2 vai 3" Dokumentācija**

## Apraksts

Šī ir interaktīva spēle, kurā spēlētājs sacenšas ar datoru. Spēles pamatā ir skaitļa secīga dalīšana ar 2 vai 3, cenšoties iegūt punktus. Datora gājienu aprēķināšanai tiek izmantoti divi algoritmi: Minimax un Alpha-Beta.

## Spēles Noteikumi

1.  **Sākums:** Spēle sākas ar sākuma skaitli, kurš dalās gan ar 2, gan ar 3 (proti, dalās ar 6).
2.  **Gājiens:** Katrā gājienā spēlētājs (cilvēks vai dators) izdara izvēli – dalīt pašreizējo skaitli ar 2 vai 3.
3.  **Punktu Piešķiršana:** Punkti tiek piešķirti pēc katra gājiena, pamatojoties uz dalīšanas rezultātu:
    *   Ja iegūtais skaitlis ir **pāra**: +1 punkts spēlētājam, kurš veica gājienu.
    *   Ja iegūtais skaitlis ir **nepāra**: -1 punkts spēlētājam, kurš veica gājienu.
    *   Ja iegūtais skaitlis beidzas ar ciparu **0 vai 5**: +1 punkts tiek pievienots kopējai "bankai".
4.  **Beigas:** Spēle noslēdzas, kad pašreizējais skaitlis kļūst 2 vai 3.
    *   Ja spēle beidzas ar skaitli **2**: spēlētājs, kurš veica pēdējo gājienu, saņem visus bankā uzkrātos punktus.
    *   (Ja spēle beidzas ar skaitli 3, bankas punkti netiek īpaši piešķirti).

## Instalācija

Lai spēlētu spēli, jūsu sistēmā ir jābūt uzstādītam:

1.  **Python:** Versija 3.x vai jaunāka.
2.  **PyGame bibliotēka:** To var instalēt, terminālī vai komandrindā izpildot komandu:
    ```bash
    pip install pygame
    ```

## Lietošana

1.  **Palaišana:** Atveriet termināli vai komandrindu, aizejat uz direktoriju, kur atrodas spēles fails, un palaidiet to ar komandu:
    ```bash
    python main.py
    ```

2.  **Sākotnējie Iestatījumi:** Sekojiet norādījumiem ekrānā, lai konfigurētu spēli:
    *   Izvēlieties sākuma skaitli (tiks piedāvātas vairākas iespējas).
    *   Norādiet, kurš spēlētājs sāks spēli (cilvēks vai dators).
    *   Izvēlieties algoritmu, ko dators izmantos gājienu aprēķināšanai (Minimax vai Alpha-Beta).
    *   Ievadiet algoritma meklēšanas dziļumu (ieteicamais diapazons: 3-7). Lielāks dziļums nozīmē gudrāku, bet potenciāli lēnāku datora pretinieku.

3.  **Spēles Gaita:** Veiciet gājienus, kad ir jūsu kārta, izvēloties dalītāju (2 vai 3).

4.  **Noslēgums:** Pēc spēles beigām tiks parādīta rezultātu statistika, un jums būs iespēja sākt jaunu spēli vai iziet.

## Projekta Struktūra (Galvenās Sastāvdaļas)

*   `transposition_table`: Datu struktūra, kas saglabā jau aprēķinātus spēles stāvokļus, lai paātrinātu datora lēmumu pieņemšanu nākotnē.
*   `GameState` klase: Pārvalda un uzglabā visu aktuālo informāciju par spēles stāvokli (pašreizējais skaitlis, spēlētāju punkti, bankas saturs, kura spēlētāja gājiens utt.).
*   `GameSettings` klase: Satur spēles konfigurācijas iestatījumus, kas tika izvēlēti sākumā (sākuma skaitlis, izvēlētais algoritms, tā dziļums).
*   `GameStats` klase: Atbild par spēles statistikas uzskaiti, apkopošanu.

## Izmantotie Algoritmi

Datora gājienu loģikai tiek izmantoti divi standarta spēļu teorijas algoritmi:

1.  **Minimax:** Klasisks rekursīvs algoritms, kas pēta spēles koku, lai atrastu optimālo gājienu, pieņemot, ka pretinieks arī spēlēs optimāli. Tas cenšas maksimizēt savu rezultātu un minimizēt pretinieka rezultātu.
2.  **Alpha-Beta:** Optimizēta Minimax algoritma versija. Tā izmanto "alfa-beta atzarošanu" (alpha-beta pruning), lai efektīvi nogrieztu spēles koka zarus, kuri garantēti nesniegs labāku rezultātu par jau atrasto, tādējādi ievērojami paātrinot aprēķinus, īpaši pie lielāka meklēšanas dziļuma.
