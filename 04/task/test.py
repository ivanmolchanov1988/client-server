import unittest
import server01
import client01
import argparse


class Test_client_server(unittest.TestCase):
    def test_server_parser(self):
        test_parser = argparse.ArgumentParser()

        self.assertEqual((server01.createParser().parse_args().addr,
                          server01.createParser().parse_args().port),
                         ('', 7777))

    def test_client_parser(self):
        self.assertEqual((client01.createParser().parse_args().addr,
                          client01.createParser().parse_args().port),
                         ('', 7777))


if __name__ == '__main__':
    unittest.main()