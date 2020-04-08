# Сервер

import asyncio
from asyncio import transports
from typing import Optional


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")

                # Проверяем, что логин еще не занят. Если занят, то разрываем соединение
                for client in self.server.clients:
                    if self.login == client.login and self != client:
                        self.transport.write(f"Логин {self.login} занят, попробуйте другой\r\n".encode())
                        print(f"{self.login} неверное имя пользователя")
                        self.transport.close()
                        return
                self.transport.write(f"Привет, {self.login}!\r\n".encode())

                # посылаем историю сообщений подключенному клиенту
                self.send_history()
            else:
                self.transport.write("Неправильный логин\r\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}"
        if len(self.server.messages) == 10:
            self.server.messages.pop(0)
        self.server.messages.append(message)

        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self):
        for message in self.server.messages:
            self.transport.write(message.encode())


class Server:
    clients: list
    messages: list

    def __init__(self):
        self.clients = []
        self.messages = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
