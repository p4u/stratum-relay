'''
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
'''

import socket
import log
import manager
import time


class Client():

    def __init__(self, host, port):
        self.host = host
        self.ip = socket.gethostbyname(host)
        self.port = int(port)
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.setblocking(1)

    def connect(self):
        self.conn.connect((self.ip, self.port))
        return self.conn

    def send(self, msg):
        self.conn.sendall(msg.encode())
        data = self.conn.recv(1024).decode()
        return data

    def close(self):
        self.conn.close()


class Server():

    def __init__(self, host, port):
        self.host = host
        self.port = int(port)
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.setblocking(1)
        self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.log = log.Log('listener')
        self.conn.bind((self.host, self.port))

    def listen(self):
        self.log.info('listening on %s:%s' % (self.host, self.port))
        self.conn.listen(50)
        try:
            current_conn, addr = self.conn.accept()
        except InterruptedError:
            return False
        current_conn.setblocking(1)
        return current_conn

    def recive(self):
        data = self.current_conn.recv(1024).decode()
        return data

    def send(self, msg):
        self.current_conn.sendall(msg.encode())
        data = self.current_conn.recv(1024).decode()
        return data

    def close(self):
        self.conn.shutdown(0)
        self.conn.close()
