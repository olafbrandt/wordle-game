import string, re, random
from collections import Counter
from sys import prefix
from xmlrpc.client import Boolean
from colorama import Fore, Back, Style, init
from enum import Enum
import copy
import math
import time

init(autoreset=True)

recalc_count = 0
recalc_timers = [0.0] * 6

class WCommand(Enum):
    HelpSolve = 'HelpSolve'
    NewWord = 'NewWord'
    Possibles = 'Possibles'
    Recommend = 'Recommend'
    Quit = 'Quit'

class WColor(Enum):
    X = 'X'
    B = 'B'
    Y = 'Y'
    G = 'G'

def wcolorize(s='', template=''):
    cnt = 0
    res = ''
    cmap = {
        WColor.G.value: Fore.BLACK + Back.GREEN,
        WColor.Y.value: Fore.BLACK + Back.YELLOW,
        WColor.B.value: Fore.WHITE + Back.BLACK }
    for i in range(min(len(s), len(template))):
        t = template[i].upper()
        if (t in cmap):
            res += '{}{}{}'.format(Style.RESET_ALL + Style.BRIGHT + cmap[t], s[i], Style.RESET_ALL)
        else:
            res += s[i]
        cnt += 1
    res += s[cnt:]
    return (res)

class Guess:
    def __init__(self):
        self.guess = ''
        self.colors = ''
        self.cmd = None
    
    def collect_guess(self, count=1):
        self.cmd = None
        guess = None
        try:   
            while True:
                print('#{} Guess:  '.format(count), end='')
                guess = input().strip().upper()
                if (re.match('^[A-Z]{5}$', guess)):
                    break
                if (guess == 'Q'):
                    self.cmd = WCommand.Quit
                elif (guess == '1'):
                    self.cmd = WCommand.HelpSolve
                elif (guess == '2'):
                    self.cmd = WCommand.NewWord
                elif (guess == '3'):
                    self.cmd = WCommand.Possibles
                elif (guess == '4'):
                    self.cmd = WCommand.Recommend
                elif (guess == '5'):
                    self.cmd = WCommand.Quit
                else:
                    print ('Guess must be 5 letters or a valid command.')
                    continue
                break
        except EOFError:
            print ('\nEOF')
            self.cmd = WCommand.Quit
        self.guess = guess
    
    def collect_colors(self, count=1):
        self.colors = None
        try:
            while True:
                print('#{} Colors: '.format(count), end='')
                colors = input().strip().upper()
                if (re.match('^[GYB]{5}$', colors)):
                    self.colors = colors
                    break
                if (colors == 'Q'):
                    self.cmd = WCommand.Quit
                    break
                print ('Colors must be 5 colors (G, Y, B). Or \'Q\' to exit.')
        except EOFError:
            print ('\nEOF')
            self.cmd = WCommand.Quit

    def compute_colors(self, answer:str):
        ans = list(answer)
        colors = list('-' * len(ans))
        for i in range(len(ans)):
            if (self.guess[i] == ans[i]):
                colors[i] = 'G'
                ans[i] = '-'

        for i in range(len(ans)):
            if (colors[i] == '-'):
                if (self.guess[i] in ans):
                    colors[i] = 'Y'
                    ans[ans.index(self.guess[i])] = '-'
                elif (colors[i] != 'G'):
                    colors[i] = 'B'
        self.colors = colors

    def __str__(self):
        return (wcolorize(self.guess, self.colors))          

