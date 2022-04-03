import json
import logging
import os

import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext

import texts

USERS_FILE = os.path.join('.', 'data', 'users.json')


def send_message(context: CallbackContext, chat_id: int, text: str, reply_markup=None):
	global users
	try:
		context.bot.send_message(
			chat_id=chat_id,
			text=text,
			reply_markup=reply_markup,
		)
	except telegram.error.Unauthorized:
		del users[context.job.context]
		save_users(users)


def my_keyboard(text=texts.B_NEXT) -> ReplyKeyboardMarkup:
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
			[[InlineKeyboardButton(text=texts.B_FLIP, callback_data='flip')]],
			resize_keyboard=True
		)
	return InlineKeyboardMarkup(
		[
			[InlineKeyboardButton(text=texts.B_FLIP, callback_data='flip')],
			[
				InlineKeyboardButton(text=texts.B_REMOVE, callback_data='delete'),
				InlineKeyboardButton(text=texts.B_EDIT, callback_data='edit'),
				InlineKeyboardButton(text=texts.B_UP, callback_data='up'),
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


def log(*args) -> None:
	text = ' '.join(args)
	logging.info(f'update: {text}')
