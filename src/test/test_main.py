import logging
import unittest

from spacel.main import setup_logging


class TestMain(unittest.TestCase):
    def setUp(self):
        self.root_logger = logging.getLogger()
        for handler in list(self.root_logger.handlers):
            self.root_logger.removeHandler(handler)

    def test_setup_logging(self):
        setup_logging()
        self.assertEquals(1, len(self.root_logger.handlers))

    def test_setup_logging_twice(self):
        setup_logging(logging.INFO)
        setup_logging(logging.INFO)
        self.assertEquals(1, len(self.root_logger.handlers))

    def test_setup_logging_debug(self):
        setup_logging(logging.DEBUG)
        stream_handler = self.root_logger.handlers[0]
        self.assertEquals(logging.DEBUG, stream_handler.level)
