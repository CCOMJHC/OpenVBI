import uuid
import json
import openvbi.core.metadata as md
from openvbi import version

def report_metadata(m: md.Metadata, tag: str) -> None:
    d = json.dumps(m.metadata(), indent=2)
    print(f'{tag}:')
    print(d)

# Phase 1: Mandatory metadata.  The core provider ID information, logger identifiers, and
# referencing information are REQUIRED by B.12.

# The provider name and e-mail are set by default at construction.  Note that
# this specific e-mail is not functional!
metadata = md.Metadata("OpenVBI", "hello@openvbi.org")

# The unique ID for the logger should start with the DCDB TrustedNode ID, typically
# 5-6 characters, a hyphen, and then a UUID4.  This needs to stay unique to the logger
# for the life of the installation, since DCDB uses it to group uploads.
unique_id = "OPNVBI-" + str(uuid.uuid4())

# The logger identifier and version can help post-processors understand what to expect from
# the dataset (in terms of processing, quirks, etc.)
metadata.setIdentifiers(unique_id, "WIBL", "1.5.1")

# The vertical reference defines what the depth reported is measured from; the position specifies
# where offsets are measured from.
metadata.setReferencing(md.VerticalReference.TRANSDUCER, md.VerticalReferencePosition.GNSS)

report_metadata(metadata, 'Required Metadata')

# Phase 2: Recommended metadata.  Extra information here adds to the clarity of the output, and
# is recommended, but not essential

metadata.setVessel('Private Vessel', 'White Rose of Drachs', 65.0)
metadata.setVesselID(md.VesselIdentifier.MMSI, '369958000')
metadata.addSensor(md.SensorType.SOUNDER, 'Garmin', 'GT-50', [4.2, 0.0, 5.4], draft=1.4, draftUncert = 0.2, frequency = 200000)
# Note that parameters can be set to 'None' if unknown.
metadata.addSensor(md.SensorType.GNSS, 'Litton Marine Systems', 'LMX420', position=None)

metadata.setProcessingFlags(True, True, True)
metadata.setComment('Example metadata only, not valid for post-processing')

report_metadata(metadata, 'Recommended Metadata')

# Phase 3: Processing metadata.  This section forms a lineage description of the processing
# steps that have been applied to the data since it was captured.

metadata.addProcessingAction(md.ProcessingType.ALGORITHM, None, name='Deduplication', source='OpenVBI', version=version())
metadata.addProcessingAction(md.ProcessingType.VERTREDUCTION, None, reference='ChartDatum' , datum='MLLW', method='Observed Waterlevel', model='NOAA Zone Tides')

report_metadata(metadata, 'Processing Metadata')

# Phase 4: Ensure that the metadata is valid!
valid, errors = metadata.validate()
if valid:
    print('Metadata validated!')
else:
    print('Metadata is not valid; CSBSchema said:')
    print(errors)