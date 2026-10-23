import os
import random
import json
from datetime import date, timedelta

from flask import (Flask, request, redirect, url_for, session,
                   render_template_string, Response)
from markupsafe import Markup, escape

app = Flask(__name__)
# ===================== PRIVATE SETTINGS =====================
# PIN and secret key live in local_settings.json, which is NOT in Git.
# Copy local_settings.example.json to local_settings.json and fill it in.
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_settings.json")
if not os.path.exists(SETTINGS_FILE):
    raise SystemExit("local_settings.json is missing: copy local_settings.example.json "
                     "to local_settings.json and set your own PIN and secret_key.")
with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
    _private = json.load(f)
app.secret_key = _private["secret_key"]
PIN = str(_private["pin"])
app.permanent_session_lifetime = timedelta(days=365)

# ===================== SETTINGS =====================
ROUNDS = 5
WORDS_PER_ROUND = 10
NEW_PER_DAY = 10
CENTS_CHOICE = 5
CENTS_TYPE = 10
CENTS_HALF = 5                    # wrong article, one typo, or hint used
STREAK_DAYS = 7                   # bonus every 7 days in a row
STREAK_BONUS = 100                # cents
WEEKLY_GOAL = 150                 # correct answers per week
WEEKLY_GOAL_BONUS = 200           # cents
INTERVALS = [0, 0, 1, 3, 7, 14]   # days until next review per box (box 0 = choice, 1+ = typing)
LEARNED_BOX = 3                   # typed correctly on 2 different days
MASTERED_BOX = len(INTERVALS) - 1
DAY_LABELS = ["Δε", "Τρ", "Τε", "Πε", "Πα", "Σα", "Κυ"]
GAME_KEYS = ["queue", "index", "round", "round_correct", "round_ok", "round_cents",
             "game_correct", "game_cents", "learn_queue", "learn_index",
             "retype", "feedback", "bonus_msg", "hint", "game_date"]
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "progress.json")

# ===================== WORDS (Level 1) =====================
words = {
    # --- Nursing ---
    "der Patient": "ο ασθενής",
    "die Pflegekraft": "ο νοσηλευτής",
    "der Arzt": "ο γιατρός",
    "das Fieber": "ο πυρετός",
    "der Blutdruck": "η πίεση",
    "der Puls": "ο σφυγμός",
    "die Spritze": "η ένεση",
    "die Infusion": "ο ορός",
    "der Verband": "ο επίδεσμος",
    "die Wunde": "η πληγή",
    "das Medikament": "το φάρμακο",
    "die Tablette": "το χάπι",
    "die Schmerzen": "οι πόνοι",
    "das Blut": "το αίμα",
    "der Rollstuhl": "το αναπηρικό καροτσάκι",
    "die Station": "η πτέρυγα",
    "der Notfall": "το επείγον",
    "die Schicht": "η βάρδια",
    "der Nachtdienst": "η νυχτερινή βάρδια",
    "die Übergabe": "η παράδοση βάρδιας",
    "das Pflegeheim": "το γηροκομείο",
    "das Bett": "το κρεβάτι",
    "die Visite": "η επίσκεψη γιατρών",

    # --- Body ---
    "der Kopf": "το κεφάλι",
    "der Bauch": "η κοιλιά",
    "der Rücken": "η πλάτη",
    "die Brust": "το στήθος",
    "der Arm": "ο βραχίονας",
    "die Hand": "το χέρι",
    "das Bein": "το πόδι",
    "das Knie": "το γόνατο",
    "das Herz": "η καρδιά",
    "die Lunge": "ο πνεύμονας",
    "der Magen": "το στομάχι",
    "die Haut": "το δέρμα",
    "der Hals": "ο λαιμός",
    "das Auge": "το μάτι",

    # --- Symptoms ---
    "der Husten": "ο βήχας",
    "der Schwindel": "η ζάλη",
    "die Übelkeit": "η ναυτία",
    "das Erbrechen": "ο εμετός",
    "der Durchfall": "η διάρροια",
    "die Verstopfung": "η δυσκοιλιότητα",
    "die Atemnot": "η δύσπνοια",
    "die Allergie": "η αλλεργία",
    "die Entzündung": "η φλεγμονή",
    "die Blutung": "η αιμορραγία",

    # --- Equipment ---
    "das Fieberthermometer": "το θερμόμετρο",
    "das Blutdruckmessgerät": "το πιεσόμετρο",
    "die Handschuhe": "τα γάντια",
    "der Mundschutz": "η μάσκα",
    "das Desinfektionsmittel": "το απολυμαντικό",
    "der Katheter": "ο καθετήρας",
    "das Pflaster": "ο λευκοπλάστης",
    "die Windel": "η πάνα",
    "die Klingel": "το κουδούνι",

    # --- Hospital ---
    "das Krankenhaus": "το νοσοκομείο",
    "die Krankenschwester": "η νοσοκόμα",
    "die Ärztin": "η γιατρός",
    "der Angehörige": "ο συγγενής",
    "die Aufnahme": "η εισαγωγή",
    "die Entlassung": "το εξιτήριο",
    "die Operation": "η επέμβαση",
    "die Intensivstation": "η εντατική",
    "die Notaufnahme": "τα επείγοντα",
    "der Termin": "το ραντεβού",

    # --- Verbs ---
    "messen": "μετράω",
    "waschen": "πλένω",
    "helfen": "βοηθάω",
    "verabreichen": "χορηγώ",
    "desinfizieren": "απολυμαίνω",
    "wechseln": "αλλάζω",
    "umlagern": "αλλάζω θέση",
    "beobachten": "παρακολουθώ",
    "dokumentieren": "καταγράφω",
    "anziehen": "ντύνω",
    "schlucken": "καταπίνω",
    "atmen": "αναπνέω",

    # --- Daily care ---
    "die Pflege": "η φροντίδα",
    "das Zimmer": "το δωμάτιο",
    "die Toilette": "η τουαλέτα",
    "das Essen": "το φαγητό",
    "das Wasser": "το νερό",
    "die Decke": "η κουβέρτα",
    "das Kissen": "το μαξιλάρι",
    "die Seife": "το σαπούνι",
    "das Handtuch": "η πετσέτα",
    "der Rollator": "το περπατούρι",
    "die Waage": "η ζυγαριά",
    "das Rezept": "η συνταγή",
    "die Salbe": "η αλοιφή",
    "die Tropfen": "οι σταγόνες",
    "die Temperatur": "η θερμοκρασία",
    "das Gewicht": "το βάρος",
    "der Stuhlgang": "η κένωση",
    "der Urin": "τα ούρα",
    "schlafen": "κοιμάμαι",
    "essen": "τρώω",
    "trinken": "πίνω",
    "aufstehen": "σηκώνομαι",
}


