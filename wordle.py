"""Wordle Game

Play something like the NYTimes Wordle, or help you solve it.
"""
import sys
import re
import random
import string
import time
from collections import Counter
from enum import Enum
try:
    from colorama import Fore, Back, Style, init
except ModuleNotFoundError:
    print('colorama is not installed. Consider "pip install colorama" ...')
    exit()

init(autoreset=True)

recalc_count = 0
recalc_timers = [0.0] * 6

class WCommand(Enum):
    HelpMsg = 'HelpMsg'
    HelpSolve = 'HelpSolve'
    NewWord = 'NewWord'
    Possibles = 'Possibles'
    Recommend = 'Recommend'
    Auto = 'Auto'
    Quit = 'Quit'

class WColor(Enum):
    X = 'X'
    B = 'B'
    Y = 'Y'
    G = 'G'

def wcolorize(s:str='', template:str='') -> str:
    cnt = 0
    res = ''
    cmap = {
        WColor.G.value: Fore.BLACK + Back.GREEN,
        WColor.Y.value: Fore.BLACK + Back.YELLOW,
        WColor.B.value: Fore.WHITE + Back.BLACK,
        WColor.X.value: Fore.BLACK + Back.WHITE
    }
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
        self.guess = None
        self.colors = None
        self.input = None
        self.cmd:WCommand = None
    
    def help_msg(self) -> None:
        print ('Commands: 1. Web-Game, 2. New Word, 3. Possibilities, 4. Recommend, 5. Auto, 6. Quit')
        print ('Guess input must be 5 letters [A-Z].')
        print ('Color input must be 5 colors [GYB]{5}.')

    def collect_input(self, prompt:str, count:int, colorize:bool=True) -> None:
        self.cmd  = None
        if (count <= 6 or not colorize):
            print(prompt.format(count), end='')
        else:
            print('{}{}{}'.format(Style.RESET_ALL + Style.BRIGHT + Fore.RED, prompt.format(count), Style.RESET_ALL), end='')
        try:
            self.input = input().strip().upper()
        except EOFError:
            print ('\nEOF')
            self.cmd = WCommand.Quit
        return (self.cmd)

    def parse_input_cmds(self) -> bool:
        if (self.input == '?'):
            self.cmd = WCommand.HelpMsg
        elif (self.input == 'Q'):
            self.cmd = WCommand.Quit
        elif (self.input == '1'):
            self.cmd = WCommand.HelpSolve
        elif (self.input == '2'):
            self.cmd = WCommand.NewWord
        elif (self.input == '3'):
            self.cmd = WCommand.Possibles
        elif (self.input == '4'):
            self.cmd = WCommand.Recommend
        elif (self.input == '5'):
            self.cmd = WCommand.Auto
        elif (self.input == '6'):
            self.cmd = WCommand.Quit
        return (self.cmd is not None)

    def parse_guess(self, inp:str = None) -> bool:
        self.guess = None
        if inp is None:
            inp = self.input
        if re.match('^[A-Z]{5}$', inp):
            self.guess = inp
            return True
        return False

    def parse_colors(self, inp:str = None) -> bool:
        if inp is None:
            inp = self.input
        if re.match('^[GYB]{5}$', inp):
            self.colors = inp
            return True
        return False

    def compute_colors(self, guess:str, answer:str) -> None:
        answer = list(answer)
        colors = list('-' * 5)
        for i, ch in enumerate(answer):
            if (guess[i] == ch):
                colors[i] = 'G'
                answer[i] = '-'

        for i, ch in enumerate(answer):
            if (colors[i] == '-'):
                if (guess[i] in answer):
                    colors[i] = 'Y'
                    answer[answer.index(guess[i])] = '-'
                elif (colors[i] != 'G'):
                    colors[i] = 'B'
        self.colors = ''.join(colors)

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
        print ('                  {}'.format(' '.join(list(string.ascii_uppercase))))
        print ('d.min_count       {}'.format(' '.join(f'{k}-{v}' for k,v in self.min_count.items())))
        print ('d.max_count       {}'.format(' '.join(f'{k}-{v}' for k,v in self.max_count.items())))
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

    def update_descriptor (self, g:Guess, verbose:bool = False):
        verbose = True
        color_order = 'GYBX'

        pairs = list(zip(g.colors, g.guess))
        sorted_pairs = sorted(pairs, key=lambda pair: pair[1]+str(color_order.index(pair[0])))
        if verbose:
            print (f'sorted_pairs = {list(sorted_pairs)}')
        first_i = 0
        for i in range(5):
            pair = sorted_pairs[i]
            if color_order.index(pair[0]) < color_order.index(self.alpha_colors[pair[1]]):
                self.alpha_colors[pair[1]] = pair[0]
            if pair[1] != sorted_pairs[first_i][1]:
                first_i = i
            if pair[0] == WColor.B.value:
                self.max_count[pair[1]] = min(self.max_count[pair[1]], i - first_i)
                if verbose:
                    print (f'Max count of letter "{pair[1]}" is {self.max_count[pair[1]]}')
            else:
                self.min_count[pair[1]] = max(self.min_count[pair[1]], i - first_i + 1)
                if verbose:
                    print (f'Min count of letter "{pair[1]}" is {self.min_count[pair[1]]}')
        min_sum = sum(self.min_count.values())
        for c in string.ascii_uppercase:
            self.max_count[c] = min(self.max_count[c], 5 - min_sum + self.min_count[c])

        if verbose:
            self.pprint('update decriptor - PRE')
            print (f'guess={g}')
            print (f'guess={g.guess}, pairs={pairs}')
        for i, (color, letter) in enumerate(pairs):
            if color == 'B':
                if g.guess.count(letter) <= 1:
                    for s in self.sets:
                        s -= set(letter)
                    if verbose:
                        print (f'Letter "{letter}" removed from each position')
                else:
                    if verbose:
                        print (f'Letter "{letter}" not removed because duplicate')
            elif color == 'G':
                self.sets[i] = set(letter)
                if verbose:
                    print (f'All letters except "{letter}" removed from position {i}')
            elif color == 'Y':
                self.sets[i] = self.sets[i] - set(letter)
                if verbose:
                    print (f'Letter "{letter}" removed from position {i}')
        if verbose:
            self.pprint('decriptor updated - POST')

        for ch in string.ascii_uppercase:
            if self.max_count[ch] == 0:
                msg = False
                for j in range(5):
                    if ch in self.sets[j]:
                        msg = True                        
                        self.sets[j] = self.sets[j] - set(ch)
                if msg:
                    if verbose:
                        print (f'Letter {ch} removed from each position. Because zero max count.')

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
        self.auto_mode = False
        self.hard_mode = False
        self.stats = Counter()
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

    def best_guesses(self, d: Descriptor, guess_count:int=5):
        scores = Counter()
        word_count = 0
        ans_count = 0
        print_count = 0
        total = len(self.possible_words) * len(d.remaining_words)
        start_time = time.time()
        min_of_max = len(self.possible_words)

        timers = [0] * 6

        if (self.hard_mode):
            guess_words = d.remaining_words
        else:
            guess_words = self.possible_words

        for word in guess_words:
            score = []

            g = Guess()
            g.guess = word

            word_count += 1
            ans_count = (word_count - 1) * len(d.remaining_words)
            for ans in d.remaining_words:
                t1 = time.time()
                dd = self.state.copy()
                t2 = time.time()
                g.compute_colors(g.guess, ans)
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
        recs = {x: scores[x] for x in d.remaining_words if x in scores and scores[x] <= min_of_max}
        if (len(recs) == 0):
            is_remaing = False
            recs = {x: count for x, count in scores.items() if count <= min_of_max}
        recs = recs.keys()
        if (guess_count < len(recs)):
            recs = random.sample(recs, guess_count)
        return (min_of_max, list(recs), is_remaing)

    def play(self):
        g = None
        pwi = iter(self.possible_words)

        while True:

            count = 0
            self.reset_state()
            print ('{}'.format('=' * 20))
            if (self.auto_mode):
                try:
                    self.answer = next(pwi)
                    print ('Selecting word {} in the list of {} words.'.format(sum(self.stats.values()), len(self.possible_words)))
                except StopIteration:
                    print ('Complete all words. Exiting.')
                    exit()
            else:
                self.answer = random.choice(self.possible_words)
                print ('Picking a random wordle from {} possibilities.'.format(len(self.possible_words)))

            while True:                
                while True:
                    if (not self.auto_mode):
                        print ('{}'.format('-' * 20))
                        #print ('Commands: 1. Web-Game, 2. New Word, 3. Possibilities, 4. Recommend, 5. Auto, 6. Quit')

                    for i in range(len(self.guesses)):
                        color_on = Style.RESET_ALL + Style.BRIGHT + Fore.RED
                        color_off = Style.RESET_ALL
                        if (i+1 <= 6):
                            color_on = ''
                            color_off = ''
                        print ('{}Guess #{}:{}  {}'.format(color_on, i+1, color_off, self.guesses[i]))

                    if (not self.auto_mode):
                        self.state.pprint_keyboard()

                    g = Guess()
                    if (self.auto_mode):
                        if (count+1 == 1):
                            g.guess = 'ARISE'
                        else:
                            (frw, words, ispw)  = self.best_guesses(self.state)
                            g.guess = words[0]
                    else:
                        g.collect_input('Guess  #{}:  ', count+1)
                        if (not g.parse_input_cmds()):
                            if (not g.parse_guess()):
                                g.cmd = WCommand.HelpMsg

                    if g.cmd is not None:
                        if (g.cmd == WCommand.Quit):
                            break
                        if (g.cmd == WCommand.Possibles) or (g.cmd == WCommand.Recommend):
                            lp = len(self.state.remaining_words)
                            print (f'Remaining Wordles: {len(self.state.remaining_words)}', end='')
                            print (f'{("  " + " ".join(self.state.remaining_words[0:7]), "")[lp > 8]}')
                        
                        if (g.cmd == WCommand.Recommend):
                            (frw, words, ispw)  = self.best_guesses(self.state)
                            print (f'Try one of these {("","*possible* ")[ispw==1]}words: [{','.join(words)}]')
                            print (f'This will reduce the set of remaining possibilities to at most {frw} words.')
                            continue
                        
                        elif (g.cmd == WCommand.NewWord):
                            self.answer = None
                            count = 0
                            self.reset_state()
                            self.answer = random.choice(self.possible_words)
                            print ('OK. picking a random wordle from {} possibilities.'.format(len(self.possible_words)))
                            continue

                        elif (g.cmd == WCommand.Auto):
                            self.answer = None
                            count = 0
                            self.reset_state()
                            self.auto_mode = True
                            self.answer = next(pwi)
                            print ('Stand back. Entering full-auto mode.')
                            continue

                        elif (g.cmd == WCommand.HelpSolve):
                            self.answer = None
                            count = 0
                            self.reset_state()
                            print ('Ready to help you solve NYT Wordle.')
                            continue

                        elif (g.cmd == WCommand.HelpMsg):
                            g.help_msg()
                            continue

                    else:
                        break

                if (g.cmd == WCommand.Quit): break

                if self.answer:
                    g.compute_colors(g.guess, self.answer)
                else:
                    g.collect_input('Colors #{}:  ', count+1)
                    if (not g.parse_input_cmds()):
                        if (not g.parse_colors()):
                            g.cmd = WCommand.HelpMsg
                    if g.cmd == WCommand.Quit:
                        break

                count += 1
                self.state.update_descriptor(g)
                self.guesses.append(g)
                self.state.recalculate(self.pw_counters, False)


                if g.guess == self.answer:

                    print ('-' * 20)
                    for i,g in enumerate(self.guesses):
                        print (f'Guess #{i+1}:  {g}')
                    if self.auto_mode:
                        self.stats.update([count])
                    else:
                        self.state.pprint_keyboard()

                    print (f'Wordle {g} found in {count} guesses!')
                    if self.auto_mode:
                        print (f'Summary solving stats: {self.stats}')
                        if not self.hard_mode and count > 6:
                            print ('Auto failed to solve in 6 guesses.')
                            exit()
                    break

            if g.cmd == WCommand.Quit:
                break
        print ('Quitting')

def main(fname):
    game = Wordle()
    game.play()

if __name__ == "__main__":
    main(open(sys.argv[1], encoding="utf-8") if len(sys.argv) > 1 else sys.stdin)