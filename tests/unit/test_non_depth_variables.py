from pathlib import Path

from openvbi.adaptors import factory, Loader
from openvbi.adaptors.dcdb import CSVWriter

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
        writer = CSVWriter()
        writer.write(data, basepath)
        assert basepath.with_suffix('.csv').exists()
    except Exception as e:
        print(f"Error encountered: {str(e)}")
        exception_thrown = True
    assert not exception_thrown
