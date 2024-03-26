import geopandas
import time
from openvbi.adaptors.ydvr import load_data
from openvbi.core.observations import generate_depth_table
from openvbi.timestamping.obs import generate_observations
from openvbi.corrections.waterlevel.noaa import SingleStation

startTime = time.perf_counter()
data = load_data('/Users/brc/Projects-Extras/OpenVBI/ExampleData/00030095.DAT')
endTime = time.perf_counter()
print(f'LoadData:             {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

startTime = time.perf_counter()
depths = generate_observations(data, 'Depth')
endTime = time.perf_counter()
print(f'GenerateObservations: {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

startTime = time.perf_counter()
depths_table = generate_depth_table(depths)
endTime = time.perf_counter()
print(f'GenerateDepthTable:   {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

startTime = time.perf_counter()
depths_geo = geopandas.GeoDataFrame(depths_table, geometry=geopandas.points_from_xy(depths_table.lon, depths_table.lat))
depths_geo = depths_geo.set_crs(4326)
endTime = time.perf_counter()
print(f'GenerateGeoDataFrame: {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

startTime = time.perf_counter()
seattle = SingleStation('9447130')
seattle.preload(depths_geo)
endTime = time.perf_counter()
print(f'PreloadSingleStation: {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

startTime = time.perf_counter()
depths_geo = seattle.correct(depths_geo)
endTime = time.perf_counter()
print(f'Correct:              {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')
