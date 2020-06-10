import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GstVideo, GLib

Gst.init(None)

class settings:
    outRtmp = "rtmp://127.0.0.1:1935/live live=1"
    outHLS = "http://x.x.x.x:x/hls"
    playListLocation = "/var/www/hls/stream.m3u8"
    fileLocation = "/var/www/hls/segment1080p-%05d.ts"
    defRtmpSrc = "rtmp://xxxx"
    width = 640
    height = 480
    x1 = 320
    y1 = 240
   

class Streamer:
    otype = 'rtmp'
    source1 = settings.defRtmpSrc
    source2 = settings.defRtmpSrc
    source3 = settings.defRtmpSrc
    source4 = settings.defRtmpSrc
    def __init__(self, s1, s2, s3, s4, outType):
        
        if s1 is not None:
            self.source1 = s1
        if s2 is not None:
            self.source2 = s2
        if s3 is not None:
            self.source3 = s3
        if s4 is not None:
            self.source4 = s4
            
        self.otype = outType
        Gst.debug_set_active(True)
        Gst.debug_set_default_threshold(3)
        
        self.mainloop = GLib.MainLoop()

        self.pipeline = Gst.Pipeline()
        
        self.clock = self.pipeline.get_pipeline_clock()

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::error', self.on_error)

        sources = [
            ['rtmpsrc', self.source1],
            ['rtmpsrc', self.source2],
            ['rtmpsrc', self.source3],
            ['rtmpsrc', self.source4]
        ]
        
        # Video input
        index = 0
        for source in sources:
            self.malm([
                [source[0], None, {'location':source[1], 'do-timestamp': 1}],
                ['queue', None, {}],
                ['decodebin', 'decoder{}'.format(index), {'use-buffering':1}]
            ])
            
            decoder = getattr(self, 'decoder{}'.format(index))

            prev = None
            self.malm([
                ['queue', 'video_in{}'.format(index), {}],
                ['videoconvert', None, {}],
                ['videoscale', None, {}],
                ['capsfilter', None, {'caps': 'video/x-raw, width={}, height={}'.format(settings.x1, settings.y1)}],
                ['queue', 'video_out{}'.format(index), {}]
            ])
            prev = None
            self.malm([
                ['queue', 'audio_in{}'.format(index), {}],
                ['audioconvert', None, {}],
                #['audioresample', None, {}],
                #['capsfilter', None, {'caps': 'audio/x-raw, rate=44100'}],
                ['queue', 'audio_out{}'.format(index) ,{}]
            ])
            
            if index == 0:
                decoder.connect('pad-added', self.__on_decoded_pad)
            elif index == 1:
                decoder.connect('pad-added', self.__on_decoded_pad1)
            elif index == 2:
                decoder.connect('pad-added', self.__on_decoded_pad2)
            elif index == 3:
                decoder.connect('pad-added', self.__on_decoded_pad3)
            
            index += 1
        
        #video mixer
        prev = None
        self.malm([
            ['videomixer', 'm', {}],
            ['videoscale', None, {}],
            ['capsfilter', None, {'caps': 'video/x-raw, width={}, height={}'.format(settings.width, settings.height)}],
            ['videorate', None, {}],
            ['capsfilter', None, {'caps': 'video/x-raw, framerate=30000/1001'}],
            ['queue', None, {}],
            ['x264enc', None, {'tune': 'zerolatency'}],
            ['queue', 'vmix_out', {}]
        ])
        vmix_pads = []
        vmix_pads.append(self.m.get_request_pad('sink_%u'))
        vmix_pads.append(self.m.get_request_pad('sink_%u'))
        vmix_pads.append(self.m.get_request_pad('sink_%u'))
        vmix_pads.append(self.m.get_request_pad('sink_%u'))
        
        vmix_pads[1].set_property('xpos', settings.x1)
        vmix_pads[2].set_property('ypos', settings.y1)
        vmix_pads[3].set_property('xpos', settings.x1)
        vmix_pads[3].set_property('ypos', settings.y1)
        
        vmix_pads[0].set_offset(2000000000)
        #audio mixer
        prev = None
        self.malm([
            ['audiomixer', 'ma', {}],
            ['audioconvert', None, {}],
            ['queue', None, {}],
            ['voaacenc', None, {'bitrate': 96000}],
            ['queue', None, {'max-size-bytes': 0, 'max-size-buffers': 0, 'max-size-time': 0}],
            ['aacparse', None, {}],
            ['queue', 'amix_out', {}]
        ])
        prev = None
        if self.otype == 'rtmp':#flvmux for streaming to RTMP
            self.malm([
                ['flvmux', 'smux', {'streamable': 1}],
                ['rtmpsink', None, {'sync': 0, 'location': settings.outRtmp}]
            ])
        elif self.otype == 'hls':#mpegtsmux for streaming to HLS
            self.malm([
                ['mpegtsmux', 'smux', {}],
                ['hlssink', None, {'playlist-root': settings.outHLS, 'playlist-location': settings.playListLocation, 'location': settings.fileLocation, 'max-files': 20, 'target-duration': 8}]
            ])
        else:
            print(self.otype + ' is not supported, Exiting...')
            return

        # Video input
        index = 0
        for source in sources:
            video_out = getattr(self, 'video_out{}'.format(index))
            audio_out = getattr(self, 'audio_out{}'.format(index))
            video_out.link(self.m)
            audio_out.link(self.ma)
            index += 1
        
        self.amix_out.link(self.smux)
        self.vmix_out.link(self.smux)
    
    def __link_decode_pad(self, pad, data, index):
        if data.get_property('caps')[0].to_string().startswith('video'):
            pad.link(getattr(self, 'video_in{}'.format(index)))
        else:
            pad.link(getattr(self, 'audio_in{}'.format(index)))
    
    def __on_decoded_pad(self, pad, data):
        self.__link_decode_pad(pad, data, 0)
            
    def __on_decoded_pad1(self, pad, data):
        self.__link_decode_pad(pad, data, 1)

    def __on_decoded_pad2(self, pad, data):
        self.__link_decode_pad(pad, data, 2)
            
    def __on_decoded_pad3(self, pad, data):
        self.__link_decode_pad(pad, data, 3)

    def run(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        GLib.timeout_add(2 * 1000, self.do_keyframe, None)
        self.mainloop.run()

    def stop(self): 
        print('Exiting...')
        Gst.debug_bin_to_dot_file(self.pipeline, Gst.DebugGraphDetails.ALL, 'stream')
        self.pipeline.set_state(Gst.State.NULL)
        self.mainloop.quit()

    def do_keyframe(self, user_data):
        # Forces a keyframe on all video encoders
        event = GstVideo.video_event_new_downstream_force_key_unit(self.clock.get_time(), 0, 0, True, 0)
        self.pipeline.send_event(event)

        return True

    def on_error(self, bus, msg):
        print('on_error', msg.parse_error())

    def malm(self, to_add):
        # Make-add-link multi
        prev = None
        for n in to_add:
            element = Gst.ElementFactory.make(n[0], n[1])
            if not element:
                raise Exception('cannot create element {}'.format(n[0]))

            if n[1]: setattr(self, n[1], element)

            for p, v in n[2].items():
                if p == 'caps':
                    caps = Gst.Caps.from_string(v)
                    element.set_property('caps', caps)
                else:
                    element.set_property(p, v)

            self.pipeline.add(element)
            if prev: prev.link(element)

            prev = element
