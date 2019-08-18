#!/usr/bin/python
import threading
import time
import sys
import argparse
import traceback
import subprocess
if sys.version_info[0] < 3:
    from Queue import Queue
else:
    from queue import Queue

num_local_workers = 1


class LocalWorker(threading.Thread):
    def __init__(self, host, job_queue, out_filename):
        threading.Thread.__init__(self)
        self.host = host
        self.job_queue = job_queue
        self.out_filename = out_filename

    def run(self):
        self.process_jobs()

    def process_jobs(self):
        while True:
            local_cmd, status = self.job_queue.get()  # blocking

            if status == 'STOP':
                self.job_queue.put((None, 'STOP'))
                break

            if status == 'AWAITING':
                localtime = time.asctime(time.localtime(time.time()))
                slocal_cmd = local_cmd.replace(r'\"', r'"')
                print('Datetime: {0} host: local_{1} cmd: {2}'.format(
                    localtime, self.host, slocal_cmd))

                proc = subprocess.run(slocal_cmd,
                                      shell=True,
                                      stdout=subprocess.PIPE)  # blocking

                if proc.returncode != 0:
                    # we failed, let others do that and we just quit
                    print('local_{0} failed. (returncode: {1})'.format(
                        self.host, proc.returncode))
                    self.job_queue.put((local_cmd, 'AWAITING'))
                    self.job_queue.task_done()
                    break
                else:
                    stdout_str = proc.stdout.decode('utf-8')
                    if stdout_str and self.out_filename:
                        with open(self.out_filename, 'a') as fp:
                            fp.write(stdout_str)
                    elif stdout_str:
                        print(stdout_str)
                    self.job_queue.task_done()
        sys.stdout.write('local worker {0} quit.\n'.format(self.host))


class SSHWorker(threading.Thread):
    def __init__(self, host, job_queue, out_filename):
        threading.Thread.__init__(self)
        self.host = host
        self.job_queue = job_queue
        self.out_filename = out_filename

    def run(self):
        self.process_jobs()

    def process_jobs(self):
        while True:
            local_cmd, status = self.job_queue.get()  # blocking

            if status == 'STOP':
                self.job_queue.put((None, 'STOP'))
                break

            if status == 'AWAITING':
                ssh_cmd = "ssh " + self.host
                job = "{0} \"{1}\"".format(ssh_cmd, local_cmd)

                localtime = time.asctime(time.localtime(time.time()))
                print('Datetime: {0} host: {1} cmd: {2}'.format(
                    localtime, self.host, job))

                proc = subprocess.run(job, shell=True,
                                      stdout=subprocess.PIPE)  # blocking

                if proc.returncode != 0:
                    # we failed, let others do that and we just quit
                    print('{0} failed. (returncode: {1})'.format(
                        self.host, proc.returncode))
                    self.job_queue.put((local_cmd, 'AWAITING'))
                    self.job_queue.task_done()
                    break
                else:
                    stdout_str = proc.stdout.decode('utf-8')
                    if stdout_str and self.out_filename:
                        with open(self.out_filename, 'a') as fp:
                            fp.write(stdout_str)
                    elif stdout_str:
                        print(stdout_str)
                    self.job_queue.task_done()
        sys.stdout.write('worker {0} quit.\n'.format(self.host))


def parse_hosts(filename=None):
    if not filename: return []

    with open(filename, 'r') as fp:
        hosts = [line.rstrip('\n') for line in fp]
        if not hosts:
            print('Warning: {} is empty.'.format(filename))
    return hosts


def parse_jobs(filename):
    with open(filename, 'r') as fp:
        jobs = [line.rstrip('\n') for line in fp]
        if not jobs:
            raise Exception(filename + ' is empty')
    return jobs


def dispatch(host_cfg, job_cfg, num_local_workers, out_filename=None):
    if num_local_workers is None: num_local_workers = 1

    job_queue = Queue()
    hosts = parse_hosts(host_cfg)

    # fire ssh workers
    for host in hosts:
        worker = SSHWorker(host, job_queue, out_filename)
        worker.start()

    # Fill the queue
    for job in parse_jobs(job_cfg):
        job_queue.put((job, 'AWAITING'))

    # fire local workers
    for host in range(num_local_workers):
        worker = LocalWorker(host, job_queue, out_filename)
        worker.start()

    job_queue._put = job_queue.queue.appendleft

    job_queue.join()
    job_queue.put((None, 'STOP'))

    print("Exiting Main Thread")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dispatcher')
    parser.add_argument('--host',
                        type=str,
                        metavar='host configuration',
                        help='Specify hosts configuration file')
    parser.add_argument('--job',
                        type=str,
                        metavar='job configuration',
                        required=True,
                        help='Specify jobs configuration file')
    parser.add_argument('--num_local_workers',
                        type=int,
                        metavar='local worker',
                        help='Specify the number of local workers')
    parser.add_argument(
        '--out_filename',
        type=str,
        metavar='raw result filename',
        help='Specify the filename storing the results from each worker')
    args = parser.parse_args()

    dispatch(args.host, args.job, args.num_local_workers, args.out_filename)
