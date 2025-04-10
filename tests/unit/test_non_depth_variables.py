from pathlib import Path
import traceback

import pandas as pd

from openvbi.adaptors import factory, Loader
from openvbi.adaptors.generic_ascii import GenericASCIIWriter

from tests.fixtures import data_path, temp_path


def test_non_depth_nmea2000(data_path, temp_path):
    data_file: Path = data_path / '00010001.DAT.lzma'
    exception_thrown: bool = False
    try:
        loader: Loader = factory.get_loader(data_file)
        data = loader.load(data_file)
        data.generate_observations(['Depth', 'WaterTemperature'])
        # Write data to CSV file
        basepath = temp_path / '00010001'
        writer = GenericASCIIWriter()
        writer.write(data, basepath, columns='waterTemp')
        assert basepath.with_suffix('.csv').exists()
        # Read data back
        csv_data = pd.read_csv(basepath.with_suffix('.csv'))
        assert (2072, 5) == csv_data.shape
        assert 'LON' in csv_data
        assert 'LAT' in csv_data
        assert 'TIME' in csv_data
        assert 'DEPTH' in csv_data
        assert 'WATERTEMP' in csv_data
        assert 2072 == csv_data['LON'][~csv_data['LON'].isna()].shape[0]
        assert 2072 == csv_data['LAT'][~csv_data['LAT'].isna()].shape[0]
        assert 2072 == csv_data['TIME'][~csv_data['TIME'].isna()].shape[0]
        assert 1381 == csv_data['DEPTH'][~csv_data['DEPTH'].isna()].shape[0]
        assert 691 == csv_data['WATERTEMP'][~csv_data['WATERTEMP'].isna()].shape[0]
    except Exception as e:
        print(f"Error encountered: {str(e)}")
        print(traceback.format_exc())
        exception_thrown = True
    assert not exception_thrown