# ===================== DATA =====================
def load_progress():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    data.setdefault("days", {})
    data.setdefault("boxes", {})
    data.setdefault("payments", [])
    data.setdefault("mistakes", {})
    data.setdefault("goals_paid", [])
    return data


def save_progress(progress):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def get_today(progress):
    today = date.today().isoformat()
    day = progress["days"].setdefault(today, {})
    day.setdefault("correct", 0)
    day.setdefault("wrong", 0)
    day.setdefault("cents", 0)
    day.setdefault("rounds", 0)
    day.setdefault("done", [])
    day.setdefault("new", [])
    return day


# ===================== ANSWER CHECKING =====================
def normalize(text):
    text = " ".join(text.split())      # trim and collapse spaces
    text = text.lower()
    text = text.replace("ä", "ae")
    text = text.replace("ö", "oe")
    text = text.replace("ü", "ue")
    text = text.replace("ß", "ss")
    return text


def check_answer(answer, correct):
    return normalize(answer) == normalize(correct)


def split_article(text):
    parts = text.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() in ("der", "die", "das"):
        return parts[0], parts[1]
    return "", text


def distance(a, b):
    # number of single-letter edits between two strings (Levenshtein)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def grade(answer, correct):
    a = normalize(answer)
    c = normalize(correct)
    if a == c:
        return "ok"
    a_art, a_noun = split_article(a)
    c_art, c_noun = split_article(c)
    if c_art and a_noun == c_noun:
        return "article"               # right word, wrong or missing article
    if len(c) >= 4 and distance(a, c) == 1:
        return "almost"                # one letter wrong
    return "wrong"


def make_hint(word):
    art, noun = split_article(word)
    hint = noun[0] + " _" * (len(noun) - 1)
    return (art + " " + hint).strip()


def article_html(word):
    art, rest = split_article(word)
    if art:
        return Markup('<span class="{0}">{0}</span> {1}'.format(art, escape(rest)))
    return escape(word)


app.jinja_env.filters["art"] = article_html


# ===================== LEARNING LOGIC =====================
def word_box(progress, word):
    return progress["boxes"].get(word, {"box": 0})["box"]


def update_box(progress, word, correct):
    today = date.today()
    entry = progress["boxes"].get(word, {"box": 0, "due": today.isoformat()})
    if correct:
        entry["box"] = min(entry["box"] + 1, MASTERED_BOX)
    else:
        entry["box"] = 0
    entry["due"] = (today + timedelta(days=INTERVALS[entry["box"]])).isoformat()
    progress["boxes"][word] = entry
    return entry["box"]


def repeat_today(progress, word):
    # half-right answer: same box, but the word comes back today
    entry = progress["boxes"].get(word, {"box": 0})
    entry["due"] = date.today().isoformat()
    progress["boxes"][word] = entry


def pick_words(progress, day):
    today = date.today().isoformat()
    boxes = progress["boxes"]
    due, new, later = [], [], []

    for w in words:
        if w in day["done"]:
            continue
        if w not in boxes:
            new.append(w)
        elif boxes[w]["due"] <= today:
            due.append(w)
        else:
            later.append(w)

    random.shuffle(due)
    random.shuffle(new)
    due.sort(key=lambda w: boxes[w]["box"])      # weakest words first
    later.sort(key=lambda w: boxes[w]["due"])    # soonest due first
    new_quota = max(0, NEW_PER_DAY - len(day["new"]))
    return (due + new[:new_quota] + later)[:WORDS_PER_ROUND]


def make_options(key):
    others = []
    for w in words:
        if w != key:
            others.append(w)
    options = random.sample(others, 3) + [key]
    random.shuffle(options)
    return options


def level_stats(progress):
    seen = 0
    learned = 0
    mastered = 0
    for w in words:
        entry = progress["boxes"].get(w)
        if entry:
            seen += 1
            if entry["box"] >= LEARNED_BOX:
                learned += 1
            if entry["box"] == MASTERED_BOX:
                mastered += 1
    return seen, learned, mastered


# ===================== MONEY, STATS, BONUSES =====================
def money(progress):
    earned = 0
    for s in progress["days"].values():
        earned += s.get("cents", 0)
    paid = 0
    for p in progress["payments"]:
        paid += p["cents"]
    return earned, paid, earned - paid


def played(s):
    return s.get("correct", 0) + s.get("wrong", 0) > 0


def week_label(d):
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


def current_streak(progress):
    d = date.today()
    days = progress["days"]
    if not played(days.get(d.isoformat(), {})):
        d -= timedelta(days=1)
    streak = 0
    while played(days.get(d.isoformat(), {})):
        streak += 1
        d -= timedelta(days=1)
    return streak


