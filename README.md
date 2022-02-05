## wordle-game

Wordle game, solver, helper.  Just play it, or get hints, or optimal next guess.

Wordle has been the viral hit of early 2022.  It's simple, quick, and delightful.
There is plenty of internet chatter on game strategy.
Out of interest, I put together a command line python based version of the game.

### 2,315 Wordles means 5,359,225 opening moves
Important is that the Wordle dictionary is selection of 2315 words.  Apparently the
"official" game accepts those letter combinations as guesses as well as an additional
10657 five-letter combinations. This information comes thanks to another wordle repo
here: [rgkimball/wordlebot](//github.com/rgkimball/wordlebot).

#### How many possible words remain?
This game has some little features, like showing you the remaining possible words
based on your guess results.  This is done by maintaining the set of possible letters
for each of the 5 letter positions, as well as a minimum and maximum count of each
letter of the alphabet in the full word.  The can will let you request to see the
size of the remaining soltuion set of words.  Nice.

### Recommend optimal guess
Next, you can ask the game to recommend a guess based on what has been learned from
prior guesses.  The game will recommend the *optimal* guess.  What is the *optimal*
guess? The optimal guess is one that will result in the smallest remainin solution
set for all possible words in the current solution set. In some cases there are more
than one optimal guess, and in some cases the optimal guess is *not* in the remaining
solution set.

### Automated optimal solver
Lastly, you can put the game into full-auto mode (FSD?) and it will play through the
entire wordle dicionary.  In standard game-play mode it will solve all possible wordles
in 6 guesses or less. Some detail here: it solves 94% of words in 4 or fewer guesses,
and only one word requires 6 guesses. In hard-mode (per Internet this means you must
use all known good letters in subsequent guesses) it will solve all wordles in up to 8
guesses. Where 12 words take 7 gueses and 3 take 8 guesses.

Enjoy!

----
#### Now for some trivia (spolier alert!)
- The provably best starting word is `ARISE` (or alternately its anagram `RAISE`.  With `ARISE`
as your first guess the maximum remaining solution set is 168 words. Next best letter
combination is `ALONE` which gurantees a maximum |solution set size of
182 words.
- The hardest words to solve are ones that have a large number of adjacent
solutions.  Take `ROVER`which has 7 adjacent words that differ by one
letter: `COVER, HOVER, LOVER, MOVER, RIVER, ROGER, ROWER`.
