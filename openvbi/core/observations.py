##\file observations.py
#
# General types and routines for raw observations from VBI data files
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

from abc import ABC, abstractmethod
from typing import List
import datetime
from dataclasses import dataclass
from marulc import NMEA0183Parser, NMEA2000Parser, parse_from_iterator
from marulc.nmea2000 import unpack_complete_message
from marulc.exceptions import ParseError, ChecksumError, PGNError
from openvbi.core.types import TimeSource
from openvbi.core.statistics import PktStats

class BadData(Exception):
    pass

class RawObs(ABC):
    def __init__(self, elapsed: int, name: str, hastime: bool) -> None:
        self._elapsed = elapsed
        self._name = name
        self._hastime = hastime
    
    def Name(self) -> str:
        return self._name
    
    def Elapsed(self) -> int:
        return self._elapsed

    def SetElapsed(self, elapsed: int) -> None:
        self._elapsed = elapsed
    
    def HasTime(self) -> bool:
        return self._hastime
    
    @abstractmethod
    def MatchesTimeSource(self, source: TimeSource) -> bool:
        pass

    @abstractmethod
    def Timestamp(self) -> float:
        pass

class RawN0183Obs(RawObs):
    def __init__(self, elapsed: int, message: str) -> None:
        parser = NMEA0183Parser()
        try:
            self._data = parser.unpack(message)
            if self._data['Formatter'] == 'ZDA' or self._data['Formatter'] == 'RMC':
                has_time = True
            else:
                has_time = False
        except ChecksumError:
            raise BadData()
        except ParseError:
            raise BadData()
        super().__init__(elapsed, self._data['Formatter'], has_time)

    def MatchesTimeSource(self, source: TimeSource) -> bool:
        if not self.HasTime():
            return False
        if self.Name() == 'ZDA' and source == TimeSource.Time_ZDA:
            return True
        if self.Name() == 'RMC' and source == TimeSource.Time_RMC:
            return True
        return False
    
    def Timestamp(self) -> float:
        if not self.HasTime():
            return -1.0
        base_date = datetime.datetime(self._data['Fields']['year'], self._data['Fields']['month'], self._data['Fields']['day'])
        time_offset = datetime.timedelta(seconds = self._data['Fields']['timestamp'])
        reftime = base_date + time_offset
        return reftime.timestamp()
    
class RawN2000Obs(RawObs):
    def __init__(self, elapsed: int, pgn: int, message: bytearray) -> None:
        parser = NMEA2000Parser()
        has_time = False
        try:
            self._data = unpack_complete_message(pgn, message)
            if not hasattr(self, '_data'):
                raise BadData()
        except KeyError:
            raise BadData()
        except PGNError:
            raise BadData()
        except ParseError:
            raise BadData()
        print(self._data)
        if pgn == 126992:
            name = 'SystemTime'
            has_time = True
        elif pgn == 127257:
            name = 'Attitude'
        elif pgn == 128267:
            name = 'Depth'
        elif pgn == 129026:
            name = 'COG'
        elif pgn == 129029:
            name = 'GNSS'
        else:
            name = 'Unrecognized'
        super().__init__(elapsed, name, has_time)

    def MatchesTimeSource(self, source: TimeSource) -> bool:
        if not self.HasTime():
            return False
        if self.Name() == 'SystemTime' and source == TimeSource.Time_SysTime:
            return True
        if self.Name() == 'GNSS' and source == TimeSource.Time_GNSS:
            return True
        return False
    
    def Timestamp(self) -> float:
        if not self.HasTime():
            return -1.0
        seconds_per_day = 24.0 * 60.0 * 60.0
        if self.Name() == 'SystemTime':
            timestamp = self._data['Fields']['date'] * seconds_per_day + self._data['Fields']['time']
        elif self.Name() == 'GNSS':
            timestamp = self._data['Fields']['msg_date'] * seconds_per_day + self._data['Fields']['msg_time']
        else:
            return -1.0
        return timestamp

def count_messages(messages: List[RawObs]) -> PktStats:
    """Determine the list of messages that are available in the input data source.

        Inputs:
            messages    List of RawObs packets (that expose Name()) to enumerate
        
        Outputs:
            PktStats    Count of statistics (and interpretation faults) observed
    """
    stats = PktStats(fault_limit=10)
    for message in messages:
        stats.Observed(message.Name())
    return stats

@dataclass
class Depth:
    t: float
    lat: float
    lon: float
    depth: float
    uncrt: float

    def __init__(self, t: float, lon: float, lat: float, depth: float, uncrt: float = -1.0) -> None:
        self.t = t
        self.lat = lat
        self.lon = lon
        self.depth = depth
        self.uncrt = uncrt
