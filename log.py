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

import time
filename = None
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
            with open(file, 'a') as fd:
                fd.write("[%d][%s][%s] %s\n" %
                         (int(time.time()), type, self.id, msg))
        if stdout:
            print("[%d][%s][%s] %s" % (int(time.time()), type, self.id, msg))