def week_stats(progress, weeks_ago):
    ref = date.today() - timedelta(days=7 * weeks_ago)
    year, week, _ = ref.isocalendar()
    today_weekday = date.today().isoweekday()

    stats = {"correct": 0, "wrong": 0, "cents": 0, "days_played": 0}
    flags = [False] * 7

    for day_text, s in progress["days"].items():
        y, w, wd = date.fromisoformat(day_text).isocalendar()
        if y == year and w == week and played(s):
            stats["correct"] += s.get("correct", 0)
            stats["wrong"] += s.get("wrong", 0)
            stats["cents"] += s.get("cents", 0)
            stats["days_played"] += 1
            flags[wd - 1] = True

    answered = stats["correct"] + stats["wrong"]
    stats["accuracy"] = round(stats["correct"] / answered * 100) if answered else 0

    stats["days"] = []
    for i in range(7):
        stats["days"].append({
            "label": DAY_LABELS[i],
            "played": flags[i],
            "today": weeks_ago == 0 and i + 1 == today_weekday,
        })
    return stats


def check_bonuses(progress, day):
    messages = []

    if not day.get("streak_checked"):
        day["streak_checked"] = True
        streak = current_streak(progress)
        if streak > 0 and streak % STREAK_DAYS == 0:
            day["cents"] += STREAK_BONUS
            day["bonus"] = day.get("bonus", 0) + STREAK_BONUS
            messages.append(f"🔥 {streak} μέρες στη σειρά! Μπόνους +{STREAK_BONUS / 100:.2f} €")

    label = week_label(date.today())
    if label not in progress["goals_paid"] and week_stats(progress, 0)["correct"] >= WEEKLY_GOAL:
        progress["goals_paid"].append(label)
        day["cents"] += WEEKLY_GOAL_BONUS
        day["bonus"] = day.get("bonus", 0) + WEEKLY_GOAL_BONUS
        messages.append(f"🎯 Στόχος εβδομάδας! Μπόνους +{WEEKLY_GOAL_BONUS / 100:.2f} €")

    return " · ".join(messages) if messages else None


# ===================== GAME STATE =====================
def clear_game():
    for k in GAME_KEYS:
        session.pop(k, None)


def game_in_progress():
    if "queue" not in session:
        return False
    if session.get("game_date") != date.today().isoformat() or "learn_queue" not in session:
        clear_game()          # old-version or previous-day game is dropped
        return False
    return True


def learning_pending():
    return session.get("learn_index", 0) < len(session.get("learn_queue", []))


def start_round():
    progress = load_progress()
    day = get_today(progress)
    if day["rounds"] >= ROUNDS:
        return False
    queue = pick_words(progress, day)
    if not queue:
        return False

    today = date.today().isoformat()
    learn = []
    for w in queue:
        if w not in progress["boxes"]:
            progress["boxes"][w] = {"box": 0, "due": today}
            day["new"].append(w)
            learn.append(w)

    day["rounds"] += 1
    save_progress(progress)

    session["queue"] = queue
    session["index"] = 0
    session["round"] = day["rounds"]
    session["round_correct"] = 0
    session["round_ok"] = 0
    session["round_cents"] = 0
    session["learn_queue"] = learn
    session["learn_index"] = 0
    session["game_date"] = today
    session.pop("hint", None)
    return True


