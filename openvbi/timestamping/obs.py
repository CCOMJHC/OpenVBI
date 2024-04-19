##\file obs.py
#
# Generate a dataset from raw observations
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

import pandas
import geopandas
from typing import Tuple, Dict, Any
from openvbi.core.observations import RawObs
from openvbi.core.types import TimeSource
from openvbi.core.interpolation import InterpTable
import openvbi.core.metadata as md
from openvbi.adaptors import Dataset
from openvbi import version

class NoDepths(RuntimeError):
    pass

def generate_observations(dataset: Dataset, depth: str) -> Tuple[geopandas.GeoDataFrame, md.Metadata]:
    depth_table = InterpTable(['z',])
    position_table = InterpTable(['lon', 'lat'])

    for obs in dataset.packets:
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
    z_times = dataset.timebase.interpolate(['ref',], depth_timepoints)[0]
    z_lat, z_lon = position_table.interpolate(['lat', 'lon'], depth_timepoints)
    
    data = pandas.DataFrame(columns=['t', 'lon', 'lat', 'z', 'u'])
    for n in range(depth_table.n_points()):
        data.loc[len(data)] = [z_times[n], z_lon[n], z_lat[n], z[n], [-1.0, -1.0, -1.0]]

    if dataset.meta is None:
        # Metadata hasn't been set yet, so we generate a default input
        dataset.meta = md.Metadata()
    dataset.meta.addProcessingAction(md.ProcessingType.TIMESTAMP, None, method='Linear Interpolation', algorithm='OpenVBI', version=version())
    dataset.meta.addProcessingAction(md.ProcessingType.UNCERTAINTY, None, name='OpenVBI Default Uncertainty', parameters={}, version=version(), comment='Default (non-valid) uncertainty', reference='None')
    dataset.meta.setProcessingFlags(False, False, True)
    
    return geopandas.GeoDataFrame(data, geometry=geopandas.points_from_xy(data.lon, data.lat), crs='EPSG:4326'), dataset.meta
