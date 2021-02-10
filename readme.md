# Barebones Gstreamer Mavlink Camera

This is a barebones implementation of a MAVLink Camera using GStreamer pipelines.
## Requirements:

 - gst-rtsp-server (aur)
 - pymavlink from mavlink master
 - Other dependencies in pyproject.toml

## Usage

`python main.py /dev/videox` where videox is a h264-capable camera