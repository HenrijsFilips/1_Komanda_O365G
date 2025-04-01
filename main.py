import random
import time
import copy
import pygame

# table, kas glabā iepriekš aprēķinātus stāvokļus un to novērtējumus
# atslēga: stāvokļa tuple reprezentācija
# vērtība: vārdnīca ar score (novērtējums), depth (dziļums) un best_move (labākais gājiens)
transposition_table={}

# klase, kas glabā pilnīgu informāciju par konkrētu spēles stāvokli:
class GameState:
    def __init__(self, currentNumber, humanScore, computerScore, bankPoints, currentPlayer, isGameOver=False, move=None):
        self.currentNumber = currentNumber   # tekošais skaitlis, ar kuru notiek spēle, mainās katrā gājienā, dalot ar 2 vai 3
        self.humanScore = humanScore         # cilvēka spēlētāja punktu skaits
        self.computerScore = computerScore   # datora punktu skaits
        self.bankPoints = bankPoints         # uzkrātie bankas punkti
        self.currentPlayer = currentPlayer   # norāda, kura spēlētāja gājiens: 0 - cilvēks 1 - dators
        self.isGameOver = isGameOver         # norāda vai spēle ir beigusies, kļūst True, kad sasniedz 2 vai 3, vai skaitli kas nedalās ar 2 vai 3
        self.move = move                     # pēdējais izdarītais gājiens (2 vai 3)

    def copy(self):
        return copy.deepcopy(self) # izveido pašreizējā stāvokļa kopiju

    def to_tuple(self):#veids kā apzīmēt GameState kā hash tuple priekš Transpozīcijas
        return (self.currentNumber, self.humanScore, self.computerScore, self.bankPoints, self.currentPlayer, self.isGameOver, self.move)

# klase, kas glabā un konfigurē dažādus spēles iestatījumus
class GameSettings:
    def __init__(self, startingNumbers=None, selectedStartNumber=None, selectedAlgorithm=None, firstPlayer=0, maxDepth=10):
        self.startingNumbers = startingNumbers if startingNumbers else [] # ja tiek nodots saraksts, tad to saglabā, ja ne inicializē tukšu sarakstu
        self.selectedStartNumber = selectedStartNumber  # saglabā izraudzīto sākuma skaitli
        self.selectedAlgorithm = selectedAlgorithm      # "minimax" vai "alphabeta"
        self.firstPlayer = firstPlayer                  # 0 nozīmē, ka sāk cilvēks, 1 nozīmē, ka sāk dators
        self.maxDepth = maxDepth                        # saglabā maksimālo dziļumu, kuru algoritms izmantos lēmumu pieņemšanā


# klases mērķis ir uzkrāt un izsekot dažādus statistikas rādītājus spēles laikā
class GameStats:
    def __init__(self): # inicializē visus statistikas rādītājus ar sākotnējām vērtībām
        self.nodesVisited = 0       # uzskaita, cik daudzi mezgli tiek apmeklēti algoritma koka meklēšanas laikā
        self.moveStartTime = 0      # glabā laiku, kad sācies datora gājiens
        self.moveDuration = 0       # uzglabā datora gājiena ilgumu sekundēs
        self.gamesPlayed = 0        # uzskaita kopējo izspēlēto spēļu skaitu
        self.computerWinCount = 0   # uzskaita, cik reizes dators ir uzvarējis
        self.humanWinCount = 0      # uzskaita, cik reizes cilvēks ir uzvarējis
        self.draws = 0              # uzskaita neizšķirtu skaitu
        self.totalMoveTime = 0      # kopējais laiks, ko dators pavadījis, veicot gājienus visās spēlēs
        self.lastGameResult = None  # "cilvēks", "dators", vai "neizšķirts"

    @property # "@property" ļauj piekļūt vidējam gājiena laikam kā īpašībai
    def averageMoveTime(self):
        if self.gamesPlayed == 0:
            return 0 # ja nav izspēlēta neviena spēle atgriež 0
        return self.totalMoveTime / self.gamesPlayed # aprēķina vidējo gājiena laiku, izdalot kopējo gājienu laiku ar izspēlēto spēļu skaitu


def generate_starting_numbers(): # ģenerē 5 nejaušus skaitļus diapazonā no 10 000 līdz 20 000, kas dalās ar 2 un 3
    random_numbers = []
    for i in range(5):
        while True:
            number = random.randint(10000, 20000)
            if number % 6 == 0: # skaitļi, kas dalās ar 2 un 3 -> dalās ar 6
                random_numbers.append(number) # skaitli pievieno sarakstam
                break
    return random_numbers


def get_possible_moves(state): # funkcija atgriež iespējamo gājienu sarakstu (2 vai/un 3) no pašreizējā stāvokļa
    possible_moves = []
    if state.currentNumber % 2 == 0: # pārbauda vai dalot ar 2, tiek iegūts vesels skaitlis
        possible_moves.append(2)
    if state.currentNumber % 3 == 0: # pārbauda vai dalot ar 3, tiek iegūts vesels skaitlis
        possible_moves.append(3)
    return possible_moves


def apply_move(state, move): # izveido pilnīgu tekošo spēles stāvokļa kopiju
    new_state = state.copy() # nepieciešams, lai nemainītu oriģinālo stāvokli, tas ļauj eksperimentēt ar gājieniem, nezaudējot sākotnējo informāciju

    new_number = state.currentNumber // move # izdala pašreizējo skaitli ar izvēlēto gājienu (2 vai 3)
    new_state.currentNumber = new_number # atjaunina stāvokļa tekošo skaitli ar jauno skaitli
    new_state.move = move # saglabā pēdējo izdarīto gājienu stāvoklī

    # atjaunina iegūtos punktus, balstoties uz spēles noteikumiem
    if new_number % 2 == 0: # pāra skaitlis
        if state.currentPlayer == 0:  # cilvēks spēlētājs
            new_state.humanScore += 1
        else: # dators spēlētājs
            new_state.computerScore += 1
    else:  # nepāra skaitlis
        if state.currentPlayer == 0:  # cilvēks spēlētājs
            new_state.humanScore -= 1
        else: # dators spēlētājs
            new_state.computerScore -= 1

    if new_number % 10 == 0 or new_number % 10 == 5: # pārbauda vai skaitlis beidzas ar 0 vai 5, atjaunina banku
        new_state.bankPoints += 1 # bankai pieskaita 1 punktu

    if new_number == 2 or new_number == 3: # pārbauda, vai spēle ir beigusies (sasniegts 2 vai 3)
        new_state.isGameOver = True
        if new_number == 2: # ja skaitlis ir 2, 'currentPlayer' saņem bankas punktus
            if state.currentPlayer == 0:  # cilvēks spēlētājs
                new_state.humanScore += new_state.bankPoints
            else:  # dators spēlētājs
                new_state.computerScore += new_state.bankPoints
            new_state.bankPoints = 0

    new_state.currentPlayer = 1 - state.currentPlayer # momaina spēlētāju: 0->1  1->0 (cilvēks-0  dators-1)
    return new_state # atgriež jauno spēles stāvokli pēc gājiena


def evaluate_state(state, depth):
    """
    novērtē pašreizējo stāvokli no datora viedokļa
    atgriež rezultātu, kurā lielākas vērtības ir labākas datoram

    Parametri:
        state: pašreizējais spēles stāvoklis
        depth: cik dziļi vēl var iet kokā
        
    Atgriež:
        int: heiristiskā vērtība stāvoklim (lielāka vērtība = labāk datoram)
    """
    if state.isGameOver:# ja spēle beigusies, novērtē pamatojoties uz to, kurš uzvarēja
        if state.computerScore > state.humanScore:
            return 1000 - depth  # datora uzvara, vēlams ātrāk
        elif state.humanScore > state.computerScore:
            return -1000 + depth  # cilvēka uzvara, vēlams vēlāk
        else:
            return 0  # neizšķirts

    # pamatnovērtējums
    score = state.computerScore - state.humanScore # aprēķina pamatnovērtējumu kā starpību starp datora un cilvēka punktiem
    possible_moves = get_possible_moves(state) # iegūst visus iespējamos gājienus no pašreizējā stāvokļa

    # Papildu punkti par nākamā skaitļa tipu (pāra/nepāra)
    for move in possible_moves: # izmēģina visus iespējamos gājienus
        next_number = state.currentNumber // move # nosaka nākošo gājienu
        if next_number % 2 == 0:
            score += 5  # ja nākošais pāra, papildus punkti
        else:
            score -= 2 # ja nākošais nepāra, punkti noņemti

    # apsver bankas punktus - vērtīgāk, ja var tikt pie rezultāta 2
    if state.currentNumber == 4 or state.currentNumber == 6: # skaitļi var novest līdz rezultātam 2
        if state.currentPlayer == 1:  # datora gājiens
            score += state.bankPoints * 2  # dators var iegūt šos punktus
        else:
            score -= state.bankPoints * 2  # spēlētājs var iegūt šos punktus
    else:
        # parasts bankas punktu novērtējums (virsotnes, kas nav 4 vai 6)
        score += state.bankPoints * 0.5

    return score # atgriež heiristisko vērtību


