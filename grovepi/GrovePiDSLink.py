from dslink import DSLink, Configuration, Node
import grovepi

sensors = [
    "D2",
    "D3",
    "D4",
    "D5",
    "D6",
    "D7",
    "D8",
    "A0",
    "A1",
    "A2",
]


class GrovePiDSLink(DSLink):
    def start(self):
        print("Connected")

    def get_default_nodes(self):
        super_root = self.get_root_node()

        for sensor in sensors:
            node = Node(sensor, super_root)
            node.set_type("number")
            node.set_value(0)
            node.set_config("$writable", "config")
            node.set_value_callback = self.set_value_callback
            super_root.add_child(node)

        return super_root

    def set_value_callback(self, node, value):
        if node.name[:1] is "D":
            grovepi.digitalWrite(int(node.name[1:]), value)
        elif node.name[:1] is "A":
            grovepi.analogWrite(int(node.name[1:]), value)

if __name__ == "__main__":
    GrovePiDSLink(Configuration(name="GrovePi", responder=True, no_save_nodes=True))
