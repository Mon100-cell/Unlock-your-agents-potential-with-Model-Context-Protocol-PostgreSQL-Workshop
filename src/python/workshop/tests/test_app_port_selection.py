import socket
import unittest

from app import find_available_port


class PortSelectionTests(unittest.TestCase):
    def test_find_available_port_returns_requested_port_when_free(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]

        self.assertEqual(find_available_port(port, 5), port)

    def test_find_available_port_uses_next_free_port_when_requested_port_is_in_use(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied_sock:
            occupied_sock.bind(("127.0.0.1", 0))
            requested_port = occupied_sock.getsockname()[1]

            candidate_port = requested_port + 1
            while True:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                        probe.bind(("127.0.0.1", candidate_port))
                    break
                except OSError:
                    candidate_port += 1

            returned_port = find_available_port(requested_port, 10)

            self.assertEqual(returned_port, candidate_port)


if __name__ == "__main__":
    unittest.main()