class Descriptor:
    def __init__(self, remaining_words):
        self.sets = [set(string.ascii_uppercase)] * 5
        self.min_count = Counter()
        self.max_count = Counter(string.ascii_uppercase * 5)
        self.remaining_words = remaining_words.copy()
        self.alpha_colors = dict(zip(string.ascii_uppercase, WColor.X.value * 26))

    def copy(self):
        c = Descriptor(self.remaining_words)
        for i in range(len(c.sets)):
            c.sets[i] = self.sets[i].copy()
        c.min_count = self.min_count.copy()
        c.max_count = self.max_count.copy()
        c.alpha_colors = self.alpha_colors.copy()
        return (c)

    def pprint(self, prefix:str=None):
        if (prefix is not None):
            print ('{}'.format(prefix))
        regex = ''.join(['[' + ''.join(sorted(s)) + ']' for s in self.sets])
        ac = ' '.join([self.alpha_colors[c] for c in string.ascii_uppercase])
        print ('d.regex           {}'.format(regex))
        print ('            {}'.format(' '.join(list(string.ascii_uppercase))))
        print ('d.min_count       {}'.format(self.min_count))
        print ('d.max_count       {}'.format(self.max_count))
        #print ('d.min_count       {}'.format(' '.join([str(self.min_count[c]) for c in string.ascii_uppercase])))
        #print ('d.max_count       {}'.format(' '.join([str(self.max_count[c]) for c in string.ascii_uppercase])))
        print ('d.alpha_colors    {}'.format(wcolorize(' '.join(list(string.ascii_uppercase)), ac)))
        print ('d.remaining_words {} words'.format(len(self.remaining_words)))
        
    def pprint_keyboard (self):
        row = 'QWERTYUIOP' 
        ac = ''.join([self.alpha_colors[c] for c in row])
        print ('{}'.format(wcolorize(' '.join(list(row)), ' '.join(list(ac)))))

        row = 'ASDFGHJKL'
        ac = ''.join([self.alpha_colors[c] for c in row])
        print (' {}'.format(wcolorize(' '.join(list(row)), ' '.join(list(ac)))))

        row = 'ZXCVBNM'
        ac = ''.join([self.alpha_colors[c] for c in row])
        print ('  {}'.format(wcolorize(' '.join(list(row)), ' '.join(list(ac)))))

    def update_descriptor (self, g:Guess, verbose:bool=False):
        #verbose = True
        color_order = 'GYBX'
        
        pairs = list(zip(list(g.colors), list(g.guess)))
        sorted_pairs = sorted(pairs, key=lambda pair: pair[1]+str(color_order.index(pair[0])))
        if verbose: print ('sorted_pairs={}'.format(list(sorted_pairs)))
        first_i = 0
        for i in range(5):
            pair = sorted_pairs[i]
            if (color_order.index(pair[0]) < color_order.index(self.alpha_colors[pair[1]])):
                self.alpha_colors[pair[1]] = pair[0]
            if (pair[1] != sorted_pairs[first_i][1]):
                first_i = i
            if (pair[0] == WColor.B.value):
                self.max_count[pair[1]] = min(self.max_count[pair[1]], i - first_i)
                if verbose: print ('Max count of letter \'{}\' is {}'.format(pair[1], self.max_count[pair[1]]))
            else:
                self.min_count[pair[1]] = max(self.min_count[pair[1]], i - first_i + 1)
                if verbose: print ('Min count of letter \'{}\' is {}'.format(pair[1], self.min_count[pair[1]]))
        min_sum = sum(self.min_count.values())
        for c in string.ascii_uppercase:
            self.max_count[c] = min(self.max_count[c], 5 - min_sum + self.min_count[c])

        if verbose: self.pprint('update decriptor')
        if verbose: print ('guess={}'.format(g))
        if verbose: print ('guess={}, pairs={}'.format(g.guess, pairs))
        for i in range(len(pairs)):
            pair = pairs[i]
            if (pair[0] == 'B'):
                if (len(re.findall(pair[1], g.guess)) <= 1):
                    for j in range(len(self.sets)):
                        self.sets[j] = self.sets[j] - set(pair[1])
                    if verbose: print ('Letter \'{}\' removed from each position'.format(pair[1]))
                else:
                    if verbose: print ('Letter \'{}\' not removed because duplicate'.format(pair[1]))
                    None
            elif (pair[0] == 'G'):
                self.sets[i] = set(pair[1])
                if verbose: print ('All letters except \'{}\' removed from position {}'.format(pair[1], i))
            elif (pair[0] == 'Y'):
                self.sets[i] = self.sets[i] - set(pair[1])
                if verbose: print ('Letter \'{}\' removed from position {}'.format(pair[1], i))

        for ch in string.ascii_uppercase:
            if (self.max_count[ch] == 0):
                msg = False
                for j in range(5):
                    if (ch in self.sets[j]):
                        msg = True                        
                        self.sets[j] = self.sets[j] - set(ch)
                if msg:
                    if verbose: print ('Letter {} removed from each position. Because zero max count.'.format(ch))
                    None

    def recalculate(self, pw_counters, verbose:bool=False):

        global recalc_count

        t0 = time.time()

        t1 = time.time()

        cMin = self.min_count

        t2 = time.time()

        ok_words = []
        for w in self.remaining_words:
            keep = True
            cWord = pw_counters[w]
            for i in self.min_count.items():
                if (cWord[i[0]] < i[1]):
                    keep = False
                    if verbose: print ('cWord={}\ncMin={}'.format(cWord, self.min_count))
                    if verbose: print ('Remove \'{}\'. Fails min_count requirement'.format(w))
                    break

            if keep:
                ok_words.append(w)
        if verbose: print ('Remaining words: {} - {} = {}, applied min count rule.'.format(len(self.remaining_words), len(self.remaining_words) - len(ok_words), len(ok_words)))
        self.remaining_words = ok_words
        
        t3 = time.time()

        ok_words = []
        for w in self.remaining_words:
            keep = True
            cWord = pw_counters[w]
            for i in cWord.items():
                if (self.max_count[i[0]] < i[1]):
                    keep = False
                    if verbose: print ('cWord={}\ncMax={}'.format(cWord, self.max_count))
                    if verbose: print ('Remove \'{}\'. Fails max count requirement'.format(w))
                    break

            if keep:
                ok_words.append(w)

        if verbose: print ('Remaining words: {} - {} = {}, applied max count rule.'.format(len(self.remaining_words), len(self.remaining_words) - len(ok_words), len(ok_words)))
        self.remaining_words = ok_words

        t4 = time.time()

        regex = ''.join(['[' + ''.join(sorted(s)) + ']' for s in self.sets])
        if verbose: print (regex)
        ok_words = re.findall(regex, ' '.join(self.remaining_words)) or []

        if verbose: print ('Remaining words: {} - {} = {}, applied regex'.format(len(self.remaining_words), len(self.remaining_words) - len(ok_words), len(ok_words)))
        self.remaining_words = ok_words

        t5 = time.time()
        
        recalc_timers[0] += t5 - t0
        recalc_timers[1] += t1 - t0
        recalc_timers[2] += t2 - t1
        recalc_timers[3] += t3 - t2
        recalc_timers[4] += t4 - t3
        recalc_timers[5] += t5 - t4
        
        recalc_count += 1
        if (recalc_count % 10 == 0):
            pctg = [recalc_timers[i]/recalc_timers[0]*100.0 for i in range(1,6)]
            #print ('Recalc: {:6.2f}  {:6.2f}%  {:6.2f}%  {:6.2f}%  {:6.2f}%  {:6.2f}%  '.format(recalc_timers[0], *pctg))


