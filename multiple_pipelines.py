import gi
from threading import Thread
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GLib

#Initializes the GStreamer library, setting up internal path lists, registering built-in elements, and loading standard plugins.
Gst.init(None)

class GstServer(GstRtspServer.RTSPServer, Thread):
    def __init__(self, device, **properties):
        super(GstServer, self).__init__(**properties)
        Thread.__init__(self)
        Gst.init(None)
        self.device = device

    def run(self):
        print("RTSP server starting")
        self.factory = GstRtspServer.RTSPMediaFactory()
        #self.factory.set_launch('videotestsrc pattern=ball ! video/x-raw,width=640,height=480 ! videoconvert ! x264enc bitrate=50000 ! video/x-h264, profile=baseline !rtph264pay config-interval=1 name=pay0 pt=96 ')
        self.factory.set_launch(f'v4l2src device={self.device} ! video/x-h264,width=1920,height=1080 ! h264parse !rtph264pay config-interval=1 name=pay0 pt=96 ')
        self.factory.set_shared(True)
        self.get_mount_points().add_factory("/test", self.factory)
        self.attach(None)
        loop = GLib.MainLoop()
        print("RTSP server starting main loop")
        loop.run()
