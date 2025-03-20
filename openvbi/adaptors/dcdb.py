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
from pathlib import Path
from typing import Dict,Tuple,Any
import geopandas
import pandas
import numpy as np
import json
from datetime import datetime, timezone
import openvbi.core.metadata as md
from openvbi.core.observations import Dataset

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

def write_geojson(dataset: Dataset, filename: str | Path, **kwargs) -> None:
    FMT_OBS_TIME='%Y-%m-%dT%H:%M:%S.%fZ'
    feature_lst = []
    for n in range(len(dataset.depths)):
        timestamp = datetime.fromtimestamp(dataset.depths['t'].iloc[n], tz=timezone.utc).strftime(FMT_OBS_TIME)
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    dataset.depths['lon'].iloc[n],
                    dataset.depths['lat'].iloc[n]
                ]
            },
            "properties": {
                "depth": dataset.depths['z'].iloc[n],
                "uncertainty": dataset.depths['u'].iloc[n],
                "time": timestamp
            }
        }
        feature_lst.append(dict(feature))
    data = dataset.meta.metadata()
    data['features'] = feature_lst
    with open(filename, 'w') as f:
        json.dump(data, f, **kwargs)

def write_csv_json(dataset: Dataset, basename: str | Path, **kwargs) -> None:
    match basename:
        case str():
            basepath: Path = Path(basename)
        case Path():
            basepath: Path = basename
        case _:
            raise ValueError(f"Expected basename to be of type str or Path, but it was of type {type(basename)}")

    working_depths = dataset.depths.copy()
    working_depths['TIME'] = working_depths['t'].transform(lambda x: datetime.utcfromtimestamp(x).isoformat() + 'Z')
    working_depths.to_csv(basepath.with_suffix('.csv'), columns=['lon', 'lat', 'z', 'TIME'], index=False, header=['LON', 'LAT', 'DEPTH', 'TIME'])
    meta = dataset.meta.metadata()
    meta['properties']['trustedNode']['convention'] = 'XYZ GeoJSON CSB 3.1'
    with open(basepath.with_suffix('.json'), 'w') as f:
        json.dump(meta['properties'], f, **kwargs)
