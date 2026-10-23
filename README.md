# WortSchatz 💰

A small web app that helps my wife learn German vocabulary for her
nursing job in Austria, with a reward system: every correct answer
earns cents, paid out as pocket money.

*"Wortschatz" means vocabulary in German, literally "word treasure".*

Built with Python and Flask, playable on her phone.

## How it works

### Learning
- 📖 **Learning cards:** every new word is shown first as a card
  (Greek, German, pronunciation)
- 🔘 **Multiple choice** for new words: +5 cent
- ⌨️ **Typing** once she knows the word: +10 cent
- ✍️ **Wrong answer:** she sees the correct word and must type it once to continue
- 🟡 **Wrong article** or **one typo:** half points (+5 cent), and the word comes back
- 💡 **Hint:** shows the article, the first letter and the length (+5 cent instead of 10)
- 🎨 **Colored articles:** der = blue, die = red, das = green
- 🔊 **Pronunciation** button using the browser's speech synthesis
- 📦 **Spaced repetition (Leitner boxes):** wrong words come back often,
  known words come back less and less, but never disappear
- 🐢 **Max 10 new words per day**, the rest is review
- 📖 **Mistakes diary:** all words she got wrong, hardest first

### Game
- ⏱️ **Max 5 rounds of 10 words per day**, unused rounds are lost
- ↩️ **Back to menu** anytime, and resume later from the same point
- 🎉 **Confetti** on a perfect 10/10 round
- 🔥 **Streak:** +1 € bonus every 7 days in a row
- 🎯 **Weekly goal:** 150 correct answers, +2 € bonus
- 📈 **Level progress:** words seen, learned and mastered

### Dashboard and money
- 📅 **Weekly dashboard:** days played, correct, wrong, accuracy, earnings
- 📊 **Last week** summary
- 💶 **Payments:** "to pay" balance with a "Paid ✓" button and payment history
- 🏆 **Totals:** everything earned and everything paid

### App
- 🔒 **PIN** login
- 🌓 **Light / dark theme** button (follows the phone by default)
- 📱 **Home screen icon**

## Run locally
1. `pip install flask`
2. Copy `local_settings.example.json` to `local_settings.json`
   and set your own PIN and a long random `secret_key`
3. `python app.py`
4. Open `http://127.0.0.1:5000`

## Settings
All amounts and limits are at the top of `app.py` (SETTINGS):
rounds per day, words per round, new words per day,
cents per answer, streak and weekly goal bonuses.
The PIN and the secret key are in `local_settings.json` (not in Git).

## Files
- `app.py`: the web app (words, logic, pages)
- `local_settings.example.json`: template for `local_settings.json`
- `local_settings.json`: PIN and secret key (not in Git)
- `progress.json`: her progress and earnings, created automatically (not in Git)

## Roadmap
- [x] Basic quiz, Greek -> German
- [x] Lenient answer check (case, spaces, ae/oe/ue/ss)
- [x] Flask web version for the phone
- [x] Dashboard with weekly stats
- [x] PIN login
- [x] Max 5 rounds per day
- [x] Leitner boxes (spaced repetition)
- [x] Level progress
- [x] Pronunciation button
- [x] Payments with "Paid ✓"
- [x] Back to menu and resume
- [x] Learning cards, multiple choice, retype after mistake, article colors
- [x] Half points for wrong article or one typo
- [x] Hint button
- [x] Confetti on 10/10
- [x] Streak bonus and weekly goal
- [x] Mistakes diary
- [x] Light / dark theme
- [x] Home screen icon
- [x] Deploy on PythonAnywhere
- [ ] Austrian words (Spital, Jänner...)
- [ ] Plural forms and example sentences
- [ ] Level 2 and words in a CSV file