import os
from threading import Thread
import typing as t
import queue
from queue import Queue, ShutDown


def tee(
    stream: t.BinaryIO | t.IO[bytes],
) -> tuple[t.BinaryIO, t.BinaryIO]:
    ar_fd, aw_fd = os.pipe()
    br_fd, bw_fd = os.pipe()

    a_io = open(ar_fd, "rb")
    b_io = open(br_fd, "rb")

    a_queue = _create_pipe_to_queue(aw_fd)
    b_queue = _create_pipe_to_queue(bw_fd)

    _read_into_queues(stream, [a_queue, b_queue])
    return a_io, b_io


def _read_into_queues(stream: t.BinaryIO | t.IO[bytes], queues: list[queue.Queue]):
    def thread(stream: t.BinaryIO | t.IO[bytes], queues: list[queue.Queue]):
        CHUNK_SIZE = 1024 * 32
        while True:
            data = stream.read(CHUNK_SIZE)

            if len(data) > 0:
                [queue.put(data) for queue in queues]
            else:
                stream.close()
                [queue.shutdown() for queue in queues]
                return

    Thread(target=thread, args=(stream, queues)).start()


def _create_pipe_to_queue(fd: int):
    queue = Queue()

    def thread(
        fd: int,
        queue: Queue,
    ):
        f = open(fd, "wb")
        try:
            while True:
                try:
                    data = queue.get(block=True)
                except ShutDown:
                    return
                else:
                    f.write(data)
        finally:
            try:
                f.close()
            except Exception:
                pass

    Thread(target=thread, args=(fd, queue), daemon=True).start()
    return queue
