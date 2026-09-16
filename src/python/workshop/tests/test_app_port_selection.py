import socket
import unittest

from app import find_available_port


class PortSelectionTests(unittest.TestCase):
    def test_find_available_port_returns_free_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]

        self.assertEqual(find_available_port(port, 5), port)


if __name__ == "__main__":
    unittest.main()
