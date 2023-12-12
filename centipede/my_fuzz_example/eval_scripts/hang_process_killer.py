import argparse
import psutil
import time

WAKEUP_INTERVAL = 10


def kill_process(target_binary:str, timeout:int):
    """
    Kill process if it hangs for more than timeout seconds
    :param target_binary: target binary name
    :param timeout: timeout in seconds
    :return: None
    """
    while True:
        print("Heartbeat")
        for proc in psutil.process_iter():
            try:
                if proc.exe() == target_binary:
                    if proc.status() == psutil.STATUS_ZOMBIE:
                        proc.kill()
                    elif proc.status() == psutil.STATUS_RUNNING:
                        if time.time() - proc.create_time() > timeout:
                            proc.kill()
            except psutil.Error:
                pass
        time.sleep(WAKEUP_INTERVAL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hang process killer, used for fuzzing with centipede")
    parser.add_argument("target_binary", type=str, default=None,
                        help="Full path to target binary. Should be the same as in centipede config")
    parser.add_argument("timeout", type=int, default=300,
                        help="Timeout in seconds")
    args = parser.parse_args()
    kill_process(args.target_binary, args.timeout)
