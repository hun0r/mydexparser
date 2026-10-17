from parser import Type, Obj, File
from struct import unpack
import builtins
from typing import Any


@Type
def byte(buff: File) -> builtins.int:
    return unpack("<b", buff.read(1))[0]


@Type
def ubyte(buff: File) -> builtins.int:
    return unpack("<B", buff.read(1))[0]


@Type
def short(buff: File) -> builtins.int:
    return unpack("<h", buff.read(2))[0]


@Type
def ushort(buff: File) -> builtins.int:
    return unpack("<H", buff.read(2))[0]


@Type
def int(buff: File) -> builtins.int:
    return unpack("<i", buff.read(4))[0]


@Type
def uint(buff: File) -> builtins.int:
    return unpack("<I", buff.read(4))[0]


@Type
def long(buff: File) -> builtins.int:
    return unpack("<q", buff.read(8))[0]


@Type
def ulong(buff: File) -> builtins.int:
    return unpack("<Q", buff.read(8))[0]


@Type
def uleb128(buff: File) -> builtins.int:
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
def sleb128(buff: File) -> builtins.int:
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
def uleb128p1(buff: File) -> builtins.int:
    return builtins.int(uleb128.parse(buff)) + 1


class type_id_item(Obj):
    descriptor_idx: uint


class string_data_item(Obj):
    utf16_size: uleb128
    data: ubyte["utf16_size"]


class string_id_item(Obj):
    string_data_off: uint


class proto_id_item(Obj):
    shorty_idx: uint
    return_type_idx: uint
    parameters_off: uint


class field_id_item(Obj):
    class_idx: ushort
    type_idx: ushort
    name_idx: uint


class method_id_item(Obj):
    class_idx: ushort
    proto_idx: ushort
    name_idx: uint


class class_def_item(Obj):
    class_idx: uint
    access_flags: uint
    superclass_idx: uint
    interfaces_off: uint
    source_file_idx: uint
    annotations_off: uint
    class_data_off: uint
    static_values_off: uint


class call_site_id_item(Obj):
    call_site_off: uint


class method_handle_item(Obj):
    method_handle_type: ushort
    unused1: ushort
    field_or_method_id: ushort
    unused2: ushort


class type_item(Obj):
    type_idx: ushort


class type_list(Obj):
    size: uint
    list: type_item["size"]


class annotation_set_ref_item(Obj):
    annotations_off: uint


class annotation_set_ref_list(Obj):
    size: uint
    list: annotation_set_ref_item["size"]


class annotation_off_item(Obj):
    annotation_off: uint


class annotation_set_item(Obj):
    size: uint
    entries: annotation_off_item["size"]


class field_annotation(Obj):
    field_idx: uint
    annotations_off: uint


class method_annotation(Obj):
    method_idx: uint
    annotations_off: uint


class parameter_annotation(Obj):
    method_idx: uint
    annotations_off: uint


class annotations_directory_item(Obj):
    class_annotations_off: uint
    fields_size: uint
    annotated_methods_size: uint
    annotated_parameters_size: uint
    field_annotations: field_annotation["fields_size"]
    method_annotations: method_annotation["annotated_methods_size"]
    parameter_annotations: parameter_annotation["annotated_parameters_size"]


class encoded_field(Obj):
    field_idx_diff: uleb128
    access_flags: uleb128


class encoded_method(Obj):
    method_idx_diff: uleb128
    access_flags: uleb128
    code_off: uleb128


class class_data_item(Obj):
    static_fields_size: uleb128
    instance_fields_size: uleb128
    direct_methods_size: uleb128
    virtual_methods_size: uleb128
    static_fields: encoded_field["static_fields_size"]
    instance_fields: encoded_field["instance_fields_size"]
    direct_methods: encoded_method["direct_methods_size"]
    virtual_methods: encoded_method["virtual_methods_size"]


class code_item(Obj):
    registers_size: ushort
    ins_size: ushort
    outs_size: ushort
    tries_size: ushort
    debug_info_off: uint
    insns_size: uint
    insns: ushort["insns_size"]


class debug_info_item(Obj):
    line_start: uleb128
    parameters_size: uleb128
    parameter_names: uleb128p1["parameters_size"]


class annotation_item(Obj):
    visibility: ubyte
    annotation: ubyte


class encoded_array_item(Obj):
    value: ubyte


class hiddenapi_class_data_item(Obj):
    size: uint
    offsets: uint["size"]


@Type
def map_item_data(buff: File, obj: Obj) -> Any:
    return type_map[getattr(obj, "type")].parse(buff, obj, off=getattr(obj, "offset"))  # type: ignore


class map_item(Obj):
    type: ushort
    unused: ushort
    size: uint
    offset: uint
    data: map_item_data


class map_list(Obj):
    size: uint
    list: map_item["size"]


class header_item(Obj):
    magic: ubyte[8]
    checksum: uint
    signature: ubyte[20]
    file_size: uint
    header_size: uint
    endian_tag: uint
    link_size: uint
    link_off: uint
    map_off: uint
    string_ids_size: uint
    string_ids_off: uint
    type_ids_size: uint
    type_ids_off: uint
    proto_ids_size: uint
    proto_ids_off: uint
    field_ids_size: uint
    field_ids_off: uint
    method_ids_size: uint
    method_ids_off: uint
    class_defs_size: uint
    class_defs_off: uint
    data_size: uint
    data_off: uint


type_map: dict[builtins.int, Type[Any]] = {
    0x0000: header_item,
    0x0001: string_id_item,
    0x0002: type_id_item,
    0x0003: proto_id_item,
    0x0004: field_id_item,
    0x0005: method_id_item,
    0x0006: class_def_item,
    0x0007: call_site_id_item,
    0x0008: method_handle_item,
    0x1000: map_list,
    0x1001: type_list,
    0x1002: annotation_set_ref_list,
    0x1003: annotation_set_item,
    0x2000: class_data_item,
    0x2001: code_item,
    0x2002: string_data_item,
    0x2003: debug_info_item,
    0x2004: annotation_item,
    0x2005: encoded_array_item,
    0x2006: annotations_directory_item,
    0xF000: hiddenapi_class_data_item,
}


class DEXFile(Obj):
    header: header_item
