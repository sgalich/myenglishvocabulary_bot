import os
from datetime import datetime, time

import numpy
import pytz
import telegram
from dotenv import load_dotenv
from telegram.ext import CallbackContext
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          CallbackQueryHandler, Filters)

import texts
import utils
import vocabulary
from db_api import DataBase, User, Card

# TODO:  setup github actions + docker support
# todo: Add translation. Ask user after start about language to translate

load_dotenv('.env')
DB = DataBase()
DEFAULT_TIMEZONE = pytz.timezone('America/Los_Angeles')


###########################
# UTILS FUNCTIONS
###########################

def send_message(context: CallbackContext,
                 chat_id: int, text: str, reply_markup=None) -> None:
    """Send message main function."""
    text = texts.EMPTY_MESSAGE if not text else text
    try:
        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
        )
        DB.log(f'<<< {text}', user_id=chat_id, level='DEBUG')
    except telegram.error.Unauthorized:
        deactivate_user(chat_id)
        DB.log(f'Bot was blocked by user', user_id=chat_id, level='DEBUG')


def update_user(update: telegram.Update) -> User:
    """Save a new user or update last_message_datetime for a known user."""
    chat_id = update.message['chat']['id']
    username = update.message['chat']['username']
    language_code = update.message.from_user['language_code']
    user = DB.select_one(User, id=chat_id)
    if user:
        DB.update(user, last_message_datetime=datetime.now(), is_active=True)
    else:
        user = User(id=chat_id, username=username, language_code=language_code)
        DB.save(user)
        message = f'New user {username}, language: {language_code}'
        DB.log(message, user_id=chat_id)
    return user


def deactivate_user(chat_id: int) -> None:
    """Make user inactive."""
    user = DB.select_one(User, id=chat_id)
    if user:
        DB.update(user, is_active=False, last_message_datetime=datetime.now())
        DB.log(f'User {user.username} DEACTIVATED!', user_id=chat_id)


##############################
# HANDLERS FUNCTIONS & other
##############################

def message(update: telegram.Update, context: CallbackContext) -> None:
    message = update.message
    chat_id = message['chat']['id']
    message_text = update.message['text']
    DB.log(f'>>> {message_text}', user_id=chat_id, level='DEBUG')
    user = update_user(update)
    # Reply
    if user.is_editing:
        continue_edit_card(update, context, user)
    elif message_text == texts.B_NEXT:
        send_random_card(context, chat_id)
    else:
        title = message_text.split('\n')[0]
        card = DB.select_one(Card, user_id=chat_id, title=title)
        if card:
            DB.update(card, added=card.added + 1)
        else:
            card = Card(
                user_id=chat_id,
                title=title,
                definition=vocabulary.get_definition(title),
                pronunciation=vocabulary.get_pronunciation(title),
                synonyms=vocabulary.get_synonyms(title)
            )
            DB.save(card)
            DB.log(f'New card: \'{title}\'', user_id=chat_id)
        update_card_empty_attributes(card)
        send_message(
            context=context,
            chat_id=chat_id,
            text=texts.CARD_BACK.format(
                title=title,
                pronunciation=card.pronunciation,
                definition=card.definition,
                synonyms=card.synonyms
            ),
            reply_markup=utils.inline_keyboard(),
        )
    # Setup every day reminder
    if not context.job_queue.jobs():
        context.job_queue.run_daily(
            everyday_reminder,
            time(hour=23, minute=0, tzinfo=DEFAULT_TIMEZONE),
            days=(0, 1, 2, 3, 4, 5, 6),
            context=update.message.chat_id
        )


def everyday_reminder(context: CallbackContext) -> None:
    chat_id = context.job.context
    user = DB.select_one(User, id=chat_id, is_active=True)
    if user and 1 <= (datetime.now() - user.last_message_datetime).days:
        send_random_card(context, chat_id)
    message = (f'User not found for the chat_id {chat_id}'
               f', unable to send an everyday reminder.')
    DB.log(message, level='ERROR', user_id=chat_id)
    return None


