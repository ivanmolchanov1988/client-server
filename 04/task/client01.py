# клиент отправляет запрос серверу;
# сервер отвечает соответствующим кодом результата.
# Клиент и сервер должны быть реализованы в виде отдельных скриптов, содержащих соответствующие функции.
# Функции клиента:
#   сформировать presence-сообщение;
#   отправить сообщение серверу;
#   получить ответ сервера;
#   разобрать сообщение сервера;
#       параметры командной строки скрипта client.py <addr> [<port>]:
#       addr — ip-адрес сервера;
#       port — tcp-порт на сервере, по умолчанию 7777.

from socket import *
import pickle
import argparse


# для параметров
def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=7777, type=int)
    parser.add_argument('-a', '--addr', default='')
    return parser


if __name__ == '__main__':
    parser = createParser()
    namespace = parser.parse_args()

    s = socket(AF_INET, SOCK_STREAM)  # создадим сокет TCP
    s.connect((namespace.addr, namespace.port))  # соединение с сервером
    msg = {
        'action': 'authenticate',
        'time': '<unix timestamp>',
        'user': {
            'account_name': 'IVAN',
            'passwod': 'password000'
        }
    }
    s.send(pickle.dumps(msg))
    data = s.recv(1024)
    print('Сообщение от сервера: ', pickle.loads(data), ', длиной ', len(data))
    s.close()