# ===================== PAGES (HTML) =====================
LAYOUT = """
<!doctype html>
<html lang="el">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#1f6feb">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="WortSchatz">
  <link rel="manifest" href="{{ url_for('manifest') }}">
  <link rel="icon" type="image/svg+xml" href="{{ url_for('icon') }}">
  <link rel="apple-touch-icon" href="{{ url_for('icon') }}">
  <title>WortSchatz</title>
  <script>
    // apply the saved theme before the page is drawn (no flicker)
    try {
      var saved = localStorage.getItem("theme");
      if (saved) document.documentElement.setAttribute("data-theme", saved);
    } catch (e) {}

    function toggleTheme() {
      var root = document.documentElement;
      var current = root.getAttribute("data-theme");
      if (!current) {
        current = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      }
      var next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) {}
    }

    function speak(text) {
      if (!("speechSynthesis" in window)) return;
      speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(text);
      u.lang = "de-DE";
      u.rate = 0.9;
      speechSynthesis.speak(u);
    }
  </script>
  <style>
    :root { --blue:#1f6feb; --gold:#f2b705; --green:#1a7f37; --red:#cf222e;
            --bg:#f4f6fb; --card:#fff; --text:#111; --muted:#6b7280;
            --soft:#eef1f6; --line:#e5e7eb; --border:#d0d7de; --btn:#e5e7eb;
            --okbg:#dafbe1; --badbg:#ffebe9; --warnbg:#fff3c4; --greek:#333;
            --der:#1f6feb; --die:#cf222e; --das:#1a7f37; }
    /* dark: follow the phone, unless she chose light */
    @media (prefers-color-scheme: dark) {
      :root:not([data-theme="light"]) {
              --bg:#0d1117; --card:#161b22; --text:#e6edf3; --muted:#9aa4b2;
              --soft:#21262d; --line:#30363d; --border:#30363d; --btn:#30363d;
              --okbg:#12361f; --badbg:#3d1418; --warnbg:#3d3410; --greek:#c9d1d9;
              --der:#58a6ff; --die:#ff7b72; --das:#3fb950; }
    }
    /* dark: chosen with the button */
    :root[data-theme="dark"] {
              --bg:#0d1117; --card:#161b22; --text:#e6edf3; --muted:#9aa4b2;
              --soft:#21262d; --line:#30363d; --border:#30363d; --btn:#30363d;
              --okbg:#12361f; --badbg:#3d1418; --warnbg:#3d3410; --greek:#c9d1d9;
              --der:#58a6ff; --die:#ff7b72; --das:#3fb950; }
    body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
           background: var(--bg); color: var(--text); max-width: 480px;
           margin: 0 auto; padding: 16px; font-size: 18px; }
    .header { display: flex; justify-content: space-between; align-items: center; }
    h1 { font-size: 26px; margin: 4px 0 12px; }
    h1 a { color: inherit; text-decoration: none; }
    .theme { border: none; background: var(--card); color: var(--text); font-size: 22px;
             width: 44px; height: 44px; border-radius: 50%; cursor: pointer;
             box-shadow: 0 2px 8px rgba(0,0,0,.08); }
    .menu { display: inline-block; color: var(--blue); text-decoration: none;
            font-size: 16px; font-weight: 600; margin-bottom: 6px; }
    .card { background: var(--card); border-radius: 14px; padding: 16px;
            margin: 12px 0; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
    .hero { background: linear-gradient(135deg, var(--blue), #5b9dff);
            color: #fff; text-align: center; }
    .hero .muted { color: #dbe7ff; }
    .label { text-transform: uppercase; font-size: 13px; letter-spacing: 1px; opacity: .85; }
    .big { font-size: 44px; font-weight: 700; }
    .card-title { font-weight: 700; margin-bottom: 10px; }
    .muted { color: var(--muted); font-size: 14px; }
    .grid { display: grid; grid-template-columns: repeat(3, 1fr);
            text-align: center; margin: 14px 0; }
    .num { font-size: 28px; font-weight: 700; }
    .ok { color: var(--green); }
    .bad { color: var(--red); }
    .der { color: var(--der); font-weight: 700; }
    .die { color: var(--die); font-weight: 700; }
    .das { color: var(--das); font-weight: 700; }
    .days { display: flex; gap: 4px; }
    .day { flex: 1; text-align: center; padding: 8px 0; border-radius: 8px;
           background: var(--soft); font-size: 14px; color: var(--muted); }
    .day.played { background: var(--gold); color: #000; font-weight: 700; }
    .day.today { outline: 2px solid var(--blue); }
    .bar { height: 10px; background: var(--soft); border-radius: 5px;
           overflow: hidden; margin: 6px 0 12px; }
    .bar div { height: 100%; background: var(--green); }
    .bar.blue div { background: var(--blue); }
    .bar.gold div { background: var(--gold); }
    .btn { display: block; width: 100%; box-sizing: border-box; margin: 12px 0;
           padding: 16px; font-size: 20px; font-weight: 700; text-align: center;
           text-decoration: none; border: none; border-radius: 12px;
           background: var(--btn); color: var(--text); cursor: pointer; }
    .btn.primary { background: var(--gold); color: #000; }
    .btn.green { background: var(--green); color: #fff; }
    .btn.choice { background: var(--card); border: 2px solid var(--border);
                  color: var(--text); margin: 8px 0; }
    .btn small { display: block; font-size: 15px; font-weight: 400; margin-top: 4px; }
    input[type=text], input[type=password] {
           font-size: 24px; width: 100%; padding: 14px; box-sizing: border-box;
           border: 2px solid var(--border); border-radius: 12px;
           background: var(--card); color: var(--text); }
    .word { font-size: 34px; font-weight: 700; text-align: center; margin: 8px 0 8px; }
    .greek { font-size: 24px; text-align: center; color: var(--greek); margin-top: 14px; }
    .hint { text-align: center; color: var(--muted); font-size: 14px; margin-bottom: 8px; }
    .hintbox { text-align: center; font-size: 26px; font-weight: 700; letter-spacing: 2px;
               background: var(--warnbg); border-radius: 10px; padding: 8px; margin-bottom: 8px; }
    .hintlink { display: block; text-align: center; color: var(--blue);
                text-decoration: none; font-size: 15px; margin-top: 4px; }
    .tag { display: inline-block; background: var(--warnbg); padding: 4px 12px;
           border-radius: 20px; font-size: 14px; font-weight: 600; }
    .feedback { padding: 12px; border-radius: 10px; font-weight: 600; margin-bottom: 8px;
                display: flex; justify-content: space-between; align-items: center; }
    .feedback.ok { background: var(--okbg); }
    .feedback.bad { background: var(--badbg); }
    .feedback.warn { background: var(--warnbg); }
    .feedback.bonus { background: var(--gold); color: #000; justify-content: center; }
    .speak { border: none; background: transparent; font-size: 26px; cursor: pointer; }
    .top { display: flex; justify-content: space-between; font-size: 15px; color: var(--muted); }
    .row { display: flex; justify-content: space-between; align-items: center;
           padding: 10px 0; border-bottom: 1px solid var(--line); }
    .confetti { position: fixed; top: -40px; z-index: 999; pointer-events: none;
                animation: fall 3s linear forwards; }
    @keyframes fall { to { transform: translateY(110vh) rotate(360deg); } }
  </style>
</head>
<body>
  <div class="header">
    <h1><a href="{{ url_for('home') }}">WortSchatz 💰</a></h1>
    <button class="theme" type="button" onclick="toggleTheme()" title="Φωτεινό / σκούρο">🌓</button>
  </div>
  {{ body|safe }}
</body>
</html>
"""

LOGIN = """
<div class="card" style="text-align:center">
  <div class="card-title">🔒 Βάλε το PIN</div>
  {% if error %}<div class="feedback bad">{{ error }}</div>{% endif %}
  <form method="post">
    <input type="password" name="pin" inputmode="numeric" autofocus autocomplete="off">
    <button class="btn primary" type="submit">Είσοδος</button>
  </form>
</div>
"""

