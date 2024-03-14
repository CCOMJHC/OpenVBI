
from enum import Enum
from openvbi.core.statistics import PktStats

## Encapsulate the types of real-world time information that can be used
#
# In order to establish the relationship between the elapsed time (i.e., time of reception) of
# each packet and the real-world time, we need to use the encoded timestamps in one of the
# packets in the file.  There are a number of choices for this, depending on what type of
# data we have in there; this enumeration provides a controlled list of the options.
class TimeSource(Enum):
    ## Use NMEA2000 packet for SystemTime
    Time_SysTime = 0
    ## Use NMEA2000 packet from GNSS observations
    Time_GNSS = 1
    ## Use NMEA0183 ZDA timestamp packets
    Time_ZDA = 2
    ## Use NMEA0183 RMC minimum data with timestamps
    Time_RMC = 3

## Exception to report that no adequate source of real-world time information is available
class NoTimeSource(Exception):
    pass

## Work out which time source should be used for real time associations
#
# There are multiple potential ways to assign a correspondence between measures of
# elapsed time and the timestamps that are available in the source observations (e.g.,
# from ZDA or RMC strings, or NMEA2000 System Time or GNSS packets).  All of these
# mechanisms can be used, but in general we prefer to use System Time if available,
# then GNSS (since NMEA2000 arrives faster, it should have lower latency that NMEA0183),
# but then will use either ZDA, or as a last resort RMC from NMEA0183 packets.  This
# code translates the available packets into an enum for further reference.

def determine_time_source(stats: PktStats) -> TimeSource:
    """Work out which source of time can be used to provide the translation between
       elapsed time (local time-stamps that indicate a monotonic clock tick at the
       logger when the packet is received) to a real world time.  The preference is
       to use NMEA2000 system time packets, but then to attempt to use GNSS packets,
       and then finally to drop back to NMEA0183 ZDA or RMC packets (in that order)
       if required.

        Inputs:
            stats   (PktStats) Statistics on which packets have been seen in the data
        
        Outputs:
            TimeSource enum for which source should be used for timestamping
    """
    if stats.Seen('SystemTime'):
        rtn = TimeSource.Time_SysTime
    elif stats.Seen('GNSS'):
        rtn = TimeSource.Time_GNSS
    elif stats.Seen('ZDA'):
        rtn = TimeSource.Time_ZDA
    elif stats.Seen('RMC'):
        rtn = TimeSource.Time_RMC
    else:
        raise NoTimeSource()
    return rtn
