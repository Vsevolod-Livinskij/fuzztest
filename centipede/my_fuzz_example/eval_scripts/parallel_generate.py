import argparse
import multiprocessing
import os
import queue
import signal
import subprocess
import time

SEEDS_NUM = 10000
SLEEP_TIME = 1

def run_cmd(cmd, time_out=None, num=-1, memory_limit=None):
    is_time_expired = False
    shell = False
    if memory_limit is not None:
        shell = True
        new_cmd = "ulimit -v " + str(memory_limit) + " ; "
        new_cmd += " ".join(i for i in cmd)
        cmd = new_cmd
    start_time = os.times()
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True, shell=shell) as process:
        try:
            output, err_output = process.communicate(timeout=time_out)
            ret_code = process.poll()
        except subprocess.TimeoutExpired:
            # Sigterm is good enough here and compared to sigkill gives a chance to the processes
            # to clean up after themselves.
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            # once in a while stdout/stderr may not exist when the process is killed, so using try.
            try:
                output, err_output = process.communicate()
            except ValueError:
                output = b''
                err_output = b''
            is_time_expired = True
            ret_code = None
        except:
            # Something really bad is going on, so better to send sigkill
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            process.wait()
            raise
    end_time = os.times()
    elapsed_time = end_time.children_user - start_time.children_user + \
                   end_time.children_system - start_time.children_system
    return ret_code, output, err_output, is_time_expired, elapsed_time

def single_task(tid, task_queue=None, result_dir="results"):
    print("Task %d started" % tid)
    while True:
        # TODO: this is not a good way to stop the process, but it works for now.
        seed = ""
        if task_queue is not None:
            # Python multiprocessing queue may raise empty exception
            # even for non-empty queue, so do several attempts to not loos workers.
            for i in range(3):
                try:
                    seed = task_queue.get_nowait()
                except queue.Empty:
                    time.sleep(1/(tid+1))
                else:
                    break
            if seed == "done":
                break
            ret_code, stdout, stderr, is_time_expired, elapsed_time = \
                run_cmd(['./generate_once.sh', str(tid), str(seed)], time_out=60, num=tid)
    print("Task %d finished" % tid)


def run_parallel(seeds_num=SEEDS_NUM, num_jobs=multiprocessing.cpu_count(), result_dir="results"):
    task_queue = multiprocessing.Queue()
    for s in range(seeds_num):
        task_queue.put(s)

    task_threads = [0] * num_jobs
    for num in range(num_jobs):
        task_threads[num] = multiprocessing.Process(target=single_task, args=(num,task_queue, result_dir))
        task_threads[num].start()

    for num in range(num_jobs):
        task_queue.put("done")

    any_alive = True
    while any_alive:
        time.sleep(SLEEP_TIME)
        any_alive = False
        for num in range(num_jobs):
            any_alive |= task_threads[num].is_alive()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds-num", type=int, default=SEEDS_NUM, help="Number of seeds to generate")
    parser.add_argument( "-j", "--jobs", type=int, default=multiprocessing.cpu_count(), help="Number of parallel jobs")
    parser.add_argument("--result-dir", type=str, default="results", help="Directory to store results")
    args = parser.parse_args()
    run_parallel(seeds_num=args.seeds_num, num_jobs=args.jobs, result_dir=args.result_dir)