MENU_LINK = """
<a class="menu" href="{{ url_for('home') }}">← Μενού</a>
"""

COLORS_HELP = """
<div class="muted" style="text-align:center">
  <span class="der">der</span> αρσενικό ·
  <span class="die">die</span> θηλυκό / πληθυντικός ·
  <span class="das">das</span> ουδέτερο
</div>
"""

FEEDBACK = """
{% if bonus_msg %}
  <div class="feedback bonus"><span>🎁 {{ bonus_msg }}</span></div>
{% endif %}
{% if feedback %}
  <div class="feedback {{ 'warn' if feedback.kind in ['article', 'almost'] else 'ok' }}">
    <span>
      {% if feedback.kind == 'ok' %}✓ Σωστό! {{ feedback.word|art }} · +{{ feedback.cents }} cent
      {% elif feedback.kind == 'article' %}🟡 Σωστή λέξη, λάθος άρθρο! {{ feedback.word|art }} · +{{ feedback.cents }} cent
      {% elif feedback.kind == 'almost' %}🟡 Σχεδόν! Σωστό: {{ feedback.word|art }} · +{{ feedback.cents }} cent
      {% else %}👍 Τώρα το ξέρεις: {{ feedback.word|art }}{% endif %}
    </span>
    <button type="button" class="speak" data-w="{{ feedback.word }}"
            onclick="speak(this.dataset.w)">🔊</button>
  </div>
{% endif %}
"""

CONFETTI = """
<script>
  (function () {
    var items = ["🎉", "🪙", "⭐", "💰", "🎊"];
    for (var i = 0; i < 60; i++) {
      var s = document.createElement("span");
      s.className = "confetti";
      s.textContent = items[i % items.length];
      s.style.left = (Math.random() * 100) + "vw";
      s.style.fontSize = (16 + Math.random() * 18) + "px";
      s.style.animationDelay = (Math.random() * 1.5) + "s";
      document.body.appendChild(s);
      setTimeout(function (el) { el.remove(); }, 5000, s);
    }
  })();
</script>
"""

LEARN = MENU_LINK + """
<div class="card" style="text-align:center">
  <span class="tag">📖 Καινούργια λέξη {{ number }}/{{ total }}</span>
  <div class="greek">{{ greek }}</div>
  <div class="word">{{ word|art }}</div>
  <button class="btn" type="button" data-w="{{ word }}" onclick="speak(this.dataset.w)">🔊 Άκου</button>
  <a class="btn primary" href="{{ url_for('learned') }}">Την είδα ✓</a>
</div>
""" + COLORS_HELP

QUESTION = MENU_LINK + FEEDBACK + """
<div class="card">
  <div class="top">
    <span>Γύρος {{ round }}/{{ rounds }} · Λέξη {{ number }}/{{ total_words }}</span>
    <span>💰 {{ "%.2f"|format(coins / 100) }} €</span>
  </div>
  <div class="bar blue"><div style="width: {{ (number - 1) * 100 // total_words }}%"></div></div>
  <div class="word">{{ greek }}</div>

  {% if mode == 'choice' %}
    <div class="hint">🔘 Διάλεξε τη σωστή λέξη · {{ cents_choice }} cent</div>
    <form method="post" action="{{ url_for('answer') }}">
      {% for o in options %}
        <button class="btn choice" type="submit" name="answer" value="{{ o }}">{{ o|art }}</button>
      {% endfor %}
    </form>
  {% else %}
    {% if hint_text %}
      <div class="hintbox">💡 {{ hint_text }}</div>
      <div class="hint">⌨️ Γράψε τη λέξη με το άρθρο · {{ cents_half }} cent (με βοήθεια)</div>
    {% else %}
      <div class="hint">⌨️ Γράψε τη λέξη με το άρθρο · {{ cents_type }} cent</div>
    {% endif %}
    <form method="post" action="{{ url_for('answer') }}">
      <input type="text" name="answer" placeholder="στα γερμανικά..." autofocus
             autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false">
      <button class="btn primary" type="submit">Έλεγχος</button>
    </form>
    {% if not hint_text %}
      <a class="hintlink" href="{{ url_for('hint') }}">💡 Βοήθεια (η λέξη πιάνει {{ cents_half }} cent)</a>
    {% endif %}
  {% endif %}
</div>
"""

RETYPE = MENU_LINK + FEEDBACK + """
<div class="card" style="text-align:center">
  <div class="feedback bad"><span>✗ Λάθος. Η σωστή λέξη είναι:</span></div>
  <div class="greek">{{ greek }}</div>
  <div class="word">{{ word|art }}</div>
  <button class="btn" type="button" data-w="{{ word }}" onclick="speak(this.dataset.w)">🔊 Άκου</button>
  {% if error %}
    <div class="feedback bad"><span>Δεν είναι ακριβώς ίδιο, ξαναδοκίμασε 🙂</span></div>
  {% endif %}
  <form method="post" action="{{ url_for('retype') }}">
    <div class="hint" style="margin-top:12px">✍️ Γράψ' το μία φορά για να συνεχίσεις</div>
    <input type="text" name="answer" autofocus
           autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false">
    <button class="btn primary" type="submit">Συνέχεια</button>
  </form>
</div>
"""