def update_card_empty_attributes(card: Card) -> None:
    """Make another attempt to find some attributes for card."""
    # TODO: Do I need to update empty fields???
    #  That make sence if there are some changes in the vocabulary module.
    #  Anyway this could be weird. Maybe user want to keep some filed empty,
    #  in this case bot would add a value every time, which is odd.
    pass
    # if not card.definition:
    #     card.definition = vocabulary.get_definition(card.title)
    #     DB.update(card)
    # if not card.pronunciation:
    #     card.pronunciation = vocabulary.get_pronunciation(card.title)
    #     DB.update(card)
    # if not card.synonyms:
    #     card.synonyms = vocabulary.get_synonyms(card.title)
    #     DB.update(card)


def send_random_card(context: CallbackContext, chat_id: int) -> None:
    """Choose a word with these rules:
    as much ADDED as MORE chance
    as much FLIPPED as MORE chance
    as much SHOWN as LESS chance
    as much UP pressed as LESS chance.
    """
    cards = DB.select_all(Card, user_id=chat_id)
    if not cards:
        send_message(
            context=context,
            chat_id=chat_id,
            text=texts.EMPTY_VOCABULARY,
            reply_markup=utils.my_keyboard(''),
        )
        return None
    cards_list = []
    probabilities = []
    for card in cards:
        cards_list.append(card)
        weight = ((card.added + 1) * (card.flipped + 1)
                  / (card.shown + 1) / (card.learned + 1))
        probabilities.append(weight)
    probabilities_sum = sum(probabilities)
    probabilities = [x / probabilities_sum for x in probabilities]
    card = numpy.random.choice(cards_list, p=probabilities)
    send_message(
        context=context,
        chat_id=chat_id,
        text=texts.CARD_FRONT.format(
            title=card.title,
            pronunciation=card.pronunciation,
            added=card.added,
            shown=card.shown
        ),
        reply_markup=utils.inline_keyboard()
    )
    DB.update(card, shown=card.shown + 1)


def inline_callback(update: telegram.Update, context: CallbackContext) -> None:
    chat_id = update.callback_query.from_user.id
    callback = update.callback_query.data
    message_text = update.callback_query.message.text
    title = message_text.split('\n')[0]
    card = DB.select_one(Card, user_id=chat_id, title=title)
    if callback == 'flip':
        if '👁' in message_text:
            DB.log('Flip FRONT -> BACK', user_id=chat_id, level='DEBUG')
            text = texts.CARD_BACK.format(
                title=card.title,
                pronunciation=card.pronunciation,
                definition=card.definition,
                synonyms=card.synonyms
            )
            DB.update(card, flipped=card.flipped + 1)
        else:
            DB.log('Flip BACK -> FRONT', user_id=chat_id, level='DEBUG')
            text = texts.CARD_FRONT.format(
                title=card.title,
                pronunciation=card.pronunciation,
                added=card.added,
                shown=card.shown
            )
        update.callback_query.edit_message_text(
            text=text,
            reply_markup=utils.inline_keyboard()
        )
    elif callback == 'delete':
        # todo: try card.delete() + commit ?
        DB.delete(Card, user_id=chat_id, title=title)
        update.callback_query.message.delete()
    elif callback == 'up':
        DB.update(card, learned=card.learned + 1)
        send_random_card(context, chat_id)
        # Hide delete/up/edit buttons
        update.callback_query.edit_message_text(
            text=update.callback_query.message.text,
            reply_markup=utils.inline_keyboard(mini=True)
        )
    elif callback == 'edit':
        user = DB.select_one(User, id=chat_id)
        DB.update(
            user,
            is_editing=True,
            editing_card_id=card.id,
            editing_status='pronunciation'
        )
        send_message(
            context=context,
            chat_id=chat_id,
            text=texts.EDIT_PRONUNCIATION
        )
        send_message(
            context=context,
            chat_id=chat_id,
            text=card.pronunciation,
            reply_markup=utils.my_keyboard(text=texts.EDIT_KEEP_FIELD)
        )
        # Hide delete/up/edit buttons
        update.callback_query.edit_message_text(
            text=update.callback_query.message.text,
            reply_markup=utils.inline_keyboard(mini=True)
        )


