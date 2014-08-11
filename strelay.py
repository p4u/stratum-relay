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


def signal_handler(signal, frame):
    log.info('exit')
    pool.shutdown(0)
    pool.close()
    for c in connections:
        c[1].shutdown(0)
        c[1].close()
    for thread in threading.enumerate():
        if thread.isAlive():
            thread._Thread__stop()
    sys.exit(0)

log = Log.Log('main')
signal.signal(signal.SIGINT, signal_handler)
server_listen = connection.Server("0.0.0.0", 3334)
connections = []

while True:
    miner = server_listen.listen()
    pool_connection = connection.Client("stratum.nicehash.com", 3333)
    pool = pool_connection.connect()
    proxy = connection.Proxy(pool)
    proxy.add_miner(miner)
    t = threading.Thread(target=proxy.start, args=[])
    t.daemon = True
    t.start()
    connections.append([t, miner])
