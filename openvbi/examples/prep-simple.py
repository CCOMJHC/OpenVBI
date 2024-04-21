import copy
from openvbi.adaptors.ydvr import load_data
from openvbi.filters.thresholding import shoaler_than, deeper_than
from openvbi.filters.timeslot import before_time, after_time
from openvbi.corrections.waterlevel.noaa import SingleStation, ZoneTides
from openvbi.adaptors.dcdb import write_geojson

# Pull in data from YachtDevices raw binary file, and convert to depths assuming NMEA2000 data
data = load_data('00030095.DAT')
data.generate_observations('Depth')

# Calibrate acceptable depth and time windows for data (note that these are simply for
# demonstration purposes: this cuts off a lot of valid data!)
min_depth = data.depths['z'].min()
max_depth = data.depths['z'].max()
depth_range = max_depth - min_depth
shoal_threshold = min_depth + depth_range/3.0
deep_threshold = max_depth - depth_range/3.0

min_time = data.depths['t'].min() + 10.0*60.0 # Remove first ten minutes
max_time = data.depths['t'].max() - 10.0*60.0 # Remove last ten minutes

# Generate filters for shoal/deep depth, and early/late time
shoal = shoaler_than(shoal_threshold)
deep = deeper_than(deep_threshold)
early = before_time(min_time)
late = after_time(max_time)

# Filter for depth window, and time window
data = early.Execute(late.Execute(deep.Execute(shoal.Execute(data))))

# Correct for waterlevel using NOAA zoned tides and live API for waterlevels
zone_tide_wl = ZoneTides('tide_zone_polygons_new_WGS84_merge.shp')
zone_tide_wl.preload(data)
zone_tide_wl.correct(data)

# Generate B.12-format GeoJSON output
write_geojson(data, '00030095.json', indent=2)
