#!/usr/bin/python
# qcow2-parser
# Copyright (C) 2017 Nir Soffer <nirsof@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

"""
qcow2 header parser
"""

import struct

BIG_ENDIAN = ">"


class Struct(object):

    def __init__(self, fields, byte_order=BIG_ENDIAN):
        self.keys = [key for key, _ in fields]
        fmt = byte_order + "".join(code for _, code in fields)
        self.struct = struct.Struct(fmt)

    def unpack_from(self, f, offset=0):
        # seek to from begin
        f.seek(offset, 0)
        data = f.read(self.struct.size)
        values = self.struct.unpack(data)
        return {key: value for key, value in zip(self.keys, values)}


HEADER_V2 = Struct([
    ("magic", "I"),
    ("version", "I"),
    ("backing_file_offset", "Q"),
    ("backing_file_size", "I"),
    ("cluster_bits", "I"),
    ("size", "Q"),
    ("crypt_method", "I"),
    ("l1_size", "I"),
    ("l1_table_offset", "Q"),
    ("refcount_table_offset", "Q"),
    ("refcount_table_clusters", "I"),
    ("nb_snapshots", "I"),
    ("snapshots_offset", "Q"),
])

HEADER_V3 = Struct([
    ("incompatible_features", "Q"),
    ("compatible_features", "Q"),
    ("refcount_order", "I"),
    ("header_length", "I"),
])

L1_ENTRY_SIZE = 8 # 64 bit
L1_ENTRY = Struct([
    ("l1_entry", "Q"),
])

L2_ENTRY_SIZE = 8 # 64 bit
L2_ENTRY = Struct([
    ("l2_entry", "Q"),
])


def parse(file):
    info = HEADER_V2.unpack_from(file, 0)
    if info["version"] == 3:
        v3_info = HEADER_V3.unpack_from(file, 0)
        info.update(v3_info)
    if info["cluster_bits"] and info["size"]:
        info["cluster_size"] = 1 << info["cluster_bits"];
        info["clusters"] = info["size"] / info["cluster_size"];
    if info['l1_table_offset']:
        pos = info['l1_table_offset']
        l1 = []
        while pos < info['l1_table_offset'] + info['l1_size'] * L1_ENTRY_SIZE:
            l1_entry_packed = L1_ENTRY.unpack_from(file, pos)
            l1_entry = {
                "l2_table_offset": (l1_entry_packed['l1_entry'] >> 8) & 0x7fffffffffffff,
                "non_cow": (l1_entry_packed['l1_entry'] >> 63),
            }
            if l1_entry["l2_table_offset"] and info["clusters"]:
                l2 = []
                l2_pos = l1_entry["l2_table_offset"]
                while l2_pos < l1_entry["l2_table_offset"] + info["clusters"] * L2_ENTRY_SIZE:
                    l2 += [L2_ENTRY.unpack_from(file, l2_pos)]
                    l2_pos += L2_ENTRY_SIZE
                l1_entry["l2?"] = l2
            l1 += [l1_entry]
            pos += L1_ENTRY_SIZE
        info['l1'] = l1
    return info


if __name__ == "__main__":
    import sys
    import json
    filename = sys.argv[1]
    with open(filename, "rb") as f:
        info = parse(f)
        print("qcow2 dump: {}"
              .format(json.dumps(info, indent=4, sort_keys=True)))
