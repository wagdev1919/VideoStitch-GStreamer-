# VideoStitch-GStreamer-
This python project compose 4 ingest videos to one screen video, stream this out via HLS or RTMP.
This code is similar to follow pipeline.

gst-launch-1.0 -vvv -e \
flvmux streamable=true name=smux ! rtmpsink sync=false location='rtmp://127.0.0.1:1935/live live=1' \
videomixer name=m sink_1::xpos=320 sink_2::ypos=240 sink_3::xpos=320 sink_3::ypos=240 ! videoscale! video/x-raw,width=640,height=480 ! videorate ! video/x-raw,framerate=30/1 ! queue ! x264enc tune=zerolatency ! smux. \
audiomixer name=ma ! audioconvert ! voaacenc bitrate=96000 ! queue max-size-buffers=0 max-size-bytes=0 max-size-time=0 ! aacparse ! smux. \
rtmpsrc location={input1} do-timestamp=true ! decodebin name=decoder \
decoder. ! videoconvert ! videoscale ! video/x-raw,width=320,height=240 ! m.sink_0 \
decoder. ! audioconvert ! audioresample ! "audio/x-raw,rate=44100" ! queue ! ma. \
rtmpsrc location={input2} do-timestamp=true ! decodebin name=decoder1 \
decoder1. ! videoconvert ! videoscale ! video/x-raw,width=320,height=240 ! m.sink_1 \
decoder1. ! audioconvert ! audioresample ! "audio/x-raw,rate=44100" ! queue ! ma. \
rtmpsrc location={input3} do-timestamp=true ! decodebin name=decoder2 \
decoder2. ! videoconvert ! videoscale ! video/x-raw,width=320,height=240 ! m.sink_2 \
decoder2. ! audioconvert ! audioresample ! "audio/x-raw,rate=44100" ! queue ! ma. \
rtmpsrc location={input4} do-timestamp=true ! decodebin name=decoder3 \
decoder3. ! videoconvert ! videoscale ! video/x-raw,width=320,height=240 ! m.sink_3 \
decoder3. ! audioconvert ! audioresample ! "audio/x-raw,rate=44100" ! queue ! ma.
