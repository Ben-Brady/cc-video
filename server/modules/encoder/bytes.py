import struct


class ByteWriter:
    cursor: int = 0
    array: bytearray

    def __init__(self, length: int) -> None:
        self.array = bytearray(length)

    def write(self, data: bytes | bytearray) -> None:
        self.array[self.cursor : self.cursor + len(data)] = data
        self.cursor += len(data)

    def writeByte(self, value: int) -> None:
        data = struct.pack("c", bytes([value]))
        self.write(data)

    def build(self):
        if self.cursor != len(self.array):
            raise ValueError(
                "Did not write correct ith measuamount to ByteWriter:\n"
                f"expected={len(self.array)} actual={self.cursor}"
            )

        return self.array


class ByteReader:
    __slots__ = ("cursor", "array")

    cursor: int
    array: bytes

    def __init__(self, data: bytes) -> None:
        self.array = data
        self.cursor = 0

    def read(self, length: int) -> bytes:
        data = self.array[self.cursor : self.cursor + length]
        self.cursor += length
        if self.cursor > len(self.array):
            raise IndexError("Out of data")
        return data

    def readByte(self) -> int:
        return self.read(1)[0]
