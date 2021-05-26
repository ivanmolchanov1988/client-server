# -*- coding: utf-8 -*-

import select
from socket import socket, AF_INET, SOCK_STREAM
import inspect
import time
import pickle
import argparse
import logging
from functools import wraps
import json
import log.server_log_config

###### Декоратор ######
def decor_log(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        logger = logging.getLogger('client.log')
        logger.debug(f'{func.__name__} вызвана из '
                     f'{inspect.stack()[1][3]}')
        res = func(*args, **kwargs)
        return res
    return decorated
############################


###### Для параметров ######
def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=7777, type=int)
    parser.add_argument('-a', '--address', default='')
    return parser


### CLASS begin ###
class Server:
    __slots__ = [
        'params_namespace',
        'logger',
        'clients_online',
        'oSocket',
        'response',
        'clients',
        'clientsOnline',
        'oChats',
    ]
    def __init__(self, params_namespace, logger):
        self.logger = logger
        self.logger.debug(f'Создали экземпляр Server')

        self.oSocket = socket(AF_INET, SOCK_STREAM)
        self.oSocket.bind((params_namespace.address, params_namespace.port))
        self.oSocket.listen(3)
        self.oSocket.settimeout(0.2)  # Таймаут для операций с сокетом
        self.clients = {}
        with open("Users.json", "r") as rf:
            self.clients = json.load(rf)
        self.clientsOnline = []
        self.oChats = {}
        with open("chats.json", "r") as rf:
            self.oChats = json.load(rf)
        self.response = {
            'connect': {
                'response': 200,
                'alert': 'Готов к подключению',
            },
            'authorization': {
                'OK': {
                    'response': 200,
                    'alert': 'Авторизация прошла успешно',
                },
                'occupied': {
                    'response': 409,
                    'alert': 'Кто-то уже подключен под Вашим именем и паролем'
                },
                'passNmae': {
                    'response': 402,
                    'alert': 'Пользователь с таким именем уже зарегистрирован или Вы ввели не верный пароль'
                },
            },
            'chat': {
                'response': 200,
            },
        }

    @decor_log
    def chats(self, client, data, condition) -> []:
        response = {}
        with open("chats.json", "r") as rf:
            self.oChats = json.load(rf)
        self.logger.debug(f'Клиент в чатах:\n{client}')
        @decor_log
        def createChat(write, rf, user):
            chatData = {
                    'users': [write['user']['login']],
                    'msg': [
                        {
                            'user': write['user']['login'],
                            'msg': write['msg']
                        },
                    ],
                }
            with open("chats.json", "w") as wf:
                rf[write['nChat']] = chatData
                json.dump(rf, wf)

        if data['nChat'] not in self.oChats.keys():
            createChat(data, self.oChats, client)
        else:
            if data['user']['login'] not in self.oChats[data['nChat']]['users']:
                self.oChats[data['nChat']]['users'].append(data['user']['login'])
            self.oChats[data['nChat']]['msg'].append({'user': data['user']['login'],
                                                      'msg': data['msg']})
            with open("chats.json", "w") as wf:
                json.dump(self.oChats, wf)

        return self.oChats[data['nChat']]['msg']

    @decor_log
    def client_listener(self):
        @decor_log
        def read_requests(r_clients, all_clients):
            """ Чтение запросов из списка клиентов
            """
            responses = {}  # Словарь ответов сервера вида {сокет: запрос}
            for sock in r_clients:
                try:
                    data = pickle.loads(sock.recv(1024))
                    responses[sock] = data
                except:
                    self.logger.debug(f'Клиент {sock.fileno()} {sock.getpeername()} отключился')
                    all_clients.remove(sock)
            return responses

        @decor_log
        def write_responses(requests, w_clients, all_clients):

            @decor_log
            def response_to_client(client, response, condition, chat=None):
                response['time'] = str(time.time())
                response['action'] = condition
                response['chat'] = chat
                client.send(pickle.dumps(response))
                self.logger.debug(f'Отправлено сообщение клиенту:\n'
                                  f'{response}')

            @decor_log
            def authorization(client, data, condition):
                def addUserInDB(data):
                    with open("Users.json", "w") as wf:
                        json.dump(data, wf)

                user = data['user']
                oLen = len([i for i in self.clients.keys() if i == user['login']])
                params = [client, self.response[condition], condition]
                if oLen == 1:
                    if user['login'] in self.clients.keys() and user['pass'] == self.clientsOnline[user['login']]:
                        params[1] = params[1]['OK']
                        response_to_client(*params)
                    elif user['login'] in self.clientsOnline:
                        self.logger.debug(f'Кто-то подключается второй раз!')
                        params[1] = params[1]['occupied']
                        response_to_client(*params)
                    elif user['login'] in self.clients.keys():
                        self.logger.debug(f'Клиент уже зарегистрирован')
                        params[1] = params[1]['passName']
                        response_to_client(*params)
                if oLen == 0:
                    self.clients[user['login']] = user['pass']
                    #self.clientsOnline.append(user['login'])
                    addUserInDB(self.clients)
                    self.logger.debug(f'Добавили нового пользователя в {self.clients}')
                    params[1] = params[1]['OK']
                    response_to_client(*params)

            #write_responses#
            for sock in w_clients:
                if sock in requests:
                    try:
                        # Подготовить и отправить ответ сервера
                        if requests[sock]['action'] == 'connect':
                            self.logger.debug(f'Клиент просит подключения:\n{requests[sock]}')
                            response_to_client(sock, self.response[requests[sock]['action']], requests[sock]['action'])
                            # client.close()

                        if requests[sock]['action'] == 'authorization':
                            self.logger.debug(f'Клиент пробует авторизоваться:\n{requests[sock]}')
                            authorization(sock, requests[sock], requests[sock]['action'])

                        if requests[sock]['action'] == 'chat':
                            self.logger.debug(f'Клиент что-то пишет:\n{requests[sock]}')
                            respChat = self.chats(sock, requests[sock], requests[sock]['action'])
                            response_to_client(sock, self.response[requests[sock]['action']], requests[sock]['action'], respChat)

                        # Эхо-ответ сделаем чуть непохожим на оригинал
                        #sock.send(resp.upper())
                    except:  # Сокет недоступен, клиент отключился
                        self.logger.debug(f'Клиент {sock.fileno()} {sock.getpeername()} отключился')
                        sock.close()
                        all_clients.remove(sock)


        '''Слушатель'''
        while True:
            try:
                conn, addr = self.oSocket.accept()  # Проверка подключений
            except OSError as e:
                pass  # timeout вышел
            else:
                self.clientsOnline.append(conn)
            finally:
                # Проверить наличие событий ввода-вывода
                wait = 10
                r = []
                w = []
                try:
                    r, w, e = select.select(self.clientsOnline, self.clientsOnline, [], wait)
                except:
                    pass  # Ничего не делать, если какой-то клиент отключился

                requests = read_requests(r, self.clientsOnline)  # Сохраним запросы клиентов
                if requests:
                    write_responses(requests, w, self.clientsOnline)  # Выполним отправку ответов клиентам


#### CLASS end ####

###### Запускаем ######
def main():
    logger = logging.getLogger('server_log')
    logger.debug('Запуск server02.py')
    try:
        parser = create_parser()
        namespace = parser.parse_args()

        server = Server(namespace, logger)
        server.client_listener()
    except Exception as e:
        logger.error(e)




if __name__ == '__main__':
    main()
    #mainloop()
    ### только для урока/примера - как получить имя родительской функции