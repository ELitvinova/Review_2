import requests
import telebot
from telebot import types
from telebot import apihelper
import time

"""
This module provides telegram bot, sending images from Stanford Dogs Dataset,
using Dogs API.
"""


# initializing bot object with our telegram token
with open('telegram.token') as token_file:
    token = token_file.read()
bot = telebot.TeleBot(token)


apihelper.proxy = {'http' : 'http://176.107.133.176:8080'}

text_messages = {
    'start':
        'Welcome! Please, ask me for some dog pictures, '
        'using command /dog. Or you can ask for /help',
    'help':
        'You can ask for a picture of random dog, using command /dog. '
        'If you want a picture of a special breed, you can use command /breed'
        ' with the name of the breed right after it. \n\n'
        'Example: \n'
        '/breed terrier\n\n'
        'To get the list af all available breeds, '
        'use command /all',
    '404':
        'Sorry, we cannot find it. Try something else.'
}

# list of all breeds in our dataset
breeds_list = requests.get('https://dog.ceo/api/breeds/list/all').\
    json()['message']


def prepare_list_message():
    message = 'Here is the list of all available breeds:\n'
    for breed in breeds_list.keys():
        message += '{}\n'.format(breed)
        if len(breeds_list[breed]) > 0:
            for sub in breeds_list[breed]:
                message += '   {} {}\n'.format(sub, breed)
    return message


# string message with the list of all breeds in our dataset
list_message = prepare_list_message()


def check_error(message, response):
    """
    If everything is OK, returns False, otherwise returns True.
    """
    if response.status_code == 200:
        return False
    if response.status_code == 404:
        bot.send_message(message.chat.id, text_messages['404'])
    # logging
    with open('log.txt', 'a') as log_f:
        log_f.write('{} message: {}, code: {}\n'.
                    format(time.strftime('%Y%m%d_%H%M%S'),
                           message.text, response.status_code))
    return True


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, text_messages['start'])


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, text_messages['help'])


@bot.message_handler(commands=['dog'])
def get_random_dog(message):
    """
    This function provides an image of random dog from the dataset.
    """
    # getting response from the dataset
    response = requests.get('https://dog.ceo/api/breeds/image/random')

    # if any error occurs, it would be handled in check_error function
    if check_error(message, response):
        return

    # getting image from the response
    got_message = response.json()
    photo = got_message['message']
    # sending image
    bot.send_photo(message.chat.id, photo)


@bot.message_handler(commands=['all'])
def get_breeds_list(message):
    """
    This function provides the list of all breeds
    and sub-breeds in our dataset.
    """
    # if this function is called for the first time, building the message
    if list_message == "":
        prepare_list_message()
    # sending the message
    bot.send_message(message.chat.id, list_message)


@bot.message_handler(commands=['breed'])
def get_by_breed(message):
    """
    This function checks if there are any sub-breeds in the breed
    and if it is a real breed. If there are more than one sub-breed
    in our dataset, we call function to choose it. If not, image of
    this breed is sent to the user.
    """
    # getting breed from the message
    breed = message.text.lower().split()

    # if we cannot find breed in the message
    if len(breed) != 2:
        bot.send_message(message.chat.id,
                         'You should use this command as in the example in /help')
        return

    breed = breed[1]

    # if we do not have this bread in our dataset, we cannot send it
    if breed not in breeds_list:
        bot.send_message(message.chat.id, text_messages['404'])
        return

    # if there are more than one sub-breed in this bread,
    # we ask user to select which one he wants to receive
    if len(breeds_list[breed]) > 1:
        select_sub_breed(message, breed)
        return

    # getting response from the dataset
    response = requests.get('https://dog.ceo/api/breed/{}/images/random'.
                            format(breed))

    # if any error occurs, it would be handled in check_error function
    if check_error(message, response):
        return

    # getting image from the response
    got_message = response.json()
    photo = got_message['message']
    # sending image
    bot.send_photo(message.chat.id, photo)


def get_by_sub_breed(message):
    """
    This function sends an image of sub-breed, entered in message.
    """
    try:
        sub_breed, breed = message.text.split()
    except Exception:
        bot.send_message(message.chat.id, 'Ooops, you did something wrong...')
        return

    # getting response from the dataset
    response = requests.get('https://dog.ceo/api/breed/{}-{}/images/random'.
                            format(breed, sub_breed))

    # if any error occurs, it would be handled in check_error function
    if check_error(message, response):
        return

    # getting image from the response
    got_message = response.json()
    photo = got_message['message']
    # sending image
    bot.send_photo(message.chat.id, photo)


def select_sub_breed(message, breed):
    """
    This function provides a keyboard to help user to enter the sub-breed name.
    Also it redirects his answer to function, sending image of this sub-breed.
    """
    # creating special keyboard
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2)
    buttons = []

    # creating buttons
    for sub in breeds_list[breed]:
        buttons.append('{} {}'.format(sub, breed))

    # adding buttons to the keyboard
    markup.add(*buttons)
    # sending this keyboard as the answer to the incoming message
    msg = bot.reply_to(message, 'Select sub-breed', reply_markup=markup)
    # setting function get_by_sub_breed as a handler for the user's response
    bot.register_next_step_handler(msg, get_by_sub_breed)


bot.polling()
