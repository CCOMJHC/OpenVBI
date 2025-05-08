# Plans for future development of OpenVBI

## Adding support for speed over ground

### NMEA 0183
Support for the following NMEA 0138 sentences would be necessary for providing SOG from logger files (see 
[here](https://github.com/MO-RISE/marulc/blob/master/marulc/nmea0183_sentence_formatters.json#L857C9-L905C11)):
```json
{
  "RMA": {
    "Fields": [
      {
        "Id": "data_status",
        "Description": "Data status"
      },
      {
        "Id": "lat",
        "Description": "Latitude"
      },
      {
        "Id": "lat_dir",
        "Description": "Latitude Direction"
      },
      {
        "Id": "lon",
        "Description": "Longitude"
      },
      {
        "Id": "lon_dir",
        "Description": "Longitude Direction"
      },
      {
        "Id": "not_used_1",
        "Description": "Not Used 1"
      },
      {
        "Id": "not_used_2",
        "Description": "Not Used 2"
      },
      {
        "Id": "spd_over_grnd",
        "Description": "Speed over ground"
      },
      {
        "Id": "crse_over_grnd",
        "Description": "Course over ground"
      },
      {
        "Id": "variation",
        "Description": "Variation"
      },
      {
        "Id": "var_dir",
        "Description": "Variation Direction"
      }
    ],
    "Description": ""
  }
}
```

Also for SOG 
(see [here](https://github.com/MO-RISE/marulc/blob/master/marulc/nmea0183_sentence_formatters.json#L963C9-L1019C11)):
```json
{
  "RMC": {
    "Fields": [
      {
        "Id": "timestamp",
        "Description": "Timestamp"
      },
      {
        "Id": "status",
        "Description": "Status"
      },
      {
        "Id": "lat",
        "Description": "Latitude"
      },
      {
        "Id": "lat_dir",
        "Description": "Latitude Direction"
      },
      {
        "Id": "lon",
        "Description": "Longitude"
      },
      {
        "Id": "lon_dir",
        "Description": "Longitude Direction"
      },
      {
        "Id": "spd_over_grnd",
        "Description": "Speed Over Ground"
      },
      {
        "Id": "true_course",
        "Description": "True Course"
      },
      {
        "Id": "datestamp",
        "Description": "Datestamp"
      },
      {
        "Id": "mag_variation",
        "Description": "Magnetic Variation"
      },
      {
        "Id": "mag_var_dir",
        "Description": "Magnetic Variation Direction"
      },
      {
        "Id": "mode_indicator",
        "Description": "Mode Indicator"
      },
      {
        "Id": "nav_status",
        "Description": "Navigational Status"
      }
    ],
    "Description": "Recommended Minimum Specific GPS/TRANSIT Data"
  }
}
```

### NMEA 2000
Support for the following NMEA 2000 PGNs would be necessary for providing SOG from logger files
(see [here](https://github.com/MO-RISE/marulc/blob/master/marulc/nmea2000_pgn_specifications.json#L12108C7-L12178C31) 
for more info):
```json
 {
     "PGN": 129026,
     "Id": "cogSogRapidUpdate",
     "Description": "COG & SOG, Rapid Update",
     "Type": "Single",
     "Complete": true,
     "Length": 8,
     "RepeatingFields": 0,
     "Fields": [
         {
             "Order": 1,
             "Id": "sid",
             "Name": "SID",
             "BitLength": 8,
             "BitOffset": 0,
             "BitStart": 0,
             "Signed": false},
         {
             "Order": 2,
             "Id": "cogReference",
             "Name": "COG Reference",
             "BitLength": 2,
             "BitOffset": 8,
             "BitStart": 0,
             "Type": "Lookup table",
             "Signed": false,
             "EnumValues": [
                 {"name": "True", "value": "0"},
                 {"name": "Magnetic", "value": "1"},
                 {"name": "Error", "value": "2"},
                 {"name": "Null", "value": "3"}]},
         {
             "Order": 3,
             "Id": "reserved",
             "Name": "Reserved",
             "Description": "Reserved",
             "BitLength": 6,
             "BitOffset": 10,
             "BitStart": 2,
             "Type": "Binary data",
             "Signed": false},
         {
             "Order": 4,
             "Id": "cog",
             "Name": "COG",
             "BitLength": 16,
             "BitOffset": 16,
             "BitStart": 0,
             "Units": "rad",
             "Resolution": "0.0001",
             "Signed": false},
         {
             "Order": 5,
             "Id": "sog",
             "Name": "SOG",
             "BitLength": 16,
             "BitOffset": 32,
             "BitStart": 0,
             "Units": "m/s",
             "Resolution": "0.01",
             "Signed": false},
         {
             "Order": 6,
             "Id": "reserved",
             "Name": "Reserved",
             "Description": "Reserved",
             "BitLength": 16,
             "BitOffset": 48,
             "BitStart": 0,
             "Type": "Binary data",
             "Signed": false}]},
```

Also for SOG (see [here](https://github.com/MO-RISE/marulc/blob/master/marulc/nmea2000_pgn_specifications.json#L22404C7-L22524C31)
for more info):
```json
 {
     "PGN": 130577,
     "Id": "directionData",
     "Description": "Direction Data",
     "Type": "Fast",
     "Complete": false,
     "Missing": [
         "Fields",
         "FieldLengths",
         "Precision",
         "SampleData"],
     "Length": 14,
     "RepeatingFields": 0,
     "Fields": [
         {
             "Order": 1,
             "Id": "dataMode",
             "Name": "Data Mode",
             "BitLength": 4,
             "BitOffset": 0,
             "BitStart": 0,
             "Type": "Lookup table",
             "Signed": false,
             "EnumValues": [
                 {"name": "Autonomous", "value": "0"},
                 {"name": "Differential enhanced", "value": "1"},
                 {"name": "Estimated", "value": "2"},
                 {"name": "Simulator", "value": "3"},
                 {"name": "Manual", "value": "4"}]},
         {
             "Order": 2,
             "Id": "cogReference",
             "Name": "COG Reference",
             "BitLength": 2,
             "BitOffset": 4,
             "BitStart": 4,
             "Type": "Lookup table",
             "Signed": false,
             "EnumValues": [
                 {"name": "True", "value": "0"},
                 {"name": "Magnetic", "value": "1"},
                 {"name": "Error", "value": "2"},
                 {"name": "Null", "value": "3"}]},
         {
             "Order": 3,
             "Id": "reserved",
             "Name": "Reserved",
             "Description": "Reserved",
             "BitLength": 2,
             "BitOffset": 6,
             "BitStart": 6,
             "Type": "Binary data",
             "Signed": false},
         {
             "Order": 4,
             "Id": "sid",
             "Name": "SID",
             "BitLength": 8,
             "BitOffset": 8,
             "BitStart": 0,
             "Signed": false},
         {
             "Order": 5,
             "Id": "cog",
             "Name": "COG",
             "BitLength": 16,
             "BitOffset": 16,
             "BitStart": 0,
             "Units": "rad",
             "Resolution": "0.0001",
             "Signed": false},
         {
             "Order": 6,
             "Id": "sog",
             "Name": "SOG",
             "BitLength": 16,
             "BitOffset": 32,
             "BitStart": 0,
             "Units": "m/s",
             "Resolution": "0.01",
             "Signed": false},
         {
             "Order": 7,
             "Id": "heading",
             "Name": "Heading",
             "BitLength": 16,
             "BitOffset": 48,
             "BitStart": 0,
             "Units": "rad",
             "Resolution": "0.0001",
             "Signed": false},
         {
             "Order": 8,
             "Id": "speedThroughWater",
             "Name": "Speed through Water",
             "BitLength": 16,
             "BitOffset": 64,
             "BitStart": 0,
             "Units": "m/s",
             "Resolution": "0.01",
             "Signed": false},
         {
             "Order": 9,
             "Id": "set",
             "Name": "Set",
             "BitLength": 16,
             "BitOffset": 80,
             "BitStart": 0,
             "Units": "rad",
             "Resolution": "0.0001",
             "Signed": false},
         {
             "Order": 10,
             "Id": "drift",
             "Name": "Drift",
             "BitLength": 16,
             "BitOffset": 96,
             "BitStart": 0,
             "Units": "m/s",
             "Resolution": "0.01",
             "Signed": false}]},
```

## Adding support for wind data

### NMEA 0183
Support for the following NMEA 0138 sentences would be necessary for providing wind data from logger files
(see [here](https://github.com/MO-RISE/marulc/blob/master/marulc/nmea0183_sentence_formatters.json#L1361C9-L1422C11)):
```json
{
  "MWD": {
    "Fields": [
      {
        "Id": "direction_true",
        "Description": "Wind direction true"
      },
      {
        "Id": "true",
        "Description": "True"
      },
      {
        "Id": "direction_magnetic",
        "Description": "Wind direction magnetic"
      },
      {
        "Id": "magnetic",
        "Description": "Magnetic"
      },
      {
        "Id": "wind_speed_knots",
        "Description": "Wind speed knots"
      },
      {
        "Id": "knots",
        "Description": "Knots"
      },
      {
        "Id": "wind_speed_meters",
        "Description": "Wind speed meters/second"
      },
      {
        "Id": "meters",
        "Description": "Wind speed"
      }
    ],
    "Description": "Wind Direction\n    NMEA 0183 standard Wind Direction and Speed, with respect to north."
  }, 
 "MWV": {
     "Fields": [
         {
             "Id": "wind_angle",
             "Description": "Wind angle"
         },
         {
             "Id": "reference",
             "Description": "Reference"
         },
         {
             "Id": "wind_speed",
             "Description": "Wind speed"
         },
         {
             "Id": "wind_speed_units",
             "Description": "Wind speed units"
         },
         {
             "Id": "status",
             "Description": "Status"
         }
     ],
     "Description": "Wind Speed and Angle\n    NMEA 0183 standard Wind Speed and Angle, in relation to the vessel's\n    bow/centerline."
 }
}
```

Also need heading and speed through water to go from apparent to magnetic/true wind direction 
(see [here](https://github.com/MO-RISE/marulc/blob/master/marulc/nmea0183_sentence_formatters.json#L1478C9-L1514C11)
for more info):
```json
 {
  "VHW": {
    "Fields": [
      {
        "Id": "heading_true",
        "Description": "Heading true degrees"
      },
      {
        "Id": "true",
        "Description": "heading true"
      },
      {
        "Id": "heading_magnetic",
        "Description": "Heading Magnetic degrees"
      },
      {
        "Id": "magnetic",
        "Description": "Magnetic"
      },
      {
        "Id": "water_speed_knots",
        "Description": "Water speed knots"
      },
      {
        "Id": "knots",
        "Description": "Knots"
      },
      {
        "Id": "water_speed_km",
        "Description": "Water speed kilometers"
      },
      {
        "Id": "kilometers",
        "Description": "Kilometers"
      }
    ],
    "Description": "Water Speed and Heading"
  }
}
```

### NMEA 2000
Support for the following NMEA 2000 PGNs would be necessary for providing wind data from logger files
(see [here](https://github.com/MO-RISE/marulc/blob/master/marulc/nmea2000_pgn_specifications.json#L19739C7-L19799C31) 
for more info):
```json
 {
     "PGN": 130306,
     "Id": "windData",
     "Description": "Wind Data",
     "Type": "Single",
     "Complete": true,
     "Length": 8,
     "RepeatingFields": 0,
     "Fields": [
         {
             "Order": 1,
             "Id": "sid",
             "Name": "SID",
             "BitLength": 8,
             "BitOffset": 0,
             "BitStart": 0,
             "Signed": false},
         {
             "Order": 2,
             "Id": "windSpeed",
             "Name": "Wind Speed",
             "BitLength": 16,
             "BitOffset": 8,
             "BitStart": 0,
             "Units": "m/s",
             "Resolution": "0.01",
             "Signed": false},
         {
             "Order": 3,
             "Id": "windAngle",
             "Name": "Wind Angle",
             "BitLength": 16,
             "BitOffset": 24,
             "BitStart": 0,
             "Units": "rad",
             "Resolution": "0.0001",
             "Signed": false},
         {
             "Order": 4,
             "Id": "reference",
             "Name": "Reference",
             "BitLength": 3,
             "BitOffset": 40,
             "BitStart": 0,
             "Type": "Lookup table",
             "Signed": false,
             "EnumValues": [
                 {"name": "True (ground referenced to North)", "value": "0"},
                 {"name": "Magnetic (ground referenced to Magnetic North)", "value": "1"},
                 {"name": "Apparent", "value": "2"},
                 {"name": "True (boat referenced)", "value": "3"},
                 {"name": "True (water referenced)", "value": "4"}]},
         {
             "Order": 5,
             "Id": "reserved",
             "Name": "Reserved",
             "BitLength": 21,
             "BitOffset": 43,
             "BitStart": 3,
             "Type": "Binary data",
             "Signed": false}]},
```

Also need heading and speed through water to go from apparent to magnetic/true wind direction:
Heading (see [here](https://github.com/MO-RISE/marulc/blob/master/marulc/nmea2000_pgn_specifications.json#L8461C7-L8531C31)
for more information):
```json

 {
     "PGN": 127250,
     "Id": "vesselHeading",
     "Description": "Vessel Heading",
     "Type": "Single",
     "Complete": true,
     "Length": 8,
     "RepeatingFields": 0,
     "Fields": [
         {
             "Order": 1,
             "Id": "sid",
             "Name": "SID",
             "BitLength": 8,
             "BitOffset": 0,
             "BitStart": 0,
             "Signed": false},
         {
             "Order": 2,
             "Id": "heading",
             "Name": "Heading",
             "BitLength": 16,
             "BitOffset": 8,
             "BitStart": 0,
             "Units": "rad",
             "Resolution": "0.0001",
             "Signed": false},
         {
             "Order": 3,
             "Id": "deviation",
             "Name": "Deviation",
             "BitLength": 16,
             "BitOffset": 24,
             "BitStart": 0,
             "Units": "rad",
             "Resolution": "0.0001",
             "Signed": true},
         {
             "Order": 4,
             "Id": "variation",
             "Name": "Variation",
             "BitLength": 16,
             "BitOffset": 40,
             "BitStart": 0,
             "Units": "rad",
             "Resolution": "0.0001",
             "Signed": true},
         {
             "Order": 5,
             "Id": "reference",
             "Name": "Reference",
             "BitLength": 2,
             "BitOffset": 56,
             "BitStart": 0,
             "Type": "Lookup table",
             "Signed": false,
             "EnumValues": [
                 {"name": "True", "value": "0"},
                 {"name": "Magnetic", "value": "1"},
                 {"name": "Error", "value": "2"},
                 {"name": "Null", "value": "3"}]},
         {
             "Order": 6,
             "Id": "reserved",
             "Name": "Reserved",
             "Description": "Reserved",
             "BitLength": 6,
             "BitOffset": 58,
             "BitStart": 2,
             "Type": "Binary data",
             "Signed": false}]},
 ```

Speed through water (while we're at it, get speed over ground; 
see [here](https://github.com/MO-RISE/marulc/blob/master/marulc/nmea2000_pgn_specifications.json#L22404C7-L22524C31)
for more info):
```json
 {
     "PGN": 130577,
     "Id": "directionData",
     "Description": "Direction Data",
     "Type": "Fast",
     "Complete": false,
     "Missing": [
         "Fields",
         "FieldLengths",
         "Precision",
         "SampleData"],
     "Length": 14,
     "RepeatingFields": 0,
     "Fields": [
         {
             "Order": 1,
             "Id": "dataMode",
             "Name": "Data Mode",
             "BitLength": 4,
             "BitOffset": 0,
             "BitStart": 0,
             "Type": "Lookup table",
             "Signed": false,
             "EnumValues": [
                 {"name": "Autonomous", "value": "0"},
                 {"name": "Differential enhanced", "value": "1"},
                 {"name": "Estimated", "value": "2"},
                 {"name": "Simulator", "value": "3"},
                 {"name": "Manual", "value": "4"}]},
         {
             "Order": 2,
             "Id": "cogReference",
             "Name": "COG Reference",
             "BitLength": 2,
             "BitOffset": 4,
             "BitStart": 4,
             "Type": "Lookup table",
             "Signed": false,
             "EnumValues": [
                 {"name": "True", "value": "0"},
                 {"name": "Magnetic", "value": "1"},
                 {"name": "Error", "value": "2"},
                 {"name": "Null", "value": "3"}]},
         {
             "Order": 3,
             "Id": "reserved",
             "Name": "Reserved",
             "Description": "Reserved",
             "BitLength": 2,
             "BitOffset": 6,
             "BitStart": 6,
             "Type": "Binary data",
             "Signed": false},
         {
             "Order": 4,
             "Id": "sid",
             "Name": "SID",
             "BitLength": 8,
             "BitOffset": 8,
             "BitStart": 0,
             "Signed": false},
         {
             "Order": 5,
             "Id": "cog",
             "Name": "COG",
             "BitLength": 16,
             "BitOffset": 16,
             "BitStart": 0,
             "Units": "rad",
             "Resolution": "0.0001",
             "Signed": false},
         {
             "Order": 6,
             "Id": "sog",
             "Name": "SOG",
             "BitLength": 16,
             "BitOffset": 32,
             "BitStart": 0,
             "Units": "m/s",
             "Resolution": "0.01",
             "Signed": false},
         {
             "Order": 7,
             "Id": "heading",
             "Name": "Heading",
             "BitLength": 16,
             "BitOffset": 48,
             "BitStart": 0,
             "Units": "rad",
             "Resolution": "0.0001",
             "Signed": false},
         {
             "Order": 8,
             "Id": "speedThroughWater",
             "Name": "Speed through Water",
             "BitLength": 16,
             "BitOffset": 64,
             "BitStart": 0,
             "Units": "m/s",
             "Resolution": "0.01",
             "Signed": false},
         {
             "Order": 9,
             "Id": "set",
             "Name": "Set",
             "BitLength": 16,
             "BitOffset": 80,
             "BitStart": 0,
             "Units": "rad",
             "Resolution": "0.0001",
             "Signed": false},
         {
             "Order": 10,
             "Id": "drift",
             "Name": "Drift",
             "BitLength": 16,
             "BitOffset": 96,
             "BitStart": 0,
             "Units": "m/s",
             "Resolution": "0.01",
             "Signed": false}]},
```

