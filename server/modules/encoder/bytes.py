import struct


class ByteWriter:
    cursor: int = 0
    _array: bytearray

    def __init__(self, length: int) -> None:
        self._array = bytearray(length)

    def write(self, data: bytes | bytearray) -> None:
        self._array[self.cursor : self.cursor + len(data)] = data
        self.cursor += len(data)

    def writeByte(self, value: int) -> None:
        data = struct.pack("c", bytes([value]))
        self.write(data)

    def build(self):
        if self.cursor != len(self._array):
            raise ValueError(
                "Did not write correct amount to ByteWriter:\n"
                f"expected={len(self._array)} actual={self.cursor}"
            )

        return self._array


class ByteReader:
    cursor: int = 0
    array: bytes

    def __init__(self, data: bytes) -> None:
        self.array = data

    def read(self, length: int) -> bytes:
        data = self.array[self.cursor : self.cursor + length]
        self.cursor += length
        if self.cursor > len(self.array):
            raise IndexError("Out of data")
        return data

    def readByte(self) -> int:
        return self.read(1)[0]
