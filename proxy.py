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

import threading
import time
import log
import select
import socket
import queue
import manager

READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
READ_WRITE = READ_ONLY | select.POLLOUT
TIMEOUT = 1000


class ProxyDB(object):

    def __init__(self):
        self.db = {}  # proxy_object_id -> [proxy,thread]
        self.shutdown = False
        self.log = log.Log("proxy")

    def add_proxy(self, proxy, thread):
        self.db[id(proxy)] = [proxy, thread]

    def del_proxy(self, proxy):
        if proxy and not proxy.shutdown:
            proxy.close()
        if id(proxy) in self.db:
            del self.db[id(proxy)]

    def list(self):
        l = []
        for p in self.db.keys():
            l.append(self.db[p][0])
        return l

    def cleaner(self):
        while not self.shutdown:
            to_remove = []
            for p in self.db.keys():
                # if proxy is already mark as shutdown
                if self.db[p][0].shutdown:
                    to_remove.append(p)
                # else if thread is dead
                elif not self.db[p][1].isAlive():
                    try:
                        self.db[p][1]._Thread__stop()
                    except:
                        self.log.error("cannot stop thread!")
                    to_remove.append(p)
            for p in to_remove:
                log.info("removing proxy %s" % p)
                del self.db[p]
            time.sleep(5)


class Proxy(object):

    def __init__(self, pool, sharestats=None):
        self.pool = pool
        self.miners_queue = {}
        self.pool_queue = queue.Queue()
        self.pool_queue.put("")
        self.pool.setblocking(0)
        self.log = log.Log('proxy')
        self.new_conns = []
        self.shares = sharestats
        self.manager = manager.Manager(sharestats=self.shares)
        self.shutdown = False

    def get_info(self):
        try:
            info = {"pool": self.pool.getpeername()}
            info["miners"] = []
            for s in self.fd_to_socket.keys():
                sock = self.fd_to_socket[s]
                if sock is not self.pool:
                    info["miners"].append(sock.getpeername())
        except:
            self.log.error("some error while fetching proxy information")
            info = {}
        return info

    def add_miner(self, connection):
        if connection:
            self.miners_queue[connection.fileno()] = connection
            self.new_conns.append(connection)
            self.pool_queue.put(connection.recv(1024).decode())
            connection.setblocking(0)

    def miners_broadcast(self, msg):
        for q in self.miners_queue.keys():
            self.miners_queue[q].put(msg)

    def close(self):
        self.shutdown = True
        for s in self.fd_to_socket.keys():
            try:
                self.fd_to_socket[s].shutdown(0)
                self.fd_to_socket[s].close()
            except:
                pass

    def start(self):
        poller = select.poll()
        poller.register(self.pool, READ_WRITE)
        self.fd_to_socket = {self.pool.fileno(): self.pool}

        while not self.shutdown:
            if self.manager.force_exit:
                self.close()
                return False

            if len(self.new_conns) > 0:
                self.fd_to_socket[
                    self.new_conns[0].fileno()] = self.new_conns[0]
                poller.register(self.new_conns[0], READ_WRITE)
                self.miners_queue[self.new_conns[0].fileno()] = queue.Queue()
                del self.new_conns[0]

            events = poller.poll(TIMEOUT)
            for fd, flag in events:
                # Retrieve the actual socket from its file descriptor
                s = self.fd_to_socket[fd]

                # Socket is ready to read
                if flag & (select.POLLIN | select.POLLPRI):
                    data = s.recv(4096).decode()
                    if data:
                        if self.pool is s:
                            self.log.debug("got msg from pool: %s" % data)
                            self.miners_broadcast(self.manager.process(data))
                        else:
                            self.log.debug("got msg from miner: %s" % data)
                            self.pool_queue.put(self.manager.process(data))
                    else:
                        if self.pool is s:
                            self.log.error("connection with pool lost!")
                            self.close()
                            return False
                        else:
                            self.log.error("connection with worker lost!")
                            try:
                                poller.unregister(s)
                            except KeyError:
                                self.log.error(
                                    "socket was not registered, wtf?")
                            del self.fd_to_socket[fd]
                            del self.miners_queue[fd]
                            s.shutdown(0)
                            s.close()

                # Socket is ready for writing
                elif flag & select.POLLOUT:
                    if self.pool is s:
                        if not self.pool_queue.empty():
                            msg = self.pool_queue.get()
                            self.log.debug("sending msg to pool: %s" % msg)
                            s.sendall(msg.encode())

                    else:
                        if not self.miners_queue[fd].empty():
                            msg = self.miners_queue[fd].get()
                            self.log.debug("sending msg to miner: %s" % msg)
                            s.sendall(msg.encode())

                else:
                    self.log.debug("something weird!")

                time.sleep(0.1)
