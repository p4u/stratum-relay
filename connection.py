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
import select
import queue
import log
import manager
import time

class Client():
	def __init__(self,host,port):
		self.host = host
		self.ip = socket.gethostbyname(host)
		self.port = int(port)
		self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.conn.setblocking(1)

	def connect(self):
		self.conn.connect((self.ip,self.port))
		return self.conn

	def send(self,msg):
		self.conn.sendall(msg.encode())
		data = self.conn.recv(1024).decode()
		return data

	def close(self):
		self.conn.close()

class Server():
	def __init__(self,host,port):
		self.host = host
		self.port = int(port)
		self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.conn.setblocking(1)
		self.log = log.Log('listener')
		self.conn.bind((self.host, self.port))

	def listen(self):
		self.log.info('listening on %s:%s' %(self.host,self.port))
		self.conn.listen(50)
		current_conn, addr = self.conn.accept()
		current_conn.setblocking(1)
		return current_conn

	def recive(self):
		data = self.current_conn.recv(1024).decode()
		return data

	def send(self,msg):
		self.current_conn.sendall(msg.encode())
		data = self.current_conn.recv(1024).decode()
		return data

	def close(self):
		self.conn.shutdown(0)
		self.conn.close()

READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
READ_WRITE = READ_ONLY | select.POLLOUT
TIMEOUT = 1000
	
class Proxy():
	def __init__(self,pool):
		self.pool = pool
		self.miners_queue = {}
		self.pool_queue = queue.Queue()
		self.pool_queue.put("")
		self.pool.setblocking(0)	
		self.log = log.Log('proxy')
		self.manager = manager.Manager()
		self.new_conns = []

	def add_miner(self,connection):
		self.miners_queue[connection.fileno()] = connection
		self.new_conns.append(connection)
		self.pool_queue.put(connection.recv(1024).decode())
		connection.setblocking(0)

	def miners_broadcast(self,msg):
		for q in self.miners_queue.keys():
			self.miners_queue[q].put(msg)

	def close(self):
		for s in self.fd_to_socket.keys():
			self.fd_to_socket[s].shutdown(0)
			self.fd_to_socket[s].close()
			
	def start(self):
		poller = select.poll()
		poller.register(self.pool, READ_WRITE)
		self.fd_to_socket = { self.pool.fileno():self.pool }

		while True:
			if len(self.new_conns) > 0:
				self.fd_to_socket[self.new_conns[0].fileno()] = self.new_conns[0]
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
							self.log.debug("got msg from pool: %s" %data)
							self.miners_broadcast(self.manager.process(data))
						else:
							self.log.debug("got msg from miner: %s" %data)
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
								self.log.error("socket was not registered, wtf?")
							del self.fd_to_socket[fd]
							del self.miners_queue[fd]
							s.shutdown(0)
							s.close()

				# Socket is ready for writing
				elif flag & select.POLLOUT:
					if self.pool is s:
						if not self.pool_queue.empty():
							msg = self.pool_queue.get()
							self.log.debug("sending msg to pool: %s" %msg)
							s.sendall(msg.encode())
					
					else:
						if not self.miners_queue[fd].empty():
							msg = self.miners_queue[fd].get()
							self.log.debug("sending msg to miner: %s" %msg)
							s.sendall(msg.encode())

				else:
					self.log.error("something weird!")

				time.sleep(0.1)
