from collections import OrderedDict
from dslink import DSLink, Configuration, Node, Value
import dsa_grovepi as grovepi
import grove_rgb_led
from math import isnan
from twisted.internet import reactor

_NUMERALS = '0123456789abcdefABCDEF'
_HEXDEC = {v: int(v, 16) for v in (x+y for x in _NUMERALS for y in _NUMERALS)}


def rgb(triplet):
    return _HEXDEC[triplet[0:2]], _HEXDEC[triplet[2:4]], _HEXDEC[triplet[4:6]]


class GrovePiDSLink(DSLink):
    addresses = OrderedDict([
        ("D2", ["digital", 2]),
        ("D3", ["pwm", 3]),
        ("D4", ["digital", 4]),
        ("D5", ["pwm", 5]),
        ("D6", ["pwm", 6]),
        ("D7", ["digital", 7]),
        ("D8", ["digital", 8]),
        ("A0", ["analog", 0]),
        ("A1", ["analog", 1]),
        ("A2", ["analog", 2]),
        ("I2C-1", ["i2c", 1]),
        ("I2C-2", ["i2c", 2]),
        ("I2C-3", ["i2c", 3]),
    ])

    modules = [
        "LED",
        "RGB LCD",
        "Light Sensor",
        "Rotary Angle Sensor",
        "Ultrasonic Ranger",
        "Buzzer",
        "Sound Sensor",
        "Button",
        "Relay",
        "Temp and Humid"
    ]

    def __init__(self, config):
        self.do_restore = True
        DSLink.__init__(self, config)

    def start(self):
        self.profile_manager.create_profile("add_module")
        self.profile_manager.register_callback("add_module", self.add_module)

        self.profile_manager.create_profile("remove_module")
        self.profile_manager.register_callback("remove_module", self.remove_module)

        if self.restore:
            self.restore(self.super_root)

        reactor.callLater(0.1, self.update_values)

    def restore(self, node):
        for child_name in node.children:
            child = node.children[child_name]
            if node.children:
                self.restore(child)
            if "@callback" in child.attributes:
                if child.attributes["@callback"] == "module":
                    child.set_value_callback = self.set_value
                elif child.attributes["@callback"] == "rgb_text":
                    child.set_value_callback = self.set_text
                elif child.attributes["@callback"] == "rgb_color":
                    child.set_value_callback = self.set_color
            if "@mode" in child.attributes and "@address":
                mode = child.attributes["@mode"]
                address = self.addresses[child.attributes["@address"]][1]
                if mode == "output":
                    grovepi.pinMode(address, "OUTPUT")
                elif mode == "input":
                    grovepi.pinMode(address, "INPUT")

    def get_default_nodes(self):
        self.do_restore = False
        super_root = self.get_root_node()

        add_module = Node("add_module", super_root)
        add_module.set_display_name("Add Module")
        add_module.set_profile("add_module")
        add_module.set_parameters([
            {
                "name": "Name",
                "type": "string"
            },
            {
                "name": "Type",
                "type": self.module_enum()
            },
            {
                "name": "Address",
                "type": self.address_enum()
            }
        ])
        add_module.set_columns([
            {
                "name": "Success",
                "type": "string"
            }
        ])
        add_module.set_invokable("config")

        poll_speed = Node("poll_speed", super_root)
        poll_speed.set_display_name("Poll Speed")
        poll_speed.set_type("number")
        poll_speed.set_value(0.1)
        poll_speed.set_config("$writable", "config")

        super_root.add_child(add_module)
        super_root.add_child(poll_speed)

        return super_root

    def set_value(self, node, value):
        if type(value) == bool:
            grovepi.digitalWrite(self.addresses[node.attributes["@address"]][1], value)
        elif type(value) == int:
            if node.attributes["@type"] == "pwm":
                node.set_value(value)
                grovepi.analogWrite(self.addresses[node.attributes["@address"]][1], self.percent_to_pwm(value))
            else:
                node.set_value(value)
                grovepi.analogWrite(self.addresses[node.attributes["@address"]][1], self.percent_to_analog(value))

    def set_color(self, node, value):
        red, green, blue = rgb(hex(int(value))[2:].zfill(6))
        grove_rgb_led.set_rgb(red, green, blue)
        return []

    def set_text(self, node, value):
        text = str(value)
        grove_rgb_led.set_text(text)
        return []

    def add_module(self, parameters):
        if "Name" not in parameters.params:
            return [["Invalid name."]]
        node = Node(str(parameters.params["Name"]), self.super_root)
        node.set_attribute("@callback", "module")
        module_type = parameters.params["Type"]
        address = parameters.params["Address"]
        address_type = self.addresses[address][0]
        node.set_attribute("@module", module_type)
        node.set_attribute("@address", address)
        node.set_attribute("@type", address_type)
        node.set_value_callback = self.set_value
        node.set_config("$writable", "write")
        if module_type == "LED":
            if address_type == "pwm":
                grovepi.pinMode(self.addresses[address][1], "OUTPUT")
                node.set_type("number")
                node.set_attribute("@mode", "output")
                node.set_attribute("@unit", "%")
            elif address_type == "digital":
                grovepi.pinMode(self.addresses[address][1], "OUTPUT")
                node.set_type("bool")
                node.set_attribute("@mode", "output")
            else:
                return [["Requires pwm or digital"]]
        elif module_type == "RGB LCD":
            node.add_child(self.color_node(node))
            node.add_child(self.text_node(node))
        elif module_type == "Light Sensor":
            if address_type == "analog":
                node.set_type("number")
                node.set_attribute("@unit", "%")
                node.set_attribute("@mode", "input")
            else:
                return [["Requires analog"]]
        elif module_type == "Rotary Angle Sensor":
            if address_type == "analog":
                grovepi.pinMode(self.addresses[address][1], "INPUT")
                node.set_type("number")
                node.set_attribute("@unit", "%")
                node.set_attribute("@mode", "input")
            else:
                return [["Requires analog"]]
        elif module_type == "Ultrasonic Ranger":
            if address_type == "digital" or address_type == "pwm":
                grovepi.pinMode(self.addresses[address][1], "INPUT")
                node.set_type("number")
                node.set_attribute("@unit", "cm")
                node.set_attribute("@mode", "input")
            else:
                return [["Requires digital or pwm"]]
        elif module_type == "Buzzer":
            if address_type == "digital" or address_type == "pwm":
                grovepi.pinMode(self.addresses[address][1], "OUTPUT")
                node.set_type("number")
                node.set_attribute("@mode", "output")
            else:
                return [["Requires digital or pwm"]]
        elif module_type == "Sound Sensor":
            if address_type == "analog":
                grovepi.pinMode(self.addresses[address][1], "INPUT")
                node.set_type("number")
                node.set_attribute("@unit", "%")
                node.set_attribute("@mode", "input")
            else:
                return [["Requires analog"]]
        elif module_type == "Button":
            if address_type == "digital" or address_type == "pwm":
                grovepi.pinMode(self.addresses[address][1], "INPUT")
                node.set_type("bool")
                node.set_attribute("@mode", "input")
            else:
                return [["Requires digital or pwm"]]
        elif module_type == "Relay":
            if address_type == "digital" or address_type == "pwm":
                grovepi.pinMode(self.addresses[address][1], "OUTPUT")
                node.set_type("bool")
                node.set_attribute("@mode", "output")
            else:
                return [["Requires digital or pwm"]]
        elif module_type == "Temp and Humid":
            if address_type == "digital" or address_type == "pwm":
                grovepi.pinMode(self.addresses[address][1], "INPUT")
                node.add_child(self.temp_node(node))
                node.add_child(self.humid_node(node))
                node.set_attribute("@mode", "input")
            else:
                return [["Requires digital or pwm"]]

        node.add_child(self.remove_module_node(node))

        self.super_root.add_child(node)

        return [
            [
                "Success!"
            ]
        ]

    def remove_module(self, parameters):
        self.super_root.remove_child(parameters.node.parent.name)
        return []

    @staticmethod
    def set_digital_node(root, name="Set Digital"):
        slug = name.replace(" ", "_").lower()
        node = Node(slug, root)
        node.set_display_name(name)
        node.set_config("$is", "set_digital")
        node.set_parameters([
            {
                "name": "Value",
                "type": "bool"
            }
        ])
        node.set_invokable("write")
        return node

    @staticmethod
    def set_analog_node(root, name="Set Analog"):
        slug = name.replace(" ", "_").lower()
        node = Node(slug, root)
        node.set_display_name(name)
        node.set_config("$is", "set_analog")
        node.set_parameters([
            {
                "name": "Value",
                "type": "number"
            }
        ])
        node.set_invokable("write")
        return node

    @staticmethod
    def remove_module_node(root):
        node = Node("remove_module", root)
        node.set_display_name("Remove Module")
        node.set_config("$is", "remove_module")
        node.set_invokable("config")
        return node

    def color_node(self, root):
        node = Node("color", root)
        node.set_attribute("@callback", "rgb_color")
        node.set_display_name("Color")
        node.set_type("dynamic")
        node.set_config("$editor", "color")
        node.set_config("$writable", "write")
        node.set_value_callback = self.set_color
        return node

    def text_node(self, root):
        node = Node("text", root)
        node.set_attribute("@callback", "rgb_text")
        node.set_display_name("Text")
        node.set_type("string")

        node.set_config("$writable", "write")
        node.set_value_callback = self.set_text
        return node

    def temp_node(self, root):
        node = Node("temp", root)
        node.set_display_name("Temperature")
        node.set_type("number")
        node.set_attribute("@unit", "C")
        return node

    def humid_node(self, root):
        node = Node("humid", root)
        node.set_display_name("Humidity")
        node.set_type("number")
        node.set_attribute("@unit", "%")
        return node

    def update_values(self):
        for child_name in self.super_root.children:
            child = self.super_root.children[child_name]
            try:
                if child.is_subscribed() and "@type" in child.attributes and "@mode" in child.attributes and child.attributes["@mode"] == "input":
                    address = self.addresses[child.attributes["@address"]][1]
                    port_type = child.attributes["@type"]
                    module = child.attributes["@module"]
                    if port_type == "pwm" or port_type == "digital":
                        if module == "Ultrasonic Ranger":
                            try:
                                child.set_value(grovepi.ultrasonicRead(address))
                            except TypeError:
                                pass
                        else:
                            val = grovepi.digitalRead(address)
                            if val != 255:
                                child.set_value(bool(val))
                    elif port_type == "analog":
                        child.set_value(self.analog_to_percent(grovepi.analogRead(address)))
                    elif port_type == "i2c":
                        pass
                    else:
                        raise ValueError("Unhandled type %s" % child.attributes["@type"])
                elif "@type" in child.attributes and "@mode" in child.attributes and child.attributes["@mode"] == "input":
                    module = child.attributes["@module"]
                    address = self.addresses[child.attributes["@address"]][1]
                    if module == "Temp and Humid":
                        temp = child.get("/temp")
                        humid = child.get("/humid")
                        if temp.is_subscribed() or humid.is_subscribed():
                            dht = grovepi.dht(address, 0)
                            if type(dht) is list and not isnan(dht[0]) and not isnan(dht[1]):
                                temp.set_value(dht[0])
                                humid.set_value(dht[1])

            except IOError:
                pass

        if self.super_root.get("/poll_speed").get_value() is None:
            self.super_root.get("/poll_speed").set_value(0.1)
        reactor.callLater(self.super_root.get("/poll_speed").get_value(), self.update_values)


    def module_enum(self):
        i = []
        for module in self.modules:
            i.append(module)
        return Value.build_enum(i)

    def address_enum(self):
        i = []
        for address in self.addresses:
            i.append(address)
        return Value.build_enum(i)

    @staticmethod
    def pwm_to_percent(val):
        return (val / float(255)) * 100

    @staticmethod
    def analog_to_percent(val):
        return (val / float(1023)) * 100

    @staticmethod
    def percent_to_pwm(val):
        return int((val / float(100)) * 255)

    @staticmethod
    def percent_to_analog(val):
        return int((val / float(100)) * 1023)


if __name__ == "__main__":
    GrovePiDSLink(Configuration(name="GrovePi", responder=True))
