##\file teamsurv.py
#
# Read files of NMEA0183 data logged by the TeamSurv logger
#
# Copyright 2023 OpenVBI Project.  All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

from openvbi.core.observations import RawN0183Obs, BadData, Dataset
from openvbi.core.timebase import determine_time_source, generate_timebase

def load_data(filename: str) -> Dataset:
    rtn: Dataset = Dataset()

    with open(filename) as f:
        for message in f:
            try:
                obs = RawN0183Obs(None, message)
                rtn.packets.append(obs)
                rtn.stats.Observed(obs.Name())
            except BadData:
                pass
    rtn.timesrc = determine_time_source(rtn.stats)

    # TeamSurv systems don't have elapsed time (and intermingle two streams of
    # data from the two interfaces without warning), so you can't tell when the packets
    # were received.  We therefore attempt to fake this as best we can be establishing the
    # timestamps on each packet that has one, and then assuming that other packets appear
    # at the midpoint between those timestamps.  This works reasonably so long as there is
    # a regular time tick like a SystemTime or ZDA, but will otherwise fail.
    realtime_elapsed_zero = None
    for n in range(len(rtn.packets)):
        if rtn.packets[n].HasTime() and rtn.packets[n].MatchesTimeSource(rtn.timesrc):
            packet_real_time = rtn.packets[n].Timestamp()
            if realtime_elapsed_zero is None:
                realtime_elapsed_zero = packet_real_time
                rtn.packets[n].SetElapsed(0.0)
            else:
                rtn.packets[n].SetElapsed(1000.0*(packet_real_time - realtime_elapsed_zero))
    
    # Now we need to patch up all the packets with elapsed time still set to None
    oldest_position = None
    for n in range(len(rtn.packets)):
        if rtn.packets[n].Elapsed() is not None:
            if oldest_position is None:
                # First time we've seen something that has a timestamp
                oldest_position = n
            else:
                # Subsequent timestamped data, so (oldest_position, n) need set to the mean
                # time of the two timestamped packets (which is the best we can do, since we
                # don't have any record of when they actually arrived)
                target_elapsed_time = (rtn.packets[oldest_position].Elapsed() + rtn.packets[n].Elapsed())/2.0
                for i in range(oldest_position+1,n):
                    rtn.packets[i].SetElapsed(target_elapsed_time)
                # Update position of the previous timestamp to now
                oldest_position = n

    rtn.timebase = generate_timebase(rtn.packets, rtn.timesrc)

    return rtn