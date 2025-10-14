##\file types.py
#
# General types for VBI data
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

from enum import Enum
from abc import ABC, abstractmethod
from typing import Tuple, Any

## Encapsulate the types of real-world time information that can be used
#
# In order to establish the relationship between the elapsed time (i.e., time of reception) of
# each packet and the real-world time, we need to use the encoded timestamps in one of the
# packets in the file.  There are a number of choices for this, depending on what type of
# data we have in there; this enumeration provides a controlled list of the options.
class TimeSource(Enum):
    ## Use NMEA2000 packet for SystemTime
    Time_SysTime = 0
    ## Use NMEA2000 packet from GNSS observations
    Time_GNSS = 1
    ## Use NMEA0183 ZDA timestamp packets
    Time_ZDA = 2
    ## Use NMEA0183 RMC minimum data with timestamps
    Time_RMC = 3

## Exception to report that no adequate source of real-world time information is available
class NoTimeSource(Exception):
    pass

class RawObs(ABC):
    def __init__(self, elapsed: float, name: str, hastime: bool) -> None:
        self._elapsed = elapsed
        self._name = name
        self._hastime = hastime
    
    def Name(self) -> str:
        return self._name
    
    def Elapsed(self) -> float:
        return self._elapsed

    def SetElapsed(self, elapsed: float) -> None:
        self._elapsed = elapsed
    
    def HasTime(self) -> bool:
        return self._hastime
    
    @abstractmethod
    def MatchesTimeSource(self, source: TimeSource) -> bool:
        pass

    @abstractmethod
    def Timestamp(self) -> float:
        pass

    @abstractmethod
    def Depth(self) -> float:
        pass

    @abstractmethod
    def Position(self) -> Tuple[float,float]:
        pass

    @abstractmethod
    def WaterTemperature(self) -> float:
        """
        Water temperature in degrees Kelvin
        :return:
        """
        pass

class NoDataFound(RuntimeError):
    pass

class NoDepths(NoDataFound):
    pass
