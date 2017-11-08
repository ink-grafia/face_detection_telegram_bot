from telebot import types

import tempfile
import config
import telebot
import numpy
import urllib.request
from detector import Detector
import cv2
import json
from multiprocessing.pool import ThreadPool
from user import user

detector = Detector()
bot = telebot.TeleBot(config.token)
users=[]
@bot.message_handler(content_types=["text"])
def repeat_all_text(message):
    print(str(message.chat.id) + ', got the text, sample response')
    bot.send_message(message.chat.id, "Пришлите фотографию, исходя из которой нужно сделать фото профиля")


@bot.message_handler(content_types=['photo'])
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
        print(str(cur_user.chat_id) +' started working on a picture in a new thread')
        async_result = pool.apply_async(process_photo_message, args=(message,cur_user))
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
    elif usr.tries+1 >= len(detector.haarcascades) or usr.tries+1 >= len(detector.haarcascades) and cv_mat is None:
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
            bot.send_message(chat_id, "Хорошо, приятно было с вами работать")
            if cur_user:
                cur_user.tries = 0
        elif call.data == "false":
            print(str(cur_user.chat_id) + ' didn\'t accept our cropping, we will try again or stop')
            if (cur_user.tries+1 >= len(detector.haarcascades)):
                bot.send_message(chat_id, "К сожалению лицо не было найдено! Может попробуем другую фотографию?")
                cur_user.tries=0
                print(str(cur_user.chat_id) + ' didn\'t accept our cropping and he\'s ran out of tries')
            else:
                detector.next_haarcascade_for_user(next(usr for usr in users if usr.chat_id == chat_id))
                process_photo_message(call.message, cur_user)


def url_to_image(url):
    response = urllib.request.urlopen(url)
    result = response.read()
    image = numpy.asarray(bytearray(result), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return image


# TODO update by webhooks
if __name__ == '__main__':
    bot.polling(none_stop=True)
