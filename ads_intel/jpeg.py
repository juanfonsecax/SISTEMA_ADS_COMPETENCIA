from __future__ import annotations

SOF_MARKERS = {
    0xC0,
    0xC1,
    0xC2,
    0xC3,
    0xC5,
    0xC6,
    0xC7,
    0xC9,
    0xCA,
    0xCB,
    0xCD,
    0xCE,
    0xCF,
}

STANDALONE_MARKERS = {0x01, 0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9}


def is_jpeg(data: bytes) -> bool:
    return len(data) >= 2 and data[0] == 0xFF and data[1] == 0xD8


def jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    if not is_jpeg(data):
        return None
    index = 2
    size = len(data)
    while index + 1 < size:
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        if marker == 0xFF:
            index += 1
            continue
        if marker in STANDALONE_MARKERS:
            index += 2
            continue
        if marker == 0xDA:
            return None
        if index + 4 > size:
            return None
        segment_length = int.from_bytes(data[index + 2 : index + 4], "big")
        if segment_length < 2 or index + 2 + segment_length > size:
            return None
        if marker in SOF_MARKERS and segment_length >= 7:
            height = int.from_bytes(data[index + 5 : index + 7], "big")
            width = int.from_bytes(data[index + 7 : index + 9], "big")
            if width > 0 and height > 0:
                return width, height
            return None
        index += 2 + segment_length
    return None
