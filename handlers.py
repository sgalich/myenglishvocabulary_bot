import random

import numpy
from PyDictionary import PyDictionary
import eng_to_ipa
from googletrans import Translator
from googletrans.models import Translated

from texts import texts
import utils

# TODO: Send cards every day if I didn't use it

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
			cards={}
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

	if message_text == texts['b_next']:
		send_random_card(context, chat_id)
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


def send_random_card(context, chat_id):
	"""Chooses a word with these rules:
	as much ADDED as MORE chance
	as much DOWN pressed as MORE chance
	as much SHOWN as LESS chance
	as much UP pressed as LESS chance
	"""

	def send_card(context, chat_id, word):
		card = users[chat_id]['cards'][word]
		DEPRECATED_SEARCH(word, card)
		context.bot.send_message(
			chat_id=chat_id,
			text=generate_front_side(word, card),
			reply_markup=utils.inline_keyboard(),
		)

	cards = users[chat_id]['cards']
	words_list = []
	probabilities = []
	for word, card in cards.items():
		words_list.append(word)
		weight = (card['added'] + 1) * (card['down'] + 1) / (card['shown'] + 1) / (card['up'] + 1)
		probabilities.append(weight)
	probabilities_sum = sum(probabilities)
	probabilities = [x / probabilities_sum for x in probabilities]
	chosen_word = numpy.random.choice(words_list, p=probabilities)
	cards[chosen_word]['shown'] += 1
	utils.save_users(users)
	send_card(context, chat_id, chosen_word)



def DEPRECATED_SEARCH(word, card):
	###############
	# Temporary ###
	if not card.get('definition'):
		card['definition'] = get_definition(word)
	if not card.get('pronunciation'):
		card['pronunciation'] = get_pronunciation(word)
	if not card.get('synonyms'):
		card['synonyms'] = get_synonyms(word)
	if not card.get('translation'):
		card['translation'] = get_translation(word)
	utils.save_users(users)






def generate_front_side(word, card):
	# Append get & shown notation
	added = card['added']
	added = f'{added:,}'
	shown = card['shown']
	shown = f'{shown:,}'
	pronunciation = card['pronunciation']
	front_side = f"""{word}
[ {pronunciation} ]

📥 {added} 👁️ {shown}
"""
	return front_side


def generate_back_side(word, card):
	definition = card['definition']
	synonyms = card['synonyms']
	translation = card['translation']
	back_side = f"""{definition}

📖 {word}: {synonyms}

🗣️ {translation}
"""
	return back_side


def get_definition(word):
	"""Get definition of the word."""
	first_word = word.split()[0]    # Leave only 1st word
	meaning = dictionary.meaning(first_word)
	definition = ""
	if meaning:
		for part_of_speech, def_list in meaning.items():
			definition += f'\n\n{part_of_speech}'
			for dfntn in def_list:
				definition += f'\n\t– {dfntn}'
	return definition


def get_pronunciation(word):
	pronunciation = eng_to_ipa.convert(''.join(word))
	return pronunciation


def get_synonyms(word):
	first_word = word.split()[0]  # Leave only 1st word
	synonyms = dictionary.synonym(first_word)
	synonyms = ', '.join(synonyms) if synonyms else ''
	return synonyms


def get_translation(word):
	translation = translator.translate(word, src='en', dest='ru').text    # TODO: Add different languages ???
	translation = translation if translation != word else ''
	return translation


def save_word(context, chat_id, new_word):
	new_word = utils.clear(new_word)
	user = users[chat_id]
	cards = user['cards']
	new_card = None
	for word in cards.keys():
		if new_word == word:
			new_card = cards[word]
			new_card['added'] += 1
			break
	if not new_card:
		new_card = dict(
			added=1,
			shown=0,
			up=0,
			down=0,
			definition=get_definition(new_word),
			pronunciation=get_pronunciation(new_word),
			synonyms=get_synonyms(new_word),
			translation=get_translation(new_word)
		)
		cards[new_word] = new_card
	DEPRECATED_SEARCH(new_word, new_card)
	utils.save_users(users)
	context.bot.send_message(
		chat_id=chat_id,
		text=new_card['pronunciation'],
		reply_markup=utils.my_keyboard(),
	)
	context.bot.send_message(
		chat_id=chat_id,
		text=generate_back_side(new_word, new_card),
		reply_markup=utils.inline_keyboard(),
	)


def inline_callback(update, context):
	chat_id = update.callback_query.from_user.id
	callback = update.callback_query.data
	message_text = update.callback_query.message.text
	if callback == 'flip':
		flip_card(update, chat_id, message_text)
	else:
		if callback == 'delete':
			delete_word(context, update, chat_id, message_text)
		elif callback == 'down':
			downgrade_word(context, chat_id, message_text)
		elif callback == 'up':
			upgrade_word(context, chat_id, message_text)
		elif callback == 'edit':
			edit_word(context, chat_id, message_text)
		update.callback_query.edit_message_text(
			text=update.callback_query.message.text,
			reply_markup=utils.inline_keyboard(mini=True)
		)


def find_the_word(message_text):
	if '👁️' in message_text:
		word = message_text.split('\n')[0]
	else:
		word = message_text.split('📖 ')[1].split(': ')[0]
	return word


def flip_card(update, chat_id, message_text):
	word = find_the_word(message_text)
	card = users[chat_id]['cards'][word]
	if '👁️' in message_text:
		text = generate_back_side(word, card)
	else:
		text = generate_front_side(word, card)
	update.callback_query.edit_message_text(
		text=text,
		reply_markup=utils.inline_keyboard()    # TODO: Check and save this inline (mini if it was mini)
	)


def delete_word(context, update, chat_id, message_text):
	word = find_the_word(message_text)
	cards = users[chat_id]['cards']
	del cards[word]
	utils.save_users(users)
	update.callback_query.message.delete()
	send_random_card(context, chat_id)


def downgrade_word(context, chat_id, message_text):
	word = find_the_word(message_text)
	users[chat_id]['cards'][word]['down'] += 1
	utils.save_users(users)
	send_random_card(context, chat_id)


def upgrade_word(context, chat_id, message_text):
	word = find_the_word(message_text)
	users[chat_id]['cards'][word]['up'] += 1
	utils.save_users(users)
	send_random_card(context, chat_id)


# TODO: Create this function
def edit_word(context, chat_id, message_text):
	pass


def stop(update, context):
	"""Stop handler."""
	chat_id = update.message['chat']['id']
	del users[chat_id]
	utils.save_users(users)
