import unittest
import mock
import logging
import ConfigParser
from  decimal import Decimal
import sqlalchemy.exc
import sqlalchemy.orm.exc
import sys

import nupay

def db_config():
    config = ConfigParser.RawConfigParser()
    config.add_section("Database")
    config.set("Database", "url", "sqlite:///:memory:")
    config.set("Database", "echo", "True")
    #config.set("Database", "url", "postgresql://testuser:fnord23@localhost:5432/testtokendb")
    config.set("Database", "allow_bootstrap", "True")
    return config

class SessionManagerTest(unittest.TestCase):
    
    def setUp(self):
        #logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(level=logging.ERROR)
        self.config = db_config()

    def test_create_session(self):
        self.session_manager = nupay.ServerSessionManager(self.config)
        session = self.session_manager.create_session()
        self.assertIsInstance(session, nupay.ServerSession)
        session.close()

    def test_create_session_manager(self):
        self.session_manager = nupay.ServerSessionManager(self.config)

    def test_create_bad_session_mamager(self):
        self.config.set("Database", "url", "postgresql://testuser:fnord233@localhost:5432/testtokendb")
        self.assertRaises(nupay.SessionConnectionError, nupay.ServerSessionManager, self.config)

class SessionTest(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
        #logging.basicConfig(level=logging.ERROR)
        self.config = db_config()
        self.session_manager = nupay.ServerSessionManager(self.config)
        self.session_manager.bootstrap_db()
        session = self.session_manager.create_session()

    def tearDown(self):
        pass

    def test_bad_validation(self):
        session = self.session_manager.create_session()
        session.create_tokens(Decimal(5))
        session.close()
 
        hashes = [nupay.Token().hash, nupay.Token().hash]
        session = self.session_manager.create_session()
        credit = session.validate_hashes(hashes)
        self.assertEqual(credit, 0)
        session.close()
    
    def test_create_token(self):
        session = self.session_manager.create_session()
        session.create_tokens(Decimal(5))
        session.close()
 
    def test_good_validation(self):
        session = self.session_manager.create_session()
        tokens = session.create_tokens(Decimal(1))
        hashes = [t.hash for t in tokens]
        session.close()
        
        session = self.session_manager.create_session()
        credit = session.validate_hashes(hashes)
        self.assertEqual(credit, Decimal('1'))
        session.close()
 
    def test_double_validation(self):
        session = self.session_manager.create_session()
        tokens = session.create_tokens(Decimal(1))
        hashes = [t.hash for t in tokens]
        session.close()
        
        session = self.session_manager.create_session()
        credit = session.validate_hashes(hashes)
        self.assertEqual(credit, Decimal('1'))
        session.close()
 
        session = self.session_manager.create_session()
        credit = session.validate_hashes(hashes)
        self.assertEqual(credit, Decimal('1'))
        session.close()
       
    def test_bad_cash(self):
        session = self.session_manager.create_session()
        tokens = session.create_tokens(Decimal(2))
        hashes = [t.hash for t in tokens]
        session.close()

        session = self.session_manager.create_session()
        session.validate_hashes(hashes)
        self.assertRaises(nupay.NotEnoughCreditError, session.cash, Decimal(2.1))
        self.assertEqual(0, session.total)
        self.assertEqual(Decimal(2), session.credit)
        session.close()

    def test_good_cash(self):
        session = self.session_manager.create_session()
        tokens = session.create_tokens(Decimal(2))
        hashes = [t.hash for t in tokens]
        session.close()

        session = self.session_manager.create_session()
        session.validate_hashes(hashes)
        session.cash(Decimal(2.0))
        self.assertEqual(Decimal(2.0), session.total)
        self.assertEqual(Decimal(0), session.credit)
        session.close()

    def test_good_cash_split(self):
        session = self.session_manager.create_session()
        tokens = session.create_tokens(Decimal(2))
        hashes = [t.hash for t in tokens]
        session.close()

        session = self.session_manager.create_session()
        session.validate_hashes(hashes)
        session.cash(Decimal(1.0))
        session.cash(Decimal(0.25))
        self.assertRaises(nupay.NotEnoughCreditError, session.cash, Decimal(1.0))
        self.assertEqual(Decimal(1.5), session.total)
        self.assertEqual(Decimal(0.5), session.credit)
        session.close()

    def test_rollback(self):
        session = self.session_manager.create_session()
        tokens = session.create_tokens(Decimal(2))
        hashes = [t.hash for t in tokens]
        session.close()

        session = self.session_manager.create_session()
        session.validate_hashes(hashes)
        session.cash(Decimal(1.0))
        tokens = (session.cash(Decimal(0.25)))
        session.rollback(tokens)
        self.assertRaises(nupay.RollbackError, session.rollback, tokens)
        session.cash(Decimal(1.0))
        self.assertRaises(nupay.NotEnoughCreditError, session.cash, Decimal(1.0))
        self.assertEqual(Decimal(2.0), session.total)
        session.close()
    
    def test_create_user(self):
        session = self.session_manager.create_session()
        session.create_user('foo')
        self.assertRaises(sqlalchemy.exc.IntegrityError, session.create_user, 'foo')
 
    def test_create_account(self):
        session = self.session_manager.create_session()
        session.create_account('foo')
        self.assertRaises(sqlalchemy.exc.IntegrityError, session.create_account, 'foo')
    
    def test_grant_right(self):
        session = self.session_manager.create_session()
        user = session.create_user('user1')
        account = session.create_account('account1')
        session.grant_right(user, account, 'foo right')
    
    def test_check_right(self):
        session = self.session_manager.create_session()
        user = session.create_user('user1')
        account = session.create_account('account1')
        session.grant_right(user, account, 'foo right')
        session.close()

        session = self.session_manager.create_session()
        user = session.get_user('user1')
        account = session.get_account('account1')
        session.check_right(user, account, 'foo right')
        
        self.assertRaises(nupay.PermissionError, session.check_right, user, account, 'foo_right')
    
    def test_get_user(self):
        session = self.session_manager.create_session()
        user1 = session.create_user('user1')
        user2 = session.create_user('user2')
        session.close()

        session = self.session_manager.create_session()
        self.assertEquals('user1', session.get_user('user1').name)
        self.assertRaises(sqlalchemy.orm.exc.NoResultFound, session.get_user, 'foo user')

    def test_get_account(self):
        session = self.session_manager.create_session()
        account1 = session.create_user('account1')
        account2 = session.create_user('account2')
        session.close()

        session = self.session_manager.create_session()
        self.assertEquals('account1', session.get_user('account1').name)
        self.assertRaises(sqlalchemy.orm.exc.NoResultFound, session.get_user, 'foo user')

    def test_good_transfer(self):
        session = self.session_manager.create_session()
        origin = session.create_account('origin')
        destination = session.create_account('destination')
        user = session.create_user('user')
        session.grant_right(user, origin, 'draw')
        session.grant_right(user, destination, 'deposit')
        
        session.transfer(origin = origin, destination = destination, amount = Decimal(1), user = user)

    def test_bad_transfers(self):
        session = self.session_manager.create_session()
        origin = session.create_account('origin')
        destination = session.create_account('destination')
        user = session.create_user('user')
        session.grant_right(user, origin, 'deposit')
        session.grant_right(user, destination, 'deposit')
        
        self.assertRaises(nupay.PermissionError, session.transfer, origin = origin, destination = destination, amount = Decimal(1), user = user)
        
        session.grant_right(user, origin, 'draw')
        self.assertRaises(nupay.LogicError, session.transfer, origin = origin, destination = origin, amount = Decimal(1), user = user)


if __name__ == '__main__':
    unittest.main()
