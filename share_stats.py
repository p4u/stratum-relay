import time
import datetime
import subprocess
import threading
import log as Log


class Shares(object):
    shares = {}

    def __init__(self, identifier='shares'):
        self.accepted_jobs = 0
        self.rejected_jobs = 0
        self.lock = threading.Lock()
        self.last_job_time = datetime.datetime.now()
        self.shares = {}
        self.log = Log.Log(identifier)

    def get_last_job_secs(self):
        return int(
            (datetime.datetime.now() -
             self.last_job_time).total_seconds())

    def set_module(self, module):
        try:
            mod_fd = open("%s" % (module), 'r')
            mod_str = mod_fd.read()
            mod_fd.close()
            exec(mod_str)
            self.on_share = on_share
            self.log.info('loaded sharenotify module %s' % module)

        except IOError:
            self.log.error('cannot load sharenotify snippet')

            def do_nothing(job_id, worker_name, init_time, dif):
                pass
            self.on_share = do_nothing

    def register_job(self, job_id, worker_name, dif, accepted, sharenotify):
        if self.accepted_jobs + self.rejected_jobs >= 65535:
            self.accepted_jobs = 0
            self.rejected_jobs = 0
            self.log.info("reseting statistics")
        self.last_job_time = datetime.datetime.now()
        if accepted:
            self.accepted_jobs += 1
        else:
            self.rejected_jobs += 1

        if not (worker_name in self.shares):
            self.shares[worker_name] = [0, 0]
        if accepted:
            if self.shares[worker_name][0] > 10 ** 16:
                self.shares[worker_name][0] = 0
            self.shares[worker_name][0] += dif
            self.log.debug(
                "registering accepted share for worker %s and diff %s" % (worker_name, dif))

        else:
            if self.shares[worker_name][1] > 10 ** 16:
                self.shares[worker_name][1] = 0
            self.shares[worker_name][1] += dif
            self.log.debug(
                "registering rejected share for worker %s and diff %s" % (worker_name, dif))

        if sharenotify:
            self._execute_snippet(job_id, worker_name, dif, accepted)

    def _execute_snippet(self, job_id, worker_name, dif, accepted):
        self.log.info("current active threads: %s" % threading.active_count())
        if threading.active_count() > 10:
            try:
                self.log.error("deadlock detected, trying to release it")
                self.lock.release()
            except Exception as e:
                self.log.error("%s" % e)
        init_time = time.time()
        t = threading.Thread(
            target=self.on_share,
            args=[
                self,
                job_id,
                worker_name,
                init_time,
                dif,
                accepted])
        t.daemon = True
        t.start()
