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
    parser.add_argument("device", help="video device")

    args = parser.parse_args()
    DefinitionGenerator().generate(args.device)
    stream1=GstServer(args.device)
    mavlink = MavlinkCameraManager(args.device)
    server = CameraDefinitionServer(args.device, 5000)
    stream1.start()
    server.start()
    mavlink.start()
    stream1.join()
