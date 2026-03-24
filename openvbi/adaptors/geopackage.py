from pathlib import Path
import json
import sqlite3
import xml.etree.ElementTree as ET

import geopandas

import openvbi.core.metadata as md
from openvbi.core.observations import Dataset
from openvbi.adaptors import Loader, Writer

FILE_EXTENSION: str = '.gpkg'

class GeoPackageWriter(Writer):
    @staticmethod
    def suffix() -> str:
        return FILE_EXTENSION
    
    def write(self, data: Dataset, filename: str | Path, **kwargs) -> None:
        metadata = data.meta.metadata()
        data.data.to_file(filename, driver='GPKG', index=False, metadata={'OpenVBI': json.dumps(metadata)})

class GeoPackageLoader(Loader):
    @staticmethod
    def suffix() -> str:
        return FILE_EXTENSION
    
    def load(self, filename: str | Path, **kwargs) -> Dataset:
        data = geopandas.read_file(filename)
        if not set(['t', 'z', 'lon', 'lat']).issubset(data.columns):
            raise ValueError(f'file {filename} does not have minimum column set')
        
        # Unfortunately, there is no standard way of getting the metadata back from the GPKG, so we need
        # to select from the SQLite file directly, and then parse the XML that the driver writes ...
        with sqlite3.connect(filename) as con:
            records = con.execute('SELECT * from gpkg_metadata;').fetchall()
            if not records:
                raise ValueError(f'file {filename} does not have metadata records')
            
            file_metadata_records: list[str] = []
            for r in records:
                root = ET.fromstring(r[4])
                if root.tag != 'GDALMultiDomainMetadata':
                    continue
                for child in root:
                    if child.tag != 'Metadata':
                        continue
                    for record in child:
                        if record.tag != 'MDI' or record.attrib['key'] != 'OpenVBI' or not record.text:
                            continue
                        file_metadata_records.append(record.text)
            if len(file_metadata_records) != 1:
                raise ValueError('file has non-unique metadata record for OpenVBI')
            file_metadata = json.loads(file_metadata_records[0])
        meta = md.Metadata()
        meta.adopt(file_metadata)
        dataset: Dataset = Dataset()
        dataset.adopt(data, meta)
        return dataset
