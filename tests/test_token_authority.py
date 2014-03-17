import unittest
import mock
import logging
import ConfigParser
from  decimal import Decimal
import sys

import nupay

def db_config():
    config = ConfigParser.RawConfigParser()
    config.add_section("Database")
    config.set("Database", "url", "sqlite:///:memory:")
    #config.set("Database", "url", "postgresql://testuser:fnord23@localhost:5432/testtokendb")
    config.set("Database", "allow_bootstrap", "True")
    return config

class TokenAuthorityConnectionTest(unittest.TestCase):
    
    def setUp(self):
        #logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
        logging.basicConfig(level=logging.ERROR)
        self.config = db_config()

    def test_create_token_authority(self):
        ta = nupay.TokenAuthority(self.config)

        self.assertIsInstance(ta, nupay.TokenAuthority)

    def test_create_bad_database_uri(self):
        self.config.set("Database", "url", "postgresql://testuser:fnord233@localhost:5432/testtokendb")
        self.assertRaises(nupay.SessionConnectionError, nupay.TokenAuthority, self.config)

class TokenAuthorityTest(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
        #logging.basicConfig(level=logging.ERROR)
        self.config = db_config()
        self._ta = nupay.TokenAuthority(self.config)
        self._ta.bootstrap_db()

    def tearDown(self):
        pass

    def test_create_token(self):
        t = self._ta.create_token(Decimal(2))
        self.assertIsInstance(t, nupay.Token)

if __name__ == '__main__':
    unittest.main()
