import time
from openvbi.adaptors.ydvr import load_data
from openvbi.timestamping.obs import generate_observations
from openvbi.filters.thresholding import shoaler_than, deeper_than
from openvbi.corrections.waterlevel.noaa import SingleStation

startTime = time.perf_counter()
data = load_data('/Users/brc/Projects-Extras/OpenVBI/ExampleData/00030095.DAT')
endTime = time.perf_counter()
print(f'LoadData:             {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

startTime = time.perf_counter()
depths = generate_observations(data, 'Depth')
endTime = time.perf_counter()
print(f'GenerateObservations: {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

print(depths)
min_depth = depths['z'].min()
max_depth = depths['z'].max()
depth_range = max_depth - min_depth
shoal_threshold = min_depth + depth_range/3.0
deep_threshold = max_depth - depth_range/3.0
print(f'Filter thresholds: shoal {shoal_threshold:.3f} m, deep {deep_threshold:.3f} m')
startTime = time.perf_counter()
shoal = shoaler_than(shoal_threshold)
deep = deeper_than(deep_threshold)
depths = deep.Execute(shoal.Execute(depths))
endTime = time.perf_counter()
print(depths)
print(f'Filters:              {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

startTime = time.perf_counter()
seattle = SingleStation('9447130')
seattle.preload(depths)
endTime = time.perf_counter()
print(f'PreloadSingleStation: {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

startTime = time.perf_counter()
depths = seattle.correct(depths)
endTime = time.perf_counter()
print(f'Correct:              {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')
