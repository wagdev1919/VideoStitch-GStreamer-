import os
import subprocess, signal
import argparse
from streamer import Streamer

ap = argparse.ArgumentParser()
#ap.add_argument("-stype", "--sourceType", required=True, help="rtmp or hls")
ap.add_argument("-otype", "--outputType", required=False, help="rtmp or hls")
ap.add_argument("-s1", "--source1", required=False, help="URL of Source Stream1")
ap.add_argument("-s2", "--source2", required=False, help="URL of Source Stream2")
ap.add_argument("-s3", "--source3", required=False, help="URL of Source Stream3")
ap.add_argument("-s4", "--source4", required=False, help="URL of Source Stream4")

args = vars(ap.parse_args())
# display a friendly message to the user
main = Streamer(args["source1"], args["source2"], args["source3"], args["source4"], args["outputType"])

try:
    main.run()
except KeyboardInterrupt:
    main.stop()