def minimax(state, depth, maximizing_player, stats):
    """
    minimax algoritms
    rekursīvi meklē optimālo gājienu izvērtējot visas iespējamās pozīcijas

    Parametri:
        state: pašreizējais spēles stāvoklis
        depth: cik dziļi vēl var iet kokā
        maximizing_player: vai tagad ir datora gājiens
        stats: objekts statistikas uzskaitei
    """
    # pieskaita apmeklēto virsotņu skaitu priekš statistikas
    stats.nodesVisited += 1

    # pārbauda vai ir sasniegtas spēles beigas:
    # 1) vairs nav atļauts iet dziļāk kokā (depth = 0)
    # 2) spēle ir beigusies
    if depth == 0 or state.isGameOver:
        return evaluate_state(state, depth)

    # iegūst visus iespējamos gājienus no pašreizējā stāvokļa
    # (skaitļi 2 vai 3 ar kuriem var dalīt)
    possible_moves = get_possible_moves(state)

    # ja nav iespējamu gājienu tad ir spēles beigas
    if not possible_moves:
        return evaluate_state(state, depth)

    # datora gājiens (max)
    if maximizing_player:
        # sākotnējā vērtība ir -inf jo meklē maksimumu
        max_eval = float('-inf')

        # izmēģina visus iespējamos gājienus
        for move in possible_moves:
            # izveido jaunu stāvokli pēc gājiena
            new_state = apply_move(state, move)

            # rekursīvi izsauc minimax ar pretinieka gājienu (False)
            # samazina dziļumu par 1 jo esam dziļāk kokā
            eval_score = minimax(new_state, depth - 1, False, stats)

            # updeitojam labāko atrasto vērtību
            max_eval = max(max_eval, eval_score)

        return max_eval

    # cilvēka gājiens (min)
    else:
        # sākotnējā vērtība ir +inf jo meklē min
        min_eval = float('inf')

        # izmēģina visus iespējamos gājienus
        for move in possible_moves:
            # izveido jaunu stāvokli pēc gājiena
            new_state = apply_move(state, move)

            # rekursīvi izsauc minimax ar datora gājienu (True)
            # samazina dziļumu par 1 jo esam dziļāk kokā
            eval_score = minimax(new_state, depth - 1, True, stats)

            # updeito mazāko atrasto vērtību
            min_eval = min(min_eval, eval_score)

        return min_eval



def alpha_beta(state, depth, alpha, beta, maximizing_player, stats):
    """
    Alpha-beta pruning algoritms ar Transpozīcijas tabulu un Move Ordering
    rekursīvi meklē optimālo gājienu izvērtējot visas iespējamās pozīcijas

    Parametri:
        state: pašreizējais spēles stāvoklis
        depth: cik dziļi vēl var iet kokā
        alpha: alpha vērtība priekš atzarošanas
        beta: beta vērtība priekš atzarošanas
        maximizing_player: vai tagad ir datora gājiens
        stats: objekts statistikas uzskaitei
    """
    # pieskaita apmeklēto virsotņu skaitu priekš statistikas
    stats.nodesVisited += 1

    # transpozīcijas tabulas pārbaude
    state_tuple = state.to_tuple()
    if state_tuple in transposition_table:
        tt_entry = transposition_table[state_tuple]
        if tt_entry['depth'] >= depth:
            return tt_entry['score']

    # pārbauda vai ir sasniegtas spēles beigas:
    # 1) vairs nav atļauts iet dziļāk kokā (depth = 0)
    # 2) spēle ir beigusies
    if depth == 0 or state.isGameOver:
        return evaluate_state(state, depth)

    # iegūst visus iespējamos gājienus no pašreizējā stāvokļa
    possible_moves = get_possible_moves(state)

    # ja nav iespējamu gājienu tad ir spēles beigas
    if not possible_moves:
        return evaluate_state(state, depth)

    # datora gājiens (max)
    if maximizing_player:
        max_eval = float('-inf')
        best_move_in_state = None

        # izmēģina visus iespējamos gājienus
        for move in possible_moves:
            # izveido jaunu stāvokli pēc gājiena
            new_state = apply_move(state, move)

            # rekursīvi izsauc alpha_beta ar pretinieka gājienu
            eval_score = alpha_beta(new_state, depth - 1, alpha, beta, False, stats)

            # updeitojam labāko atrasto vērtību
            if eval_score > max_eval:
                max_eval = eval_score
                best_move_in_state = move

            # atjaunojam alpha vērtību
            alpha = max(alpha, max_eval)
            if beta <= alpha:  # beta nogriešana
                break

        # saglabājam transpozīcijas tabulā
        transposition_table[state_tuple] = {
            'score': max_eval,
            'depth': depth,
            'best_move': best_move_in_state
        }
        return max_eval

    # cilvēka gājiens (min)
    else:
        min_eval = float('inf')
        best_move_in_state = None

        # izmēģina visus iespējamos gājienus
        for move in possible_moves:
            # izveido jaunu stāvokli pēc gājiena
            new_state = apply_move(state, move)

            # rekursīvi izsauc alpha_beta ar datora gājienu
            eval_score = alpha_beta(new_state, depth - 1, alpha, beta, True, stats)

            # updeito mazāko atrasto vērtību
            if eval_score < min_eval:
                min_eval = eval_score
                best_move_in_state = move

            # atjaunojam beta vērtību
            beta = min(beta, min_eval)
            if beta <= alpha:  # alpha nogriešana
                break

        # saglabājam transpozīcijas tabulā
        transposition_table[state_tuple] = {
            'score': min_eval,
            'depth': depth,
            'best_move': best_move_in_state
        }
        return min_eval

def best_move(state, settings, stats):
    """Funkcijas galvenais mērķis: atrast optimālāko gājienu, izmantojot minimax vai alpha-beta algoritmu
    Izvēlēties gājienu ar augstāko novērtējumu
    Uzkrāt statistiku par algoritma darbību
    """
    possible_moves = get_possible_moves(state) # iegūst visus iespējamos gājienus (2 un/vai 3) no pašreizējā stāvokļa

    if not possible_moves: # ja nav iespējamu gājienu, atgriež None
        return None

    best_score = float('-inf') # negatīva bezgalība
    best_move_choice = possible_moves[0] # noklusētais gājiens ir pirmais iespējamais gājiens
    stats.nodesVisited = 0 # apmeklēto mezglu skaits 0
    stats.moveStartTime = time.time() # fiksē gājiena sākuma laiku

    for move in possible_moves: # cikls cauri visiem iespējamajiem gājieniem
        new_state = apply_move(state, move) # izveido jaunu stāvokli pēc katra gājiena
        if settings.selectedAlgorithm == "minimax": # izvēlēts minimax algoritms
            score = minimax(new_state, settings.maxDepth - 1, False, stats)
        else:  # izvēlēts Alpha-beta algoritms
            score = alpha_beta(new_state, settings.maxDepth - 1, float('-inf'), float('inf'), False, stats)
        if score > best_score: # ja tekošā gājiena novērtējums ir labāks par līdzšinējo labāko
            best_score = score # atjaunina labāko novērtējumu
            best_move_choice = move # saglabā šo gājienu kā labāko

    stats.moveDuration = time.time() - stats.moveStartTime # aprēķina gājiena izpildes laiku
    stats.totalMoveTime += stats.moveDuration # pievieno kopējam izpildes laikam
    return best_move_choice # atgriež labāko atrasto gājienu


def display_game_result(state, stats):
    if state.humanScore > state.computerScore:
        stats.lastGameResult = "human"
        stats.humanWinCount += 1
    elif state.computerScore > state.humanScore:
        stats.lastGameResult = "computer"
        stats.computerWinCount += 1
    else:
        stats.lastGameResult = "draw"
        stats.draws += 1

    stats.gamesPlayed += 1


# Spēles noteikumu un statistikas datu iniciālizēšana:
settings = GameSettings()
stats = GameStats()

# spēles attēlošanas ekrāna izmēru definēšana un tas aizpildījums ar krāsu:
screen = pygame.display.set_mode((800, 800))
screen.fill((255, 255, 255))


