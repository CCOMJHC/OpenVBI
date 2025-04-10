from pathlib import Path
import uuid

from openvbi.adaptors import factory, Loader
import openvbi.core.metadata as md

from tests.fixtures import data_path, temp_path


def test_ydvr_non_depth(data_path, temp_path):
    ydvr_file: Path = data_path / '00030011.DAT.lzma'
    exception_thrown: bool = False

    try:
        # Load data from compressed YachtDevices file, and convert into a dataframe
        loader: Loader = factory.get_loader(ydvr_file)
        data = loader.load(ydvr_file)
        data.generate_observations(['Depth'])
    except Exception as e:
        exception_thrown = True
    assert not exception_thrown
