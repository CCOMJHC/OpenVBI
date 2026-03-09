from pathlib import Path
from openvbi.adaptors import Loader
from openvbi.adaptors.factory import LoaderFactoryByFilename
from openvbi.adaptors.generic_ascii import GenericASCIIWriter

def main():
    data_file = '../../tests/data/00010001.DAT.lzma'
    outpath_base = '/tmp/00010001'

    loader: Loader = LoaderFactoryByFilename(Path(data_file))
    data = loader.load(data_file)
    data.generate_observations(['Depth', 'WaterTemperature'])
    writer = GenericASCIIWriter()
    writer.write(data, outpath_base, columns='waterTemp')

if __name__ == '__main__':
    main()
