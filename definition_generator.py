from pyv4l2.frame import Frame
from pyv4l2.control import Control
from xml.etree.ElementTree import Element, SubElement, Comment, ElementTree, tostring, XML
from lxml import etree


class DefinitionGenerator():
    def __init__(self):
        self.used_param_names = []

    def parametrify_name(self, name: str) -> str:
        """Generates a unique parameter name from the control name.
        For example, "Exposure (Absolute)" generates CAM_EXPOSUREAB
        If there is a collision, the new parameter has a number placed as the last char
        """
        name = "CAM_" + name.replace(" ", "").replace(",",
                                                      "").replace("(", "")[:10].upper()
        while name in self.used_param_names:
            # Name would be a duplicate, replace last char with 1, 2, 3 and so on
            name = list(name)
            if name[-1] not in "1234567890":
                name[-1] = "1"
            else:
                name[-1] = chr(ord(name[-1]+1))
        name = "".join(name)
        self.used_param_names.append(name)
        return name

    def to_xml_type(self, value: str) -> str:
        # TODO: add missing types
        if value == "uint":
            return "uint32"
        if value == "int":
            return "int32"
        if value == "menu":
            return "int32"
        return value

    # def create_options(self, options, control):
    #     min = control["min"]
    #     max = control["max"]
    #     step = (max-min) / 10
    #     for i in range(11):
    #         value = int(min+i*step)
    #         option = SubElement(options, "option")
    #         option.set("name", str(value))
    #         option.set("value", str(value))

    def create_menu_options(self, options: SubElement, control: Control) -> None:
        """Populates "options" with <option> tags generated from a "menu" type v4l2 control"""
        for name, value in control["menu"].items():
            option = SubElement(options, "option")
            option.set("name", name.decode())
            option.set("value", str(value))

    def generate(self, device: str) -> None:
        """Generates a .xml camera definition file from uv4l controls of a given video device (e.g. /dev/video0)"""

        control = Control(device)
        # <mavlinkcamera> is the root element
        mavlinkcamera = Element('mavlinkcamera')

        definition = SubElement(mavlinkcamera, "definition")
        definition.set("version", "7")
        model = SubElement(definition, "model")
        model.text = "PotatoCam"
        vendor = SubElement(definition, "vendor")
        vendor.text = "PotatoFarm"

        parameters = SubElement(mavlinkcamera, "parameters")

        for control in control.get_controls():
            control_type = control["type"]
            # map the control types available for camera definition files
            param_type = self.to_xml_type(control_type)
            # create <parameter> tag
            parameter = SubElement(parameters, "parameter")
            parameter.set("name", self.parametrify_name(
                control["name"].decode()))
            parameter.set("type", param_type)
            parameter.set("default", str(control["default"]))
            # We additionally store the v4l2_id of the control for commodity reasons (use by mavlink comms)
            parameter.set("v4l2_id", str(control["id"]))
            # Add <description> tag. This shows in QGC as the title of the option
            description = SubElement(parameter, "description")
            description.text = control["name"].decode()

            # Controls with "step" attribute show in QGC as a slider
            if "step" in control and control_type == "int":
                parameter.set("step", str(control["step"]))
                parameter.set("max", str(control["max"]))
                parameter.set("min", str(control["min"]))

            # Controls with <option> tag show a dropdown in QGC
            elif control_type == "menu":
                options = SubElement(parameter, "options")
                self.create_menu_options(options, control)

        # string-fu to allow printint to console.
        string = tostring(mavlinkcamera)
        parser = etree.XMLParser(remove_blank_text=True)
        xml = etree.fromstring(string, parser=parser)
        pretty_file = etree.tostring(xml, pretty_print=True).decode()
        # print(pretty_file)

        with open("camera_definitions/example.xml", "w") as f:
            f.write(pretty_file)


if __name__ == "__main__":
    DefinitionGenerator().generate("/dev/video4")
