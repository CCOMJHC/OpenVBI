import uuid
from openvbi.adaptors.ydvr import YDVRLoader
import openvbi.core.metadata as md
from openvbi.adaptors.dcdb import GeoJSONWriter, CSVWriter

# In order to fill out the metadata, we need a DCDB-style Trusted Node identification string,
# and some core data for the provider and e-mail.
dcdb_id = 'OPNVBI'
provider_id = 'OpenVBI'
provider_email = 'hello@openvbi.org'

# In practice, you'd want to have a fixed unique identifier for the particular logger that you're
# working on.  Since this isn't available in the file being loaded, you'd need to look up the
# filename (or other information) in a database to translate to the unique identifier.  For example
# purposes here, we just make up a random identifier
unique_id = dcdb_id + '-' + str(uuid.uuid4())

# Load from YachtDevices, and convert into a dataframe
loader = YDVRLoader()
data = loader.load('/data/00030095.DAT')

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
data.generate_observations('Depth')

# Finally, write the output to a DCDB-compatible, IHO CSBWG B.12 GeoJSON file.  Note that the
# keyword parameters here are passed on to json.dump() directly, so you can control the output
# a little more directly.  Using "indent" here gives something that's more verbose but easier
# to read.
writer = GeoJSONWriter()
writer.write(data, '/data/00030095.json', indent=2)
writer = CSVWriter()
writer.write(data, '/data/00030095_copy', indent=2)
