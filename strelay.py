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
import proxy as Proxy
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
    for c in proxies.list():
        proxies.del_proxy(c)
    time.sleep(1)
    sys.exit(0)


shutdown = False
log = Log.Log('main')
signal.signal(signal.SIGINT, signal_handler)

# Share statistics module
shares = share_stats.Shares()

# Start proxy cleaner thread
proxies = Proxy.ProxyDB()
t = threading.Thread(target=proxies.cleaner, args=[])
t.daemon = True
t.start()

# Start control thread
controller = control.Control(proxydb=proxies, sharestats=shares)
t = threading.Thread(target=controller.start, args=[])
t.daemon = True
t.start()

# Start proxy cleaner
#t = threading.Thread(target=check_proxy_threads, args=[proxies])
#t.daemon = True
# t.start()

# Start listening for incoming connections
server_listen = connection.Server("0.0.0.0", 3334)

while not shutdown:
    # Wait for client connection
    miner = server_listen.listen()
    pool_connection = connection.Client(
        controller.poolmap['pool'], controller.poolmap['port'])
    pool = pool_connection.connect()
    proxy = Proxy.Proxy(pool, sharestats=shares)
    proxy.add_miner(miner)
    t = threading.Thread(target=proxy.start, args=[])
    t.daemon = True
    t.start()
    proxies.add_proxy(proxy, t)
