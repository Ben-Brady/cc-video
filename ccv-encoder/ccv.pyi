class MonitorDisplay:
    rows: int
    columns: int
    monitor_width: int
    monitor_height: int

    margin_left: int
    margin_right: int
    margin_top: int
    margin_bottom: int

    def __init__(self, grid: tuple[int, int], monitor: tuple[int, int], margin: tuple[int, int, int, int]) -> None: ...

class Image:
    width: int
    height: int
    data: bytes

    def __init__(self, width: int, height: int, data: bytes) -> None: ...


def calculate_resize_resolution(res: tuple[int, int], max_size: tuple[int, int]) -> tuple[int, int]:
    ...

def encode_frame(image: Image, diplay: MonitorDisplay) -> bytes:
    ...

def encode_frames(image: list[Image], diplay: MonitorDisplay) -> list[bytes]:
    ...