# metode, kas uzzīmes visu pirmo ekrānu priekš sākotnēja skaitļa, pirmā lietotāja un algoritma izvēles, kā arī saņems tās pirmas vērtības:
def noteikumuIzvelePirmais():
    # aizkrāsojam visu ekrānu ar balto krāsu:
    screen.fill((255, 255, 255))

    # bool tipa mainīgie, kas palīdz sekot tam, vai visas nepieciešamas vērtības (sākotnējs skaitlis, pirmais lietotājs un algoritms) ir izvēlētas; sākuma nekas nav izvēlēts -> false:
    skaitlisIzvelets = False
    speletajsIzvelets = False
    algoritmsIzvelets = False

    # veidojam mainīgo, ar kuru definēsim burtu fontu un izmērus:
    textFont = pygame.font.SysFont('Times New Roman', 30)

    # Zemāk tiek veidotas visi tekstu lauki un pogas, kas nepieciešami pirmām ekranām:
    # Tie visi ir izveidoti pēc sekojoša principa (Avots - https://www.geeksforgeeks.org/python-display-text-to-pygame-window/):

    # 1. tiek definēts mainīgais "nosaukums_text", kas satur lauka/pogas tekstu
    # 2. no šī mainīga tiek veidots jauns mainīgais rect tipa "nosaukums_text_rect". Tekstu var ievietot pa taisno uz ekrānu, bet to būs vieglāk centrēt, pārvietot, krāsot u.tml. ar rect tipa objektu
    # 3. tiek definēts jauna rect tipa objekta izvietojums ekrānā
    # 4. pygame.draw.rect - tā ir taisnstūra objekta zīmēšana. Tiek pielietota, lai izveidotu rāmīties ap tekstu. Dažreiz to ir vairāk par vienu priekš viena teksta - tad pirmais ir melnais taisnstūris, otrais - krāsains, lai izveidotos melna rāmīte ap krāsaino lauku.


    # 1. "Lūdzu, izvēlēties spēles sakotnējos nosacījumus" teksta kastītes izveide:
    sakumaNosacijumuIzvele_text = textFont.render("Lūdzu, izvēlēties spēles sakotnējos nosacījumus:", True, (255, 255, 255))
    sakumaNosacijumuIzvele_text_rect = sakumaNosacijumuIzvele_text.get_rect()
    sakumaNosacijumuIzvele_text_rect.center = (400, 75)
    pygame.draw.rect(screen, (102, 102, 255), [90, 50, 620, 50], 0)


    # 2. "1. Kāds būs sākuma skaitis: " teksta kastītes izveide:
    sakumaSkaitlaIzvele_text = textFont.render("1. Kāds būs sākuma skaitlis:", True, (255, 255, 255))
    sakumaSkaitlaIzvele_text_rect = sakumaSkaitlaIzvele_text.get_rect()
    sakumaSkaitlaIzvele_text_rect.center = (400, 165)
    pygame.draw.rect(screen, (102, 102, 255), [225, 140, 350, 50], 0)


    # 3. "2. Kurš sāks spēli: " teksta kastītes izveide:
    sakumaSpeletajuIzvele_text = textFont.render("2. Kurš sāks spēli:", True, (255, 255, 255))
    sakumaSpeletajuIzvele_text_rect = sakumaSpeletajuIzvele_text.get_rect()
    sakumaSpeletajuIzvele_text_rect.center = (400, 345)
    pygame.draw.rect(screen, (102, 102, 255), [285, 320, 230, 50], 0)


    # 4. "3. Kurš algoritms būs izmantots: " teksta kastītes izveide:
    algoritmaIzvele_text = textFont.render("3. Kurš algoritms būs izmantots:", True, (255, 255, 255))
    algoritmaIzvele_text_rect = algoritmaIzvele_text.get_rect()
    algoritmaIzvele_text_rect.center = (400, 525)
    pygame.draw.rect(screen, (102, 102, 255), [200, 500, 400, 50], 0)


    # 5. "Turpināt" teksta pogas izveide:
    turpinat_text = textFont.render("Turpināt", True, (255, 255, 255))
    turpinat_text_rect = turpinat_text.get_rect()
    turpinat_text_rect.center = (400, 725)
    pygame.draw.rect(screen, (0, 0, 0), [338, 698, 124, 54], 0)
    pygame.draw.rect(screen, (102, 102, 255), [340, 700, 120, 50], 0)


    # 6. Ģenereto skaitļu izvade ekrānā:
    pirma_skaitla_text = textFont.render(str(settings.startingNumbers[0]), True, (0, 0, 0))
    otra_skaitla_text = textFont.render(str(settings.startingNumbers[1]), True, (0, 0, 0))
    tresa_skaitla_text = textFont.render(str(settings.startingNumbers[2]), True, (0, 0, 0))
    ceturta_skaitla_text = textFont.render(str(settings.startingNumbers[3]), True, (0, 0, 0))
    piekta_skaitla_text = textFont.render(str(settings.startingNumbers[4]), True, (0, 0, 0))

    pirma_skaitla_text_rect = pirma_skaitla_text.get_rect()
    otra_skaitla_text_rect = otra_skaitla_text.get_rect()
    tresa_skaitla_text_rect = tresa_skaitla_text.get_rect()
    ceturta_skaitla_text_rect = ceturta_skaitla_text.get_rect()
    piekta_skaitla_text_rect = piekta_skaitla_text.get_rect()

    pirma_skaitla_text_rect.center = (100, 245)
    otra_skaitla_text_rect.center = (250, 245)
    tresa_skaitla_text_rect.center = (400, 245)
    ceturta_skaitla_text_rect.center = (550, 245)
    piekta_skaitla_text_rect.center = (700, 245)

    pygame.draw.rect(screen, (0, 0, 0), [48, 218, 104, 54], 2)
    pygame.draw.rect(screen, (0, 0, 0), [198, 218, 104, 54], 2)
    pygame.draw.rect(screen, (0, 0, 0), [348, 218, 104, 54], 2)
    pygame.draw.rect(screen, (0, 0, 0), [498, 218, 104, 54], 2)
    pygame.draw.rect(screen, (0, 0, 0), [648, 218, 104, 54], 2)


    # 7. Pirma spēlētāja izvēlēs pogas:
    dators_text = textFont.render("Dators", True, (0, 0, 0))
    lietotajs_text = textFont.render("Lietotājs", True, (0, 0, 0))

    dators_text_rect = dators_text.get_rect()
    lietotajs_text_rect = lietotajs_text.get_rect()

    dators_text_rect.center = (290, 425)
    lietotajs_text_rect.center = (510, 425)

    pygame.draw.rect(screen, (0, 0, 0), [228, 398, 124, 54], 2)
    pygame.draw.rect(screen, (0, 0, 0), [448, 398, 124, 54], 2)


    # 8. Algoritma izvēlēs pogas:
    miminax_text = textFont.render("Minimaksa algoritms", True, (0, 0, 0))
    alfabeta_text = textFont.render("Alfa - beta algoritms", True, (0, 0, 0))

    miminax_text_rect = miminax_text.get_rect()
    alfabeta_text_rect = alfabeta_text.get_rect()

    miminax_text_rect.center = (200, 605)
    alfabeta_text_rect.center = (600, 605)

    pygame.draw.rect(screen, (0, 0, 0), [48, 578, 304, 54], 2)
    pygame.draw.rect(screen, (0, 0, 0), [448, 578, 304, 54], 2)


    # 9. Neievādītas vērtības paziņojums:
    neievaditaVertiba_text = textFont.render("Kāda vērtība netika izvēlēta. Lūdzu, izvēlēties visas vērtības!", True, (255, 51, 51))
    neievaditaVertiba_text_rect = neievaditaVertiba_text.get_rect()
    neievaditaVertiba_text_rect.center = (400, 665)


    # visu iepriekš izveidoto teksta lauku un pogu izvade ekrānā:
    screen.blit(sakumaNosacijumuIzvele_text, sakumaNosacijumuIzvele_text_rect)
    screen.blit(sakumaSkaitlaIzvele_text, sakumaSkaitlaIzvele_text_rect)
    screen.blit(sakumaSpeletajuIzvele_text, sakumaSpeletajuIzvele_text_rect)
    screen.blit(algoritmaIzvele_text, algoritmaIzvele_text_rect)
    screen.blit(turpinat_text, turpinat_text_rect)

    screen.blit(pirma_skaitla_text, pirma_skaitla_text_rect)
    screen.blit(otra_skaitla_text, otra_skaitla_text_rect)
    screen.blit(tresa_skaitla_text, tresa_skaitla_text_rect)
    screen.blit(ceturta_skaitla_text, ceturta_skaitla_text_rect)
    screen.blit(piekta_skaitla_text, piekta_skaitla_text_rect)

    screen.blit(dators_text, dators_text_rect)
    screen.blit(lietotajs_text, lietotajs_text_rect)

    screen.blit(miminax_text, miminax_text_rect)
    screen.blit(alfabeta_text, alfabeta_text_rect)


    # uzzīmēta ekrāna atjaunošana, lai viss uzzīmētais būtu redzams:
    pygame.display.update()


    # cikls, kas darbosies, kamēr lietotājs neizvēlēsies visas nepieciešamas spēlei sākuma nosacījumus:
    while True:
        # noteic vai lietotājs ir kaut kā mijiedarbojusies ar ekrānu:
        for ev in pygame.event.get():
            # aizvēr spēles logu, ja tiek uzspiests "krustiņš":
            if ev.type == pygame.QUIT:
                pygame.quit()

            # noteic, vai lietotājs ir uzspiedis pēli ekrānā, ja tā ir - noteic pēles koordinātes uzspiešanas brīdī:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                x_mouse, y_mouse = pygame.mouse.get_pos()

                # tālāk tiks pārbaudītas pēles koordinātes, un ja tas atbilst kādai no pogam, ko ir jāizvēlas,
                # tad šī poga tiek aizkrāsota ar zaļu krāsu, bet vērtība zem pogas tiek pievienota sākuma nosacījumu klasei,
                # kā arī atbilsotšais bool mainīgais tiek mainīts uz to, ka vērtība ir izvēlēta.

                # 1. skaitļu izvēlei:
                if x_mouse >= 48 and x_mouse <= 152 and y_mouse >= 218 and y_mouse <= 272:
                    # izvēlēts pirmais skaitlis
                    pygame.draw.rect(screen, (66, 247, 84), [50, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [200, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [350, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [500, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [650, 220, 100, 50], 0)

                    screen.blit(pirma_skaitla_text, pirma_skaitla_text_rect)
                    screen.blit(otra_skaitla_text, otra_skaitla_text_rect)
                    screen.blit(tresa_skaitla_text, tresa_skaitla_text_rect)
                    screen.blit(ceturta_skaitla_text, ceturta_skaitla_text_rect)
                    screen.blit(piekta_skaitla_text, piekta_skaitla_text_rect)

                    pygame.display.update()

                    settings.selectedStartNumber = settings.startingNumbers[0]
                    skaitlisIzvelets = True


                if x_mouse >= 198 and x_mouse <= 302 and y_mouse >= 218 and y_mouse <= 272:
                    # izvēlēts otrais skaitlis
                    pygame.draw.rect(screen, (255, 255, 255), [50, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (66, 247, 84), [200, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [350, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [500, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [650, 220, 100, 50], 0)

                    screen.blit(pirma_skaitla_text, pirma_skaitla_text_rect)
                    screen.blit(otra_skaitla_text, otra_skaitla_text_rect)
                    screen.blit(tresa_skaitla_text, tresa_skaitla_text_rect)
                    screen.blit(ceturta_skaitla_text, ceturta_skaitla_text_rect)
                    screen.blit(piekta_skaitla_text, piekta_skaitla_text_rect)

                    pygame.display.update()

                    settings.selectedStartNumber = settings.startingNumbers[1]
                    skaitlisIzvelets = True


                if x_mouse >= 348 and x_mouse <= 452 and y_mouse >= 218 and y_mouse <= 272:
                    # izvēlēts trešais skaitlis
                    pygame.draw.rect(screen, (255, 255, 255), [50, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [200, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (66, 247, 84), [350, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [500, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [650, 220, 100, 50], 0)

                    screen.blit(pirma_skaitla_text, pirma_skaitla_text_rect)
                    screen.blit(otra_skaitla_text, otra_skaitla_text_rect)
                    screen.blit(tresa_skaitla_text, tresa_skaitla_text_rect)
                    screen.blit(ceturta_skaitla_text, ceturta_skaitla_text_rect)
                    screen.blit(piekta_skaitla_text, piekta_skaitla_text_rect)

                    pygame.display.update()

                    settings.selectedStartNumber = settings.startingNumbers[2]
                    skaitlisIzvelets = True


                if x_mouse >= 498 and x_mouse <= 602 and y_mouse >= 218 and y_mouse <= 272:
                    # izvēlēts ceturtais skaitlis
                    pygame.draw.rect(screen, (255, 255, 255), [50, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [200, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [350, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (66, 247, 84), [500, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [650, 220, 100, 50], 0)

                    screen.blit(pirma_skaitla_text, pirma_skaitla_text_rect)
                    screen.blit(otra_skaitla_text, otra_skaitla_text_rect)
                    screen.blit(tresa_skaitla_text, tresa_skaitla_text_rect)
                    screen.blit(ceturta_skaitla_text, ceturta_skaitla_text_rect)
                    screen.blit(piekta_skaitla_text, piekta_skaitla_text_rect)

                    pygame.display.update()

                    settings.selectedStartNumber = settings.startingNumbers[3]
                    skaitlisIzvelets = True


                if x_mouse >= 648 and x_mouse <= 752 and y_mouse >= 218 and y_mouse <= 272:
                    # izvēlēts piektais skaitlis
                    pygame.draw.rect(screen, (255, 255, 255), [50, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [200, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [350, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [500, 220, 100, 50], 0)
                    pygame.draw.rect(screen, (66, 247, 84), [650, 220, 100, 50], 0)

                    screen.blit(pirma_skaitla_text, pirma_skaitla_text_rect)
                    screen.blit(otra_skaitla_text, otra_skaitla_text_rect)
                    screen.blit(tresa_skaitla_text, tresa_skaitla_text_rect)
                    screen.blit(ceturta_skaitla_text, ceturta_skaitla_text_rect)
                    screen.blit(piekta_skaitla_text, piekta_skaitla_text_rect)

                    pygame.display.update()

                    settings.selectedStartNumber = settings.startingNumbers[4]
                    skaitlisIzvelets = True

                # 2. pirma lietotāja izvēlei:
                if x_mouse >= 228 and x_mouse <= 352 and y_mouse >= 398 and y_mouse <= 452:
                    # izvēlēts dators
                    pygame.draw.rect(screen, (66, 247, 84), [230, 400, 120, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [450, 400, 120, 50], 0)

                    screen.blit(dators_text, dators_text_rect)
                    screen.blit(lietotajs_text, lietotajs_text_rect)

                    pygame.display.update()

                    settings.firstPlayer = 1
                    speletajsIzvelets = True


                if x_mouse >= 448 and x_mouse <= 572 and y_mouse >= 398 and y_mouse <= 452:
                    # izvēlēts lietotājs
                    pygame.draw.rect(screen, (255, 255, 255), [230, 400, 120, 50], 0)
                    pygame.draw.rect(screen, (66, 247, 84), [450, 400, 120, 50], 0)

                    screen.blit(dators_text, dators_text_rect)
                    screen.blit(lietotajs_text, lietotajs_text_rect)

                    pygame.display.update()

                    settings.firstPlayer = 0
                    speletajsIzvelets = True

                # 3. algoritma izvēlēi:
                if x_mouse >= 48 and x_mouse <= 352 and y_mouse >= 578 and y_mouse <= 632:
                    # izvēlēts minimax
                    pygame.draw.rect(screen, (66, 247, 84), [50, 580, 300, 50], 0)
                    pygame.draw.rect(screen, (255, 255, 255), [450, 580, 300, 50], 0)

                    screen.blit(miminax_text, miminax_text_rect)
                    screen.blit(alfabeta_text, alfabeta_text_rect)

                    pygame.display.update()

                    settings.selectedAlgorithm = "minimax"
                    algoritmsIzvelets = True

                if x_mouse >= 448 and x_mouse <= 752 and y_mouse >= 578 and y_mouse <= 632:
                    # izvēlēts alfa-beta
                    pygame.draw.rect(screen, (255, 255, 255), [50, 580, 300, 50], 0)
                    pygame.draw.rect(screen, (66, 247, 84), [450, 580, 300, 50], 0)

                    screen.blit(miminax_text, miminax_text_rect)
                    screen.blit(alfabeta_text, alfabeta_text_rect)

                    pygame.display.update()

                    settings.selectedAlgorithm = "alphabeta"
                    algoritmsIzvelets = True

                if x_mouse >= 338 and x_mouse <= 462 and y_mouse >= 698 and y_mouse <= 752:
                    # uzspiesta poga "tuprināt"
                    # pārbaude, lai visas vērtības tika izvēlētas, ja kaut kas nav ievadīts - tiks attēlots teksts par to:
                    if skaitlisIzvelets == False or speletajsIzvelets == False or algoritmsIzvelets == False:
                        screen.blit(neievaditaVertiba_text, neievaditaVertiba_text_rect)
                        pygame.display.update()
                    else:
                        # ja viss ir ievadīts un uzspiesta poga "turpināt", darbība atgriežas uz pamatciklu:
                        return



# metode, kas uzzīmes otro ekrānu priekš dziļuma ievades, kā arī saņems ievadīto dziļumu:
def DzilumaIzvelesEkrans():
    # aizkrāsojam visu ekrānu ar balto krāsu:
    screen.fill((255, 255, 255))

    # definējam teksta fontu un izmēru:
    textFont = pygame.font.SysFont('Times New Roman', 30)

    # Zemāk tiek veidotas visi tekstu lauki un ievades lauks, kas nepieciešami otrajam ekranām:
    # Tie visi ir izveidoti pēc sekojoša principa(Avots - https://www.geeksforgeeks.org/python-display-text-to-pygame-window/):

    # 1. tiek definēts mainīgais "nosaukums_text", kas satur lauka/pogas tekstu
    # 2. no šī mainīga tiek veidots jauns mainīgais rect tipa "nosaukums_text_rect". Tekstu var ievietot pa taisno uz ekrānu, bet to būs vieglāk centrēt, pārvietot, krāsot u.tml. ar rect tipa objektu
    # 3. tiek definēts jauna rect tipa objekta izvietojums ekrānā
    # 4. pygame.draw.rect - tā ir taisnstūra objekta zīmēšana. Tiek pielietota, lai izveidotu rāmīties ap tekstu. Dažreiz to ir vairāk par vienu priekš viena teksta - tad pirmais ir melnais taisnstūris, otrais - krāsains, lai izveidotos melna rāmīte ap krāsaino lauku.


    # 1. Aicinājums izvēlēties dziļumu:
    dzilumaIzvele_text = textFont.render("Lūdzu, izvēlēties algoritma dziļumu", True, (255, 255, 255))
    dzilumaIzvele_text_rect = dzilumaIzvele_text.get_rect()
    dzilumaIzvele_text_rect.center = (400, 75)
    pygame.draw.rect(screen, (102, 102, 255), [150, 50, 500, 50], 0)


    # 2. Dziluma vērtības paskaidrojums:
    dzilumaPaskaidrojums_text = textFont.render("(augstākas vērtības padara datoru gudrāku, bet lēnāku)", True, (255, 255, 255))
    dzilumaPaskaidrojums_text_rect = dzilumaPaskaidrojums_text.get_rect()
    dzilumaPaskaidrojums_text_rect.center = (400, 165)
    pygame.draw.rect(screen, (102, 102, 255), [50, 140, 700, 50], 0)


    # 3. Dziļuma rekomendācija:
    dzilumaRekomendacija_text = textFont.render("Rekomendētas vērtības: 3-7", True, (255, 255, 255))
    dzilumaRekomendacija_text_rect = dzilumaRekomendacija_text.get_rect()
    dzilumaRekomendacija_text_rect.center = (400, 255)
    pygame.draw.rect(screen, (102, 102, 255), [200, 230, 400, 50], 0)


    # 4. "Uzsākt" poga:
    uzsakt_text = textFont.render("Uzsākt spēli!", True, (255, 255, 255))
    uzsakt_text_rect = uzsakt_text.get_rect()
    uzsakt_text_rect.center = (400, 575)
    pygame.draw.rect(screen, (0, 0, 0), [298, 548, 204, 54], 0)
    pygame.draw.rect(screen, (102, 102, 255), [300, 550, 200, 50], 0)


    # 5. Viss priekš lietotāja teksta ievades:
    # mainīgais, kas glabās ievadīto tekstu:
    lietotaja_ievadits_dzilums = ''

    ievadits_dzilums_text = textFont.render(lietotaja_ievadits_dzilums, True, (0, 0, 0))
    ievadits_dzilums_text_rect = ievadits_dzilums_text.get_rect()
    ievadits_dzilums_text_rect.center = (400, 420)
    pygame.draw.rect(screen, (0, 0, 0), [323, 393, 154, 54], 0)
    pygame.draw.rect(screen, (224, 224, 224), [325, 395, 150, 50], 0)


    # 6. Teksts priekš situācijas, kad dziļums ir ievadīts kļūdaini:
    nepareizs_dzilums_text = textFont.render("Tika ievadīts neatbilstošs dziļums. Lūdzu, atkārtojiet ievādi!", True, (255, 51, 51))
    nepareizs_dzilums_text_rect = nepareizs_dzilums_text.get_rect()
    nepareizs_dzilums_text_rect.center = (400, 700)


    # visu izveidoto lauku attēlošana ekrānā:
    screen.blit(dzilumaIzvele_text, dzilumaIzvele_text_rect)
    screen.blit(dzilumaPaskaidrojums_text, dzilumaPaskaidrojums_text_rect)
    screen.blit(dzilumaRekomendacija_text, dzilumaRekomendacija_text_rect)
    screen.blit(uzsakt_text, uzsakt_text_rect)
    screen.blit(ievadits_dzilums_text, ievadits_dzilums_text_rect)

    # ekrāna atjaunošana priekš visu lauku attēlošanas:
    pygame.display.update()

    # bool mainīgais kas noteiks, vai dziļums ir ievadīts:
    dzilumsIevadits = False

    # cikls, kurš darbosies kamēr netiks ievadīts dziļums algoritmam:
    while True:
        # noteic vai lietotājs ir kaut kā mijiedarbojusies ar ekrānu:
        for ev in pygame.event.get():
            # aizvēr spēles logu, ja tiek uzspiests "krustiņš":
            if ev.type == pygame.QUIT:
                pygame.quit()

            # !!! tālāk aprakstīta koda daļa, kas atbilst par lietotāja ievades attēlošanu ekrānā uzreiz pēc pogas nospiešanas, tika paņemta no ārējā resursa,
            # taču kods tika nedaudz pamainīts tā, lai nebūtu nepieciešams izmantot taimeri.
            # Saite: https://www.geeksforgeeks.org/how-to-create-a-text-input-box-with-pygame/
            # Aizņemta koda daļa sākās zemāk un beidzas uzreiz virs komentāra ar paziņojumu par to, kā aizņemta daļa ir pabeigta

            # Ja ir uzspiesta kāda tastatūras poga, tad tiek pārbaudīts, vai ta ir backspace poga.
            # Ja tā ir, tad no lietotāja ievadīta teksta tiek nodzēsts pēdējais elements.
            # Citādi lietotāja ievadītam tekstam tika pievienots nospiestas pogas unikoda apzīmējums
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_BACKSPACE:
                        lietotaja_ievadits_dzilums = lietotaja_ievadits_dzilums[:-1]
                else:
                    lietotaja_ievadits_dzilums += ev.unicode

            # ----- Aizņemtas koda daļas beigas ---------------------------------------------------------------

            # noteic, vai lietotājs ir uzspiedis pēli ekrānā, ja tā ir - noteic pēles koordinātes uzspiešanas brīdī:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                x_mouse, y_mouse = pygame.mouse.get_pos()

                # gadījumā, ja ir uzspiesta poga "uzsākt spēli", tad algoritma dziļumam tiek piešķirta ievadīta vērtība, pārveidota par int tipu,
                # mainīgais bool "dzilumsIevadits" par true un darbība tiek atgriezta pamatciklam.
                # prētēji - tiek izvādīts paziņojums, ka ievadīta vērtība ir kļūdaina:
                if x_mouse >= 298 and x_mouse <= 502 and y_mouse >= 548 and y_mouse <= 602:
                    try:
                        settings.maxDepth = int(lietotaja_ievadits_dzilums)
                        dzilumsIevadits = True
                    except:
                        screen.blit(nepareizs_dzilums_text, nepareizs_dzilums_text_rect)
                        pygame.display.update()
                        dzilumsIevadits = False

                    if dzilumsIevadits == True:
                        return

        # pēc katras pogas nospiešanas ekrānā tiks pārzīmēts teksts ar lietotāja izvadi, lai lietotājs varētu uzreiz redzēt ko ir ievadījis.
        # zīmēšana notiek tāpat ka katra elementa zīmēšana:
            # 1. tiek definēts mainīgais "nosaukums_text", kas satur lauka/pogas tekstu
            # 2. no šī mainīga tiek veidots jauns mainīgais rect tipa "nosaukums_text_rect". Tekstu var ievietot pa taisno uz ekrānu, bet to būs vieglāk centrēt, pārvietot, krāsot u.tml. ar rect tipa objektu
            # 3. tiek definēts jauna rect tipa objekta izvietojums ekrānā
            # 4. pygame.draw.rect - tā ir taisnstūra objekta zīmēšana. Tiek pielietota, lai izveidotu rāmīties ap tekstu.

        ievadits_dzilums_text = textFont.render(lietotaja_ievadits_dzilums, True, (0, 0, 0))
        ievadits_dzilums_text_rect = ievadits_dzilums_text.get_rect()
        ievadits_dzilums_text_rect.center = (400, 420)
        pygame.draw.rect(screen, (0, 0, 0), [323, 393, 154, 54], 0)
        pygame.draw.rect(screen, (224, 224, 224), [325, 395, 150, 50], 0)

        # teksta attēlošana ekrānā:
        screen.blit(ievadits_dzilums_text, ievadits_dzilums_text_rect)

        # ekrāna atjaunošana priekš visu lauku attēlošanas:
        pygame.display.update()



# metode, kas zīmē spēles ekrānu cilvēka un datora gājienu kopējus elementus.
# kā parametru tā saņem mainīgo "state", kas ir klases GameState objekts un glaba visus nosacījumus prieks spēlēs notikšanas:
#   - pašreizējo skaitli
#   - lietotāja punktu skaitu
#   - datora punktu skaitu
#   - punktu skaitu bankā
#   - kura spēlētaja gājiens tagad ir
def spelesEkrani(state):
    # aizkrāsojam visu ekrānu ar balto krāsu:
    screen.fill((255, 255, 255))

    # definējam teksta fontu un izmēru:
    textFont = pygame.font.SysFont('Times New Roman', 30)

    # Zemāk tiek veidotas visi tekstu lauki un pogas, kas nepieciešami jebkura spēletāja gājienu ekranām:
    # Tie visi ir izveidoti pēc sekojoša principa(Avots - https://www.geeksforgeeks.org/python-display-text-to-pygame-window/):

    # 1. tiek definēts mainīgais "nosaukums_text", kas satur lauka/pogas tekstu
    # 2. no šī mainīga tiek veidots jauns mainīgais rect tipa "nosaukums_text_rect". Tekstu var ievietot pa taisno uz ekrānu, bet to būs vieglāk centrēt, pārvietot, krāsot u.tml. ar rect tipa objektu
    # 3. tiek definēts jauna rect tipa objekta izvietojums ekrānā
    # 4. pygame.draw.rect - tā ir taisnstūra objekta zīmēšana. Tiek pielietota, lai izveidotu rāmīties ap tekstu. Dažreiz to ir vairāk par vienu priekš viena teksta - tad pirmais ir melnais taisnstūris, otrais - krāsains, lai izveidotos melna rāmīte ap krāsaino lauku.

    # 1. Teksts "Šobrīd gājienu veic":
    gajienuVeic_text = textFont.render("Šobrīd gājienu veic: ", True, (0, 0, 0))
    gajienuVeic_text_rect = gajienuVeic_text.get_rect()
    gajienuVeic_text_rect.topleft = (215, 50)
    pygame.draw.rect(screen, (0, 0, 0), [463, 48, 124, 44], 0)
    pygame.draw.rect(screen, (102, 102, 255), [465, 50, 120, 40], 0)


    # 2. Teksta "Tagad skaitlis ir" attēlošana:
    pasreiziejsSkaitlis_text = textFont.render("Tagad skaitlis ir: ", True, (0, 0, 0))
    pasreiziejsSkaitlis_text_rect = pasreiziejsSkaitlis_text.get_rect()
    pasreiziejsSkaitlis_text_rect.topleft = (240, 130)
    pygame.draw.rect(screen, (0, 0, 0), [443, 128, 124, 44], 0)
    pygame.draw.rect(screen, (102, 102, 255), [445, 130, 120, 40], 0)


    # 3. Teksta "Lietotāju skaits" attēlošana:
    lietotajaSkaits_text = textFont.render("Lietotāja skaits: ", True, (0, 0, 0))
    lietotajaSkaits_text_rect = lietotajaSkaits_text.get_rect()
    lietotajaSkaits_text_rect.topleft = (100, 220)
    pygame.draw.rect(screen, (0, 0, 0), [146, 268, 104, 44], 0)
    pygame.draw.rect(screen, (102, 102, 255), [148, 270, 100, 40], 0)


    # 4. Teksta "Datora skaits" attēlošana:
    datora_skaits_text = textFont.render("Datora skaits: ", True, (0, 0, 0))
    datora_skaits_text_rect = datora_skaits_text.get_rect()
    datora_skaits_text_rect.topright = (700, 220)
    pygame.draw.rect(screen, (0, 0, 0), [561, 268, 104, 44], 0)
    pygame.draw.rect(screen, (102, 102, 255), [563, 270, 100, 40], 0)


    # 5. Teksta "Bankā ir" attēlošana:
    banka_text = textFont.render("Bankā ir:", True, (0, 0, 0))
    banka_text_rect = banka_text.get_rect()
    banka_text_rect.center = (400, 650)
    pygame.draw.rect(screen, (0, 0, 0), [343, 683, 114, 44], 0)
    pygame.draw.rect(screen, (102, 102, 255), [345, 685, 110, 40], 0)


    # 6. Pašreizēja skaitļa attēlošana:
    pasreizejsSkaitlis_text = textFont.render(str(state.currentNumber), True, (255, 255, 255))
    pasreizejsSkaitlis_text_rect = pasreizejsSkaitlis_text.get_rect()
    pasreizejsSkaitlis_text_rect.center = (505, 150)


    # 7. Lietotāja punktu skaita attēlošana:
    lietotajaPunktuSkaits_text = textFont.render(str(state.humanScore), True, (255, 255, 255))
    lietotajaPunktuSkaits_text_rect = lietotajaPunktuSkaits_text.get_rect()
    lietotajaPunktuSkaits_text_rect.center = (198, 290)


    # 8. Datora punktu skaita attēlošana:
    datoraPunktuSkaits_text = textFont.render(str(state.computerScore), True, (255, 255, 255))
    datoraPunktuSkaits_text_rect = datoraPunktuSkaits_text.get_rect()
    datoraPunktuSkaits_text_rect.center = (613, 290)


    # 9. Punktu skaita bankā attēlošana:
    bankaPunkti_text = textFont.render(str(state.bankPoints), True, (255, 255, 255))
    bankaPunkti_text_rect = bankaPunkti_text.get_rect()
    bankaPunkti_text_rect.center = (400, 705)


    # visu teksta lauku un pogu izvade ekrānā:
    screen.blit(gajienuVeic_text, gajienuVeic_text_rect)
    screen.blit(pasreiziejsSkaitlis_text, pasreiziejsSkaitlis_text_rect)
    screen.blit(lietotajaSkaits_text,lietotajaSkaits_text_rect)
    screen.blit(datora_skaits_text, datora_skaits_text_rect)
    screen.blit(banka_text, banka_text_rect)
    screen.blit(pasreizejsSkaitlis_text, pasreizejsSkaitlis_text_rect)
    screen.blit(lietotajaPunktuSkaits_text, lietotajaPunktuSkaits_text_rect)
    screen.blit(datoraPunktuSkaits_text, datoraPunktuSkaits_text_rect)
    screen.blit(bankaPunkti_text, bankaPunkti_text_rect)

    # uzzīmēta ekrāna atjaunošana, lai viss uzzīmētais būtu redzams:
    pygame.display.update()

    # tā kā šis ekrāns tikai uzzīmē kopēju abu spēlētāju gājienu ekrānu daļas, tas nenolasa nekādas vērtības, bet tikai uzzīme visu un atgriež vadību pamatciklam:
    return



# metode, kas attēlo datus, kas nepieciešams attēlot lietotāja gājiena laikā.
# kā atribūtu tā saņem sarakstu ar iespējamiem gājieniem - cipariem, ar kuriem ir iespējams sadalīt pašreizējo skaitli:
def lietotajaGajiens(possible_moves):
    # veidojam iekšējo sarakstu, kurš kope iespējamo gājienu saraksta vērtības:
    gajienuVarianti = possible_moves

    # definējam teksta fontu un izmēru:
    textFont = pygame.font.SysFont('Times New Roman', 30)

    # Zemāk tiek veidotas visi tekstu lauki un pogas, kas nepieciešami tieši lietotāja gājienu ekranām:
    # Tie visi ir izveidoti pēc sekojoša principa(Avots - https://www.geeksforgeeks.org/python-display-text-to-pygame-window/):

    # 1. tiek definēts mainīgais "nosaukums_text", kas satur lauka/pogas tekstu
    # 2. no šī mainīga tiek veidots jauns mainīgais rect tipa "nosaukums_text_rect". Tekstu var ievietot pa taisno uz ekrānu, bet to būs vieglāk centrēt, pārvietot, krāsot u.tml. ar rect tipa objektu
    # 3. tiek definēts jauna rect tipa objekta izvietojums ekrānā
    # 4. pygame.draw.rect - tā ir taisnstūra objekta zīmēšana. Tiek pielietota, lai izveidotu rāmīties ap tekstu. Dažreiz to ir vairāk par vienu priekš viena teksta - tad pirmais ir melnais taisnstūris, otrais - krāsains, lai izveidotos melna rāmīte ap krāsaino lauku.

    # 1. Attēlojam, ka gājienu veic lietotājs:
    lietotajs_text = textFont.render("Lietotājs", True, (255, 255, 255))
    lietotajs_text_rect = lietotajs_text.get_rect()
    lietotajs_text_rect.center = (525, 70)

    # 2. Teksta "Iespējamie soļi ir atzīmēti ar zaļo krāsu" attēlošana:
    iespejamieSoli_text = textFont.render("Iespējamie soļi ir atzīmēti ar zaļo krāsu", True, (0, 0, 0))
    iespejamieSoli_text_rect = iespejamieSoli_text.get_rect()
    iespejamieSoli_text_rect.center = (400, 370)

    # 3. Aicinājuma izvēlēties ar kuru ciparu sadalīt, kā arī pašu ciparu, attēlošana:
    izveletiesSoli_text = textFont.render("Uzspiediet uz ciparu, lai ar to sadalītu pašreizējo skaitļi:", True, (0, 0, 0))
    izveletiesSoli_text_rect = izveletiesSoli_text.get_rect()
    izveletiesSoli_text_rect.center = (400, 410)

    cipars_divi_text = textFont.render("2", True, (0, 0, 0))
    cipars_divi_text_rect = cipars_divi_text.get_rect()
    cipars_divi_text_rect.center = (310, 485)

    cipars_tris_text = textFont.render("3", True, (0, 0, 0))
    cipars_tris_text_rect = cipars_tris_text.get_rect()
    cipars_tris_text_rect.center = (490, 485)

    pygame.draw.rect(screen, (0, 0, 0), [258, 458, 104, 54], 2)
    pygame.draw.rect(screen, (0, 0, 0), [438, 458, 104, 54], 2)


    # visu teksta lauku attēlošana ekrānā:
    screen.blit(lietotajs_text, lietotajs_text_rect)
    screen.blit(iespejamieSoli_text, iespejamieSoli_text_rect)
    screen.blit(izveletiesSoli_text, izveletiesSoli_text_rect)
    screen.blit(cipars_divi_text, cipars_divi_text_rect)
    screen.blit(cipars_tris_text, cipars_tris_text_rect)

    # uzzīmēta ekrāna atjaunošana, lai viss uzzīmētais būtu redzams:
    pygame.display.update()

    # bool tipa mainīgie, kas parāda vai ir iespējams pašreizējo skaitli sadlīt ar attiecīgi divi un trīs:
    varDalitArDivi = False
    varDalitArTris = False

    # cikls, kura laikā lietotājs redzēs ar kuriem cipariem var sadalīt pašreizējo skaitli un varēs to izdarīt:
    while True:
        # noteic vai lietotājs ir kaut kā mijiedarbojusies ar ekrānu:
        for ev in pygame.event.get():
            # aizvēr spēles logu, ja tiek uzspiests "krustiņš":
            if ev.type == pygame.QUIT:
                pygame.quit()

            # pārbaudam, kuras vērtības ir sarakstā ar iespējamiem gājieniem un attiecīgi no tā mainam bool tipa mainīgo vērtības:
            for i in gajienuVarianti:
                if i == 2:
                    varDalitArDivi = True
                if i == 3:
                    varDalitArTris = True

            # tālāk pārbaudam ar kuriem cipariem var sadalīt, ja ar ciparu var sadalīt, tad lauks zem tā tiek aizkrāsots ar zaļo krāsu,
            # ja dalīt ar ciparu nav iespējams - tad lauks tiek aizkrāsots ar sarkano krāsu:
            if varDalitArDivi == False:
                pygame.draw.rect(screen, (255, 51, 51), [260, 460, 100, 50], 0)
                screen.blit(cipars_divi_text, cipars_divi_text_rect)
                pygame.display.update()

            if varDalitArDivi == True:
                pygame.draw.rect(screen, (102, 255, 102), [260, 460, 100, 50], 0)
                screen.blit(cipars_divi_text, cipars_divi_text_rect)
                pygame.display.update()


            if varDalitArTris == False:
                pygame.draw.rect(screen, (255, 51, 51), [440, 460, 100, 50], 0)
                screen.blit(cipars_tris_text, cipars_tris_text_rect)
                pygame.display.update()

            if varDalitArTris == True:
                pygame.draw.rect(screen, (102, 255, 102), [440, 460, 100, 50], 0)
                screen.blit(cipars_tris_text, cipars_tris_text_rect)
                pygame.display.update()


            # noteic, vai lietotājs ir uzspiedis pēli ekrānā, ja tā ir - noteic pēles koordinātes uzspiešanas brīdī:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                x_mouse, y_mouse = pygame.mouse.get_pos()

                # ja koordinātes atbilst tam, kā lietotājs izvēlējas sadalīt ar divi, tad atgriež, ka sadalīts ir ar 2:
                if varDalitArDivi == True and x_mouse >= 258 and x_mouse <= 362 and y_mouse >= 458 and y_mouse <= 512:
                    return 2

                # ja koordinātes atbilst tam, kā lietotājs izvēlējas sadalīt ar trīs, tad atgriež, ka sadalīts ir ar 3:
                if varDalitArTris == True and x_mouse >= 438 and x_mouse <= 542 and y_mouse >= 458 and y_mouse <= 512:
                    return 3



# metode, kas attēlo datus, kas nepieciešams attēlot datora gājiena laikā.
# kā atribūtu saņem skaitli (apzīmēts ar "move"), ar kuru dators izvēlējas dalīt:
def datoraGajiens(move):
    # pievienojam iekšējo mainīgo, kura vērtība ir vienāda ar saņemta soļa vērtību:
    solis = move

    # definējam teksta fontu un izmēru:
    textFont = pygame.font.SysFont('Times New Roman', 30)

    # Zemāk tiek veidotas visi tekstu lauki un pogas, kas nepieciešami tieši datora gājienu ekranām:
    # Tie visi ir izveidoti pēc sekojoša principa(Avots - https://www.geeksforgeeks.org/python-display-text-to-pygame-window/):

    # 1. tiek definēts mainīgais "nosaukums_text", kas satur lauka/pogas tekstu
    # 2. no šī mainīga tiek veidots jauns mainīgais rect tipa "nosaukums_text_rect". Tekstu var ievietot pa taisno uz ekrānu, bet to būs vieglāk centrēt, pārvietot, krāsot u.tml. ar rect tipa objektu
    # 3. tiek definēts jauna rect tipa objekta izvietojums ekrānā
    # 4. pygame.draw.rect - tā ir taisnstūra objekta zīmēšana. Tiek pielietota, lai izveidotu rāmīties ap tekstu. Dažreiz to ir vairāk par vienu priekš viena teksta - tad pirmais ir melnais taisnstūris, otrais - krāsains, lai izveidotos melna rāmīte ap krāsaino lauku.


    # 1. Attēlojam, ka gājienu veic dators:
    dators_text = textFont.render("Dators", True, (255, 255, 255))
    dators_text_rect = dators_text.get_rect()
    dators_text_rect.center = (525, 70)

    # 2. Apmēklēto mezglu skaita attēlošana:
    mezgluApmeklets_text = textFont.render("Apmeklēto mezglu skaits: " + str(stats.nodesVisited), True, (0, 0, 0))
    mezgluApmeklets_text_rect = mezgluApmeklets_text.get_rect()
    mezgluApmeklets_text_rect.topleft = (30, 370)

    # 3. Laika, kas bija aizņemts uz soļa veikšanu, attēlošana:
    laiks_text = textFont.render("Aizņemtais laiks: " + str(round(stats.moveDuration, 6)), True, (0, 0, 0))
    laiks_text_rect = laiks_text.get_rect()
    laiks_text_rect.topright = (750, 370)


    # 4. Datora izvēlēta gājiena attēlojums:
    datoraGajiens_text = textFont.render("Datora izvēlētais solis: ", True, (0, 0, 0))
    datoraGajiens_text_rect = datoraGajiens_text.get_rect()
    datoraGajiens_text_rect.topleft = (192.5, 450)

    sadalitAr_text = textFont.render("Sadalīt ar " + str(solis), True, (0, 0, 0))
    sadalitAr_text_rect = sadalitAr_text.get_rect()
    sadalitAr_text_rect.topleft = (472, 450)

    pygame.draw.rect(screen, (0, 0, 0), [468, 448, 144, 44], 0)
    pygame.draw.rect(screen, (102, 255, 102), [470, 450, 140, 40], 0)

    # 5. Turpināt spēli pogas attēlojums:
    turpinatSpeli_text = textFont.render("Turpināt spēli", True, (255, 255, 255))
    turpinatSpeli_text_rect = turpinatSpeli_text.get_rect()
    turpinatSpeli_text_rect.center = (400, 570)
    pygame.draw.rect(screen, (0, 0, 0), [315, 548, 170, 44], 0)
    pygame.draw.rect(screen, (102, 102, 255), [317, 550, 166, 40], 0)


    # visu teksta lauku attēlošana ekrānā:
    screen.blit(dators_text, dators_text_rect)
    screen.blit(mezgluApmeklets_text, mezgluApmeklets_text_rect)
    screen.blit(laiks_text, laiks_text_rect)
    screen.blit(datoraGajiens_text, datoraGajiens_text_rect)
    screen.blit(sadalitAr_text, sadalitAr_text_rect)
    screen.blit(turpinatSpeli_text, turpinatSpeli_text_rect)

    # uzzīmēta ekrāna atjaunošana, lai viss uzzīmētais būtu redzams:
    pygame.display.update()

    # cikls, ar kura palīdzību tiks apstrādāta lietotāja mijiedarbība ar ekrānu
    # tas darbosies kamēr lietotājs nenospiedīs uz pogu "tuprināt spēli":
    while True:
        # noteic vai lietotājs ir kaut kā mijiedarbojusies ar ekrānu:
        for ev in pygame.event.get():
            # aizvēr spēles logu, ja tiek uzspiests "krustiņš":
            if ev.type == pygame.QUIT:
                pygame.quit()

            # noteic, vai lietotājs ir uzspiedis pēli ekrānā, ja tā ir - noteic pēles koordinātes uzspiešanas brīdī:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                x_mouse, y_mouse = pygame.mouse.get_pos()

                # ja pēles koordinātes nospiešanas momentā atbilstēja pogai "turpināt spēli", tad vadība tiek atgriezta pamatciklam:
                if x_mouse >= 315 and x_mouse <= 485 and y_mouse >= 548 and y_mouse <= 592:
                    return



# metode, kas attēlo spēļu statistiku:
def spelesStatistikasEkrans():
    # aizkrāsojam visu ekrānu ar balto krāsu:
    screen.fill((255, 255, 255))

    # definējam teksta fontu un izmēru:
    textFont = pygame.font.SysFont('Times New Roman', 30)

    # Zemāk tiek veidotas visi tekstu lauki un pogas, kas nepieciešami statiskitas attēlošanas ekranām:
    # Tie visi ir izveidoti pēc sekojoša principa(Avots - https://www.geeksforgeeks.org/python-display-text-to-pygame-window/):

    # 1. tiek definēts mainīgais "nosaukums_text", kas satur lauka/pogas tekstu
    # 2. no šī mainīga tiek veidots jauns mainīgais rect tipa "nosaukums_text_rect". Tekstu var ievietot pa taisno uz ekrānu, bet to būs vieglāk centrēt, pārvietot, krāsot u.tml. ar rect tipa objektu
    # 3. tiek definēts jauna rect tipa objekta izvietojums ekrānā
    # 4. pygame.draw.rect - tā ir taisnstūra objekta zīmēšana. Tiek pielietota, lai izveidotu rāmīties ap tekstu. Dažreiz to ir vairāk par vienu priekš viena teksta - tad pirmais ir melnais taisnstūris, otrais - krāsains, lai izveidotos melna rāmīte ap krāsaino lauku.

    # 1. Teksta "Spēle ir beigusies!" izvade:
    spelesBeigas_text = textFont.render("Spēle ir beigusies!", True, (0, 0, 0))
    spelesBeigas_text_rect = spelesBeigas_text.get_rect()
    spelesBeigas_text_rect.center = (400, 50)

    # 2. Teksta "Statistika:" izvade:
    statistika_text = textFont.render("Statistika:", True, (0, 0, 0))
    statistika_text_rect = statistika_text.get_rect()
    statistika_text_rect.center = (400, 110)

    # 3. Izspēlēto spēlu skaita attēlošana:
    speluSkaits_text = textFont.render("Izspēlētās spēles: " + str(stats.gamesPlayed), True, (0, 0, 0))
    speluSkaits_text_rect = speluSkaits_text.get_rect()
    speluSkaits_text_rect.topleft = (30, 160)

    # 4. Lietotāju uzvaras skaita attēlošana:
    lietotajaUzvaras_text = textFont.render("Lietotāja uzvaras: " + str(stats.humanWinCount), True, (0, 0, 0))
    lietotajaUzvaras_text_rect = lietotajaUzvaras_text.get_rect()
    lietotajaUzvaras_text_rect.topleft = (30, 210)

    # 5. Datora uzvaras skaita attēlošana:
    datoraUzvaras_text = textFont.render("Datora uzvaras: " + str(stats.computerWinCount), True, (0, 0, 0))
    datoraUzvaras_text_rect = datoraUzvaras_text.get_rect()
    datoraUzvaras_text_rect.topleft = (30, 260)

    # 6. Neizšķirto spēļu skaita attēlošana:
    draw_text = textFont.render("Neizšķirts: " + str(stats.draws), True, (0, 0, 0))
    draw_text_rect = draw_text.get_rect()
    draw_text_rect.topleft = (30, 310)

    # 7. Pēdējas spēles laikā pielietota algoritma izvade:
    algoritms_text = textFont.render("Pielietots algoritms: " + settings.selectedAlgorithm, True, (0, 0, 0))
    algoritms_text_rect = algoritms_text.get_rect()
    algoritms_text_rect.topleft = (30, 360)

    # 8. Pēdējas spēles algoritma dziļuma izvade:
    dzilums_text = textFont.render("Algoritma dziļums šī spēlē: " + str(settings.maxDepth), True, (0, 0, 0))
    dzilums_text_rect = dzilums_text.get_rect()
    dzilums_text_rect.topleft = (30, 410)

    # 9. Pēdējas spēles rezultāta izvade:
    pedejaisRezultats_text = textFont.render("Pēdējas spēles rezultāts: " + str(stats.lastGameResult), True, (0, 0, 0))
    pedejaisRezultats_text_rect = pedejaisRezultats_text.get_rect()
    pedejaisRezultats_text_rect.topleft = (30, 460)

    # 10. Vidēja datora gājiena laika izvade:
    vidLaiks_text = textFont.render("Vidējais datora gājiena laiks: " + str(stats.averageMoveTime), True, (0, 0, 0))
    vidLaiks_text_rect = vidLaiks_text.get_rect()
    vidLaiks_text_rect.topleft = (30, 510)

    # 11. Teksta "Vai Jūs vēlāties nospēlēt vēlreiz?" attēlošana:
    velreiz_text = textFont.render("Vai Jūs vēlāties nospēlēt vēlreiz?", True, (0, 0, 0))
    velreiz_text_rect = velreiz_text.get_rect()
    velreiz_text_rect.center = (400, 630)

    # 12. Varianta "Jā" attēlošana:
    ja_text = textFont.render("Jā", True, (0, 0, 0))
    ja_text_rect = ja_text.get_rect()
    ja_text_rect.center = (320, 710)

    pygame.draw.rect(screen, (0, 0, 0), [268, 688, 104, 44], 0)
    pygame.draw.rect(screen, (161, 245, 149), [270, 690, 100, 40], 0)

    # 13. Varianta "Nē" attēlošana:
    ne_text = textFont.render("Nē", True, (0, 0, 0))
    ne_text_rect = ne_text.get_rect()
    ne_text_rect.center = (480, 710)

    pygame.draw.rect(screen, (0, 0, 0), [428, 688, 104, 44], 0)
    pygame.draw.rect(screen, (240, 98, 98), [430, 690, 100, 40], 0)


    # visu teksta lauku attēlošana ekrānā:
    screen.blit(spelesBeigas_text, spelesBeigas_text_rect)
    screen.blit(statistika_text, statistika_text_rect)
    screen.blit(speluSkaits_text, speluSkaits_text_rect)
    screen.blit(lietotajaUzvaras_text, lietotajaUzvaras_text_rect)
    screen.blit(datoraUzvaras_text, datoraUzvaras_text_rect)
    screen.blit(draw_text, draw_text_rect)
    screen.blit(algoritms_text, algoritms_text_rect)
    screen.blit(dzilums_text, dzilums_text_rect)
    screen.blit(pedejaisRezultats_text, pedejaisRezultats_text_rect)
    screen.blit(vidLaiks_text, vidLaiks_text_rect)
    screen.blit(velreiz_text, velreiz_text_rect)
    screen.blit(ja_text, ja_text_rect)
    screen.blit(ne_text, ne_text_rect)

    # uzzīmēta ekrāna atjaunošana, lai viss uzzīmētais būtu redzams:
    pygame.display.update()

    # cikls, kas apstrādas lietotāja mijiedarbību ar spēli.
    # ja tiks izvēlēts atkārtot spēli, tad tas izsauks spēles pamatciklu vēlreiz.
    # ja tiks izvēlēts pabeigt spēli - tad izsaukt spēlēs beigas ekrānu un pārtrauks savu ciklu
    while True:
        # noteic vai lietotājs ir kaut kā mijiedarbojusies ar ekrānu:
        for ev in pygame.event.get():
            # aizvēr spēles logu, ja tiek uzspiests "krustiņš":
            if ev.type == pygame.QUIT:
                pygame.quit()

            # noteic, vai lietotājs ir uzspiedis pēli ekrānā, ja tā ir - noteic pēles koordinātes uzspiešanas brīdī:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                x_mouse, y_mouse = pygame.mouse.get_pos()

                # ja koordinātes atbilst pogai uzsākt no jauna ("jā"), izsauc pamatciklu vēlreiz:
                if x_mouse >= 268 and x_mouse <= 372 and y_mouse >= 688 and y_mouse <= 732:
                    play_game()

                # ja koordinātes atbilst pogai pabeigt spēli ("nē"), izsauc beigas ekrānu un pārtrauc ciklu:
                if x_mouse >= 428 and x_mouse <= 532 and y_mouse >= 688 and y_mouse <= 732:
                    beiguEkrans()
                    break


# metode, kas attēlo vārdus "paldies par spēli!", kad lietotājs nolēmj vairs nespēlēt:
def beiguEkrans():
    # aizkrāsojam visu ekrānu ar balto krāsu:
    screen.fill((255, 255, 255))

    # definējam teksta fontu un izmēru:
    textFont = pygame.font.SysFont('Times New Roman', 60)

    # veidojam teksta objektu pēc sekojoša principa:
    # 1. tiek definēts mainīgais "nosaukums_text", kas satur lauka/pogas tekstu
    # 2. no šī mainīga tiek veidots jauns mainīgais rect tipa "nosaukums_text_rect". Tekstu var ievietot pa taisno uz ekrānu, bet to būs vieglāk centrēt, pārvietot, krāsot u.tml. ar rect tipa objektu
    # 3. tiek definēts jauna rect tipa objekta izvietojums ekrānā

    paldies_text = textFont.render("Paldies par spēli!", True, (0, 0, 0))
    paldies_text_rect = paldies_text.get_rect()
    paldies_text_rect.center = (400, 400)

    # attēlojam tekstu ekrānā:
    screen.blit(paldies_text, paldies_text_rect)

    # uzzīmēta ekrāna atjaunošana, lai viss uzzīmētais būtu redzams:
    pygame.display.update()


def play_game(): # spēles pamatcikls - tas parvaldā speles gaitu:
    while True:
        # Clear the transposition table at the start of each new game
        global transposition_table
        transposition_table = {}
        for ev in pygame.event.get(): # noteic vai lietotājs ir kaut kā mijiedarbojusies ar ekrānu
            if ev.type == pygame.QUIT: # aizvēr spēles logu, ja tiek uzspiests "krustiņš"
                pygame.quit()
            pygame.init() # inicializējam visas importētas pygame bibliotekas moduļus

            settings.startingNumbers = generate_starting_numbers() # ģenerējam sākuma skaitļus:

            noteikumuIzvelePirmais() # izsaucam pirmo ekrānu, kurā lietotājs izvēlēsies sākuma spēlētāju, sākuma skaitļu un algoritmu, kuru izmantos dators
            DzilumaIzvelesEkrans() # izsaucam otro ekrānu, kurā lietotājs izvēlēsies algoritma dziļumu

            # iniciālizējam spēles stāvokli no iegūtiem sākuma nosacījumiem:
            state = GameState( # tiek inicializēts katrā spēles iterācijā ar jaunām vērtībām
                currentNumber=settings.selectedStartNumber,
                humanScore=0,
                computerScore=0,
                bankPoints=0,
                currentPlayer=settings.firstPlayer
            )

            # pašas spēles cikls, kamēr spēle nav beigusies:
            while not state.isGameOver:
                # izsaucam ekrānu ar abu spēlētāju gājienu kopējiem elementiem, kā parametru nosūtām iegūto spēles stāvokli:
                spelesEkrani(state)

                # pārbaudam, vai ir iespējamie gājieni:
                # jā iespējamo gājienu nav, pārtraucam pašas spēles ciklu:
                possible_moves = get_possible_moves(state)
                if not possible_moves:
                    state.isGameOver = True
                    break

                # ja ir iespējamie soļi, tad atkarībā no spēlētāja:
                # 1. ja spēlētajs ir lietotājs:
                if state.currentPlayer == 0:
                    # pieprāsam lietotājam izdarīt gājienu, pārādot iespējamos gājienus, kad tas ir iegūts - atjaunojas spēles stāvoklis:
                    move = lietotajaGajiens(possible_moves)
                    if move:
                        state = apply_move(state, move)


                # 2. ja spēlētajs ir dators:
                else:
                    # dators veic savu gājienu, pēc kura atjaunojam spēles stāvokli, vai nu beidzam spēli, ja nav iespēju veikt soli datoram:
                    move = best_move(state, settings, stats)

                    if move:
                        datoraGajiens(move)
                        state = apply_move(state, move)

                    else:
                        print("Computer could not find a valid move! Game over.")
                        state.isGameOver = True


            # pēc spēles pabeigšanas izsaucam statistikas ekrānu, kurā arī jautājam, vai lietotājs grib nospēlēt vēlreiz:
            display_game_result(state, stats)

            spelesStatistikasEkrans()


if __name__ == "__main__":
    play_game()
