# -*- coding: utf-8 -*-
# клиент отправляет запрос серверу;
# сервер отвечает соответствующим кодом результата.
# Клиент и сервер должны быть реализованы в виде отдельных скриптов, содержащих соответствующие функции.
# Функции сервера:
#   принимает сообщение клиента;
#   формирует ответ клиенту;
#   отправляет ответ клиенту;
#       имеет параметры командной строки:
#       -p <port> — TCP-порт для работы (по умолчанию использует 7777);
#       -a <addr> — IP-адрес для прослушивания (по умолчанию слушает все доступные адреса).
from socket import *
import pickle
import argparse
import logging
import log.server_log_config

# для параметров
def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=7777, type=int)
    parser.add_argument('-a', '--addr', default='')
    return parser


if __name__ == '__main__':
    log = logging.getLogger('server_log')
    try:
        parser = createParser()
        namespace = parser.parse_args()

        s = socket(AF_INET, SOCK_STREAM)
        s.bind((namespace.addr, namespace.port))
        log.debug(f'слушаем {namespace.port} порт')
        s.listen(5)

        while True:
            client, addr = s.accept()   # Принять запрос на соединение
            data = client.recv(1024)
            #print(pickle.loads(data))
            log.debug(f'Получено сообщение от клиента:\n{pickle.loads(data)}')
            responce = {
                'responce': 200,
                'alert': 'Привет от Сервера!'
            }
            client.send(pickle.dumps(responce))
            log.debug(f'Отправлено сообщение клиенту:\n{responce}')
            client.close();
    except Exception as e:
        log.error(e)