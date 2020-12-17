import logging
import json
import os

from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from texts import texts


USERS_FILE = os.path.join('.', 'data', 'users.json')


##################
# KEYBOARDS
##################

def my_keyboard():
	keyboard = ReplyKeyboardMarkup(
		[
			[
				KeyboardButton(texts['b_next'])
			]
		],
		resize_keyboard=True
	)
	return keyboard


def inline_keyboard():
	keyboard = InlineKeyboardMarkup(
		[
			[
				InlineKeyboardButton(text=texts['b_flip'], callback_data='flip')
			],
			[
				InlineKeyboardButton(text=texts['b_remove'], callback_data='delete'),
				InlineKeyboardButton(text=texts['b_down'], callback_data='down'),
				InlineKeyboardButton(text=texts['b_up'], callback_data='up'),
				InlineKeyboardButton(text=texts['b_edit'], callback_data='edit')
			]
		],
		resize_keyboard=True
	)
	return keyboard


def save_users(users):
	with open(USERS_FILE, 'w+') as f:
		f.write(json.dumps(users, indent=4))


def clear(word: str):
	"""Method clear string from bad symbols like double spaces, tabs, '\n' and '\r'."""
	try:
		word = word.replace('\n', '').replace('\t', ' ').replace('\r', '') \
			.replace('\xa0', '').replace('\uf0fc', '').replace('\'', '') \
			.replace('&quot;', '\"').replace('&lt;', '<').replace('&gt;', '>') \
			.replace('&ndash;', '–').replace('&mdash;', '—').replace('&rsquo;', '\"') \
			.replace('&ldquo;', '“').replace('&rdquo;', '”').replace('&ensp;', ' ') \
			.replace('&emsp;', ' ').replace('&thinsp;', ' ').replace('&zwnj;', ' ') \
			.replace('&zwj;', ' ').replace('&lrm;', ' ').replace('&rlm;', ' ') \
			.replace('&sbquo;', '\"').replace('&bdquo;', '\"').replace('&tilde;', '~') \
			.replace('&circ;', '^').replace('&amp;', '&').replace('&lsaquo;', '‹') \
			.replace('&rsaquo;', '›').replace('&permil;', '‰').replace('&euro;', '€') \
			.strip().lower()
		word = ' '.join(word.split())  # removes all double spaces
	except AttributeError:
		pass
	return word


def get_saved_info():

	def get_users(file):
		users = {}
		try:
			with open(file, 'r') as f:
				saved_users = json.loads(f.read())
		except:
			pass
		else:
			for chat_id, user in saved_users.items():
				try:
					chat_id = int(chat_id)
				except ValueError:
					pass
				users[chat_id] = user
		return users

	users = get_users(USERS_FILE)
	return users


def log(update):
	# logging.info(f"User: {update.message.chat.username}, chat id: {update.message.chat.id}, message: {update.message.text}")
	logging.info(f'update: {update}')
