from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import Boolean, Numeric
from sqlalchemy.orm import relationship, backref
from sqlalchemy import ForeignKey
from sqlalchemy.schema import UniqueConstraint
import re
import hashlib
import time
import os
import logging
from datetime import datetime

Base = declarative_base()

class Token(Base):
    __tablename__ = 'tokens'

    hash = Column(String, primary_key=True)
    used = Column(DateTime)
    created = Column(DateTime)

    def __repr__(self):
        return "<Token(hash='%s', used='%s', created='%s')>" % (self.hash, self.used, self.created)

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        t = str(int(time.time()))
        sha256 = hashlib.sha256()
        sha256.update(os.urandom(256))
        token = sha256.hexdigest()
        token += '%' + t
        self.token = token.strip()
        self.logger.debug("New token: %s"%self.token)

        sha512 = hashlib.sha512()
        sha512.update(self.token)
        self.hash = sha512.hexdigest()

        self.created = datetime.now()

class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key = True)
    name = Column(String, unique = True)
    is_cash = Column(Boolean)
    balance = Column(Numeric)
    is_kickstart = Column(Boolean)
    kickstart_target = Column(Numeric)
    is_active = Column(Boolean)
    keep_logs = Column(Boolean)

class AccountACL(Base):
    __tablename__ = 'accountacls'

    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", backref=backref('acls', order_by=id))

    account_id = Column(Integer, ForeignKey('accounts.id'))
    account = relationship("Account", backref=backref('acls', order_by=id))
    right = Column(String)

    __table_args__ = (UniqueConstraint('user_id', 'account_id', 'right', name='_uc'),)

class Pledge(Base):
    __tablename__ = 'pledges'

    id = Column(Integer, primary_key = True)
    amount = Column(Numeric)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", backref=backref('pledges', order_by=id))

    destination_id = Column(Integer, ForeignKey('accounts.id'))
    destination = relationship("Account", backref=backref('pledges', order_by=id))

    date = Column(DateTime)

    is_revoked = Column(Boolean)
    revokation_reason = Column(String)

    # TODO: what is this column for?
    token = Column(String)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key = True)
    name = Column(String, unique = True)
    max_transfer_amount = Column(Integer)
    rate_limit_in_s = Column(Integer)

class LogEntry(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", backref=backref('log_entries', order_by=id))

    amount = Column(Numeric)
    destination_account_id = Column(Integer, ForeignKey('accounts.id'))
    #destination_account = relationship("Account", backref=backref('destination_logs', order_by = id))
    destination_account = relationship("Account", foreign_keys=destination_account_id)
    
    origin_account_id = Column(Integer, ForeignKey('accounts.id'))
    #dorigin_account = relationship("Account", backref=backref('origin_logs', order_by = id))
    origin_account = relationship("Account", foreign_keys=origin_account_id)

    date = Column(DateTime)

    
