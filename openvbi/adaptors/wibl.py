#@file wibl.py
#@brief Adaptor for OpenVBI to load WIBL files using the underlying WIBL library
#
# This provides a load_data() adaptor function with options for a calibration offset and analysis
# window duration that can be used as for OpenVBI to open a WIBL data file and read it into a
# dataset compatible with OpenVBI's Dataset object.
#
# Copyright (c) 2024, University of New Hampshire, Center for Coastal and Ocean Mapping.  All Rights Reserved.

# This operates like a file adapter in OpenVBI, except that it uses the WIBL
# file loading mechanisms to read the binary data and translate into RawObs
# packets that can be stored in the TCBDataset object for further processing

import json
from typing import Dict, Any
import openvbi.adaptors.logger_file as LoggerFile
from openvbi.core.observations import RawN0183Obs, ParsedN2000, Dataset
from openvbi.core.metadata import VerticalReference, VerticalReferencePosition

def load_data(filename: str) -> Dataset:
    data: Dataset = Dataset()
    logger_UUID: str = 'NONE'
    ship_name: str = 'Anonymous'
    firmware_version: str = '0.0.0'

    with open(filename, 'rb') as f:
        source = LoggerFile.PacketFactory(f)
        while source.has_more():
            try:
                pkt = source.next_packet()
                packet = None
                if pkt is None:
                    continue
                if pkt.name() == 'Metadata':
                    # This is mandatory, so we should get at least minimal identification
                    logger_UUID = pkt.logger_name
                    ship_name = pkt.ship_name
                if pkt.name() == 'SerialiserVersion':
                    # This is mandatory
                    firmware_version = f'{pkt.major}.{pkt.minor}, N0183 {pkt.nmea0183_version}, N2000 {pkt.nmea2000_version}, IMU {pkt.imu_version}'
                if pkt.name() == 'JSONMetadata':
                    # This is optional
                    metadata = json.loads(pkt.metadata_element.decode('utf-8'))
                    data.meta.adopt(metadata)
                if pkt.name() == 'SerialString':
                    # Raw NMEA0183 strings
                    packet = RawN0183Obs(pkt.elapsed, pkt.data.decode('utf-8').strip())
                if pkt.name() == 'Depth' or pkt.name() == 'GNSS' or pkt.name() == 'SystemTime':
                    # NMEA2000 data for depth, position, and time
                    packet = ParsedN2000(pkt.elapsed, pkt)
                if packet is not None:
                    data.packets.append(packet)
                    data.stats.Observed(packet.Name())
            except LoggerFile.PacketTranscriptionError:
                pass
    
    data.meta.setIdentifiers(logger_UUID, ship_name, firmware_version)
    # In a WIBL file, it's possible that you have a full JSON metadata record embedded in the file,
    # and therefore you don't want to just over-ride the metadata --- it could be set for you!  We
    # therefore check whether the "NOTSET" detault from metadata.py is still set in some useful
    # places, and give them useful defaults if so.
    current_meta: Dict[str,Any] = data.meta.metadata()
    if current_meta['properties']['trustedNode']['providerOrganizationName'] == 'NOTSET':
        data.meta.setProviderID('OpenVBI', 'hello@openvbi.org')
    if current_meta['properties']['trustedNode']['verticalReferenceOfDepth'] == 'NOTSET':
        data.meta.setReferencing(VerticalReference.TRANSDUCER.value, VerticalReferencePosition.TRANSDUCER.value)
    data.add_timebase()

    return data
