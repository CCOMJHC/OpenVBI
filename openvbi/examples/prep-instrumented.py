import time
import pandas
import json
import copy
from openvbi.adaptors.ydvr import YDVRLoader
from openvbi.filters.thresholding import shoaler_than, deeper_than
from openvbi.filters.timeslot import before_time, after_time
from openvbi.corrections.waterlevel.noaa import SingleStation, ZoneTides
import openvbi.core.metadata as md

def report_metadata(m: md.Metadata, tag: str) -> None:
    d = json.dumps(m.metadata(), indent=2)
    print(f'{tag}:')
    print(d)

loader = YDVRLoader()
startTime = time.perf_counter()
data = loader.load('/data/00030095.DAT')
endTime = time.perf_counter()
print(f'LoadData:             {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

startTime = time.perf_counter()
data.generate_observations('Depth')
endTime = time.perf_counter()
print(f'GenerateObservations: {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

print('\nSource data after load:')
with pandas.option_context('display.float_format', '{:.6f}'.format):
    print(data.depths)
min_depth = data.depths['z'].min()
max_depth = data.depths['z'].max()
min_time = data.depths['t'].min() + 10.0*60.0 # Remove first ten minutes
max_time = data.depths['t'].max() - 10.0*60.0 # Remove last ten minutes
depth_range = max_depth - min_depth
shoal_threshold = min_depth + depth_range/3.0
deep_threshold = max_depth - depth_range/3.0
print(f'Depth filter thresholds: shoal {shoal_threshold:.3f} m, deep {deep_threshold:.3f} m')
print(f'Time filter thresholds: start {min_time} s, end {max_time} s')
startTime = time.perf_counter()
shoal = shoaler_than(shoal_threshold)
deep = deeper_than(deep_threshold)
early = before_time(min_time)
late = after_time(max_time)
data = early.Execute(late.Execute(deep.Execute(shoal.Execute(data))))
endTime = time.perf_counter()
print(f'Filters:              {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')
print('\nAfter filtering, source data are:')
with pandas.option_context('display.float_format', '{:.6f}'.format):
    print(data.depths)
report_metadata(data.meta, "After filter, metadata is:")

startTime = time.perf_counter()
single_station_wl = SingleStation('8726347')
single_station_wl.preload(data)
endTime = time.perf_counter()
print(f'PreloadSingleStation: {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

startTime = time.perf_counter()
zone_tide_wl = ZoneTides('/data/NOAA_tide_zones/tide_zone_polygons_new_WGS84_merge.shp')
zone_tide_wl.preload(data)
endTime = time.perf_counter()
print(f'PreloadZoneStation:   {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

src_depths = copy.deepcopy(data)
startTime = time.perf_counter()
single_station_wl.correct(src_depths)
endTime = time.perf_counter()
print(f'CorrectSingleStation: {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')
print('\nAfter single-station correction, depths are')
with pandas.option_context('display.float_format', '{:.6f}'.format):
    print(src_depths.depths)
report_metadata(src_depths.meta, 'Single Station Metadata')

src_depths = copy.deepcopy(data)
startTime = time.perf_counter()
zone_tide_wl.correct(src_depths)
endTime = time.perf_counter()
print(f'CorrectZoneTides:     {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')
print('\nAfter zone-tide correction, depths are:')
with pandas.option_context('display.float_format', '{:.6f}'.format):
    print(src_depths.depths)
report_metadata(src_depths.meta, 'Zone-tide Metadata')