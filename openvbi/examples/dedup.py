import time
import pandas
import geopandas
from openvbi.filters.deduplicate import deduplicate

startTime = time.perf_counter()
depths = pandas.read_csv('/Users/brc/Projects-Extras/OpenVBI/ExampleData/wibl-raw.20.csv')
depths = geopandas.GeoDataFrame(depths, geometry=geopandas.points_from_xy(depths.lon, depths.lat), crs='EPSG:4326')
endTime = time.perf_counter()
print(f'LoadData:             {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

print(depths)
startTime = time.perf_counter()
dedup = deduplicate(verbose=True)
deduped_depths = dedup.Execute(depths)
endTime = time.perf_counter()
print(deduped_depths)
print(f'Deduplicate:          {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')
