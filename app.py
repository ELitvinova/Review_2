import requests
import telebot
from telebot import types

"""
This module provides telegram bot, sending images from Stanford Dogs Dataset,
using Dogs API.
"""

text_messages = {
    'start':
        u'Welcome! Please, ask me for some dog pictures, '
        u'using command /dog. Or you can ask for /help',
    'help':
        u'You can ask for a picture of random dog, using command /dog. '
        u'If you want a picture of a special breed, you can use command /breed'
        u' with the name of the breed right after it. \n\n'
        u'Example: \n'
        u'/breed shiba\n\n'
        u'To get the list af all available breeds, '
        u'use command /all',
    '404':
        u'Sorry, we cannot find it. Try something else.'
}
# list of all breeds in our dataset
breeds_list = requests.get('https://dog.ceo/api/breeds/list/all').\
    json()['message']


def prepare_list_message():
    list_message = 'Here is the list of all available breeds:\n'
    for breed in breeds_list.keys():
        list_message += '{}\n'.format(breed)
        if len(breeds_list[breed]) > 0:
            for sub in breeds_list[breed]:
                list_message += '   {} {}\n'.format(sub, breed)
    return list_message


if __name__ == '__main__':
    with open('telegram.token') as token_file:
        token = token_file.read()
    bot = telebot.TeleBot(token)


def check_error(chat_id, response):
    if response.status_code == 200:
        return False
    if response.status_code == 404:
        bot.send_message(chat_id, text_messages['404'])
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
    response = requests.get('https://dog.ceo/api/breeds/image/random')
    print('received')
    if check_error(message.chat.id, response):
        return

    got_message = response.json()
    photo = got_message['message']
    bot.send_photo(message.chat.id, photo)


@bot.message_handler(commands=['all'])
def get_breeds_list(message):
    """
    This function provides the list of all breeds
    and sub-breeds in our dataset.
    """
    list_message = prepare_list_message()
    bot.send_message(message.chat.id, list_message)


@bot.message_handler(commands=['breed'])
def get_by_breed(message):
    """
    This function checks if there are any sub-breeds in the breed
    and if it is a real breed. If there are more than one sub-breed
    in our dataset, we call function to choose it. If not, image of
    this breed is sent to the user.
    """
    breed = message.text[7:].lower()

    if breed not in breeds_list:
        bot.send_message(message.chat.id, text_messages['404'])
        return

    if len(breeds_list[breed]) > 1:
        select_sub_breed(message, breed)
        return

    response = requests.get('https://dog.ceo/api/breed/{}/images/random'.
                            format(breed))

    if check_error(message.chat.id, response):
        return

    got_message = response.json()
    photo = got_message['message']
    print(photo)

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

    response = requests.get('https://dog.ceo/api/breed/{}-{}/images/random'.
                            format(breed, sub_breed))

    if check_error(message.chat.id, response):
        return

    got_message = response.json()
    photo = got_message['message']
    bot.send_photo(message.chat.id, photo)


def select_sub_breed(message, breed):
    """
    This function provides a keyboard to help user to enter the sub-breed name.
    Also it redirects his answer to function, sending image of this sub-breed.
    """
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2)
    buttons = []

    for sub in breeds_list[breed]:
        buttons.append('{} {}'.format(sub, breed))

    markup.add(*buttons)
    msg = bot.reply_to(message, 'Select sub-breed', reply_markup=markup)
    bot.register_next_step_handler(msg, get_by_sub_breed)


bot.polling()
