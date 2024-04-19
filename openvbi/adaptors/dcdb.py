##\file dcdb.py
#
# Read files of DCDB data
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

from typing import Dict,Tuple,Any
import geopandas
import pandas
import numpy as np
import json
from datetime import datetime, timezone
import openvbi.core.metadata as md

def load_csv_data(filename: str) -> Tuple[geopandas.GeoDataFrame, md.Metadata]:
    data = geopandas.read_file(filename)
    data = data.rename(columns={'DEPTH': 'z', 'LON': 'lon', 'LAT': 'lat'})
    data['t'] = np.fromiter((t.timestamp() for t in pandas.to_datetime(data['TIME'])), dtype='float')
    
    logger_uuid = data['UNIQUE_ID'].unique()[0]
    file_uuid = data['FILE_UUID'].unique()[0]
    ship_name = data['PLATFORM_NAME'].unique()[0]
    provider = data['PROVIDER'].unique()[0]
    
    data = data.drop(columns=['TIME', 'UNIQUE_ID','FILE_UUID', 'PROVIDER', 'PLATFORM_NAME'])
    data = data.astype({'z':'float'})
    data = data.dropna(subset=['t'])

    meta = md.Metadata()
    meta.setProviderID(provider, 'UNKNOWN')
    meta.setIdentifiers(logger_uuid, 'UNKNOWN', 'UNKNOWN')
    meta.setReferencing(md.VerticalReference.UNKNOWN, md.VerticalReferencePosition.GNSS)
    meta.setVessel('UNKNOWN', ship_name, -1.0)

    return geopandas.GeoDataFrame(data, geometry=geopandas.points_from_xy(data.lon, data.lat), crs='EPSG:4326'), meta

def write_geojson(meta: md.Metadata, depths: geopandas.GeoDataFrame, filename: str, **kwargs) -> None:
    FMT_OBS_TIME='%Y-%m-%dT%H:%M:%S.%fZ'
    feature_lst = []
    for n in range(len(depths)):
        timestamp = datetime.fromtimestamp(depths['t'].iloc[n], tz=timezone.utc).strftime(FMT_OBS_TIME)
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    depths['lon'].iloc[n],
                    depths['lat'].iloc[n]
                ]
            },
            "properties": {
                "depth": depths['z'].iloc[n],
                "uncertainty": depths['u'].iloc[n],
                "time": timestamp
            }
        }
        feature_lst.append(dict(feature))
    data = meta.metadata()
    data['features'] = feature_lst
    with open(filename, 'w') as f:
        json.dump(data, f, **kwargs)
