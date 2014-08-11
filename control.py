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


import connection
import log as Log
import share_stats
import time
import json

class Control(object):
    def __init__(self, sharestats = None):
        self.proxies = []
        self.shares = sharestats
        self.rm_shares = {}
        self.shutdown = False
        self.log = Log.Log("control")

    def add_proxy(self,proxy):
        self.proxies.append(proxy)
    
    def del_proxy(self,proxy):
        i = 0
        for p in proxies:
            if p is proxy:
                del self.proxies[i]
            i += 1

    def get_shares(self):
        shares = {}
        response = {}
        for sh in self.shares.shares.keys():
            acc, rej = self.shares.shares[sh]
            if acc + rej > 0:
                shares[sh] = {'accepted': acc, 'rejected': rej}
        self.log.debug('Shares sent: %s' % shares)
        response['shares'] = shares
        response['error'] = False
        for sh in shares.keys():
            if sh in self.rm_shares:
                rm_shares[sh]['accepted'] += shares[sh]['accepted']
                rm_shares[sh]['rejected'] += shares[sh]['rejected']
            else:
                rm_shares[sh] = shares[sh]
        return json.dumps(response, ensure_ascii=True)
 
    def clean_shares(self):
        response = {}
        self.log.debug('shares to remove: %s' % self.rm_shares)
        for sh in self.rm_shares.keys():
            stp.sharestats.shares[sh][0] -= self.rm_shares[sh]['accepted']
            stp.sharestats.shares[sh][1] -= self.rm_shares[sh]['rejected']
        self.rm_shares = {}
        response['error'] = False
        return json.dumps(response, ensure_ascii=True)
 
    def start(self):
        while not self.shutdown:
            server_listen = connection.Server("127.0.0.1", 2222)
            command = server_listen.listen()
            data = command.recv(2048).decode()
            try:
                jdata = json.loads(data)
                query = jdata['query']
                execute = True
            except:
                self.log.error("cannot understand control command: %s" %data)
                execute = False
            if execute:
                self.log.info("executing query %s" %query)
                if query == "getshares":
                    response = self.get_shares()
                elif query == "cleanshares":
                    response = self.clean_shares()
                else:
                    response = str({'error': True})
                command.sendall(response.encode())
            else:
                command.sendall(str({'error': True}).encode())

            command.shutdown(0)
            command.close()
            time.sleep(0.5)
                
        
        