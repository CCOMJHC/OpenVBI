from openvbi.adaptors.ydvr import YDVRLoader
from openvbi.adaptors.dcdb import GeoJSONWriter
from openvbi.core.metadata import Metadata, VerticalReference, VerticalReferencePosition
from openvbi.workflow import apply_workflow
from openvbi.workflow.basic_workflow import BasicWorkflow
import uuid

provider_name: str = 'OPENVBI'
provider_email: str = 'hello@openvbi.org'
vessel_name: str = 'R/V Collector'
logger_uuid: str = provider_name + '-' + str(uuid.uuid4())

meta: Metadata = Metadata()

meta.setProviderID(provider_name, provider_email)
meta.setIdentifiers(logger_uuid, 'YDVR-04N', '1.0')
meta.setReferencing(VerticalReference.TRANSDUCER.value, VerticalReferencePosition.GNSS.value)
meta.setVesselName(vessel_name)

workflow: BasicWorkflow = BasicWorkflow(YDVRLoader(), 'Depth', GeoJSONWriter(), meta)

result, processed, errors = apply_workflow('/data', '/data', workflow)

if result:
    print(f'Processing succeeded: {processed}.')
else:
    print(f'Processing succeeded: {processed}')
    print(f'Processing failed: {errors}')
