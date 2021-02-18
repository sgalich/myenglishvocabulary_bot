import numpy
from PyDictionary import PyDictionary
import eng_to_ipa
import requests
import scrapy

from texts import texts
import utils


# TODO: Send cards every day if I didn't use it


dictionary = PyDictionary()
users = {}


def save_user(message):
	"""Save user's data."""

	def create_new_user():
		users[chat_id] = dict(
			chat_id=chat_id,
			lang=message.from_user['language_code'],
			username=message['chat']['username'],
			edit=None,
			cards={}
		)
		utils.save_users(users)

	chat_id = message['chat']['id']
	if not users.get(chat_id):
		create_new_user()


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

	utils.log(f'>>> {chat_id}: {message_text}')

	if users[chat_id].get('edit'):
		continue_edit_card(update, context, chat_id)
	elif message_text == texts['b_next']:
		send_random_card(context, chat_id)
	else:
		for word in message_text.split('\n'):
			save_word(context, chat_id, word)


def send_random_card(context, chat_id):
	"""Chooses a word with these rules:
	as much ADDED as MORE chance
	as much FLIPPED as MORE chance
	as much SHOWN as LESS chance
	as much UP pressed as LESS chance
	"""

	def send_card(context, chat_id, word):
		card = users[chat_id]['cards'][word]
		research_word_attributes(word, card)
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
		weight = (card['added'] + 1) * (card['flipped'] + 1) / (card['shown'] + 1) / (card['up'] + 1)
		probabilities.append(weight)
	probabilities_sum = sum(probabilities)
	probabilities = [x / probabilities_sum for x in probabilities]
	chosen_word = numpy.random.choice(words_list, p=probabilities)
	cards[chosen_word]['shown'] += 1
	utils.save_users(users)
	send_card(context, chat_id, chosen_word)


def research_word_attributes(word, card):
	if not card.get('definition'):
		card['definition'] = get_definition(word)
	if not card.get('pronunciation'):
		card['pronunciation'] = get_pronunciation(word)
	if not card.get('synonyms'):
		card['synonyms'] = get_synonyms(word)
	utils.save_users(users)


# TODO: Add examples
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
	back_side = f"""{definition}

📖 {word}: {synonyms}
"""
	return back_side


def get_definition(word: str) -> str:
	"""Get definition of the word."""
	first_word = word.split()[0]    # Leave only 1st word
	url = f'http://wordnetweb.princeton.edu/perl/webwn?s={first_word}'
	definition = ""
	response = requests.get(url).text
	response = scrapy.selector.Selector(text=response)
	parts_of_speech = response.xpath('//h3/text()').getall()
	for part_of_speech in parts_of_speech:
		definition += f'\n\n{part_of_speech}'
		all_definitions_xpath = f'//h3[text()="{part_of_speech}"]/following-sibling::ul//li/text()'
		all_definitions = response.xpath(all_definitions_xpath).getall()
		for definition_var in all_definitions:
			definition_var = definition_var.strip(', ').strip().replace('(', '', 1)
			definition_var = definition_var[::-1].replace(')', '', 1)[::-1]
			if definition_var:
				definition += f'\n\t– {definition_var}'
	return definition


def get_pronunciation(word):
	pronunciation = eng_to_ipa.convert(''.join(word))
	return pronunciation


def get_synonyms(word):
	first_word = word.split()[0]  # Leave only 1st word
	synonyms = dictionary.synonym(first_word)
	synonyms = ', '.join(synonyms) if synonyms else ''
	return synonyms


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
			flipped=0,
			definition=get_definition(new_word),
			pronunciation=get_pronunciation(new_word),
			synonyms=get_synonyms(new_word)
		)
		cards[new_word] = new_card
	research_word_attributes(new_word, new_card)
	utils.save_users(users)
	pronunciation = new_card['pronunciation']
	context.bot.send_message(
		chat_id=chat_id,
		text=f'[ {pronunciation} ]',
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
		elif callback == 'up':
			upgrade_word(context, chat_id, message_text)
			# Hide delete/up/edit buttons
			update.callback_query.edit_message_text(
				text=update.callback_query.message.text,
				reply_markup=utils.inline_keyboard(mini=True)
			)
		elif callback == 'edit':
			start_edit_card(context, chat_id, message_text)
			# Hide delete/up/edit buttons
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
		card['flipped'] += 1
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


def upgrade_word(context, chat_id, message_text):
	word = find_the_word(message_text)
	users[chat_id]['cards'][word]['up'] += 1
	utils.save_users(users)
	send_random_card(context, chat_id)


def start_edit_card(context, chat_id, message_text):
	word = find_the_word(message_text)
	users[chat_id]['edit'] = {
		'word': word,
		'status': 'pronunciation'
	}
	context.bot.send_message(
		chat_id=chat_id,
		text=texts['edit_pronunciation']
	)
	pronunciation = users[chat_id]['cards'][word]['pronunciation']
	context.bot.send_message(
		chat_id=chat_id,
		text=pronunciation,
		reply_markup=utils.my_keyboard(text=pronunciation),
	)

# TODO: Remake it with inline keyboard
#  (choose what to edit after edit button is pressed and edit only one thing per try)
def continue_edit_card(update, context, chat_id):
	word = users[chat_id]['edit']['word']
	status = users[chat_id]['edit']['status']
	message_text = update.message['text']
	if status == 'pronunciation':
		users[chat_id]['cards'][word]['pronunciation'] = message_text
		users[chat_id]['edit']['status'] = 'definition'
		context.bot.send_message(
			chat_id=chat_id,
			text=texts['edit_definition']
		)
		definition = users[chat_id]['cards'][word]['definition']
		context.bot.send_message(
			chat_id=chat_id,
			text=definition,
			reply_markup=utils.my_keyboard(text=definition),
		)
	elif status == 'definition':
		users[chat_id]['cards'][word]['definition'] = message_text
		users[chat_id]['edit']['status'] = 'synonyms'
		context.bot.send_message(
			chat_id=chat_id,
			text=texts['edit_synonyms']
		)
		synonyms = users[chat_id]['cards'][word]['synonyms']
		context.bot.send_message(
			chat_id=chat_id,
			text=synonyms,
			reply_markup=utils.my_keyboard(text=synonyms),
		)
	elif status == 'synonyms':
		users[chat_id]['cards'][word]['synonyms'] = message_text
		users[chat_id]['edit'] = None
		utils.save_users(users)
		context.bot.send_message(
			chat_id=chat_id,
			text=texts['edit_finished'],
			reply_markup=utils.my_keyboard(),
		)
		context.bot.send_message(
			chat_id=chat_id,
			text=generate_back_side(word, users[chat_id]['cards'][word]),
			reply_markup=utils.inline_keyboard(),
		)


def stop(update, context):
	"""Stop handler."""
	chat_id = update.message['chat']['id']
	del users[chat_id]
	utils.save_users(users)
