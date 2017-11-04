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


@bot.message_handler(content_types=["text"])
def repeat_all_text(message):
    bot.send_message(message.chat.id, "Пришлите фотографию, исходя из которой нужно сделать фото профиля")


@bot.message_handler(content_types=['photo'])
def photo(message):
    try:
        process_photo_message(message)
    except Exception as e:
        bot.send_message(message.chat.id, "Ой, что-то пошло не так")
        bot.send_message(message.chat.id, "Может попробуем другую фотографию?")


def process_photo_message(message):
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
    bot.send_photo(message.chat.id, saved_image)
    saved_image.close()

    os.remove(result['file_id'] + '.png')


def url_to_image(url):
    response = urllib.request.urlopen(url)
    result = response.read()
    image = numpy.asarray(bytearray(result), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return image


if __name__ == '__main__':
    bot.polling(none_stop=True)
