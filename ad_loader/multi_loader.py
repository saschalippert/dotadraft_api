import logging
import queue
import random
import signal
import string
import time
from datetime import datetime
from multiprocessing import Process, Queue, Lock

from requests import Timeout
from sqlitedict import SqliteDict

from loader import get_matches, filter_matches, MatchRequestError
from logging_util import load_logging_config

load_logging_config()
logger = logging.getLogger()


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def reader_proc(queue, lock, key, id):
    sqldict = SqliteDict('matches_db.sqlite', autocommit=True)
    running = True
    killer = GracefulKiller()

    user = get_random_string(10)
    while running and not killer.kill_now:
        try:
            seq_num = str(queue.get())

            if seq_num == "STOP":
                break

            retrieved_matches = get_matches(key, seq_num, user)

            if retrieved_matches:
                filtered_matches = filter_matches(retrieved_matches)

                with lock:
                    max_start_time = -1

                    for match in filtered_matches.values():
                        seq_num = match["match_seq_num"]
                        max_start_time = max(max_start_time, match["start_time"])

                        if seq_num in sqldict:
                            logger.warning(f"overwriting {seq_num}")

                        sqldict[seq_num] = match

                    count_filtered_matches = len(filtered_matches)
                    latest_match_datetime = datetime.fromtimestamp(max_start_time)

                    logger.info(f"{id} retrieved {count_filtered_matches} unique matches from {latest_match_datetime}")

                time.sleep(7)
        except MatchRequestError as e:
            logger.error(f"{id} request nok status {e.status}")
            user = get_random_string(10)
            time.sleep(30)
        except Timeout:
            logger.error(f"{id} request timeout")
            user = get_random_string(10)
            time.sleep(30)
        except Exception as e:
            logger.exception(e)
            time.sleep(30)
        except KeyboardInterrupt:
            running = False
            with lock:
                logger.info("interrupted")

    logger.info(f"shutdown worker {id}")

    sqldict.close()


def main():
    sqldict = SqliteDict('matches_db.sqlite', autocommit=True)

    logger.info(f"{len(sqldict)} matches in db")
    match_seq_num = 4771550310

    for key, value in sqldict.iteritems():
        match_seq_num = max(int(key), match_seq_num)

    sqldict.close()

    logger.info(f"last match seq num {match_seq_num}")

    keys = ["apikey1", "apikey2", "apikey3"]

    lock = Lock()
    p_queue = Queue(len(keys))

    processes = []

    for i, key in enumerate(keys):
        reader_p = Process(target=reader_proc, args=(p_queue, lock, key, i))
        reader_p.daemon = True
        reader_p.start()
        processes.append(reader_p)

    running = True
    killer = GracefulKiller()

    step_size = 150

    match_seq_num = match_seq_num + step_size

    while running and not killer.kill_now:
        try:
            p_queue.put(match_seq_num, timeout=5.0)
            match_seq_num = match_seq_num + step_size
        except queue.Full:
            pass
        except Exception as e:
            logger.exception(e)
        except KeyboardInterrupt:
            running = False
            with lock:
                logger.info("interrupted")

    logger.info("shutdown main")


if __name__ == '__main__':
    main()
