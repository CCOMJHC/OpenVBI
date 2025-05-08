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

from collections.abc import Collection
from typing import List, Tuple
import datetime
from dataclasses import dataclass

import pandas
import geopandas

from marulc import NMEA0183Parser, NMEA2000Parser
from marulc.nmea2000 import unpack_complete_message, get_description_for_pgn
from marulc.exceptions import ParseError, ChecksumError, PGNError

import bitstruct

from openvbi.core.types import TimeSource, RawObs, NoDataFound
from openvbi.core.statistics import PktStats
from openvbi.core.interpolation import InterpTable
from openvbi.core.timebase import determine_time_source, generate_timebase
import openvbi.core.metadata as md
import openvbi.core.unit_conversion as uc
from openvbi import version
from openvbi.adaptors.logger_file import DataPacket


DEPENDENT_VARS = {'Depth': 'z',                     # NMEA2000
                  'DPT': 'z',                       # NMEA0183
                  'DBT': 'z',                       # NMEA0183
                  'WaterTemperature': 'waterTemp',  # NMEA2000
                  'MTW': 'waterTemp'                # NMEA0183
                 }


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

        match self.Name():
            case 'ZDA':
                base_date = datetime.datetime(self._data['Fields']['year'], self._data['Fields']['month'], self._data['Fields']['day'])
                time_offset = datetime.timedelta(seconds = self._data['Fields']['timestamp'])
            case 'RMC':
                base_date = datetime.datetime.strptime(str(self._data['Fields']['datestamp']), '%d%m%y')
                time_offset = datetime.datetime.strptime(str(self._data['Fields']['timestamp']), '%H%M%S') - datetime.datetime(1900, 1, 1)
            case _:
                raise ValueError(f"Unable to parse timestamp for NMEA0183 message of name {self.Name()}")

        reftime = (base_date + time_offset).astimezone(tz=datetime.timezone.utc)
        return reftime.timestamp()
    
    def Depth(self) -> float:
        if self.Name() != 'DPT' and self.Name() != 'DBT':
            raise BadData()
        return self._data['Fields']['depth_meters']

    def Position(self) -> Tuple[float,float]:
        if self.Name() != 'GGA':
            raise BadData()
        raw_lon = self._data['Fields']['lon']
        raw_lat = self._data['Fields']['lat']
        if not isinstance(raw_lon, float) or not isinstance(raw_lat, float):
            raise BadData()
        lon = int(raw_lon/100) + (raw_lon % 100)/60
        if self._data['Fields']['lon_dir'] == 'W':
            lon = - lon
        lat = int(raw_lat/100) + (raw_lat % 100)/60
        if self._data['Fields']['lat_dir'] == 'S':
            lat = - lat
        return (lon, lat)

    def WaterTemperature(self) -> float:
        if self.Name() != 'MTW':
            raise BadData()
        temp = float(self._data['Fields']['temperature'])
        unit = self._data['Fields']['units']
        return uc.to_temperature_kelvin(temp, unit)


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
        elif pgn == 130577:
            name = 'DirectionData'
        elif pgn == 130316 and self._data['Fields']['source'] == 0:
            name = 'WaterTemperature'
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
    
    def Depth(self) -> float:
        if self.Name() != 'Depth':
            raise BadData()
        return self._data['Fields']['depth']

    def Position(self) -> Tuple[float,float]:
        match self.Name():
            case 'GNSS' | 'Position, Rapid Update':
                lon = self._data['Fields']['longitude']
                lat = self._data['Fields']['latitude']
                return lon, lat
            case _:
                raise BadData()

    def WaterTemperature(self) -> float:
        if self.Name() != 'WaterTemperature':
            raise BadData()
        temp = float(self._data['Fields']['temperature'])
        return uc.to_temperature_kelvin(temp, 'K')


