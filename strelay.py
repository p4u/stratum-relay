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
import json
import string
import time
import signal
import sys
import manager
import connection
import threading
import log as Log
import share_stats
import control

def signal_handler(signal, frame):
    shutdown = True
    controller.shutdown = True
    log.info('exit')
    if pool:
        pool.shutdown(0)
        pool.close()
    for c in connections:
        if c: c.close()
    time.sleep(1)
    sys.exit(0)

shutdown = False
log = Log.Log('main')
shares = share_stats.Shares()
signal.signal(signal.SIGINT, signal_handler)

# Start control thread
controller = control.Control(sharestats=shares)
t = threading.Thread(target=controller.start, args=[])
t.daemon = True
t.start()

# Start listening for incoming connections
server_listen = connection.Server("0.0.0.0", 3334)
connections = []

while not shutdown:
    # Wait for client connection
    miner = server_listen.listen()
    pool_connection = connection.Client("stratum.nicehash.com", 3333)
    pool = pool_connection.connect()
    proxy = connection.Proxy(pool,sharestats=shares)
    proxy.add_miner(miner)
    connections.append(proxy)
    t = threading.Thread(target=proxy.start, args=[])
    t.daemon = True
    t.start()
