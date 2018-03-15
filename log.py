import time
filename = ' '
stdout = True
verbose = 3


class Log():

    def __init__(self, id='any'):
        self.id = id

    def error(self, msg):
        if verbose > 0:
            self.write(msg, 'error')

    def warning(self, msg):
        if verbose > 1:
            self.write(msg, 'warning')

    def info(self, msg):
        if verbose > 2:
            self.write(msg, 'info')

    def debug(self, msg):
        if verbose > 3:
            self.write(msg, 'debug')

    def write(self, msg, type):
        if filename:
            with open(filename, 'a') as fd:
                fd.write("[%d][%s][%s] %s\n" %
                         (int(time.time()), type, self.id, msg))
        if stdout:
            print("[%s][%s][%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), type, self.id, msg))