class ParsedN2000(RawObs):
    def __init__(self, elapsed: int, data: DataPacket) -> None:
        if data.name() == 'SystemTime' or data.name() == 'GNSS':
            has_time = True
        else:
            has_time = False
        super().__init__(elapsed, data.name(), has_time)
        self._data = data
        
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
            timestamp = self._data.date * seconds_per_day + self._data.timestamp
        elif self.Name() == 'GNSS':
            timestamp = self._data.msg_date * seconds_per_day + self._data.msg_timestamp
        else:
            return -1.0
        return timestamp

    def Depth(self) -> float:
        if self.Name() != 'Depth':
            raise BadData()
        return self._data.depth

    def Position(self) -> Tuple[float,float]:
        if self.Name() != 'GNSS':
            raise BadData()
        return (self._data.longitude, self._data.latitude)

    def WaterTemperature(self) -> float:
        if self.Name() != 'WaterTemperature':
            raise BadData()
        if self._data.tempSource != 0:
            raise BadData()
        return self._data.temperature

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
    data:       geopandas.GeoDataFrame

    def __init__(self):
        self.packets = list()
        self.stats = PktStats(fault_limit=10)
        self.timesrc = None
        self.timebase = None
        self.meta = md.Metadata()
        self.data = None

    def add_timebase(self) -> None:
        '''This determines, given a list ot raw packets, which time source should be used for
        generating the time lookup tables, and then generates the lookup table from the relevant
        messages using this source.  This is typically done by the loader code in openvbi.adaptors
        but is included here for completeness.
        '''
        self.timesrc = determine_time_source(self.stats)
        self.timebase = generate_timebase(self.packets, self.timesrc)


    def generate_observations(self, obs_vars: Collection[str]) -> None:
        vars = set()
        for ov in obs_vars:
            if ov not in DEPENDENT_VARS.keys():
                raise ValueError(f"Unknown observation variable {ov}")
            vars.add(DEPENDENT_VARS[ov])
        dep_var_table = InterpTable(vars)
        position_table = InterpTable(['lon', 'lat'])

        for obs in self.packets:
            if obs.Elapsed() is None:
                continue
            obs_name = obs.Name()
            if obs_name in obs_vars:
                val = None
                match obs_name:
                    case 'Depth' | 'DPT' | 'DBT':
                        val = obs.Depth()
                    case 'WaterTemperature' | 'MTW':
                        val = obs.WaterTemperature()
                if val is not None:
                    dep_var_table.add_point(obs.Elapsed(), DEPENDENT_VARS[obs_name], val)
            elif obs_name in ['GGA', 'GNSS']:
                position_table.add_points(obs.Elapsed(), ('lon', 'lat'), obs.Position())
            elif obs_name == 'Position, Rapid Update':
                position_table.add_points(obs.Elapsed(), ('lon', 'lat'), obs.Position())

        dep_var_timepoints = dep_var_table.ind()
        if len(dep_var_timepoints) == 0:
            raise NoDataFound()
        dep_vars = {}
        for v in vars:
            dep_vars[v] = dep_var_table.var(v)
        times = self.timebase.interpolate(['ref', ], dep_var_timepoints)[0]
        lat, lon = position_table.interpolate(['lat', 'lon'], dep_var_timepoints)

        dep_cols = list(dep_vars.keys())
        cols = ['t', 'lon', 'lat'] + dep_cols
        emit_u: bool = False
        if 'z' in vars:
            cols += 'u'
            emit_u: bool = True

        data = pandas.DataFrame(columns=cols)
        for n in range(dep_var_table.n_points()):
            row = [times[n], lon[n], lat[n]]
            for dep_var in dep_vars.values():
                row.append(dep_var[n])
            if emit_u:
                row.append([-1.0, -1.0, -1.0])
            data.loc[len(data)] = row

        self.data = geopandas.GeoDataFrame(data, geometry=geopandas.points_from_xy(data.lon, data.lat), crs='EPSG:4326')

        self.meta.addProcessingAction(md.ProcessingType.TIMESTAMP, None, method='Linear Interpolation', algorithm='OpenVBI', version=version())
        self.meta.addProcessingAction(md.ProcessingType.UNCERTAINTY, None, name='OpenVBI Default Uncertainty', parameters={}, version=version(), comment='Default (non-valid) uncertainty', reference='None')
        self.meta.setProcessingFlags(False, False, True)
