##\file timebase.py
#
# Provide time source determination, and time-base construction
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
from openvbi.core.statistics import PktStats
from openvbi.core.types import TimeSource, NoTimeSource, RawObs
from openvbi.core.interpolation import InterpTable

## Work out which time source should be used for real time associations
#
# There are multiple potential ways to assign a correspondence between measures of
# elapsed time and the timestamps that are available in the source observations (e.g.,
# from ZDA or RMC strings, or NMEA2000 System Time or GNSS packets).  All of these
# mechanisms can be used, but in general we prefer to use System Time if available,
# then GNSS (since NMEA2000 arrives faster, it should have lower latency that NMEA0183),
# but then will use either ZDA, or as a last resort RMC from NMEA0183 packets.  This
# code translates the available packets into an enum for further reference.

def determine_time_source(stats: PktStats) -> TimeSource:
    """Work out which source of time can be used to provide the translation between
       elapsed time (local time-stamps that indicate a monotonic clock tick at the
       logger when the packet is received) to a real world time.  The preference is
       to use NMEA2000 system time packets, but then to attempt to use GNSS packets,
       and then finally to drop back to NMEA0183 ZDA or RMC packets (in that order)
       if required.

        Inputs:
            stats   (PktStats) Statistics on which packets have been seen in the data
        
        Outputs:
            TimeSource enum for which source should be used for timestamping
    """
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
