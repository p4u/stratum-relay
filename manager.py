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

import json
import string
import log

class Manager():
	def __init__(self):
		self.jobs = {} # job_id -> [difficulty,#sent]
		self.jobs_pending_ids = {} # id -> job_id
		self.difficulty = 1
		self.authid = None
		self.username = '14MQUGn97dFYHGxXwaHqoCX175b9fwYUMo'
		self.password = 'x'
		self.real_username = None
		self.real_password = None
		self.log = log.Log('manager')

	def add_job(self,jid):
		self.log.debug("Adding job: %s" %jid)
		self.jobs[jid] = [self.difficulty,0]

	def clean_jobs(self):
		self.log.debug("Cleaning jobs")
		self.jobs = {}
		self.jobs_pending_ids = {}

	def process(self,msg):
		output = ""
		for l in msg.splitlines():
			try:
				jmsg = json.loads(l)
			except:
				self.log.error("cannot decode %s" %l)
				self.log.error("-------------------------------------------------------------")
				self.log.error(msg)
				self.log.error("-------------------------------------------------------------")

				continue
			if 'method' in jmsg:
				self.log.debug("got method: %s" %jmsg['method'])
				if jmsg['method'] == 'mining.authorize' and ('params' in jmsg):
					user = jmsg['params'][0]
					passw = jmsg['params'][1]
					self.log.info("got user: %s/%s" %(user,passw))
					self.real_username = user
					self.real_password = passw
					jmsg['params'][0] = self.username
					jmsg['params'][1] = self.password
					self.authid = jmsg['id']

				elif jmsg['method'] == 'mining.notify' and ('params' in jmsg):
					#print(jmsg)
					new_id = jmsg['params'][0]
					clean_jobs = jmsg['params'][8]
					if clean_jobs: self.clean_jobs()
					self.add_job(new_id)

				elif jmsg['method'] == 'mining.set_difficulty' and ('params' in jmsg):
					self.difficulty = float(jmsg['params'][0])
					self.log.info("setting difficulty to %s" %(self.difficulty))
				
				elif jmsg['method'] == 'mining.submit' and ('params' and 'id' in jmsg):
					jid = jmsg['params'][1]
					if jid in self.jobs:
						self.jobs[jid][1] += 1
						self.jobs_pending_ids[jmsg['id']] = jid
					else:
						self.log.warning("job %s not found" %jid)
					jmsg['params'][0] = self.username

			elif 'result' and 'id' in jmsg:
				if jmsg['id'] == self.authid:
					if jmsg['result']:
						self.log.info('worker authorized!')
						self.authid = None
					else:
						self.log.error('worker not authorized!')

				elif jmsg['id'] in self.jobs_pending_ids:
					jid = self.jobs_pending_ids[jmsg['id']]
					if self.jobs[jid][1] > 0:
						self.jobs[jid][1] -= 1
						diff = self.jobs[jid][0]
						if jmsg['result']:
							self.log.info('share ACCEPTED for jobid %s, size %s, worker %s' %(jid,diff,self.real_username))
						else:
							self.log.info('share REJECTED for jobid %s, size %s, worker %s' %(jid,diff,self.real_username))
					else:
						diff = self.jobs[jid][0]
						self.log.info('share REJECTED for jobid %s, size %s, worker %s' %(jid,diff,self.real_username))
						self.log.warning('job %s not submited by miner or stale share!' %jid)

			output += json.dumps(jmsg) + '\n'
		return output
