import os
from threading import Thread
import typing as t
import time
import queue
from queue import Queue, ShutDown, Empty

def tee(stream: t.IO[bytes]) -> tuple[t.IO[bytes], t.IO[bytes]]:
    ar_fd, aw_fd = os.pipe()
    br_fd, bw_fd = os.pipe()
    a_queue = Queue()
    b_queue = Queue()

    Thread(
        target=_read_into_queues,
        args=(stream, [a_queue, b_queue]),
        daemon=True
    ).start()

    Thread(
        target=_write_to_pipe,
        args=(a_queue, aw_fd, "A"),
        daemon=True
    ).start()
    Thread(
        target=_write_to_pipe,
        args=(b_queue, bw_fd, "B"),
        daemon=True
    ).start()

    a = open(ar_fd, "rb")
    b = open(br_fd, "rb")
    return a, b


def _read_into_queues(stream: t.IO[bytes], queues: list[queue.Queue]):
    CHUNK_SIZE = 1024 * 32
    try:
        while True:
            data = stream.read(CHUNK_SIZE)

            if len(data) > 0:
                [queue.put(data) for queue in queues]
            else:
                stream.close()
                [queue.shutdown() for queue in queues]
                return
    except Exception as e:
        print(e)


def _write_to_pipe(queue: Queue, fd: int, name: str):
    f = open(fd, "wb")
    total = 0

    while True:
        time.sleep(0.01)
        try:
            data = queue.get(timeout=0.01)
        except Empty:
            time.sleep(0.01)
            continue
        except ShutDown:
            f.close()
            return
        except Exception as e:
            print(e)
        else:
            total += len(data)

            f.write(data)
