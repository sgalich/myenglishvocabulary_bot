import random

from PyDictionary import PyDictionary
import eng_to_ipa as ipa
from googletrans import Translator
from googletrans.models import Translated
from texts import texts
import utils


dictionary = PyDictionary()
translator = Translator()
users = {}
# user:
# {
# 	chat_id (int): {
#       chat_id: int,
#       lang: en/ru/uk/...
#       username: ''
#       unknown: [
#           {
#               word: 'toddler',
#               get: 2,    # how much did user send this word
#               shown: 14    # how much did bot show this word to a user
#           }, ...
#       ],
#       familiar: [...],
#       known: [...]
# }


# UTILS

# def send_stats(update):
# 	m_m = 0
# 	m_b = 0
# 	m_f = 0
# 	f_m = 0
# 	f_b = 0
# 	f_f = 0
# 	for _, user in users.items():
# 		if 'real' in update.message['text'] and 'test' in str(user['chat_id']):
# 			continue
# 		if user['profile']['sex_my'] == 'male':
# 			if user['profile']['sex_req'] == 'male':
# 				m_m += 1
# 			elif user['profile']['sex_req'] == 'both':
# 				m_b += 1
# 			elif user['profile']['sex_req'] == 'female':
# 				m_f += 1
# 		elif user['profile']['sex_my'] == 'female':
# 			if user['profile']['sex_req'] == 'male':
# 				f_m += 1
# 			elif user['profile']['sex_req'] == 'both':
# 				f_b += 1
# 			elif user['profile']['sex_req'] == 'female':
# 				f_f += 1
# 	males_count = m_f + m_m + m_b
# 	females_count = f_m + f_f + f_b
# 	males_percentage = '{:.1f}'.format(males_count / (males_count + females_count) * 100)
# 	females_percentage = '{:.1f}'.format(females_count / (males_count + females_count) * 100)
# 	stats_mes = f"""
# Males: {males_count} ({males_percentage}%)
# \t\t\tlooking for
# \t\t\twomen: {m_f}
# \t\t\tmen: {m_m}
# \t\t\tboth: {m_b}
#
# Females: {females_count} ({females_percentage}%)
# \t\t\tlooking for
# \t\t\tmen: {f_m}
# \t\t\twomen: {f_f}
# \t\t\tboth: {f_b}
#
# Users total: {males_count + females_count}
# """
# 	update.message.reply_text(stats_mes, parse_mode='Markdown')




def save_user(message):
	"""Save user's data."""

	def create_new_user():
		users[chat_id] = dict(
			chat_id=chat_id,
			lang=message.from_user['language_code'],
			username=message['chat']['username'],
			unknown=[],
			familiar=[],
			known=[]
		)
		utils.save_users(users)

	chat_id = message['chat']['id']
	if not users.get(chat_id):
		create_new_user()


# HANDLERS

def start(update, context):
	"""The first message handler."""
	save_user(update.message)
	update.message.reply_text(texts['start'])
	update.message.reply_text(
		texts['help'],
		reply_markup=utils.my_keyboard()
	)
	user = users[update.message['chat']['id']]
	utils.log(f'A new user: {user}')


def message(update, context):
	chat_id = update.message['chat']['id']
	try:
		_ = users[chat_id]
	except KeyError:
		start(update, context)
		return None
	message_text = update.message['text']

	utils.log(f'MESSAGE from: {chat_id}, text: {message_text}')

	if message_text == texts['b_all_known']:
		send_list(update, 'known')
	elif message_text == texts['b_all_familiar']:
		send_list(update, 'familiar')
	elif message_text == texts['b_all_unknown']:
		send_list(update, 'unknown')
	elif message_text == texts['b_known']:
		send_word(context, chat_id, 'known')
	elif message_text == texts['b_familiar']:
		send_word(context, chat_id, 'familiar')
	elif message_text == texts['b_unknown']:
		send_word(context, chat_id, 'unknown')
	else:
		for word in message_text.split('\n'):
			save_word(update, word)
		# add this word to unknown, remove this word from other baskets


def send_list(update, basket):
	chat_id = update.message['chat']['id']
	basket_list = users[chat_id][basket]
	basket_words = [x['word'] for x in basket_list]
	basket_words = '\n'.join(sorted(basket_words))
	basket_words += texts['total'].format(len(basket_list))
	update.message.reply_text(
		basket_words,
		reply_markup=utils.my_keyboard()
	)


def send_word(context, chat_id, basket):
	basket_list = users[chat_id][basket]
	if basket_list:
		word = random.choice(basket_list)    # TODO: Show words w/ highest 'get' at first
		word['shown'] += 1
		utils.save_users(users)
		reply_text = word['word']
		if basket == 'unknown':
			reply_text = get_definition(reply_text)
		context.bot.send_message(
			chat_id=chat_id,
			text=reply_text,
			reply_markup=utils.inline_keyboard(),
		)
	else:
		context.bot.send_message(
			chat_id=chat_id,
			text=texts['nothing_to_show']
		)


