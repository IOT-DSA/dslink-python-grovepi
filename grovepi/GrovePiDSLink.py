from dslink import DSLink, Configuration, Node, Value
import grovepi
import grove_rgb_led
from twisted.internet import reactor

sensors = {
    "D2": ["digital", 2],
    "D3": ["pwm", 3],
    "D4": ["digital", 4],
    "D5": ["pwm", 5],
    "D6": ["pwm", 6],
    "D7": ["digital", 7],
    "D8": ["digital", 8],
    "A0": ["analog", 0],
    "A1": ["analog", 1],
    "A2": ["analog", 2]
}


class GrovePiDSLink(DSLink):
    def start(self):
        self.profile_manager.create_profile("add_sensor")
        self.profile_manager.register_callback("add_sensor", self.add_sensor)

        self.profile_manager.create_profile("add_lcd")
        self.profile_manager.register_callback("add_lcd", self.add_lcd)

        self.profile_manager.create_profile("remove_sensor")
        self.profile_manager.register_callback("remove_sensor", self.remove_sensor)

        self.profile_manager.create_profile("set_digital")
        self.profile_manager.register_callback("set_digital", self.set_digital)

        self.profile_manager.create_profile("set_analog")
        self.profile_manager.register_callback("set_analog", self.set_analog)

        self.profile_manager.create_profile("set_rgb")
        self.profile_manager.register_callback("set_rgb", self.set_rgb)

        self.profile_manager.create_profile("set_text")
        self.profile_manager.register_callback("set_text", self.set_text)

        reactor.callLater(0.1, self.update_values)

    def get_default_nodes(self):
        super_root = self.get_root_node()

        add_sensor = Node("add_sensor", super_root)
        add_sensor.set_display_name("Add Sensor")
        add_sensor.set_config("$is", "add_sensor")
        add_sensor.set_parameters([
            {
                "name": "Name",
                "type": "string"
            },
            {
                "name": "Sensor",
                "type": self.sensor_enum()
            }
        ])
        add_sensor.set_invokable("config")

        add_lcd = Node("add_lcd", super_root)
        add_lcd.set_display_name("Add LCD")
        add_lcd.set_config("$is", "add_lcd")
        add_lcd.set_parameters([
            {
                "name": "Name",
                "type": "string"
            }
        ])
        add_lcd.set_invokable("config")

        super_root.add_child(add_sensor)
        super_root.add_child(add_lcd)

        return super_root

    @staticmethod
    def set_digital(parameters):
        grovepi.digitalWrite(int(parameters.node.parent.attributes["@address"]), parameters.params["Value"])
        return []

    @staticmethod
    def set_analog(parameters):
        grovepi.analogWrite(int(parameters.node.parent.attributes["@address"]), int(parameters.params["Value"]))
        return []

    @staticmethod
    def set_rgb(parameters):
        red = int(parameters.params["Red"])
        green = int(parameters.params["Green"])
        blue = int(parameters.params["Blue"])
        grove_rgb_led.set_rgb(red, green, blue)
        return []

    @staticmethod
    def set_text(parameters):
        text = str(parameters.params["Text"])
        grove_rgb_led.set_text(text)
        return []

    def add_sensor(self, parameters):
        sensor_type = sensors[str(parameters.params["Sensor"])][0]
        address = sensors[parameters.params["Sensor"]][1]
        sensor = Node(parameters.params["Name"], self.super_root)
        sensor.set_type("int")
        sensor.set_attribute("@port", str(parameters.params["Sensor"]))
        sensor.set_attribute("@address", address)
        sensor.set_attribute("@type", sensor_type)
        self.super_root.add_child(sensor)
        if sensor_type is "digital":
            sensor.add_child(self.set_digital_node(sensor))
        elif sensor_type is "analog":
            sensor.add_child(self.set_analog_node(sensor))
        elif sensor_type is "pwm":
            sensor.add_child(self.set_digital_node(sensor))
            sensor.add_child(self.set_analog_node(sensor))
        sensor.add_child(self.remove_sensor_node(sensor))
        return []

    def add_lcd(self, parameters):
        lcd = Node(str(parameters.params["Name"]), self.super_root)
        lcd.add_child(self.set_rgb_node(lcd))
        lcd.add_child(self.remove_sensor_node(lcd))
        lcd.add_child(self.set_text_node(lcd))
        self.super_root.add_child(lcd)
        return []

    def remove_sensor(self, parameters):
        self.super_root.remove_child(parameters.node.parent.name)
        return []

    @staticmethod
    def set_digital_node(root):
        node = Node("set_digital", root)
        node.set_display_name("Set Digital")
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
    def set_analog_node(root):
        node = Node("set_analog", root)
        node.set_display_name("Set Analog")
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
    def remove_sensor_node(root):
        node = Node("remove_sensor", root)
        node.set_display_name("Remove Sensor")
        node.set_config("$is", "remove_sensor")
        node.set_invokable("config")
        return node

    @staticmethod
    def set_rgb_node(root):
        node = Node("set_rgb", root)
        node.set_display_name("Set RGB")
        node.set_config("$is", "set_rgb")
        # TODO(logangorence): Use DGLux color picker.
        node.set_parameters([
            {
                "name": "Red",
                "type": "int",
                "default": 255
            },
            {
                "name": "Green",
                "type": "int",
                "default": 255
            },
            {
                "name": "Blue",
                "type": "int",
                "default": 255
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
            if "@type" in child.attributes:
                if child.attributes["@type"] == "pwm":
                    child.set_value(grovepi.analogRead(child.attributes["@address"]))

        reactor.callLater(0.1, self.update_values)

    @staticmethod
    def sensor_enum():
        i = []
        for sensor in sensors:
            i.append(sensor)
        return Value.build_enum(i)

if __name__ == "__main__":
    GrovePiDSLink(Configuration(name="GrovePi", responder=True))
