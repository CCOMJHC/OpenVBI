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

from typing import List
import datetime
from dataclasses import dataclass
import pandas
import geopandas
from marulc import NMEA0183Parser, NMEA2000Parser
from marulc.nmea2000 import unpack_complete_message, get_description_for_pgn
from marulc.exceptions import ParseError, ChecksumError, PGNError
import bitstruct
from openvbi.core.types import TimeSource, RawObs, NoDepths
from openvbi.core.statistics import PktStats
from openvbi.core.interpolation import InterpTable
import openvbi.core.metadata as md
from openvbi import version

class BadData(Exception):
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
        except bitstruct.Error:
            raise BadData()
        except TypeError:
            raise BadData()
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
            # Attempt to get the PGN name from the MARULC database.  We could do this for
            # all PGNs, but the names above are for data that we use everywhere, and we
            # want them to be consistent.
            try:
                descr = get_description_for_pgn(pgn)
                name = descr['Description']
            except ValueError:
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

def generate_depth_table(depths: List[Depth]) -> geopandas.GeoDataFrame:
    tab = pandas.DataFrame(columns=['t', 'lon', 'lat', 'z', 'u'])
    for d in depths:
        tab.loc[len(tab)] = [d.t, d.lon, d.lat, d.depth, d.uncrt]
    return geopandas.GeoDataFrame(tab, geometry=geopandas.points_from_xy(tab.lon, tab.lat), crs='EPSG:4326')

def generate_depth_list(depths: geopandas.GeoDataFrame) -> List[Depth]:
    out = list()
    for n in range(len(depths)):
        target = Depth(depths['t'][n], depths['lat'][n], depths['lon'][n], depths['z'][n], -1.0)
        if 'u' in depths:
            target.uncrt = depths['u'][n]
        out.append(target)
    return out

@dataclass
class Dataset:
    packets:    List[RawObs]
    stats:      PktStats
    timesrc:    TimeSource
    timebase:   InterpTable
    meta:       md.Metadata
    depths:     geopandas.GeoDataFrame

    def __init__(self):
        self.packets = list()
        self.stats = PktStats(fault_limit=10)
        self.timesrc = None
        self.timebase = None
        self.meta = md.Metadata()
        self.depths = None
    
    def generate_observations(self, depth: str) -> None:
        depth_table = InterpTable(['z',])
        position_table = InterpTable(['lon', 'lat'])

        for obs in self.packets:
            if obs.Name() == depth and obs.Elapsed() is not None:
                if depth == 'Depth':
                    # NMEA2000
                    depth_table.add_point(obs.Elapsed(), 'z', obs._data['Fields']['depth'])
                else:
                    # NMEA0183
                    depth_table.add_point(obs.Elapsed(), 'z', obs._data['Fields']['depth_meters'])
            if obs.Name() == 'GGA' and obs.Elapsed() is not None:
                raw_lon = obs._data['Fields']['lon']
                raw_lat = obs._data['Fields']['lat']
                if isinstance(raw_lon, float) and isinstance(raw_lat, float):
                    lon = raw_lon/100 + (raw_lon % 100)/60
                    if obs._data['Fields']['lon_dir'] == 'W':
                        lon = - lon
                    lat = raw_lat/100 + (raw_lat % 100)/60
                    if obs._data['Fields']['lat_dir'] == 'S':
                        lat = - lat
                    position_table.add_points(obs.Elapsed(), ('lon', 'lat'), (lon, lat))
            if obs.Name() == 'GNSS' and obs.Elapsed() is not None:
                lon = obs._data['Fields']['longitude']
                lat = obs._data['Fields']['latitude']
                position_table.add_points(obs.Elapsed(), ('lon', 'lat'), (lon, lat))
        
        depth_timepoints = depth_table.ind()
        if len(depth_timepoints) == 0:
            raise NoDepths()
        z = depth_table.var('z')
        z_times = self.timebase.interpolate(['ref',], depth_timepoints)[0]
        z_lat, z_lon = position_table.interpolate(['lat', 'lon'], depth_timepoints)
        
        data = pandas.DataFrame(columns=['t', 'lon', 'lat', 'z', 'u'])
        for n in range(depth_table.n_points()):
            data.loc[len(data)] = [z_times[n], z_lon[n], z_lat[n], z[n], [-1.0, -1.0, -1.0]]

        self.depths = geopandas.GeoDataFrame(data, geometry=geopandas.points_from_xy(data.lon, data.lat), crs='EPSG:4326')

        self.meta.addProcessingAction(md.ProcessingType.TIMESTAMP, None, method='Linear Interpolation', algorithm='OpenVBI', version=version())
        self.meta.addProcessingAction(md.ProcessingType.UNCERTAINTY, None, name='OpenVBI Default Uncertainty', parameters={}, version=version(), comment='Default (non-valid) uncertainty', reference='None')
        self.meta.setProcessingFlags(False, False, True)
