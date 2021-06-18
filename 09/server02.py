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

class Server:
    __slots__ = [
        'serverOFF',
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
        self.serverOFF = False

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
                200: {'alert': 'Готов к подключению'},
                503: {'alert': 'Сервис недоступен'},
                501: {'alert': 'У меня нет ответа на этот запрос'},
            },
            'registration': {
                200: {'alert': 'Пользователь создан'},
                409: {'alert': 'Логин занят'},
            },
            'chat': {
                'response': 200,
            },
            'authorization': {
                200: {'alert': 'OK'},
                409: {'alert': 'Неверный пароль'},
                401: {'alert': 'Не авторизован'},
            },
            'create_chat': {
                200: {'alert': 'OK'},
                409: {'alert': 'Чат с таким именем уже существует'},
            },
        }

    @decor_log
    def read_requests(self, r_clients, all_clients)->{}:
        '''Чтение запросов из списка клиентов'''
        responses = {} #Словарь ответов сервера {сокет: запрос}
        for sock in r_clients:
            try:
                data = pickle.loads(sock.recv(1024))
                responses[sock] = data
                self.logger.debug(f'Получили сообщение от клиента{data}')
            except:
                self.logger.debug(f'Клиент {sock.fileno()} {sock.getpeername()} отключился')
                all_clients.remove(sock)
            return responses

    @decor_log
    def response_to_client(self, client, params):
        response = self.response[params[0]][params[1]]
        response['time'] = str(time.time())
        response['action'] = params[0]
        response['response'] = params[1]
        client.send(pickle.dumps(response))
        self.logger.debug(f'оправлено сообщение клиенту:\n'
                          f'{response}')

    @decor_log
    def registration(self, request)->int:
        try:
            #clients = {}
            with open('Users.json', 'r') as rf:
                clients = json.load(rf)
                if request['login'] in clients:
                    return 409
                else:
                    with open('Users.json', 'w') as wf:
                        clients[request['login']] = request['pswrd']
                        json.dump(clients, wf)
                    return 200
        except Exception as e:
            self.logger.error('REGISTRATION', e)

    @decor_log
    def authorization(self, request)->int:
        try:
            with open('Users.json', 'r') as rf:
                clients = json.load(rf)
                if request['login'] in clients:
                    if request['pswrd'] == clients[request['login']]:
                        return 200
                    else:
                        return 409
                else:
                    return 401
        except Exception as e:
            self.logger.error('AUTHORIZATION', e)

    @decor_log
    def create_chat(self, request)->int:
        try:
            with open('chats.json', 'r') as rf:
                chats = json.load(rf)
            if (request['chat_name'], request['chat_creator']) in chats:
                return 409
            else:
                return 200
        except Exception as e:
            self.logger.error('CREATE_CHAT', e)

    @decor_log
    def conditions(self, requests, w_clients, all_clients):
        for sock in w_clients:
            if sock in requests:
                try:
                    # Подготовить и отправить ответ сервера
                    if not self.serverOFF:
                        action = requests[sock]['action']
                        if action in self.response:
                            if action == 'connect':
                                self.response_to_client(sock, ['connect', 200])
                            if action == 'registration':
                                i = self.registration(requests[sock])
                                self.response_to_client(sock, ['registration', i])
                            if action == 'authorization':
                                i = self.authorization(requests[sock])
                                self.response_to_client(sock, ['authorization', i])
                            if action == 'create_chat':
                                i = self.create_chat(requests[sock])
                                self.response_to_client(sock, ['create_chat', i])
                        else:
                            self.response_to_client(sock, ['connect', 501])
                    else:
                        self.response_to_client(sock, ['connect', 503])
                except: #Сокет недоступен, клиент отключился
                    self.logger.debug(f'Клиент {sock.fileno()} {sock.getpeername()} отключился')
                    sock.close()
                    all_clients.remove(sock)

    @decor_log
    def client_listener(self):
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
                wait = 5
                r = []
                w = []
                try:
                    r, w, e = select.select(self.clientsOnline, self.clientsOnline, [], wait)
                except:
                    #pass  # Ничего не делать, если какой-то клиент отключился
                    self.clientsOnline.pop(conn)
                    print(self.clientsOnline)
                requests = self.read_requests(r, self.clientsOnline)  # Сохраним запросы клиентов
                if requests:
                    self.conditions(requests, w, self.clientsOnline)  # Выполним отправку ответов клиентам

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