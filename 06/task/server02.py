# -*- coding: utf-8 -*-
import inspect
from datetime import datetime
import time
from socket import *
import pickle
import argparse
import logging
from functools import wraps
import log.server_log_config

#декоратор log
def decorLog(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        logger = logging.getLogger('client_log')
        logger.debug(f'{func.__name__} вызвана из '
                     f'{inspect.stack()[1][3]}')
        res = func(*args, **kwargs)
        return res
    return decorated




# для параметров
def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=7777, type=int)
    parser.add_argument('-a', '--addr', default='')
    return parser

class Server:
    """docstring"""

    def __init__(self, paramsNameSpace, logger):
        """Constructor"""
        self.logger = logger
        self.logger.debug(f'Создаём экземпляр Server')

        self.oSocket = socket(AF_INET, SOCK_STREAM)
        self.oSocket.bind((paramsNameSpace.addr, paramsNameSpace.port))
        self.oSocket.listen(1)

        self.clients = {}

        self.permissionConnect = True
        self.messageSize = 1024

        self.response = {
            'connect': {
                'response': 200,
                'alert': 'Im ready to connect'
            },
            'authenticate': {
                'OK': {
                    'response': 200,
                    'alert': 'authenticate OK'
                },
                'passName': {
                    'response': 402,
                    'alert': 'This could be "wrong password" of "no account with that name"'
                },
                'occupied': {
                    'response': 409,
                    'alert': 'Someone is already connected with the given user name'
                },
            },
            'authorization': {
                'OK': {
                    'response': 200,
                    'alert': 'authorization OK'
                },
                'occupied': {
                    'response': 409,
                    'alert': 'You are already registered'
                },
                'passName': {
                    'response': 402,
                    'alert': 'This could be "wrong password" of "no account with that name"'
                },
            },
        }

    @decorLog
    def clientListener(self):
        """Listener"""
        if self.permissionConnect:
            while True:
                client, addr = self.oSocket.accept()   # Принять запрос на соединение
                data = pickle.loads(client.recv(self.messageSize))
                condition = data['action']

                if condition == 'connect':
                    self.logger.debug(f'Клиент просит подключения:\n{data}')
                    self.responseClient(client, self.response[condition], condition)
                    #client.close()

                if condition == 'authorization':
                    self.logger.debug(f'Клиент пробует авторизоваться:\n{data}')
                    self.authorization(client, data, condition)

                client.close()

    @decorLog
    def authorization(self, client, data, condition):
        user = data['user']
        oLen = len([i for i in self.clients.keys() if i == user['login']])
        params = [client, self.response[condition], condition]

        if oLen == 1:
            if user['pass'] == self.clients[user['login']]:
                self.logger.debug(f'Клиент уже зарегистрирован, пароли совпадают')
                params[1] = params[1]['occupied']
                self.responseClient(*params)
            else:
                self.logger.debug(f'Клиент уже зарегистрирован, пароли не совпадают')
                params[1] = params[1]['passName']
                self.responseClient(*params)

        elif oLen == 0:
            self.clients[user['login']] = user['pass']
            self.logger.debug(f'Добавили нового пользователя в {self.clients}')
            params[1] = params[1]['OK']
            self.responseClient(*params)

    @decorLog
    def responseClient(self, client, response, condition):
        response['time'] = str(time.time())
        response['action'] = condition
        client.send(pickle.dumps(response))
        self.logger.debug(f'Отправлено сообщение клиенту:\n{response}')




def main():
    logger = logging.getLogger('server_log')
    logger.debug(f'Запуск server02.py')
    try:
        parser = createParser()
        namespace = parser.parse_args()

        server = Server(namespace, logger)
        server.clientListener()

    except Exception as e:
        logger.error(e)

if __name__ == '__main__':
    main()