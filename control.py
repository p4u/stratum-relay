import connection
import manager
import log as Log
import share_stats
import time
import json
import copy
import proxy


class Control(object):

    poolmap = {
        "pool": "stratum.nicehash.com",
        "port": 3333,
        "user": None,
        "pass": "x",
        "backup": "us.clevermining.com",
        "backup_port": "3333"}

    def __init__(self, proxydb=None, sharestats=None):
        self.proxies = proxydb
        self.shares = sharestats
        self.rm_shares = {}
        self.shutdown = False
        self.log = Log.Log("control")
        self.listen_ip = "127.0.0.1"
        self.listen_port = 2222
        self.manager = manager.Manager()

    def get_info(self):
        info = {}
        i = 0
        for p in self.proxies.list():
            info["proxy" + str(i)] = p.get_info()
            i += 1
        return info

    def reconnect_all(self):
        # Send reconnect order to miners
        self.log.info("sending reconnect to all miners")
        proxy_list = self.proxies.list()
        for p in proxy_list:
            p.miners_broadcast(self.manager.get_reconnect())
        # Wait two seconds to let the miners get the order
        time.sleep(3)
        # Close sockets
        for p in proxy_list:
            try:
                p.close()
            except:
                pass
            self.proxies.del_proxy(p)
        tmp_proxies = []

    def set_pool(self, pool, port, user=None, passw=None, force=False):
        self.poolmap["pool"] = pool
        self.poolmap['port'] = int(port)
        if user:
            self.poolmap["user"] = user
        if passw:
            self.poolmap["pass"] = passw
        if force:
            self.reconnect_all()

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
                self.rm_shares[sh]['accepted'] += shares[sh]['accepted']
                self.rm_shares[sh]['rejected'] += shares[sh]['rejected']
            else:
                self.rm_shares[sh] = shares[sh]
        return json.dumps(response, ensure_ascii=True)

    def clean_shares(self):
        response = {}
        self.log.debug('shares to remove: %s' % self.rm_shares)
        for sh in self.rm_shares.keys():
            self.shares.shares[sh][0] -= self.rm_shares[sh]['accepted']
            self.shares.shares[sh][1] -= self.rm_shares[sh]['rejected']
        self.rm_shares = {}
        response['error'] = False
        return json.dumps(response, ensure_ascii=True)

    def start(self):
        server_listen = connection.Server(self.listen_ip, self.listen_port)
        while not self.shutdown:
            response = {}
            command = server_listen.listen()
            data = command.recv(2048).decode()
            try:
                jdata = json.loads(data.replace("'", '"'))
                query = jdata['query']
                execute = True
            except:
                self.log.error("cannot understand control command: %s" % data)
                execute = False
            if execute:
                self.log.info("executing query %s" % query)

                if query == "getshares":
                    response = self.get_shares()

                elif query == "cleanshares":
                    response = self.clean_shares()

                elif query == "getinfo":
                    response = json.dumps(
                        str(self.get_info()), ensure_ascii=True)

                elif query == 'setpool':
                    host = jdata['host'] if 'host' in jdata else None
                    port = jdata['port'] if 'port' in jdata else None
                    user = jdata['user'] if 'user' in jdata else None
                    passw = jdata['passw'] if 'passw' in jdata else None
                    response = str({"error": False})
                    if host and port and user and passw:
                        self.set_pool(host, port, user=user, passw=passw)
                    elif host and port and user:
                        self.set_pool(host, port, user=user)
                    elif host and port:
                        self.set_pool(host, port)
                    else:
                        response = str({"error": True})

                    self.reconnect_all()

                elif query == 'setbackup':
                    pass

                else:
                    response = str({"error": True})

                command.sendall(response.encode())
            else:
                command.sendall(str({"error": True}).encode())

            command.shutdown(0)
            command.close()
            time.sleep(0.5)
