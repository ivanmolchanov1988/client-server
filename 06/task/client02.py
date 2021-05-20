# -*- coding: utf-8 -*-

from datetime import datetime
import time
from socket import *
import pickle
import argparse
import logging
from functools import wraps
import inspect
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
    parser.add_argument('-a', '--addr', default='')
    parser.add_argument('--authorize', default=False, type=str)
    parser.add_argument('--login', type=str)
    parser.add_argument('--pswrd', type=str)
    parser.add_argument('--survey', default=False, type=bool)
    return parser

class Client:
    """docstring"""

    def __init__(self, paramsNameSpace, logger):
        """Constructor"""
        self.logger = logger
        self.logger.debug(f'Создаём экземпляр Client')

        self.oSocket = socket(AF_INET, SOCK_STREAM)
        self.params = paramsNameSpace

    @decorLog
    def serverSurvey(self):
        """Listener"""
        ###### 1 ######
        self.oSocket.connect((self.params.addr, self.params.port))
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
        self.oSocket.close()

    @decorLog
    def authorization(self, namespace):
        ###### 2 ######
        self.oSocket.connect((self.params.addr, self.params.port))
        msg = {
            'action': 'authorization',
            'time': str(time.time()),
            'user': {
                'login': namespace.login,
                'pass': namespace.pswrd,
            },
        }
        self.oSocket.send(pickle.dumps(msg))
        self.logger.debug(f'Отправлено сообщение серверу: \n{msg}')
        data = self.oSocket.recv(1024)
        response_dict = pickle.loads(data)
        self.logger.debug(f'Получено сообщение от сервера: \n{response_dict}')
        # self.oSocket.close()




def main():
    logger = logging.getLogger('client_log')
    logger.debug(f'Запуск client02.py')
    try:
        parser = createParser()
        namespace = parser.parse_args()

        client = Client(namespace, logger)
        if namespace.survey:
            client.serverSurvey()
        elif namespace.authorize:
            client.authorization(namespace)
        else:
            logger.debug(f'Не выбран параметр')

    except Exception as e:
        logger.error(e)


if __name__ == '__main__':
    main()