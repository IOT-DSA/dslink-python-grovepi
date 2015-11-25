from dslink import DSLink, Configuration, Node, Value
import dsa_grovepi as grovepi
import grove_rgb_led
from twisted.internet import reactor

_NUMERALS = '0123456789abcdefABCDEF'
_HEXDEC = {v: int(v, 16) for v in (x+y for x in _NUMERALS for y in _NUMERALS)}


def rgb(triplet):
    return _HEXDEC[triplet[0:2]], _HEXDEC[triplet[2:4]], _HEXDEC[triplet[4:6]]


class GrovePiDSLink(DSLink):
    addresses = {
        "D2": ["digital", 2],
        "D3": ["pwm", 3],
        "D4": ["digital", 4],
        "D5": ["pwm", 5],
        "D6": ["pwm", 6],
        "D7": ["digital", 7],
        "D8": ["digital", 8],
        "A0": ["analog", 0],
        "A1": ["analog", 1],
        "A2": ["analog", 2],
        "I2C-1": ["i2c", 1],
        "I2C-2": ["i2c", 2],
        "I2C-3": ["i2c", 3]
    }

    modules = [
        "LED",
        "LCD",
        "Light Sensor",
        "Rotary Angle Sensor",
        "Ultrasonic Ranger",
        "Buzzer",
        "Sound Sensor",
        "Button",
        "Relay",
        "Temp and Humid"
    ]

    def start(self):
        self.profile_manager.create_profile("add_module")
        self.profile_manager.register_callback("add_module", self.add_module)

        self.profile_manager.create_profile("remove_module")
        self.profile_manager.register_callback("remove_module", self.remove_module)

        self.profile_manager.create_profile("set_digital")
        self.profile_manager.register_callback("set_digital", self.set_digital)

        self.profile_manager.create_profile("set_analog")
        self.profile_manager.register_callback("set_analog", self.set_analog)

        self.profile_manager.create_profile("set_color")
        self.profile_manager.register_callback("set_color", self.set_color)

        self.profile_manager.create_profile("set_text")
        self.profile_manager.register_callback("set_text", self.set_text)

        reactor.callLater(0.1, self.update_values)

    def get_default_nodes(self):
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

        super_root.add_child(add_module)

        return super_root

    def set_digital(self, parameters):
        grovepi.digitalWrite(self.addresses[parameters.node.parent.attributes["@address"]][1], parameters.params["Value"])
        return []

    def set_analog(self, parameters):
        grovepi.analogWrite(self.addresses[parameters.node.parent.attributes["@address"]][1], int(parameters.params["Value"]))
        return []

    @staticmethod
    def set_color(parameters):
        red, green, blue = rgb(hex(int(parameters.params["Color"]))[2:].zfill(6))
        grove_rgb_led.set_rgb(red, green, blue)
        return []

    @staticmethod
    def set_text(parameters):
        text = str(parameters.params["Text"])
        grove_rgb_led.set_text(text)
        return []

    def add_module(self, parameters):
        if "Name" not in parameters.params:
            return [["Invalid name."]]
        node = Node(str(parameters.params["Name"]), self.super_root)
        module_type = parameters.params["Type"]
        address = parameters.params["Address"]
        address_type = self.addresses[address][0]
        node.set_attribute("@module", module_type)
        node.set_attribute("@address", address)
        node.set_attribute("@type", address_type)
        if module_type == "LED":
            if address_type == "pwm":
                grovepi.pinMode(self.addresses[address][1], "OUTPUT")
                node.add_child(self.set_analog_node(node, name="Set Brightness"))
                node.set_type("int")
                node.set_attribute("@mode", "output")
            elif address_type == "digital":
                grovepi.pinMode(self.addresses[address][1], "OUTPUT")
                node.add_child(self.set_digital_node(node, name="Toggle"))
                node.set_type("int")
                node.set_attribute("@mode", "output")
            else:
                return [["LED doesn't work on that."]]
        elif module_type == "LCD":
            node.add_child(self.set_color_node(node))
            node.add_child(self.set_text_node(node))
            node.set_attribute("@mode", "output")
        elif module_type == "Light Sensor":
            if address_type == "analog":
                node.set_type("int")
                node.set_attribute("@mode", "input")
            else:
                return [["Light Sensor doesn't work on that."]]
        elif module_type == "Rotary Angle Sensor":
            if address_type == "analog":
                grovepi.pinMode(self.addresses[address][1], "INPUT")
                node.set_type("int")
                node.set_attribute("display", "percent")
                node.set_attribute("@mode", "input")
            else:
                return [["Rotary Angle Sensor doesn't work on that."]]
        elif module_type == "Ultrasonic Ranger":
            if address_type == "digital" or address_type == "pwm":
                grovepi.pinMode(self.addresses[address][1], "INPUT")
                node.set_type("number")
                node.set_attribute("@unit", "cm")
                node.set_attribute("@mode", "input")
            else:
                return [["Ultrasonic Ranger doesn't work on that."]]
        elif module_type == "Buzzer":
            if address_type == "digital" or address_type == "pwm":
                grovepi.pinMode(self.addresses[address][1], "OUTPUT")
                node.add_child(self.set_digital_node(node, name="Toggle"))
                node.add_child(self.set_analog_node(node, name="Set Frequency"))
                node.set_type("number")
                node.set_attribute("@mode", "output")
            else:
                return [["Buzzer doesn't work on that."]]
        elif module_type == "Sound Sensor":
            if address_type == "analog":
                grovepi.pinMode(self.addresses[address][1], "INPUT")
                node.set_type("number")
                node.set_attribute("@unit", "dB")
                node.set_attribute("@mode", "input")
            else:
                return [["Sound Sensor doesn't work on that."]]
        elif module_type == "Button":
            if address_type == "digital" or address_type == "pwm":
                grovepi.pinMode(self.addresses[address][1], "INPUT")
                node.set_type("number")
                node.set_attribute("@mode", "input")
            else:
                return [["Button doesn't work on that."]]
        elif module_type == "Relay":
            if address_type == "digital" or address_type == "pwm":
                grovepi.pinMode(self.addresses[address][1], "OUTPUT")
                node.add_child(self.set_digital_node(node, name="Toggle"))
                node.set_type("number")
                node.set_attribute("@mode", "output")
            else:
                return [["Button doesn't work on that."]]
        elif module_type == "Temp and Humid":
            if address_type == "digital" or address_type == "pwm":
                grovepi.pinMode(self.addresses[address][1], "INPUT")
                node.set_type("array")
                node.set_attribute("@mode", "input")

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
                "type": "int"
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

    @staticmethod
    def set_color_node(root):
        node = Node("set_color", root)
        node.set_display_name("Set Color")
        node.set_config("$is", "set_color")
        node.set_parameters([
            {
                "name": "Color",
                "type": "color",
            }
        ])
        node.set_invokable("write")
        return node

    @staticmethod
    def set_text_node(root):
        node = Node("set_text", root)
        node.set_display_name("Set Text")
        node.set_config("$is", "set_text")
        node.set_parameters([
            {
                "name": "Text",
                "type": "string"
            }
        ])
        node.set_invokable("write")
        return node

    def update_values(self):
        for child_name in self.super_root.children:
            child = self.super_root.children[child_name]
            if child.is_subscribed() and "@type" in child.attributes and "@mode" in child.attributes and child.attributes["@mode"] == "input":
                try:
                    address = self.addresses[child.attributes["@address"]][1]
                    port_type = child.attributes["@type"]
                    module = child.attributes["@module"]
                    if port_type == "pwm" or port_type == "digital":
                        if module == "Ultrasonic Ranger":
                            try:
                                child.set_value(grovepi.ultrasonicRead(address))
                            except TypeError:
                                pass
                        elif module == "Temp and Humid":
                            dht = grovepi.dht(address, 0)
                            if type(dht) is list:
                                child.set_value(dht)
                        else:
                            child.set_value(grovepi.digitalRead(address))
                    elif port_type == "analog":
                        child.set_value(grovepi.analogRead(address))
                    elif port_type == "i2c":
                        pass
                    else:
                        raise ValueError("Unhandled type %s" % child.attributes["@type"])
                except IOError:
                    pass

        reactor.callLater(0.1, self.update_values)

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

if __name__ == "__main__":
    GrovePiDSLink(Configuration(name="GrovePi", responder=True))
