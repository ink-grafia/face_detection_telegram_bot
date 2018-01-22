# -*- coding: utf-8 -*-
#token = '495979993:AAFwGS24bVM4AYrTLvr9LbMaoLcO8-SIObk'
token = '467250601:AAF7DpSX8MR0qhWGfopBJ7yn9BsjBUcauO0'

#WEBHOOK_HOST = '85.17.15.165'
WEBHOOK_HOST = '85.17.15.165'
WEBHOOK_PORT = 8443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
IMAGES_PORT = 443
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % token

ratio=3./4
