##\file timebase.py
#
# Generate a reliable timebase from raw time observations
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

from typing import List
from openvbi.core.types import TimeSource, NoTimeSource
from openvbi.core.observations import RawObs
from openvbi.core.interpolation import InterpTable
from openvbi.core.statistics import PktStats

def determine_timesource(stats: PktStats) -> TimeSource:
    if stats.Seen('SystemTime'):
        rtn = TimeSource.Time_SysTime
    elif stats.Seen('GNSS'):
        rtn = TimeSource.Time_GNSS
    elif stats.Seen('ZDA'):
        rtn = TimeSource.Time_ZDA
    elif stats.Seen('RMC'):
        rtn = TimeSource.Time_RMC
    else:
        raise NoTimeSource()
    return rtn

def generate_timebase(messages: List[RawObs], source: TimeSource) -> InterpTable:
    time_table = InterpTable(['ref',])
    for message in messages:
        if message.HasTime() and message.MatchesTimeSource(source):
            time_table.add_point(message.Elapsed(), 'ref', message.Timestamp())
    return time_table
