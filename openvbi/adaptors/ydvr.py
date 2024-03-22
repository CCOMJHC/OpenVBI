##\file ydvr.py
#
# Read files of NMEA2000 data logged by the Yacht Devices logger
#
# Copyright 2023 OpenVBI Project.  All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

import struct
from typing import Tuple, Union
from openvbi.adaptors import Dataset
from openvbi.core.observations import RawN2000Obs, BadData
from openvbi.core.statistics import PktFaults
import openvbi.timestamping.timebase as timebase
from marulc.nmea2000 import get_description_for_pgn
from marulc.exceptions import ParseError

def TranslateCANId(id: int) -> Tuple[int, int, int, int]:
    pf = (id >> 16) & 0xFF
    ps = (id >> 8) & 0xFF
    dp = (id >> 24) & 1
    source = (id >> 0) & 0xFF
    priority = (id >> 26) & 0x7
    if pf < 240:
        destination = ps
        pgn = (dp << 16) + (pf << 8)
    else:
        destination = 0xFF
        pgn = (dp << 16) + (pf << 8) + ps
    
    return priority, pgn, source, destination

def IsMultiPacket(pgn: int) -> bool:
    multipackets = (
     65240, 126208, 126464, 126720, 126983, 126984, 126985, 126986, 126987, 126988, 126996,
    126998, 127233, 127237, 127489, 127496, 127497, 127498, 127503, 127504, 127506, 127507,
    127509, 127510, 127511, 127512, 127513, 127514, 128275, 128520, 129029, 129038, 129039,
    129040, 129041, 129044, 129045, 129284, 129285, 129301, 129302, 129538, 129540, 129541,
    129542, 129545, 129547, 129549, 129551, 129556, 129792, 129793, 129794, 129795, 129796,
    129797, 129798, 129799, 129800, 129801, 129802, 129803, 129804, 129805, 129806, 129807,
    129808, 129809, 129810, 130052, 130053, 130054, 130060, 130061, 130064, 130065, 130066,
    130067, 130068, 130069, 130070, 130071, 130072, 130073, 130074, 130320, 130321, 130322,
    130323, 130324, 130567, 130577, 130578, 130816)
    if pgn in multipackets:
        return True
    else:
        return False

def next_packet(f) -> Tuple[int, int, bytearray]:
    t_buffer = f.read(2)
    if len(t_buffer) == 0:
        return -1, -1, ""
    elapsed = struct.unpack('<H', t_buffer)[0]
    id_buffer = f.read(4)
    msgid = struct.unpack('<L', id_buffer)[0]

    priority: int = 0
    source: int = 0
    destination: int = 0
    pgn: int = 0

    if msgid == 0xFFFFFFFF:
        pgn = msgid
    else:
        priority, pgn, source, destination = TranslateCANId(msgid)
    
    if pgn == 59904:
        datalen = 3
    elif pgn == 0xFFFFFFFF:
        datalen = 8
    elif IsMultiPacket(pgn):
        multi_buffer = f.read(2)
        _, datalen = struct.unpack('<BB', multi_buffer)
    else:
        datalen = 8

    packet = f.read(datalen)

    return elapsed, pgn, packet


def load_data(filename: str) -> Dataset:
    data: Dataset = Dataset()

    with open(filename, 'rb') as f:
        while f:
            pkt_name = 'Unknown'
            elapsed, pgn, packet = next_packet(f)
            try:
                descr = get_description_for_pgn(pgn)
                pkt_name = descr['Description']
            except ValueError:
                pkt_name = 'Unknown'
            if elapsed < 0:
                break
            try:
                obs = RawN2000Obs(elapsed, pgn, packet)
                data.packets.append(obs)
                data.stats.Observed(obs.Name())
            except BadData as e:
                data.stats.Observed(pkt_name)
                data.stats.Fault(pkt_name, PktFaults.DecodeFault)
            except ParseError as e:
                data.stats.Observed(pkt_name)
                data.stats.Fault(pkt_name, PktFaults.ParseFault)
            except RuntimeError as e:
                data.stats.Observed(pkt_name)
                data.stats.Fault(pkt_name, PktFaults.DecodeFault)
    
    data.timesrc = timebase.determine_timesource(data.stats)
    data.timebase = timebase.generate_timebase(data.packets, data.timesrc)

    return data
