import os

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import ReplyKeyboardMarkup, KeyboardButton

import texts

USERS_FILE = os.path.join('.', 'data', 'users.json')


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