def read_words_file(filename:str):
    with open(filename) as file:
        wordlist = [w.upper() for w in file.read().splitlines()]
    return (wordlist)

class Wordle:
    def __init__(self):
        self.reset_state()

    def reset_state(self):
        self.possible_words = read_words_file("wordle-answers-alphabetical.txt")
        self.possible_guesses = read_words_file("wordle-allowed-guesses.txt")
        self.state = Descriptor(self.possible_words)
        self.answer = None
        self.guesses = []
        self.pw_counters = {}
        for w in self.possible_words:
            self.pw_counters[w] = Counter(w)
    
    def best_guesses_x(self, d: Descriptor, guess_count:int=5):
        scores = Counter()
        setmask = [(1,0)[len(s) <= 1] for s in d.sets]
        for word_a in self.possible_words:
            score = 0
            orig_word_a = word_a
            set_a = set([word_a[i] for i in range(5) if setmask[i]])
            for word_b in self.remaining_words:
                set_b = set([word_b[i] for i in range(5) if setmask[i]])
                if (len(set_a.intersection(set_b)) > 0):
                    score += 1
            scores[orig_word_a] = score

        return (scores.most_common(guess_count))

    def best_guesses(self, d: Descriptor, guess_count:int=5):
        scores = Counter()
        word_count = 0
        ans_count = 0
        print_count = 0
        total = len(self.possible_words) * len(d.remaining_words)
        start_time = time.time()
        min_of_max = len(self.possible_words)

        timers = [0] * 6

        for word in self.possible_words:
            score = []

            g = Guess()
            g.guess = word

            word_count += 1
            ans_count = (word_count - 1) * len(d.remaining_words)
            for ans in d.remaining_words:
                t1 = time.time()
                dd = self.state.copy()
                t2 = time.time()
                g.compute_colors(ans)
                t3 = time.time()
                #print ('g={} ans={}'.format(g, ans))
                dd.update_descriptor(g)
                t4 = time.time()
                dd.recalculate(self.pw_counters, False)
                t5 = time.time()

                score.append(len(dd.remaining_words))
                if (len(dd.remaining_words) > min_of_max):
                    score.append(9999)
                    break

                t6 = time.time()

                print_count += 1
                ans_count += 1 
                elapsed_time = time.time() - start_time
                print ('Evaluating {} scenarios: {:6.2f}% complete. (Rate: {}/sec)'.format(total, (ans_count / total) * 100, ans_count // elapsed_time), end ='\r')
            
                t7 = time.time()

                timers[0] += t2 - t1
                timers[1] += t3 - t2
                timers[2] += t4 - t3
                timers[3] += t5 - t4
                timers[4] += t6 - t5
                timers[5] += t7 - t6

                if (print_count % 10 == 0):
                    total_time = sum(timers)
                    timers_pctg = [x / total_time * 100.0 for x in timers]
                    #print ('{}'.format(timers), end='\r')
                    if False:
                        print ('Total: {:6.2f} Timers: {:6.2f}%  {:6.2f}%  {:6.2f}%  {:6.2f}%  {:6.2f}%  {:6.2f}%x'.format(total_time,
                            timers_pctg[0], timers_pctg[1], timers_pctg[2], timers_pctg[3], timers_pctg[4], timers_pctg[5]), end='\r')

            #print (word, score)
            if max(score) != 9999:
                scores[word] = max(score)
                min_of_max = min(min_of_max, scores[word])
        
        print()

        #print ('{}\n{}\n{}'.format('=' * 80, scores, '=' * 80))

        is_remaing = True
        recommendations = {x: scores[x] for x in d.remaining_words if x in scores and scores[x] <= min_of_max}
        if (len(recommendations) == 0):
            #print ('Remaining words are not best')
            is_remaing = False
            recommendations = {x: count for x, count in scores.items() if count <= min_of_max}
        #print ('Recommendations: ',recommendations)
        recommendations = recommendations.keys()
        if (guess_count < len(recommendations)):
            recommendations = random.sample(recommendations, guess_count)
        return (min_of_max, list(recommendations), is_remaing)

    def help(self):
        print ('I am ready to help solve a wordle.')
        count = 0
        while True:
            self.state.recalculate(self.pw_counters, False)

            if False and count >= 0:
                bg = self.best_guesses(self.state)
                print ('recommend = {}'.format(bg))

            lp = len(self.state.remaining_words)
            print ('Remaining Wordles: {}'.format(len(self.state.remaining_words), ('')), end='')
            print ('{}'.format('  '+(' '.join(self.state.remaining_words[0:7]),'')[lp > 8]))
            if (lp <= 1):
                print ("Wordle Found!")
                break

            count += 1
            g = Guess()
            g.collect_guess(count)
            
            self.state.update_descriptor(g)

    def play(self):
        g = None

        while True:

            count = 0
            self.reset_state()
            self.answer = random.choice(self.possible_words)
            print ('{}'.format('=' * 20))
            print ('Picking a random wordle from {} possibilities.'.format(len(self.possible_words)))

            while True:                
                while True:
                    print ('{}'.format('-' * 20))
                    print ('Commands: 1. Solve NYT, 2. New Word, 3. Possibilities, 4. Recommend, 5. Quit')

                    for i in range(len(self.guesses)):
                        print ('Guess #{}:  {}'.format(i+1, self.guesses[i]))

                    self.state.pprint_keyboard()

                    g = Guess()
                    g.collect_guess(count+1)
                    if g.cmd is not None:
                        if (g.cmd == WCommand.Quit): break
                        if (g.cmd == WCommand.Possibles) or (g.cmd == WCommand.Recommend):
                            lp = len(self.state.remaining_words)
                            print ('Remaining Wordles: {}'.format(len(self.state.remaining_words), ('')), end='')
                            print ('{}'.format('  '+(' '.join(self.state.remaining_words[0:7]),'')[lp > 8]))
                        
                        if (g.cmd == WCommand.Recommend):
                            bg = self.best_guesses(self.state)
                            print ('Recommend = {}'.format(bg))
                            continue
                        
                        elif (g.cmd == WCommand.NewWord):
                            self.answer = None
                            count = 0
                            self.reset_state()
                            self.answer = random.choice(self.possible_words)
                            print ('Picking a random wordle from {} possibilities.'.format(len(self.possible_words)))
                            continue

                        elif (g.cmd == WCommand.HelpSolve):
                            self.answer = None
                            count = 0
                            self.reset_state()
                            print ('Ready to help you solve NYT Wordle.')
                            continue
                    else:
                        break

                if (g.cmd == WCommand.Quit): break

                count += 1
                if self.answer:
                    g.compute_colors(self.answer)
                else:
                    g.collect_colors()
                    if (g.cmd == WCommand.Quit): break

                self.state.update_descriptor(g)
                self.guesses.append(g)
                self.state.recalculate(self.pw_counters, False)


                if (g.guess == self.answer):

                    print ('{}'.format('=' * 20))
                    for i in range(len(self.guesses)):
                        print ('Guess #{}:  {}'.format(i+1, self.guesses[i]))
                    self.state.pprint_keyboard()

                    print ('Wordle {} found in {} guesses!'.format(g, count))
                    break

            if (g.cmd == WCommand.Quit): break
        print ('Quitting')

game = Wordle()
game.play()