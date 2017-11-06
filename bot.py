from telebot import types

import config
import telebot
import numpy
import urllib.request
import os
from detector import Detector
import cv2
import json

detector = Detector()
bot = telebot.TeleBot(config.token)

tries = 0
msg = None


@bot.message_handler(content_types=["text"])
def repeat_all_text(message):
    bot.send_message(message.chat.id, "Пришлите фотографию, исходя из которой нужно сделать фото профиля")


@bot.message_handler(content_types=['photo'])
def photo(message):
    process_photo_message(message)


def process_photo_message(message):
    global msg, tries
    tries += 1
    msg = message
    file_id_url = 'https://api.telegram.org/bot<bot_token>/getFile?file_id=<the_file_id>'
    result = json.load(urllib.request.urlopen(file_id_url
                                              .replace('<bot_token>',
                                                       str(config.token))
                                              .replace('<the_file_id>',
                                                       str(message.photo[len(message.photo) - 1].file_id))))['result']
    file_path = result['file_path']
    file_path_url = 'https://api.telegram.org/file/bot<token>/<file_path>'
    cv_mat = url_to_image(file_path_url
                          .replace('<token>', config.token)
                          .replace('<file_path>', file_path))

    cv_mat = detector.detect_head(cv_mat)

    # TODO change temp solution: now pic saves in project directory
    cv2.imwrite(result['file_id'] + '.png', cv_mat)
    # it was needed for FileIO, because telegram doesn't want to send Image from PIL, binary list or binary numpy array
    saved_image = open(result['file_id'] + '.png', 'br')
    keyboard = types.InlineKeyboardMarkup()
    callback_true = types.InlineKeyboardButton(text="Всё верно", callback_data="true")
    callback_false = types.InlineKeyboardButton(text="Есть ошибка", callback_data="false")
    keyboard.add(callback_true)
    keyboard.add(callback_false)
    saved_image.seek(0)
    first = saved_image.read(1)
    if first:
        saved_image.seek(0)
        bot.send_photo(message.chat.id, saved_image, reply_markup=keyboard)
    else:
        if tries >= len(detector.haarcascades):
            tries = 0
            detector.default_haarcascade()
            bot.send_message(msg.chat.id, "Лицо не найдено, попробуйте другую фотографию")
            saved_image.close()
            os.remove(result['file_id'] + '.png')
        elif tries < len(detector.haarcascades):
            detector.next_haarcascade()
            saved_image.close()
            os.remove(result['file_id'] + '.png')
            process_photo_message(message)


# В большинстве случаев целесообразно разбить этот хэндлер на несколько маленьких
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    # Если сообщение из чата с ботом
    if call.message:
        if call.data == "true":
            global msg
            bot.send_message(msg.chat.id, "Хорошо, приятно было с вами работать")
            msg = None
        elif call.data == "false":
            detector.next_haarcascade()
            process_photo_message(msg)


def url_to_image(url):
    response = urllib.request.urlopen(url)
    result = response.read()
    image = numpy.asarray(bytearray(result), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return image


# TODO update by webhooks
if __name__ == '__main__':
    bot.polling(none_stop=True)
