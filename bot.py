# -*- coding: utf-8 -*-
import datetime
import logging
import os

import cherrypy
import cv2
import telebot

import config
import processing
from detector import Detector
from processing import prepare_url, url_to_cv2, process_photo_message
from user import user

# initialization
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


# handlers
@bot.message_handler(content_types=["text"])
def repeat_all_text(message):
    pass
    # bot.send_message(message.chat.id, "Пришлите фотографию, исходя из которой нужно сделать фото профиля")


@bot.message_handler(func=lambda message: True, content_types=['photo'])
def photo(message, is_callback=False):
    cur_user: user = next((usr for usr in users if usr.chat_id == message.chat.id), False)
    if not cur_user:
        cur_user = user(message.chat.id)
        users.append(cur_user)
    if is_callback:
        while not process_photo_message(message, cur_user, detector, bot) and cur_user.tries <= len(
                detector.haarcascades):
            pass
    else:
        process_photo_message(message, cur_user, detector, bot)


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
        path = '/root/profile_pics/'
        if call.data == "true":
            processing.write_log(datetime.datetime.now().isoformat(),
                                 call.message.chat.id,
                                 call.from_user.first_name,
                                 call.from_user.last_name,
                                 call.from_user.username,
                                 "accepted our cropping",
                                 path + str(call.message.chat.id) + '.png')
            try:  # TODO do not replace current photo
                old = [ele for ele in os.listdir(path + "old/")
                       if ele.startswith(str(call.message.chat.id))]
                if len(old) == 0:
                    os.rename(path + str(call.message.chat.id) + '.png',
                              path + "old/" + str(call.message.chat.id) + "_0" + '.png')
                else:
                    last = sorted([ele.replace(str(call.message.chat.id) + "_", "")
                                  .replace(".png", "") for ele in old])[-1]
                    os.rename(path + str(call.message.chat.id) + '.png',
                              path + "old/" + str(call.message.chat.id) + "_" + str(int(last) + 1) + '.png')
            except OSError:
                pass
            cv2.imwrite(filename=path + str(call.message.chat.id) + '.png',
                        img=url_to_cv2(prepare_url(call.message)))
            # bot.edit_message_text(text='', chat_id=chat_id, message_id=call.message.message_id)
            bot.send_message(chat_id, "Хорошо, приятно было с вами работать")
            users.remove(cur_user)
            if cur_user:
                cur_user.tries = 0
        elif call.data == "false":
            if (cur_user.tries + 1 >= len(detector.haarcascades)):
                bot.send_message(chat_id, "К сожалению лицо не было найдено! Может попробуем другую фотографию?")

                users.remove(cur_user)
                # bot.edit_message_text(text='', chat_id=chat_id, message_id=call.message.message_id)
                cur_user.tries = 0
                processing.write_log(datetime.datetime.now().isoformat(),
                                     call.message.chat.id,
                                     call.from_user.first_name,
                                     call.from_user.last_name,
                                     call.from_user.username,
                                     "didn\'t accept our cropping and he\'s ran out of tries",
                                     path + str(call.message.chat.id) + '.png')
            else:
                res_user = next(usr for usr in users if usr.chat_id == chat_id)
                detector.next_haarcascade_for_user(res_user)
                process_photo_message(call.message, cur_user, detector, bot)
        bot.edit_message_reply_markup(chat_id, call.message.message_id)


# starting service

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
