# -*- coding: utf-8 -*-

from datetime import datetime
import time
from socket import *
import pickle
import argparse
import logging
from functools import wraps
import inspect
from numpy import mean
import log.client_log_config

#декоратор log
# def decorLog(func):
#     logger = logging.getLogger('client_log')
#     logger.debug(f'{func.__name__}')
#     #print('я тут')
#     #print(func.__name__)
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
    parser.add_argument('-a', '--address', default='')
    #parser.add_argument('--authorize', default=False, type=str)
    #parser.add_argument('--login', type=str)
    #parser.add_argument('--pswrd', type=str)
    #parser.add_argument('--survey', default=False, type=bool)
    return parser

class Client:
    """docstring"""

    def __init__(self, paramsNameSpace, logger):
        """Constructor"""
        self.logger = logger
        self.logger.debug(f'Создаём экземпляр Client')

        self.oSocket = socket(AF_INET, SOCK_STREAM)
        self.params = paramsNameSpace

        self.loginPass = []

        self.clientPermissions = []


    @decorLog
    def serverSurvey(self):
        """Listener"""
        ###### 1 ######
        self.oSocket.connect((self.params.address, self.params.port))
        msg = {
            'action': 'connect',
            'time': str(time.time()),
            'alert': 'Please connect',
        }
        self.oSocket.send(pickle.dumps(msg))
        self.logger.debug(f'Отправлено сообщение серверу: \n{msg}')
        data = self.oSocket.recv(1024)
        response_dict = pickle.loads(data)
        self.logger.debug(f'Получено сообщение от сервера: \n{response_dict}')

        if response_dict['response'] == 200:
            self.clientPermissions.append(True)
        else:
            self.clientPermissions.append(False)
            print('Сервер не готов принять соединение')
            self.logger.debug('Сервер разорвал соединение')
            self.oSocket.close()

        self.getLoginPass()

    @decorLog
    def goChat(self):
        msg = {
            'action': 'chat',
            'time': str(time.time()),
            'user': {
                'login': self.loginPass[0],
                'pass': self.loginPass[1],
            },
        }

        newPerson = True
        while True:
            if newPerson:
                nChat = input('Введите номер чата: ')
                inp = input('Ваше сообщение: ')
                if inp == 'exit':
                    break
                newPerson = False
            else:
                inp = input('Ваше сообщение(N для выхода): ')
                if inp == 'N':
                    self.goChat()
            msg['msg'] = inp
            msg['nChat'] = nChat
            self.oSocket.send(pickle.dumps(msg))
            self.logger.debug(f'Отправлено сообщение серверу: \n{msg}')
            data = self.oSocket.recv(1024)
            response_dict = pickle.loads(data)
            self.logger.debug(f'Получено сообщение от сервера: \n{response_dict}')

    @decorLog
    def getLoginPass(self):
        login = input('Ведите логин или N для выхода: ')
        if login[0] == 'N':
            self.oSocket.close()
        else:
            pswrd = input('Ведите пароль или N для выхода: ')
            if pswrd == 'N':
                self.oSocket.close()
            else:
                self.loginPass.append(login)
                self.loginPass.append(pswrd)
                self.authorization()


    #@decorLog
    def authorization(self):
        ###### 2 ######
        #self.oSocket.connect((self.params.addr, self.params.port))
        msg = {
            'action': 'authorization',
            'time': str(time.time()),
            'user': {
                'login': self.loginPass[0],
                'pass': self.loginPass[1],
            },
        }
        self.oSocket.send(pickle.dumps(msg))
        self.logger.debug(f'Отправлено сообщение серверу: \n{msg}')
        data = self.oSocket.recv(1024)
        response_dict = pickle.loads(data)
        self.logger.debug(f'Получено сообщение от сервера: \n{response_dict}')
        if response_dict['response'] == 200:
            self.clientPermissions.append(True)
            self.goChat()

        if response_dict['response'] == 409:
            print(response_dict['alert'])
            self.clientPermissions.append(False)
            self.oSocket.close()
        if response_dict['response'] == 402:
            self.getLoginPass()
        # self.oSocket.close()


def main():
    logger = logging.getLogger('client_log')
    logger.debug(f'Запуск client02.py')
    try:
        parser = createParser()
        namespace = parser.parse_args()

        client = Client(namespace, logger)
        # if namespace.survey:
        #     client.serverSurvey()
        # elif namespace.authorize:
        #     client.authorization(namespace)
        # else:
        #     logger.debug(f'Не выбран параметр')
        client.serverSurvey()

    except Exception as e:
        logger.error(e)


if __name__ == '__main__':
    main()