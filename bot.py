# -*- coding: utf-8 -*-
#
import json
import logging
import tempfile
import urllib.request
from multiprocessing.pool import ThreadPool

import cherrypy
import cv2
import numpy
import telebot
from telebot import types

import config
from detector import Detector
from user import user

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(config.token)


# WebhookServer, process webhook calls
class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                'content-type' in cherrypy.request.headers and \
                cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)


detector = Detector()
users = []


@bot.message_handler(content_types=["text"])
def repeat_all_text(message):
    pass
    # bot.send_message(message.chat.id, "Пришлите фотографию, исходя из которой нужно сделать фото профиля")


@bot.message_handler(func=lambda message: True, content_types=['photo'])
def photo(message, is_callback=False):
    cur_user: user = next((usr for usr in users if usr.chat_id == message.chat.id), False)
    if not cur_user:
        print(str(message.chat.id) + ', first photo processing, adding to list')
        cur_user = user(message.chat.id)
        users.append(cur_user)
    if is_callback:
        print(str(cur_user.chat_id) + 'started working on a picture in current thread')
        while not process_photo_message(message, cur_user) and cur_user.tries <= len(detector.haarcascades):
            pass
    else:
        pool = ThreadPool(processes=1)
        print(str(cur_user.chat_id) + ' started working on a picture in a new thread')
        async_result = pool.apply_async(process_photo_message, args=(message, cur_user))
        async_result.get()


def process_photo_message(message, usr):
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

    cv_mat = detector.detect_head(cv_mat, usr)

    tmp_file = tempfile.TemporaryFile("w+b")
    if cv_mat is not None:
        print(str(usr.chat_id) + ', face was found, will send it to user, try #' + str(usr.tries))
        encoded_image = cv2.imencode(ext='.png', img=cv_mat)[1]
        tmp_file.write(encoded_image)
        keyboard = types.InlineKeyboardMarkup()
        callback_true = types.InlineKeyboardButton(text="Всё верно", callback_data="true")
        callback_false = types.InlineKeyboardButton(text="Есть ошибка", callback_data="false")
        keyboard.add(callback_true)
        keyboard.add(callback_false)
        tmp_file.seek(0)
        bot.send_photo(message.chat.id, tmp_file, reply_markup=keyboard)
        detector.default_haarcascade_for_user(usr)
        tmp_file.close()
    elif usr.tries >= len(detector.haarcascades) - 1 or usr.tries >= len(detector.haarcascades) - 1 and cv_mat is None:
        print(str(usr.chat_id) + ' exceeded his tries and face wasn\'t found try #' + str(usr.tries))
        usr.tries = 0
        detector.default_haarcascade_for_user(usr)
        bot.send_message(message.chat.id, "Лицо не найдено, попробуйте другую фотографию")
        tmp_file.close()
    elif cv_mat is None:
        print(str(usr.chat_id) + ', face wasn\'t found try #' + str(usr.tries))
        detector.next_haarcascade_for_user(usr)
        tmp_file.close()
        process_photo_message(message, usr)


# В большинстве случаев целесообразно разбить этот хэндлер на несколько маленьких
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    # call.message.chat.id
    chat_id = call.message.chat.id
    # Если сообщение из чата с ботом
    if call.message:

        cur_user: user = next((usr for usr in users if usr.chat_id == call.message.chat.id), False)
        if not cur_user:
            return
        if call.data == "true":
            print(str(cur_user.chat_id) + ' accepted our cropping')
            bot.edit_message_reply_markup(chat_id, call.message.message_id)
            # bot.edit_message_text(text='', chat_id=chat_id, message_id=call.message.message_id)
            bot.send_message(chat_id, "Хорошо, приятно было с вами работать")
            if cur_user:
                cur_user.tries = 0
        elif call.data == "false":
            print(str(cur_user.chat_id) + ' didn\'t accept our cropping, we will try again or stop')
            if (cur_user.tries + 1 >= len(detector.haarcascades)):
                bot.send_message(chat_id, "К сожалению лицо не было найдено! Может попробуем другую фотографию?")
                bot.edit_message_reply_markup(chat_id, call.message.message_id)

                #bot.edit_message_text(text='', chat_id=chat_id, message_id=call.message.message_id)
                cur_user.tries = 0
                print(str(cur_user.chat_id) + ' didn\'t accept our cropping and he\'s ran out of tries')
            else:
                res_user = next(usr for usr in users if usr.chat_id == chat_id)
                detector.next_haarcascade_for_user(res_user)
                process_photo_message(call.message, cur_user)


def url_to_image(url):
    response = urllib.request.urlopen(url)
    result = response.read()
    image = numpy.asarray(bytearray(result), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return image


bot.remove_webhook()
bot.set_webhook(url=config.WEBHOOK_URL_BASE + config.WEBHOOK_URL_PATH,
                certificate=open(config.WEBHOOK_SSL_CERT, 'r'))
access_log = cherrypy.log.access_log
for handler in tuple(access_log.handlers):
    access_log.removeHandler(handler)
cherrypy.config.update({
    'server.socket_host': config.WEBHOOK_LISTEN,
    'server.socket_port': config.WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': config.WEBHOOK_SSL_CERT,
    'server.ssl_private_key': config.WEBHOOK_SSL_PRIV
})
cherrypy.quickstart(WebhookServer(), config.WEBHOOK_URL_PATH, {'/': {}})
