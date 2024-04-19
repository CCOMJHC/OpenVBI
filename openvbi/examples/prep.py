import time
import pandas
from openvbi.adaptors.ydvr import load_data
from openvbi.timestamping.obs import generate_observations
from openvbi.filters.thresholding import shoaler_than, deeper_than
from openvbi.filters.timeslot import before_time, after_time
from openvbi.corrections.waterlevel.noaa import SingleStation, ZoneTides

startTime = time.perf_counter()
data = load_data('/Users/brc/Projects-Extras/OpenVBI/ExampleData/00030095.DAT')
endTime = time.perf_counter()
print(f'LoadData:             {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

startTime = time.perf_counter()
depths, data.meta = generate_observations(data, 'Depth')
endTime = time.perf_counter()
print(f'GenerateObservations: {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

print('\nSource data after load:')
with pandas.option_context('display.float_format', '{:.6f}'.format):
    print(depths)
min_depth = depths['z'].min()
max_depth = depths['z'].max()
min_time = depths['t'].min() + 10.0*60.0 # Remove first ten minutes
max_time = depths['t'].max() - 10.0*60.0 # Remove last ten minutes
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
depths = early.Execute(late.Execute(deep.Execute(shoal.Execute(depths))))
endTime = time.perf_counter()
print(f'Filters:              {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')
print('\nAfter filtering, source data are:')
with pandas.option_context('display.float_format', '{:.6f}'.format):
    print(depths)

startTime = time.perf_counter()
single_station_wl = SingleStation('8726347')
single_station_wl.preload(depths)
endTime = time.perf_counter()
print(f'PreloadSingleStation: {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

startTime = time.perf_counter()
zone_tide_wl = ZoneTides('/Users/brc/Projects-Extras/OpenVBI/ExampleData/NOAA_tide_zones/tide_zone_polygons_new_WGS84_merge.shp')
zone_tide_wl.preload(depths)
endTime = time.perf_counter()
print(f'PreloadZoneStation:   {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

src_depths = depths.copy()
startTime = time.perf_counter()
single_station_wl.correct(src_depths)
endTime = time.perf_counter()
print(f'CorrectSingleStation: {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')
print('\nAfter single-station correction, depths are')
with pandas.option_context('display.float_format', '{:.6f}'.format):
    print(src_depths)

src_depths = depths.copy()
startTime = time.perf_counter()
zone_tide_wl.correct(src_depths)
endTime = time.perf_counter()
print(f'CorrectZoneTides:     {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')
print('\nAfter zone-tide correction, depths are:')
with pandas.option_context('display.float_format', '{:.6f}'.format):
    print(src_depths)
