from dslink import DSLink, Configuration, Node, Profile
import grovepi
from twisted.internet import reactor

sensors = [
    ["D2", True, False, 2],
    ["D3", True, True, 3],
    ["D4", True, False, 4],
    ["D5", True, True, 5],
    ["D6", True, True, 6],
    ["D7", True, False, 7],
    ["D8", True, False, 8],
    ["A0", False, True, 0],
    ["A1", False, True, 1],
    ["A2", False, True, 2]
]


class GrovePiDSLink(DSLink):
    def start(self):
        self.profile_manager.create_profile(Profile("set_digital"))
        self.profile_manager.register_callback("set_digital", self.set_digital)

        self.profile_manager.create_profile(Profile("set_analog"))
        self.profile_manager.register_callback("set_analog", self.set_analog)

        reactor.callLater(0.1, self.update_values)

    def get_default_nodes(self):
        super_root = self.get_root_node()

        for sensor in sensors:
            node = Node(sensor[0], super_root)
            node.set_type("number")
            if sensor[1]:  # Digital
                set_digital = Node("Set Digital", node)
                set_digital.set_config("$is", "set_digital")
                set_digital.set_parameters([
                    {
                        "name": "Value",
                        "type": "bool"
                    }
                ])
                set_digital.set_invokable("write")
                node.add_child(set_digital)
            if sensor[2]:  # Analog
                set_analog = Node("Set Analog", node)
                set_analog.set_config("$is", "set_analog")
                set_analog.set_parameters([
                    {
                        "name": "Value",
                        "type": "int"
                    }
                ])
                set_analog.set_invokable("write")
                node.add_child(set_analog)
            super_root.add_child(node)

        return super_root

    @staticmethod
    def set_digital(parameters):
        grovepi.digitalWrite(int(parameters.node.parent.name[1:]), parameters.params["Value"])

    @staticmethod
    def set_analog(parameters):
        print(int(parameters.node.parent.name[1:]))
        print(type(parameters.params["Value"]))
        grovepi.analogWrite(int(parameters.node.parent.name[1:]), int(parameters.params["Value"]))

    def update_values(self):
        for sensor in sensors:
            # noinspection PyBroadException
            try:
                if sensor[1]:
                    self.super_root.get("/%s/" % sensor[0]).set_value(grovepi.digitalRead(sensor[3]))
                if sensor[2]:
                    self.super_root.get("/%s/" % sensor[0]).set_value(grovepi.analogRead(sensor[3]))
            except:
                pass
        reactor.callLater(0.5, self.update_values)

if __name__ == "__main__":
    GrovePiDSLink(Configuration(name="GrovePi", responder=True, no_save_nodes=True))
