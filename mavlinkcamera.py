"""
Example of how to connect to the autopilot by using mavproxy's
--udpin:0.0.0.0:9000 endpoint from the companion computer itself
"""

# Disable "Bare exception" warning
# pylint: disable=W0702
import threading
import time
import bs4
# Import mavutil
from pymavlink import mavutil
from pymavlink.dialects.v20 import common
from pymavlink.dialects.v20.common import CAMERA_CAP_FLAGS_HAS_VIDEO_STREAM
from pymavlink.dialects.v20.common import CAMERA_CAP_FLAGS_CAPTURE_VIDEO
from pyv4l2.control import Control
MAV_CMD_REQUEST_VIDEO_STREAM_INFORMATION = 2504


class MavlinkCameraManager(threading.Thread):
    param_map = {}
    param_types = {}

    def __init__(self, device, camera_id=1, thermal=False, rtspport=8554, rtspstream=None):
        super().__init__()
        self.rtspstream = rtspstream.encode("ascii") if rtspstream else None
        self.device = device
        self.camera_id = camera_id
        self.rtspport = rtspport
        self.thermal = thermal
        print("Thermal:", self.thermal)
        if self.device:
            self.control = Control(device)

    def wait_conn(self):
        """
        Sends a ping to stabilish the UDP communication and awaits for a response
        """
        msg = None
        while not msg:
            self.master.mav.ping_send(
                int(time.time() * 1e6), # Unix time in microseconds
                0, # Ping number
                0, # Request ping of all systems
                0 # Request ping of all components
            )
            msg = self.master.recv_match()
            time.sleep(0.5)

    def mavlink_type(self, xml_type):
        if xml_type == "int32":
            return mavutil.mavlink.MAV_PARAM_EXT_TYPE_INT32
        elif xml_type == "uint32":
            return mavutil.mavlink.MAV_PARAM_EXT_TYPE_UINT32
        elif xml_type == "bool":
            return mavutil.mavlink.MAV_PARAM_EXT_TYPE_UINT8

    def as_128_bytes(self, value, param_type):
        """returns values as 128 bytes"""
        if param_type == "int32":
            small = value.to_bytes(4, "little", signed=True)
            r = self.makebytes(small,128)
            print(value, param_type, " = " , r)
            return r
        if "uint" in param_type or param_type == "bool":
            return value.to_bytes(128, "little")

    def read_param(self, param_id):
        """ Read a param and return it as a PARAM_EXT_VALUE message """
        # Check if we have the parameters map cached, create if if we don't
        if len(self.param_map.keys()) == 0:
            with open("camera_definitions/example.xml") as f:
                soup = bs4.BeautifulSoup(f.read(), "lxml")
                parameters = soup.find_all("parameter")
                for parameter in parameters:
                    self.param_map[parameter["name"]] = int(parameter["v4l2_id"])
                    self.param_types[parameter["name"]] = parameter["type"]

        # grab v4l2 id equivalent of param_id
        v4l2_id = self.param_map[param_id]
        # read actual value of v4l2 control
        value = self.control.get_control_value(v4l2_id)
        print("read: ", param_id, " = ", value)
        # mav v4l2 type to xml type
        param_type = self.param_types[param_id]
        # send param_ext_value
        self.master.mav.param_ext_value_send(
            self.makestring(param_id.encode("utf-8"), 16),
            self.as_128_bytes(value, param_type),
            self.mavlink_type(param_type),
            1,
            0
        )

    def set_param(self, raw_msg):
        """Set a Camera param via mavlink"""
        msg = raw_msg.to_dict()
        param_id = msg["param_id"]
        param_type = self.param_types[param_id]
        # unpack value from 128 bytes
        value = self.convert_value(param_type, raw_msg.get_payload())
        v4l2_id = self.param_map[param_id]
        print("setting ", param_id, param_type,  "to ", value)
        # Set value
        self.control.set_control_value(v4l2_id, value)
        value = self.control.get_control_value(v4l2_id)
        # Send new value to GCS
        self.master.mav.param_ext_ack_send(
            self.makestring(param_id.encode("utf-8"), 16),
            self.as_128_bytes(value, param_type),
            self.mavlink_type(self.param_types[param_id]),
            mavutil.mavlink.PARAM_ACK_ACCEPTED
        )


    def convert_value(self, type, payload):
        """unpacks value from 128 bytes payload"""
        relevant = payload[22:26]
        if type == "uint8":
            return int.from_bytes(relevant, byteorder="little", signed=False)
        elif type == "int32":
            return int.from_bytes(relevant, byteorder="little", signed=True)
        elif type == "uint32":
            return int.from_bytes(relevant, byteorder="little", signed=False)
        print("oops", type)
        return int.from_bytes(relevant, byteorder="little", signed=True)

    def run(self):
        self.master = mavutil.mavlink_connection('udpout:127.0.0.1:14550', source_system=1, source_component=mavutil.mavlink.MAV_COMP_ID_CAMERA+self.camera_id)

        # required?
        self.wait_conn()
        print("Mavlink thread started")
        while True:
            try:
                raw_msg = self.master.recv_match()
                msg = raw_msg.to_dict()
                if msg["mavpackettype"] == "COMMAND_LONG":
                    print(msg)
                    if msg["command"] == mavutil.mavlink.MAV_CMD_REQUEST_CAMERA_INFORMATION:
                        print("got resquest for camera info, replying...")
                        self.master.mav.command_ack_send(common.MAV_CMD_REQUEST_CAMERA_INFORMATION, common.MAV_RESULT_ACCEPTED)
                        self.send_camera_information()
                    elif msg["command"] == MAV_CMD_REQUEST_VIDEO_STREAM_INFORMATION:
                        print("got resquest for video stream information")
                        print(msg)
                        self.master.mav.command_ack_send(MAV_CMD_REQUEST_VIDEO_STREAM_INFORMATION, common.MAV_RESULT_ACCEPTED)
                        self.send_video_stream_information()
                elif msg["mavpackettype"] == "PARAM_EXT_REQUEST_READ":
                    self.read_param(msg['param_id'])
                elif msg["mavpackettype"] == "PARAM_EXT_SET":
                    self.set_param(raw_msg)
            except AttributeError as e:
                if "NoneType" not in str(e):
                    print(e)

            time.sleep(0.1)
            self.send_heartbeat()

    def send_heartbeat(self):
        self.master.mav.heartbeat_send(
            0,
            mavutil.mavlink.MAV_TYPE_CAMERA,
            mavutil.mavlink.MAV_AUTOPILOT_GENERIC,
            0,
            mavutil.mavlink.MAV_STATE_STANDBY,
            3
        )

    def makestring(self, string, size):
        """ returns a 16 bytes long string"""
        raw = bytearray(size)
        for i, char in enumerate(string):
            raw[i] = char
        return raw

    def makebytes(self, string, size):
        """returns a size-sized bytes bytearray"""
        raw = bytearray(size)
        for i, char in enumerate(string):
            raw[size -(len(string)) + i] = char
        return raw

    def send_camera_information(self):
        self.master.mav.camera_information_send(
            0,
            self.makestring("camera{0}".format(self.camera_id).encode("ascii"), 32),
            self.makestring("camera{0}".format(self.camera_id).encode("ascii"), 32),
            1,
            0,
            0,
            0,
            640,
            480,
            0,
            CAMERA_CAP_FLAGS_CAPTURE_VIDEO | CAMERA_CAP_FLAGS_HAS_VIDEO_STREAM,
            0,
            self.makestring(b"http://127.0.0.1:5000", 140),
        )


    def send_video_stream_information(self):
        self.master.mav.video_stream_information_send(
            1,
            2 if self.thermal else 1,
            mavutil.mavlink.VIDEO_STREAM_TYPE_RTSP,
            mavutil.mavlink.VIDEO_STREAM_STATUS_FLAGS_RUNNING,
            30,
            1920,
            1080,
            10000,
            0,
            60,
            self.makestring("camera{0}".format(self.camera_id).encode("ascii"), 32),
            self.makestring(self.rtspstream or "rtsp://127.0.0.1:{0}/stream1".format(self.rtspport).encode("ascii"), 160),
        )
        if self.thermal:
            self.master.mav.video_stream_information_send(
                2,
                2,
                mavutil.mavlink.VIDEO_STREAM_TYPE_RTSP,
                mavutil.mavlink.VIDEO_STREAM_STATUS_FLAGS_RUNNING | mavutil.mavlink.VIDEO_STREAM_STATUS_FLAGS_THERMAL,
                30,
                1920,
                1080,
                10000,
                0,
                60,
                self.makestring("camera{0}".format(self.camera_id).encode("ascii"), 32),
                self.makestring(self.rtspstream or "rtsp://127.0.0.1:{0}/thermal".format(self.rtspport).encode("ascii"), 160),
            )