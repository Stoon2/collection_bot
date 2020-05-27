#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

This is a simple passion project to automate and simplify some processes that are currently manually done by
advisers at Vodafone UK Cairo, Egypt in Sixth Horizon branch who have more than enough on their plate.
Main credit goes to Team Karim Wael for their incredible support.

Credit to everyone who assisted with testing:

Ibrahim Meshref

Amira Elsayed

Reem Sherif

Kamal Tarek

and TM Karim Wael

Couldn't have done it without you guys! Cheers :D


________________________________________________________________________________________________________________

Extensive use of the py-telegram-bot API wrapper was used to simplify interacting with the Telegram API. This way we
did not have to code too much of our own logic into handling JSON files and their respective inputs or tags.

"""

import logging
import pickle
import config

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)
from user import User
from pymongo.mongo_client import MongoClient

TOKEN = config.TELEGRAM_API_TOKEN

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Announcing states and assigning values
TASK, VALUE_ICASE, VALUE_NBA, CLOSURE = range(4)

# Function that begins our conversation
def start(update, context):
    reply_keyboard = [['Submit iCase', 'Submit NBA'], ['Closure']]  # This way shows closure in its own row
    update.message.reply_text(
        'Hi! Please choose your task. '
        'Send /cancel to stop talking to me.\n\n',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))

    logger.info(update.message.text + ' in start')

    return TASK


# Function where a task is assigned to the conversation
def task(update, context):
    logger.info(update.message.text + ' in task function')
    reply_keyboard = [['Closure iCase', 'Closure NBA']]
    # If user wants the closure of the day, we access the CLOSURE state and send a one-time KB to query NBA or iCase
    if update.message.text == 'Closure':
        logger.info('IN CLOSURE')
        update.message.reply_text('Please reply whether you want NBA or iCase closure: ',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                                   selective=True))
        return CLOSURE

    # If user wants to submit an iCase we return the VALUE_ICASE state
    elif update.message.text == 'Submit iCase':
        user = update.message.from_user
        logger.info("Value of %s: %s", user.first_name, update.message.text)
        update.message.reply_text('Cool, now enter how many iCases you want to submit :D',
                                  reply_markup=ReplyKeyboardRemove())
        return VALUE_ICASE

    # If user wants to submit an NBA we return the VALUE_NBA state
    elif update.message.text == 'Submit NBA':
        user = update.message.from_user
        logger.info("Value of %s: %s", user.first_name, update.message.text)
        update.message.reply_text('Cool, now enter how many NBAs you want to submit :D',
                                  reply_markup=ReplyKeyboardRemove())
        return VALUE_NBA


# Function after receiving the number of iCases, processes the information to a dictionary with a (key, value pair)
# assigning the user's ID as a key, and a string containing his first and last names plus the content of his last
# message, in other words the number he just input. It has to be a number other wise it would have been rejected by the
# regex at the state MessageHandler level.

def value_icase(update, context):
    user = update.message.from_user
    logger.info("ID: %s Name: %s %s, tasks: %s", user.id, user.first_name, user.last_name, update.message.text)
    update.message.reply_text('Awesome, thank you for the submission. Make sure you call em back ' + "\U000023F0",
                              reply_markup=ReplyKeyboardRemove())

    user_crud = User(update.message)
    user_crud.submit("icase_bot")

    return ConversationHandler.END


# Function after receiving the number of NBA, processes the information to a dictionary with a (key, value pair)
# assigning the user's ID as a key, and a string containing his first and last names plus the content of his last
# message, in other words the number he just input. It has to be a number other wise it would have been rejected by the
# regex at the state MessageHandler level.

def value_nba(update, context):
    user = update.message.from_user
    logger.info("ID: %s Name: %s %s, tasks: %s", user.id, user.first_name, user.last_name, update.message.text)
    update.message.reply_text('Awesome, thank you for the NBA submission. Keep that money rolling ' + "\U0001F911!",
                              reply_markup=ReplyKeyboardRemove())
                              
    user_crud = User(update.message)
    user_crud.submit("nba_bot")

    return ConversationHandler.END


# Closure state function, the point of this function is upon receiving a message, it would query the user which value
# he wanted to summarize. For example the user sends NBA and the appropriate selection is picked in the if-else
# statements. User would have to enter one of the options otherwise he would automatically restart this state with
# a message prompting them to make a correct selection or /cancel the conversation

def closure(update, context):
    logger.info('in closure function')
    user = update.message.from_user
    client = MongoClient(config.MONGO_DB_TOKEN)
    db = client.big_team # AFTER THE CLIENT OBJECT DOT, TYPE THE NAME OF YOUR DATABASE!!!

    update.message.reply_text('Working on your request...', reply_markup=ReplyKeyboardRemove())

    if update.message.text == 'Closure NBA':
        # Switch current collection to NBA collection
        collection_name = "nba_bot"
        collection = db[collection_name]

        logger.info("User: %s Name: %s %s, submitted #%s", user.id, user.first_name, user.last_name,
                    update.message.text)
        update.message.reply_text('Collecting NBA...', reply_markup=ReplyKeyboardRemove())
        
        # calling function to concat string result
        nba_collect_summary = 'NBA Summary for: ' + str(update.message.chat.title) +'\n'
        nba_collect_summary = read_record(update, collection, nba_collect_summary) 
        
        # send string back to user
        update.message.reply_text(nba_collect_summary)

        return ConversationHandler.END

    elif update.message.text == 'Closure iCase':
        # Switch to iCase collection
        collection_name = "icase_bot"
        collection = db[collection_name]

        logger.info("User: %s Name: %s %s, submitted #%s", user.id, user.first_name, user.last_name,
                    update.message.text)
        update.message.reply_text('Collecting iCase...', reply_markup=ReplyKeyboardRemove())
        
        # calling function to concat string result
        icase_collect_summary = 'iCase Summary for: ' + str(update.message.chat.title) +'\n'
        icase_collect_summary = read_record(update, collection, icase_collect_summary)
        
        # send string back to user
        update.message.reply_text(icase_collect_summary)
        
        return ConversationHandler.END

    else:
        update.message.reply_text('I didn\'nt get that, please enter either Closure NBA or Closure iCase or /cancel'
                                  'to end this conversation.')
        return CLOSURE


# Simple function so we can read the state of a given file of a dictionary. Read the states out and return a total
# with the value of the rows line by line
def read_record(update, collection, task_string):
    for result in collection.find({}):
            if(update.message.chat.title == result["group_name"]):
                task_string = task_string + result["user_name"] + ": " + result["user_content"]
    return task_string


def not_found(update, context):
    reply_keyboard = [['Submit iCase', 'Submit NBA', 'Closure']]
    user = update.message.from_user
    logger.info('Message was not understood', user.first_name)
    update.message.reply_text('Sorry, I didn\'t get that. Please make sure you\'re entering a number only! If you want'
                              ' to end this conversation please type /cancel... Please choose an option from the'
                              ' main menu to continue.',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True))
    return TASK


def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def help(update, context):
    update.message.reply_text('To start using the bot, please enter /start. \n'
                              'To cancel at any point, please enter /cancel to exit the bot. \n'
                              'Make sure you read the bot\'s  messages carefully as it won\'t accept incorrect input')


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            # ALL MESSAGE HANDLERS EXPECT A REPLY SO THEY WORK!!!!! PLEASE BE AWARE.
            # FOR EXAMPLE VALUE_NBA IS ONLY GOING TO TRIGGER IF YOU GIVE IT A REPLY AFTER THE IF STATEMENT IS TRIGGERED
            # IN TASK STATE.
            TASK: [MessageHandler(Filters.regex('^(Submit iCase|Submit NBA|Closure)$'), task)],
            VALUE_ICASE: [MessageHandler(Filters.regex('^[-+]?[0-9]+$'), value_icase)],
            VALUE_NBA: [MessageHandler(Filters.regex('^[-+]?[0-9]+$'), value_nba)],
            CLOSURE: [MessageHandler(Filters.regex('^(Closure NBA|Closure iCase)$'), closure)]
        },

        fallbacks=[CommandHandler('cancel', cancel), MessageHandler(Filters.text, not_found)]
    )

    # Add conversation handler to dispatcher
    dp.add_handler(conv_handler)

    # Add help command handler
    updater.dispatcher.add_handler(CommandHandler('help', help))

    # Log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
