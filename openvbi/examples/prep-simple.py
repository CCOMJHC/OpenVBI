from openvbi.adaptors.ydvr import YDVRLoader
from openvbi.filters.thresholding import shoaler_than, deeper_than
from openvbi.filters.timeslot import before_time, after_time
from openvbi.corrections.waterlevel.noaa import ZoneTides
from openvbi.adaptors.dcdb import GeoJSONWriter

# Pull in data from YachtDevices raw binary file, and convert to depths assuming NMEA2000 data
loader = YDVRLoader()
data = loader.load('/data/00030095.DAT')
data.generate_observations('Depth')

data.meta.setVesselName('S/V Mjölnir')

# Calibrate acceptable depth and time windows for data (note that these are simply for
# demonstration purposes: this cuts off a lot of valid data!)
min_depth = data.data['z'].min()
max_depth = data.data['z'].max()
depth_range = max_depth - min_depth
shoal_threshold = min_depth + depth_range/3.0
deep_threshold = max_depth - depth_range/3.0

min_time = data.data['t'].min() + 10.0 * 60.0 # Remove first ten minutes
max_time = data.data['t'].max() - 10.0 * 60.0 # Remove last ten minutes

# Generate filters for shoal/deep depth, and early/late time
shoal = shoaler_than(shoal_threshold)
deep = deeper_than(deep_threshold)
early = before_time(min_time)
late = after_time(max_time)

# Filter for depth window, and time window
data = early.Execute(late.Execute(deep.Execute(shoal.Execute(data))))

# Correct for waterlevel using NOAA zoned tides and live API for waterlevels
zone_tide_wl = ZoneTides('/data/NOAA_tide_zones/tide_zone_polygons_new_WGS84_merge.shp')
zone_tide_wl.preload(data)
data = zone_tide_wl.correct(data)

# Generate B.12-format GeoJSON output
writer = GeoJSONWriter()
writer.write(data, '/data/00030095.json', indent=2)
