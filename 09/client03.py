# -*- coding: utf-8 -*-

from datetime import datetime
import time
from socket import *
import pickle
import argparse
import logging
from functools import wraps
import inspect
#from numpy import mean
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
    return parser

class Client:
    """docstring"""
    __slots__ = [
        'CONNECT',
        'logger',
        'oSocket',
        'params',
        'loginPass',
        'msg',

    ]

    def __init__(self, paramsNameSpace, logger):
        """Constructor"""
        self.logger = logger
        self.logger.debug(f'Создаём экземпляр Client')

        self.oSocket = socket(AF_INET, SOCK_STREAM)
        self.params = paramsNameSpace

        self.loginPass = {'login': None,
                          'pswrd': None}

        self.msg = {
            'connect':{
                'alert': 'Please connect',
            },
            'registration': {
                'alert': 'I need registration',
            },
            'authorization': {
                'alert': 'I need registration'
            },
            'create_chat': {
                'alert': 'Create new chat, please'
            },
        }

    @decorLog
    def sendMSG(self, action, loginPass = None, chat = None)->bool:
        try:
            msg = self.msg[action]
            if loginPass != None:
                msg['login'] = loginPass[0]
                if action == 'registration' or action == 'authorization':
                    msg['pswrd'] = loginPass[1]
            if chat != None:
                msg['chat_name'] = chat[0]
                msg['chat_creator'] = chat[1]
            oTime = str(time.time())
            msg['time'] = oTime
            msg['action'] = action
            self.oSocket.send(pickle.dumps(msg))
            self.logger.debug(f'Отправлено сообщение серверу: \n{msg}')
            return True
        except Exception as e:
            self.logger.error('SENDMSG', e)

    @decorLog
    def receiver(self)->{}:
        try:
            data = self.oSocket.recv(1024)
            response_dict = pickle.loads(data)
            self.logger.debug(f'Получено сообщение от сервера: \n{response_dict}')
            return response_dict
        except Exception as e:
            self.logger.error('RECEIVER', e)

    @decorLog
    def conditions(self):
        try:
            var = int(input('Выберете вариант из списка:\n'
                            '1: Создать новый чат\n'
                            '2: Создать новый диалог\n'
                            ''))
            if var == 1:
                chat = self.create_chat()
                self.sendMSG(action = 'create_chat', chat = chat)
        except Exception as e:
            self.logger.error('CONDITIONS', e)

    @decorLog
    def connect(self)->bool:
        try:
            action = 'connect'
            self.oSocket.connect((self.params.address, self.params.port))
            if self.sendMSG(action) and self.receiver()['response'] == 200:
                return True
            else:
                return False
        except Exception as e:
            self.logger.error('CONNECT', e)

    @decorLog
    def reg(self):
        try:
            lp = input('Напишите Логин и Пароль через пробел, или N для выхода\n')
            if lp == 'N':
                self.aut()
            else:
                if len(lp.split()) == 2:
                    action = 'registration'
                    if self.sendMSG(action, lp.split()):
                        response = self.receiver()
                        if response['response'] == 200:
                            login = lp.split()[0]
                            self.aut(login)
                        if response['response'] == 409:
                            print('Логин занят')
                            self.reg()
                    else:
                        print('Что-то пошло не так')
                        self.reg()
                else:
                    print('Введите корректные данные!')
                    self.reg()
        except Exception as e:
            self.logger.error('REG', e)

    @decorLog
    def create_chat(self)->str:
        create_chat_name = input('Введите название чата\n')
        creator = self.loginPass['login']
        result = (create_chat_name, creator)
        return result

    @decorLog
    def aut(self, login=None)->bool:
        try:
            #lp = []
            if login == None:
                response = input('Введите через пробел Логин и Пароль. Если хотите зарегистрироваться, '
                             'напишите R\n')
                lp = response.split()
            else:
                response = input('Введите Пароль. Если хотите зарегистрироваться, '
                                 'напишите R\n')
                lp = [login, response]
            if response == 'R':
                self.reg()
            else:
                if len(lp) == 2:
                    action = 'authorization'
                    if self.sendMSG(action, lp):
                        if self.receiver()['response'] == 200:
                            return True
                        else:
                            if self.receiver()['response'] == 409:
                                print('Неверный пароль')
                                self.aut(lp[0])
                            if self.receiver()['response'] == 401:
                                print('Вы не авторизованы')
                                self.reg()
                    else:
                        print('Что-то пошло не так, попробуйте ещё раз')
                        self.aut()
                else:
                    print('Введите корректные данные!')
                    self.aut()
        except Exception as e:
            self.logger.error('AUT', e)

    @decorLog
    def serverSurvey(self):
        """Listener"""
        try:
            if self.connect():
                if self.aut():
                    self.conditions()
                else:
                    print('Что-то пошло не так, попробуйте ещё раз')
                    self.aut()
            else:
                print('Сервер не отвечает')
                self.serverSurvey()
        except Exception as e:
            self.logger.error('SERVERSURVEY', e)

def main():
    logger = logging.getLogger('client_log')
    logger.debug(f'Запуск client02.py')
    try:
        parser = createParser()
        namespace = parser.parse_args()

        client = Client(namespace, logger)
        client.serverSurvey()

    except Exception as e:
        logger.error(e)


if __name__ == '__main__':
    main()