ROUND_END = MENU_LINK + FEEDBACK + """
<div class="card" style="text-align:center">
  <div class="label">Τέλος γύρου {{ round }}/{{ rounds }}</div>
  {% if perfect %}<div style="font-size:22px; margin-top:6px">🏆 Τέλειο! Όλες σωστές!</div>{% endif %}
  <div class="big">{{ round_correct }}/{{ total_words }}</div>
  <div class="muted">+{{ "%.2f"|format(round_cents / 100) }} € σε αυτόν τον γύρο</div>
  <div class="muted">💰 Σε αυτό το παιχνίδι: {{ "%.2f"|format(coins / 100) }} €</div>
</div>
{% if round < rounds %}
  <a class="btn primary" href="{{ url_for('next_round') }}">Επόμενος γύρος ➜</a>
{% else %}
  <a class="btn primary" href="{{ url_for('finish') }}">Τέλος 🎉</a>
{% endif %}
"""

FINISH = """
<div class="card hero">
  <div class="label">Μπράβο! 🎉</div>
  <div class="big">+{{ "%.2f"|format(cents / 100) }} €</div>
  <div class="muted">{{ total }} σωστές σε αυτό το παιχνίδι</div>
</div>
<div class="card">
  <div>💶 Σύνολο σήμερα: <b>{{ "%.2f"|format(day.cents / 100) }} €</b></div>
  <div class="muted">Γύροι σήμερα: {{ day.rounds }}/{{ rounds }}</div>
</div>
<a class="btn primary" href="{{ url_for('home') }}">Αρχική</a>
"""

MISTAKES = MENU_LINK + """
<div class="card">
  <div class="card-title">📖 Ημερολόγιο λαθών</div>
  {% if items %}
    <div class="muted">Οι λέξεις που σε δυσκολεύουν, με πρώτες τις πιο δύσκολες.</div>
    {% for it in items %}
      <div class="row">
        <div>
          <div>{{ it.word|art }}</div>
          <div class="muted">{{ it.greek }} · {{ it.count }}× λάθος</div>
        </div>
        <button type="button" class="speak" data-w="{{ it.word }}"
                onclick="speak(this.dataset.w)">🔊</button>
      </div>
    {% endfor %}
  {% else %}
    <div class="muted">Κανένα λάθος ακόμα! 🎉</div>
  {% endif %}
</div>
"""

HOME = """
<div class="card hero">
  <div class="label">Σήμερα</div>
  <div class="big">{{ "%.2f"|format(day.cents / 100) }} €</div>
  <div class="muted">{{ day.correct }} σωστές · Γύροι {{ day.rounds }}/{{ rounds }}</div>
  {% if streak > 0 %}<div style="margin-top:6px">🔥 {{ streak }} {{ 'μέρα' if streak == 1 else 'μέρες' }} στη σειρά</div>{% endif %}
</div>

{% if game %}
  <a class="btn primary" href="{{ url_for('question') }}">
    ▶ Συνέχισε από εκεί που έμεινες
    <small>Γύρος {{ game.round }}/{{ rounds }} · {{ game.text }}</small>
  </a>
{% elif rounds_left > 0 and available %}
  <a class="btn primary" href="{{ url_for('start') }}">
    {% if day.rounds == 0 %}▶ Ξεκίνα παιχνίδι{% else %}▶ Παίξε ξανά ({{ rounds_left }} γύροι ακόμα){% endif %}
  </a>
{% elif rounds_left > 0 %}
  <div class="card" style="text-align:center">
    🎉 Για σήμερα τα έκανες όλα!<br>Αύριο έρχονται καινούργιες λέξεις 🌙
  </div>
{% else %}
  <div class="card" style="text-align:center">
    ✅ Τελείωσες τους {{ rounds }} γύρους για σήμερα!<br>Τα λέμε αύριο 🌙
  </div>
{% endif %}

<div class="card">
  <div class="card-title">🎯 Στόχος εβδομάδας</div>
  {% if goal_done %}
    <div>✅ Τον πέτυχες! Μπόνους +{{ "%.2f"|format(goal_bonus / 100) }} €</div>
  {% else %}
    <div class="muted">{{ this_week.correct }}/{{ goal }} σωστές → μπόνους +{{ "%.2f"|format(goal_bonus / 100) }} €</div>
    <div class="bar gold"><div style="width: {{ [this_week.correct * 100 // goal, 100]|min }}%"></div></div>
  {% endif %}
  <div class="muted">🔥 Κάθε {{ streak_days }} μέρες στη σειρά: +{{ "%.2f"|format(streak_bonus / 100) }} €</div>
</div>

<div class="card">
  <div class="card-title">📈 Πίστα 1</div>
  <div class="muted">Έχεις δει: {{ seen }}/{{ word_count }} λέξεις</div>
  <div class="bar blue"><div style="width: {{ seen * 100 // word_count }}%"></div></div>
  <div class="muted">Μαθεμένες: {{ learned }}/{{ word_count }}</div>
  <div class="bar gold"><div style="width: {{ learned * 100 // word_count }}%"></div></div>
  <div class="muted">⭐ Κατακτημένες: {{ mastered }}</div>
  {% if learned == word_count %}
    <div>🎉 Η Πίστα 1 ολοκληρώθηκε! Η Πίστα 2 έρχεται σύντομα.</div>
  {% endif %}
</div>

<a class="btn" href="{{ url_for('mistakes') }}">📖 Ημερολόγιο λαθών{% if mistakes_count %} ({{ mistakes_count }}){% endif %}</a>

<div class="card">
  <div class="card-title">💶 Προς πληρωμή</div>
  <div class="big" style="text-align:center">{{ "%.2f"|format(to_pay / 100) }} €</div>
  {% if to_pay > 0 %}
    <form method="post" action="{{ url_for('paid') }}"
          onsubmit="return confirm('Σίγουρα πληρώθηκε {{ "%.2f"|format(to_pay / 100) }} €;')">
      <button class="btn green" type="submit">Πληρώθηκε ✓</button>
    </form>
  {% endif %}
  {% for p in payments[-3:]|reverse %}
    <div class="muted">✓ {{ p.date }}: {{ "%.2f"|format(p.cents / 100) }} €</div>
  {% endfor %}
</div>

<div class="card">
  <div class="card-title">📅 Αυτή η εβδομάδα</div>
  <div class="days">
    {% for d in this_week.days %}
      <div class="day {% if d.played %}played{% endif %} {% if d.today %}today{% endif %}">{{ d.label }}</div>
    {% endfor %}
  </div>
  <div class="grid">
    <div><div class="num ok">{{ this_week.correct }}</div><div class="muted">Σωστές</div></div>
    <div><div class="num bad">{{ this_week.wrong }}</div><div class="muted">Λάθη</div></div>
    <div><div class="num">{{ this_week.days_played }}/7</div><div class="muted">Μέρες</div></div>
  </div>
  <div class="muted">Ακρίβεια {{ this_week.accuracy }}%</div>
  <div class="bar"><div style="width: {{ this_week.accuracy }}%"></div></div>
  <div>💶 Κέρδη εβδομάδας: <b>{{ "%.2f"|format(this_week.cents / 100) }} €</b></div>
</div>

{% if last_week.days_played > 0 %}
<div class="card">
  <div class="card-title">📊 Προηγούμενη εβδομάδα</div>
  <div class="grid">
    <div><div class="num ok">{{ last_week.correct }}</div><div class="muted">Σωστές</div></div>
    <div><div class="num bad">{{ last_week.wrong }}</div><div class="muted">Λάθη</div></div>
    <div><div class="num">{{ last_week.accuracy }}%</div><div class="muted">Ακρίβεια</div></div>
  </div>
  <div>💶 Κέρδη: <b>{{ "%.2f"|format(last_week.cents / 100) }} €</b>
       ({{ last_week.days_played }}/7 μέρες)</div>
</div>
{% endif %}

<div class="card">
  <div class="card-title">🏆 Συνολικά</div>
  <div>Κέρδισε: <b>{{ "%.2f"|format(earned / 100) }} €</b> · Πληρώθηκε: <b>{{ "%.2f"|format(paid_total / 100) }} €</b></div>
</div>
"""

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="96" fill="#1f6feb"/>
  <circle cx="256" cy="256" r="180" fill="#f2b705" stroke="#b8860b" stroke-width="18"/>
  <text x="256" y="335" font-family="Arial, Helvetica, sans-serif" font-size="230"
        font-weight="700" text-anchor="middle" fill="#1f6feb">W</text>
