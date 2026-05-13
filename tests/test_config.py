import os

from unittest import TestCase
from unittest.mock import patch
import importlib


class TestConfig(TestCase):
    @patch.dict(os.environ, {
        'DATABASE_URI': '',
    }, clear=False)
    def test_DB_URI(self):
        """It should return custom db url"""
        from service import config
        importlib.reload(config)

        db_uri = config.DATABASE_URI
        self.assertEqual(
            db_uri, "postgresql://postgres:postgres@localhost:5432/postgres")
