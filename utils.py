import logging
import json
import os

import telegram
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from texts import texts


USERS_FILE = os.path.join('.', 'data', 'users.json')


def my_keyboard(text=texts['b_next']) -> ReplyKeyboardMarkup:
	keyboard = ReplyKeyboardMarkup(
		[
			[
				KeyboardButton(text)
			]
		],
		resize_keyboard=True
	)
	return keyboard


def inline_keyboard(mini=False) -> InlineKeyboardMarkup:
	if mini:
		return InlineKeyboardMarkup(
			[[InlineKeyboardButton(text=texts['b_flip'], callback_data='flip')]],
			resize_keyboard=True
		)
	return InlineKeyboardMarkup(
		[
			[InlineKeyboardButton(text=texts['b_flip'], callback_data='flip')],
			[
				InlineKeyboardButton(text=texts['b_remove'], callback_data='delete'),
				InlineKeyboardButton(text=texts['b_edit'], callback_data='edit'),
				InlineKeyboardButton(text=texts['b_up'], callback_data='up'),
			]
		],
		resize_keyboard=True
	)


def save_users(users: dict) -> None:
	with open(USERS_FILE, 'w+') as f:
		f.write(json.dumps(users, indent=4))


def clear(word: str) -> str:
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


def get_saved_info() -> dict:

	def get_users(file: str) -> dict:
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


def log(text: str) -> None:
	logging.info(f'update: {text}')