</svg>"""


def page(content, **values):
    body = render_template_string(content, **values)
    return render_template_string(LAYOUT, body=body)


# ===================== ROUTES =====================
@app.before_request
def require_pin():
    if request.endpoint in ("login", "static", "manifest", "icon"):
        return None
    if not session.get("auth"):
        return redirect(url_for("login"))


@app.route("/manifest.webmanifest")
def manifest():
    data = {
        "name": "WortSchatz",
        "short_name": "WortSchatz",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f4f6fb",
        "theme_color": "#1f6feb",
        "icons": [{"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml"}],
    }
    return Response(json.dumps(data), mimetype="application/manifest+json")


@app.route("/icon.svg")
def icon():
    return Response(ICON_SVG, mimetype="image/svg+xml")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("pin", "") == PIN:
            session.permanent = True
            session["auth"] = True
            return redirect(url_for("home"))
        error = "Λάθος PIN"
    return page(LOGIN, error=error)


@app.route("/")
def home():
    progress = load_progress()
    day = get_today(progress)
    seen, learned_count, mastered = level_stats(progress)
    earned, paid_total, to_pay = money(progress)
    rounds_left = max(0, ROUNDS - day["rounds"])

    game = None
    available = True
    if game_in_progress():
        total_words = len(session["queue"])
        index = session["index"]
        if learning_pending():
            text = f"κάρτα {session['learn_index'] + 1}/{len(session['learn_queue'])}"
        elif index >= total_words:
            text = "τέλος γύρου"
        else:
            text = f"λέξη {index + 1}/{total_words}"
        game = {"round": session["round"], "text": text}
    elif rounds_left > 0:
        available = len(pick_words(progress, day)) > 0

    return page(HOME,
                day=day,
                game=game,
                available=available,
                rounds=ROUNDS,
                rounds_left=rounds_left,
                streak=current_streak(progress),
                streak_days=STREAK_DAYS,
                streak_bonus=STREAK_BONUS,
                goal=WEEKLY_GOAL,
                goal_bonus=WEEKLY_GOAL_BONUS,
                goal_done=week_label(date.today()) in progress["goals_paid"],
                seen=seen,
                learned=learned_count,
                mastered=mastered,
                word_count=len(words),
                mistakes_count=len(progress["mistakes"]),
                earned=earned,
                paid_total=paid_total,
                to_pay=to_pay,
                payments=progress["payments"],
                this_week=week_stats(progress, 0),
                last_week=week_stats(progress, 1))


@app.route("/start")
def start():
    if game_in_progress():
        return redirect(url_for("question"))
    clear_game()
    session["game_correct"] = 0
    session["game_cents"] = 0
    if not start_round():
        clear_game()
        return redirect(url_for("home"))
    return redirect(url_for("question"))


@app.route("/question")
def question():
    if not game_in_progress():
        return redirect(url_for("home"))

    # 1) new words: learning cards first
    if learning_pending():
        w = session["learn_queue"][session["learn_index"]]
        return page(LEARN, word=w, greek=words[w],
                    number=session["learn_index"] + 1,
                    total=len(session["learn_queue"]))

    bonus_msg = session.pop("bonus_msg", None)

    # 2) after a wrong answer: retype the correct word
    if session.get("retype"):
        w = session["retype"]
        return page(RETYPE, word=w, greek=words[w], feedback=None,
                    bonus_msg=bonus_msg, error=request.args.get("e") == "1")

    feedback = session.pop("feedback", None)
    coins = session.get("game_cents", 0)
    total_words = len(session["queue"])

    # 3) end of round
    if session["index"] >= total_words:
        perfect = total_words > 0 and session.get("round_ok", 0) == total_words
        html = page(ROUND_END, feedback=feedback, bonus_msg=bonus_msg,
                    round=session["round"], rounds=ROUNDS, perfect=perfect,
                    round_correct=session.get("round_correct", 0),
                    round_cents=session.get("round_cents", 0),
                    total_words=total_words, coins=coins)
        if perfect:
            html = html.replace("</body>", CONFETTI + "</body>")
        return html

    # 4) the question: choice for new/weak words, typing for the rest
    key = session["queue"][session["index"]]
    mode = "choice" if word_box(load_progress(), key) == 0 else "type"
    options = make_options(key) if mode == "choice" else []
    hint_text = make_hint(key) if session.get("hint") == session["index"] else None
    return page(QUESTION, feedback=feedback, bonus_msg=bonus_msg, greek=words[key],
                mode=mode, options=options, hint_text=hint_text,
                cents_choice=CENTS_CHOICE, cents_type=CENTS_TYPE, cents_half=CENTS_HALF,
                number=session["index"] + 1, total_words=total_words,
                round=session["round"], rounds=ROUNDS, coins=coins)


@app.route("/learned")
def learned():
    if game_in_progress() and learning_pending():
        session["learn_index"] = session.get("learn_index", 0) + 1
    return redirect(url_for("question"))


@app.route("/hint")
def hint():
    if (game_in_progress() and not learning_pending() and not session.get("retype")
            and session["index"] < len(session["queue"])):
        session["hint"] = session["index"]
    return redirect(url_for("question"))


@app.route("/answer", methods=["POST"])
def answer():
    if (not game_in_progress() or learning_pending() or session.get("retype")
            or session["index"] >= len(session["queue"])):
        return redirect(url_for("question"))

    key = session["queue"][session["index"]]
    progress = load_progress()
    day = get_today(progress)
    user_answer = request.form.get("answer", "")

    mode = "choice" if word_box(progress, key) == 0 else "type"
    hint_used = session.pop("hint", None) == session["index"]

    if mode == "choice":
        result = "ok" if check_answer(user_answer, key) else "wrong"
    else:
        result = grade(user_answer, key)

    if result == "ok":
        if mode == "choice":
            cents = CENTS_CHOICE
        elif hint_used:
            cents = CENTS_HALF
        else:
            cents = CENTS_TYPE
        new_box = update_box(progress, key, True)
        if INTERVALS[new_box] > 0:          # next review is on another day
            day["done"].append(key)
        session["round_ok"] = session.get("round_ok", 0) + 1

    elif result in ("article", "almost"):
        cents = CENTS_HALF
        repeat_today(progress, key)
        progress["mistakes"][key] = progress["mistakes"].get(key, 0) + 1

    else:
        cents = 0
        update_box(progress, key, False)
        progress["mistakes"][key] = progress["mistakes"].get(key, 0) + 1

    if result == "wrong":
        day["wrong"] += 1
        session["retype"] = key
    else:
        day["correct"] += 1
        day["cents"] += cents
        session["round_correct"] = session.get("round_correct", 0) + 1
        session["round_cents"] = session.get("round_cents", 0) + cents
        session["game_correct"] = session.get("game_correct", 0) + 1
        session["game_cents"] = session.get("game_cents", 0) + cents
        session["feedback"] = {"kind": result, "word": key, "cents": cents}

    bonus = check_bonuses(progress, day)
    if bonus:
        session["bonus_msg"] = bonus

    save_progress(progress)
    session["index"] += 1
    return redirect(url_for("question"))


@app.route("/retype", methods=["POST"])
def retype():
    if not game_in_progress() or not session.get("retype"):
        return redirect(url_for("question"))
    w = session["retype"]
    if check_answer(request.form.get("answer", ""), w):
        session.pop("retype", None)
        session["feedback"] = {"kind": "retyped", "word": w}
        return redirect(url_for("question"))
    return redirect(url_for("question", e=1))


@app.route("/next_round")
def next_round():
    if not game_in_progress():
        return redirect(url_for("home"))
    if (learning_pending() or session.get("retype")
            or session["index"] < len(session["queue"])):
        return redirect(url_for("question"))
    if not start_round():
        return redirect(url_for("finish"))
    return redirect(url_for("question"))


@app.route("/finish")
def finish():
    if not game_in_progress():
        return redirect(url_for("home"))

    total = session.get("game_correct", 0)
    cents = session.get("game_cents", 0)
    day = get_today(load_progress())
    clear_game()
    return page(FINISH, total=total, cents=cents, day=day, rounds=ROUNDS)


@app.route("/mistakes")
def mistakes():
    progress = load_progress()
    items = []
    for w, count in progress["mistakes"].items():
        if w in words:
            items.append({"word": w, "greek": words[w], "count": count})
    items.sort(key=lambda it: it["count"], reverse=True)
    return page(MISTAKES, items=items)


@app.route("/paid", methods=["POST"])
def paid():
    progress = load_progress()
    _, _, to_pay = money(progress)
    if to_pay > 0:
        progress["payments"].append({"date": date.today().isoformat(), "cents": to_pay})
        save_progress(progress)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)