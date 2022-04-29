HELP = """I have these commands:
My commands:
/start - start me;
/help - see my commands;
/stats - see the statistic;
/stop - stop me.

You can control each card with these buttons:
🚫 - delete card
👍 - show card less often
✍ - edit card

On the front side of each card you will see this info: 
📥 - how many times did you add this word
👁️ - how many times have you seen this card before
"""
START_1 = f"""Привет! Я простой бот для изучения английских слов с помощью флэш карт.

Перед тем как мы начнем пожалуйста выбери свой язык. Я буду переводить английские слова, которые ты мне пришлешь, на этот язык 👇
"""
START_2 = f"""Okay, you are redy to go!

Just send me a word you want tso add and I\'ll add it in your vocabulary. Then just learn your words by viewing random cards.

{HELP}

Hope you will enjoy! And feel free to share your feedback with my creator, @sg715.
"""
STATS = 'You have {} cards.'
B_NEXT = '🎲 next random card ▶️'
B_FLIP = '↪️          FLIP OVER          ↩️'
B_REMOVE = '🚫'
B_UP = '👍'
B_EDIT = '✍️'
BUTTON_ENGLISH = '🇺🇸 Без перевода'
BUTTON_RUSSIAN = '🇷🇺 Русский'
BUTTON_ARABIC = '🇦🇪 Арабский'
BUTTON_MALAY = '🇲🇾 Малайский'
EDIT_PRONUNCIATION = 'Send a new pronunciation or keep this 👇'
EDIT_DEFINITION = 'Send a new definition or keep this 👇'
EDIT_SYNONYMS = 'Send new synonyms or keep these 👇'
EDIT_KEEP_FIELD = 'Keep this 👆'
EDIT_FINISHED = 'Done! Here is your new card:'
EMPTY_VOCABULARY = 'Your vocabulary is empty yet. Send me your first word you want to memorize.'
EMPTY_MESSAGE = '-'
# TODO: Add example sentences on the front side ????
CARD_FRONT = """{title}
[ {pronunciation} ]

📥 {added:,}   👁 {shown:,}
"""
CARD_BACK = """{title}
[ {pronunciation} ]

{definition}

📖: {synonyms}
"""
BYE = """Sorry to see you go! 😭😭😭
When you change your mind just send me /start.

Have a Good Luck! 👋
"""
