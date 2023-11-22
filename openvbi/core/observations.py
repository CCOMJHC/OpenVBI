from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from marulc import NMEA1083Parser, NMEA2000Parser
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
        parser = NMEA1083Parser()
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
        reftime = datetime.combine(self._data['Fields']['date'], self._data['Fields']['time'])
        return reftime.timestamp()
    
class RawN2000Obs(RawObs):
    def __init__(self, elapsed: int, message: str) -> None:
        parser = NMEA2000Parser()
        has_time = False
        try:
            self._data = parser.unpack(message)
        except PGNError:
            raise BadData()
        except ParseError:
            raise BadData()
        if self._data['PGN'] == 126992:
            name = 'SystemTime'
            has_time = True
        elif self.__data['PGN'] == 128267:
            name = 'Depth'
        elif self._data['PGN'] == 129029:
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
    stats = PktStats(10)
    for message in messages:
        stats.Observed(message.Name())
    return stats
