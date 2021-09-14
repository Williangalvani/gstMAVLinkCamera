import argparse
import os
from multiple_pipelines import GstServer
from camera_definition_server import CameraDefinitionServer
from mavlinkcamera import MavlinkCameraManager
from definition_generator import DefinitionGenerator

if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    # Required positional argument
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--device", help="video device h264-able")
    group.add_argument("--pipeline", help="gstreamer pipeline. show end with 'rtph264pay config-interval=1 name=pay0 pt=96'")
    parser.add_argument("--rtspport", type=int, help="port for the rtsp server to listen on", default=8554)
    parser.add_argument("--httpport", type=int, help="port for the http server to listen on", default=5000)
    parser.add_argument("--id", type=int, help="Camera Mavlink ID", default=0)
    parser.add_argument("--thermal", help="Is is thermal?", default=False, action='store_true')
    parser.add_argument("--existing-rtsp", help="Are we using an existing rtsp server?", default=None)
    args = parser.parse_args()
    if args.device:
        DefinitionGenerator().generate(args.device)
        server = CameraDefinitionServer(args.device, args.httpport)
        server.start()
        stream=GstServer(device=args.device, port=args.rtspport)
        stream.start()
        mavlink = MavlinkCameraManager(args.device, camera_id=args.id, thermal=args.thermal, rtspport=args.rtspport)
    elif args.pipeline:
        stream=GstServer(pipeline=args.pipeline, port=args.rtspport)
        stream.start()
        mavlink = MavlinkCameraManager(None, camera_id=args.id, thermal=args.thermal, rtspport=args.rtspport)
    elif args.existing_rtsp:
        print("serving existing stream...")
        mavlink = MavlinkCameraManager(None, camera_id=args.id, rtspstream=args.existing_rtsp)
    mavlink.start()
    mavlink.join()
    stream.join()
