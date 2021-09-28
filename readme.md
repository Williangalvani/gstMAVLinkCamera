# Barebones Gstreamer Mavlink Camera

This is a barebones implementation of a MAVLink Camera using GStreamer pipelines.

It is able to create rtsp streams from v4l2 devices, generated de definitions xml, and expose the controllers to QGC:

![working example](camera-example.gif "Working example")

## Requirements:

 - gst-rtsp-server (aur)
 - pymavlink
 - Other dependencies in pyproject.toml

## Usage

`python main.py /dev/videox` where videox is a h264-capable camera


Videotestsrc as a camera with ID 1
`python main.py --pipeline="videotestsrc pattern=smpte ! video/x-raw,width=640,height=480 ! videoconvert ! x264enc bitrate=50000 ! video/x-h264, profile=baseline ! rtph264pay config-interval=1 name=pay0 pt=96" --id=1 --rtspport 8555`

Videotestsrc as a Thermal camera with ID 0 (QGC has special handling of thermal cameras)

`python main.py --pipeline="videotestsrc pattern=ball ! video/x-raw,width=640,height=480 ! videoconvert ! x264enc bitrate=50000 ! video/x-h264, profile=baseline ! rtph264pay config-interval=1 name=pay0 pt=96" --id=0 --rtspport 8554 --thermal`

Publish an existing RTSP stream:

`python main.py --id 0 --existing-rtsp "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov"`
