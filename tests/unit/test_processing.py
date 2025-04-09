from pathlib import Path
import uuid

from openvbi.adaptors import factory, Loader
import openvbi.core.metadata as md
from openvbi.adaptors.dcdb import GeoJSONWriter, CSVWriter

from tests.fixtures import data_path, temp_path

def test_basic_processing(data_path, temp_path):
    ydvr_file: Path = data_path / '00030011.DAT.lzma'
    exception_thrown: bool = False

    try:
        # Load data from compressed YachtDevices file, and convert into a dataframe
        loader: Loader = factory.get_loader(ydvr_file)
        data = loader.load(ydvr_file, compressed=ydvr_file.suffix == '.lzma')
    except Exception as e:
        exception_thrown = True
    assert not exception_thrown

    # In order to fill out the metadata, we need a DCDB-style Trusted Node identification string,
    # and some core data for the provider and e-mail.
    dcdb_id = 'OPNVBI'
    provider_id = 'OpenVBI'
    provider_email = 'hello@openvbi.org'

    # In practice, you'd want to have a fixed unique identifier for the particular logger that you're
    # working on.  Since this isn't available in the file being loaded, you'd need to look up the
    # filename (or other information) in a database to translate to the unique identifier.  For example
    # purposes here, we just make up a random identifier
    unique_id_uuid: uuid.UUID = uuid.UUID('aa880fb6-1e46-42ab-b0b4-e714c94f84e5')
    unique_id = dcdb_id + '-' + str(unique_id_uuid)

    # Since there isn't a lot of information on the logger from the datafile, we need to populate the
    # metadata separately.  We focus here on the mandatory metadata.  In practice, you would probably want
    # to look up the unique identifier in a database of loggers, and pick out the appropriate metadata (or
    # potentially a pre-formatted object).
    data.meta = md.Metadata()
    data.meta.setProviderID(provider_id, provider_email)
    data.meta.setIdentifiers(unique_id, 'YDVR', '1.0')
    data.meta.setReferencing(md.VerticalReference.TRANSDUCER, md.VerticalReferencePosition.GNSS)
    data.meta.setVesselID(md.VesselIdentifier.MMSI, "000000000")

    # YachtDevices is a NMEA2000 device, so we convert 'Depth' messages for depth information
    data.generate_observations(['Depth'])

    gjson_path = temp_path / '00030095.json'
    writer = GeoJSONWriter()
    writer.write(data, gjson_path, indent=2)
    assert gjson_path.exists()
    # Don't compare to exact file size as file sizes can vary across filesystem types
    assert gjson_path.stat().st_size >= 263000

    basepath = temp_path / '00030095_copy'
    writer = CSVWriter()
    writer.write(data, basepath, indent=2)
    assert basepath.with_suffix('.csv').exists()
    # Don't compare to exact file size as file sizes can vary across filesystem types
    assert basepath.with_suffix('.csv').stat().st_size >= 46000
    assert basepath.with_suffix('.json').exists()
    # Don't compare to exact file size as file sizes can vary across filesystem types
    assert basepath.with_suffix('.json').stat().st_size >= 1000
