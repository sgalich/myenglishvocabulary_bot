import logging
import os

from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters

import handlers
import utils

load_dotenv('.env')

logging.basicConfig(
	format='%(asctime)s - %(levelname)s - %(message)s',
	level=logging.INFO,
	filename='bot.log'
)


def main():
	handlers.users = utils.get_saved_info()
	updater = Updater(os.environ['API_KEY'])
	dispatcher = updater.dispatcher
	dispatcher.add_handler(CommandHandler('start', handlers.start, pass_user_data=True))
	dispatcher.add_handler(MessageHandler(
		Filters.text & (~Filters.command),
		handlers.message,
		pass_user_data=True,
	))
	dispatcher.add_handler(CallbackQueryHandler(handlers.inline_callback))
	dispatcher.add_handler(CommandHandler('stop', handlers.stop))
	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
