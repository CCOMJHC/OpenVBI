import uuid

import openvbi.core.metadata as md
from openvbi.adaptors.ydvr import YDVRLoader
from openvbi.adaptors.dcdb import GeoJSONWriter
from openvbi.filters.outliers import Outliers

# Pull in data from YachtDevices raw binary file, and convert to depths assuming NMEA2000 data
print('1: Loading raw data and generating observations ...')
loader = YDVRLoader()
data = loader.load('00030095.DAT')
data.generate_observations(['Depth'])

data.meta.setProviderID("OpenVBI", "hello@openvbi.org")
unique_id = "OPNVBI-" + str(uuid.uuid4())
data.meta.setIdentifiers(unique_id, "YDVR", "1.0")
data.meta.setReferencing(md.VerticalReference.TRANSDUCER, md.VerticalReferencePosition.GNSS)
data.meta.setVessel('Private Vessel', 'S/V Mjölnir', 15)
data.meta.setVesselID(md.VesselIdentifier.MMSI, '369958000')

# Writing original dataset for reference
print('2: Writing reference dataset ...')
writer = GeoJSONWriter()
writer.write(data, '00030095-orig.json', indent=2)

# Default outlier detector
print('3: Detecting outliers ...')
detector = Outliers()
data = detector.Execute(data)

# Generate B.12-format GeoJSON output
print('4: Writing filtered dataset ...')
writer = GeoJSONWriter()
writer.write(data, '00030095-filt.json', indent=2)