def get_definition(word):
	f_word = word.split()[0]    # Leave only 1st word
	definition = word
	# 1. Phonetic transcription
	phonetic_transcription = ipa.convert(f_word)
	definition += f'\n[ {phonetic_transcription} ]'
	# 2. Meaning
	meaning = dictionary.meaning(f_word)
	if meaning:
		meaning_str = ""
		for part_of_speech, def_list in meaning.items():
			meaning_str += f'\n\n{part_of_speech}'
			for dfntn in def_list:
				meaning_str += f'\n\t– {dfntn}'
		definition += meaning_str
	# 3. Synonyms
	synonyms = dictionary.synonym(f_word)
	if synonyms:
		synonyms_str = ', '.join(synonyms)
		synonyms_str = f'\n\nSynonyms: {synonyms_str}'
		definition += synonyms_str
	# 4. Translation
	translation = translator.translate(word, src='en', dest='ru').text    # TODO: Add different languages
	if translation != word:
		definition += f'\n\n{translation}'
	return definition


def save_word(update, message_text):
	message_text = message_text.strip().lower()
	chat_id = update.message['chat']['id']
	user = users[chat_id]
	new_word = None
	# Try to find this word in baskets
	for i in range(len(user['unknown'])):
		word = user['unknown'][i]
		if word['word'] == message_text:
			new_word = word
			new_word['get'] += 1
			user['unknown'].pop(i)    # Remove this word from the basket
			break
	if not new_word:
		for i in range(len(user['familiar'])):
			word = user['familiar'][i]
			if word['word'] == message_text:
				new_word = word
				new_word['get'] += 1
				user['familiar'].pop(i)  # Remove this word from the basket
				break
	if not new_word:
		for i in range(len(user['known'])):
			word = user['known'][i]
			if word['word'] == message_text:
				new_word = word
				new_word['get'] += 1
				user['known'].pop(i)  # Remove this word from the basket
				break
	if not new_word:
		new_word = dict(
			word=message_text,
			get=1,
			shown=0
		)
	users[chat_id]['unknown'].append(new_word)
	utils.save_users(users)
	update.message.reply_text(
		get_definition(message_text),
		reply_markup=utils.my_keyboard()
	)


def inline_callback(update, context):
	chat_id = update.callback_query.from_user.id
	callback = update.callback_query.data
	word = update.callback_query.message.text
	word = word.split('\n')[0]    # Extraction a word from definition
	if callback == 'delete':
		delete_word(context, chat_id, word)
	elif callback == 'down':
		downgrade_word(context, chat_id, word)
	elif callback == 'up':
		upgrade_word(context, chat_id, word)
	update.callback_query.edit_message_text(text=update.callback_query.message.text)


def delete_word(context, chat_id, word_to_delete):
	user = users[chat_id]
	# Try to find this word in baskets
	for i in range(len(user['unknown'])):
		if user['unknown'][i]['word'] == word_to_delete:
			user['unknown'].pop(i)    # Remove this word from the basket
			send_word(context, chat_id, 'unknown')    # Send a next word
			word_to_delete = None
			break
	if word_to_delete:
		for i in range(len(user['familiar'])):
			if user['familiar'][i]['word'] == word_to_delete:
				user['familiar'].pop(i)    # Remove this word from the basket
				send_word(context, chat_id, 'familiar')    # Send a next word
				word_to_delete = None
				break
	if word_to_delete:
		for i in range(len(user['known'])):
			if user['known'][i]['word'] == word_to_delete:
				user['known'].pop(i)  # Remove this word from the basket
				send_word(context, chat_id, 'known')    # Send a next word
				break
	utils.save_users(users)


def downgrade_word(context, chat_id, word_to_downgrade):
	user = users[chat_id]
	# Try to find this word in baskets
	for i in range(len(user['known'])):
		if user['known'][i]['word'] == word_to_downgrade:
			word = user['known'].pop(i)  # Remove this word from the basket
			user['familiar'].append(word)
			send_word(context, chat_id, 'known')    # Send a next word
			word_to_downgrade = None
			break
	if word_to_downgrade:
		for i in range(len(user['familiar'])):
			if user['familiar'][i]['word'] == word_to_downgrade:
				word = user['familiar'].pop(i)  # Remove this word from the basket
				user['unknown'].append(word)
				send_word(context, chat_id, 'familiar')    # Send a next word
				word_to_downgrade = None
				break
	if word_to_downgrade:
		send_word(context, chat_id, 'unknown')    # Send a next word
	utils.save_users(users)


def upgrade_word(context, chat_id, word_to_upgrade):
	user = users[chat_id]
	# Try to find this word in baskets
	for i in range(len(user['unknown'])):
		if user['unknown'][i]['word'] == word_to_upgrade:
			word = user['unknown'].pop(i)    # Remove this word from the basket
			user['familiar'].append(word)
			send_word(context, chat_id, 'unknown')    # Send a next word
			word_to_upgrade = None
			break
	if word_to_upgrade:
		for i in range(len(user['familiar'])):
			if user['familiar'][i]['word'] == word_to_upgrade:
				word = user['familiar'].pop(i)  # Remove this word from the basket
				user['known'].append(word)
				send_word(context, chat_id, 'familiar')    # Send a next word
				word_to_upgrade = None
				break
	if word_to_upgrade:
		send_word(context, chat_id, 'known')    # Send a next word
	utils.save_users(users)


def stop(update, context):
	"""Stop handler."""
	chat_id = update.message['chat']['id']
	del users[chat_id]
	utils.save_users(users)
