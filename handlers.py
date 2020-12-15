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
#       cards: {
#           'toddler': {
#               added: 2,    # how much did user send this word
#               shown: 14,    # how much did bot show this word to a user
#               basket: 'unknown'/'familiar'/'known',
#               definition: '...'
#           },
#           'spite': {},
#           ...
#       }
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
			last_id=0,
			vocabulary={}
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
	# Check is it a new user
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
		choose_random_card(context, chat_id, 'known')
	elif message_text == texts['b_familiar']:
		choose_random_card(context, chat_id, 'familiar')
	elif message_text == texts['b_unknown']:
		choose_random_card(context, chat_id, 'unknown')
	else:
		for word in message_text.split('\n'):
			save_word(context, chat_id, word)
		# add this word to unknown, remove this word from other baskets


def send_list(update, basket_name: str):
	user = users[update.message['chat']['id']]
	basket_words = [word for word, card in user['cards'].items() if card['basket'] == basket_name]
	basket_words = '\n'.join(sorted(basket_words))
	basket_size = len(basket_words)
	basket_words += texts['total'].format(f'{basket_size:,}')
	update.message.reply_text(
		basket_words,
		reply_markup=utils.my_keyboard()
	)


def choose_random_card(context, chat_id, basket_name: str):
	cards = users[chat_id]['cards']
	# Create a list so that there would be 2 words w/ 'added'=2, 3 w/ 'added'=3 and so on
	weightened_basket_list = []
	for word, card in cards.items():
		if card['basket'] != basket_name:
			continue
		for _ in range(card['added']):    # add as much the same cards as much a user was looking for this word
			weightened_basket_list.append(word)
	# If there is empty
	if not weightened_basket_list:
		context.bot.send_message(
			chat_id=chat_id,
			text=texts['nothing_to_show']
		)
		return None
	chosen_word = random.choice(weightened_basket_list)
	cards[chosen_word]['shown'] += 1
	utils.save_users(users)
	send_card(context, chat_id, chosen_word)


def send_card(context, chat_id, word):
	card = users[chat_id]['cards'][word]

	###############
	# Temporary ###
	if not card.get('definition'):
		card['definition'] = get_definition(word)
		utils.save_users(users)
	###############


	context.bot.send_message(
		chat_id=chat_id,
		text=generate_word_side(word, card),
		reply_markup=utils.inline_keyboard(),
	)


def generate_word_side(word, card):
	# Append get & shown notation
	added = card['added']
	shown = card['shown']
	reply_text = word + '\n\n' + texts['get'].format(f'{added:,}') + ' ' + texts['shown'].format(f'{shown:,}')
	return reply_text


def get_definition(word):
	f_word = word.split()[0]    # Leave only 1st word
	definition = f'{word}'
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
	translation = translator.translate(word, src='en', dest='ru').text    # TODO: Add different languages ???
	if translation != word:
		definition += f'\n\n{translation}'
	return definition


def save_word(context, chat_id, new_word):
	new_word = utils.clear(new_word)
	user = users[chat_id]
	cards = user['cards']
	new_card = None
	for word in cards.keys():
		if new_word == word:
			new_card = cards[word]
			new_card['added'] += 1
			new_card['basket'] = 'unknown'    # Skip all the user's progress
			break
	if not new_card:
		new_card = dict(
			added=1,
			shown=0,
			basket='unknown',
			definition=get_definition(new_word)
		)
		cards[new_word] = new_card
	utils.save_users(users)
	send_card(context, chat_id, new_word)    # TODO: Send flipped side of the card right here


def inline_callback(update, context):
	chat_id = update.callback_query.from_user.id
	callback = update.callback_query.data
	message_text = update.callback_query.message.text
	word = message_text.split('\n')[0]    # Extraction a word from definition ????????
	if callback == 'flip':
		flip_card(update, chat_id, message_text)
	elif callback == 'delete':
		delete_word(update, chat_id, word)
	elif callback == 'down':
		downgrade_word(context, chat_id, word)
	elif callback == 'up':
		upgrade_word(context, chat_id, word)
	elif callback == 'edit':
		edit_word(context, chat_id, word)
		update.callback_query.edit_message_text(text=update.callback_query.message.text)    # TODO: differentiate for each callback


def flip_card(update, chat_id, message_text):
	word = message_text.split('\n')[0]  # Extraction a word from definition ????????
	second_line = message_text.split('\n')[1]
	side = 'card' if second_line and second_line[0] == '[' else 'word'
	if side == 'card':
		text = generate_word_side(word, users[chat_id]['cards'][word])
	else:
		text = users[chat_id]['cards'][word]['definition']
	update.callback_query.edit_message_text(
		text=text,
		reply_markup=utils.inline_keyboard(),
	)


def delete_word(update, chat_id, word):
	# TODO: try to delete flipped card is word = word and not a definition
	cards = users[chat_id]['cards']
	del cards[word]
	utils.save_users(users)
	update.callback_query.message.delete()


def downgrade_word(context, chat_id, word):
	user = users[chat_id]
	card = user['cards'][word]
	if card['basket'] == 'known':
		card['basket'] = 'familiar'
	elif card['basket'] == 'familiar':
		card['basket'] = 'unknown'
	# choose_random_card(context, chat_id, 'unknown')  # Send a next word
	utils.save_users(users)


def upgrade_word(context, chat_id, word):
	user = users[chat_id]
	card = user['cards'][word]
	if card['basket'] == 'unknown':
		card['basket'] = 'familiar'
	elif card['basket'] == 'familiar':
		card['basket'] = 'known'
	# choose_random_card(context, chat_id, 'unknown')  # Send a next word
	utils.save_users(users)


def edit_word(context, chat_id, card_to_edit):
	pass


def stop(update, context):
	"""Stop handler."""
	chat_id = update.message['chat']['id']
	del users[chat_id]
	utils.save_users(users)
