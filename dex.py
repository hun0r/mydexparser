from parser import Type, Obj
from struct import unpack

@Type
def byte(buff):
    return unpack("<b", buff.read(1))[0]


@Type
def ubyte(buff):
    return unpack("<B", buff.read(1))[0]


@Type
def short(buff):
    return unpack("<h", buff.read(2))[0]


@Type
def ushort(buff):
    return unpack("<H", buff.read(2))[0]


@Type
def int(buff):
    return unpack("<i", buff.read(4))[0]


@Type
def uint(buff):
    return unpack("<I", buff.read(4))[0]


@Type
def long(buff):
    return unpack("<q", buff.read(8))[0]


@Type
def ulong(buff):
    return unpack("<Q", buff.read(8))[0]


@Type
def uleb128(buff):
    result = 0
    shift = 0

    while True:
        raw = buff.read(1)
        if not raw:
            raise EOFError("Unexpected EOF while reading ULEB128")

        byte = raw[0]
        result |= (byte & 0x7F) << shift

        if not (byte & 0x80):
            return result

        shift += 7
        if shift >= 35:
            raise ValueError("Invalid ULEB128")


@Type
def sleb128(buff):
    result = 0
    shift = 0

    while True:
        raw = buff.read(1)
        if not raw:
            raise EOFError("Unexpected EOF while reading SLEB128")

        byte = raw[0]
        result |= (byte & 0x7F) << shift
        shift += 7

        if not (byte & 0x80):
            if byte & 0x40:
                result |= -1 << shift
            return result

        if shift >= 35:
            raise ValueError("Invalid SLEB128")


@Type
def uleb128p1(buff):
    return uleb128(buff) + 1

@Type
class header_item(Obj):
    magic = ubyte[8]
    checksum = uint
    signature = ubyte[20]
    file_size = uint
    header_size = uint
    endian_tag = uint
    link_size = uint
    link_off = uint
    map_off = uint
    string_ids_size = uint
    string_ids_off = uint
    type_ids_size = uint
    type_ids_off = uint
    proto_ids_size = uint
    proto_ids_off = uint
    field_ids_size = uint
    field_ids_off = uint
    method_ids_size = uint
    method_ids_off = uint
    class_defs_size = uint
    class_defs_off = uint
    data_size = uint
    data_off = uint

@Type
class map_item(Obj):
    type = ushort
    unused = ushort
    size = uint
    offset = uint

@Type
class map_list(Obj):
    size = uint
    list = map_item['size']

@Type
class DEXFile(Obj):
    header = header_item