# TODO: Remake it with inline keyboard
#  (choose what to edit after edit button is pressed and edit only one thing per try)
def continue_edit_card(update: telegram.Update,
                       context: CallbackContext, user: User) -> None:
    chat_id = update.message['chat']['id']
    card = DB.select_one(Card, id=user.editing_card_id)
    message_text = update.message['text']
    if user.editing_status == 'pronunciation':
        if message_text != texts.EDIT_KEEP_FIELD:
            DB.update(card, pronunciation=message_text)
        DB.update(user, editing_status='definition')
        send_message(
            context=context,
            chat_id=chat_id,
            text=texts.EDIT_DEFINITION
        )
        send_message(
            context=context,
            chat_id=chat_id,
            text=card.definition,
            reply_markup=utils.my_keyboard(text=texts.EDIT_KEEP_FIELD),
        )
    elif user.editing_status == 'definition':
        if message_text != texts.EDIT_KEEP_FIELD:
            DB.update(card, definition=message_text)
        DB.update(user, editing_status='synonyms')
        send_message(
            context=context,
            chat_id=chat_id,
            text=texts.EDIT_SYNONYMS
        )
        send_message(
            context=context,
            chat_id=chat_id,
            text=card.synonyms,
            reply_markup=utils.my_keyboard(text=texts.EDIT_KEEP_FIELD)
        )
    elif user.editing_status == 'synonyms':
        if message_text != texts.EDIT_KEEP_FIELD:
            DB.update(card, synonyms=message_text)
        DB.update(
            user,
            is_editing=False,
            editing_card_id=None,
            editing_status=None
        )
        send_message(
            context=context,
            chat_id=chat_id,
            text=texts.EDIT_FINISHED,
            reply_markup=utils.my_keyboard()
        )
        send_message(
            context=context,
            chat_id=chat_id,
            text=texts.CARD_BACK.format(
                title=card.title,
                pronunciation=card.pronunciation,
                definition=card.definition,
                synonyms=card.synonyms
            ),
            reply_markup=utils.inline_keyboard()
        )


def start(update: telegram.Update, context: CallbackContext) -> None:
    """Handle the command /start."""
    update_user(update)
    # send_message(
    #     context=context,
    #     chat_id=update.message['chat']['id'],
    #     text=texts.START
    # )
    update.message.reply_text(texts.START)


def handle_stats(update: telegram.Update, context: CallbackContext) -> None:
    """Handle the command /stats."""
    user = update_user(update)
    cards = DB.select_all(Card, user_id=user.id)
    send_message(
        context=context,
        chat_id=update.message['chat']['id'],
        text=texts.STATS.format(len(cards)),
        reply_markup=utils.inline_keyboard(),
    )


def help(update: telegram.Update, context: CallbackContext) -> None:
    """Handle the command /help."""
    update_user(update)
    send_message(
        context=context,
        chat_id=update.message['chat']['id'],
        text=texts.HELP,
        reply_markup=utils.inline_keyboard(),
    )


def stop(update: telegram.Update, context: CallbackContext) -> None:
    """Handle the command /stop."""
    chat_id = update.message['chat']['id']
    send_message(
        context=context,
        chat_id=chat_id,
        text=texts.BYE
        # TODO: Hide reply inline Keyboard after /stop command
    )
    deactivate_user(chat_id)


def handle_error(update: telegram.Update, context: CallbackContext) -> None:
    """Log all telegram API errors."""
    try:
        chat_id = update.to_dict()['from']['id']
    except:
        chat_id = None
    DB.log(str(context.error), level='ERROR', user_id=chat_id)


def main():
    """Start bot."""
    updater = Updater(os.environ['API_KEY'])
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(
        Filters.text & (~Filters.command),
        message,
        pass_user_data=True,
    ))
    dispatcher.add_handler(CallbackQueryHandler(inline_callback))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('stats', handle_stats))
    dispatcher.add_handler(CommandHandler('stop', stop))
    dispatcher.add_error_handler(handle_error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
