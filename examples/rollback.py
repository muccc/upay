import ConfigParser
import sys
import nupay
from decimal import Decimal

config = ConfigParser.RawConfigParser()
config.read(sys.argv[1])

tokens = nupay.read_tokens_from_file(sys.argv[2])

with nupay.SessionManager(config).create_session() as session:
    session.validate_tokens(tokens)
    try:
        transaction = session.cash(Decimal(sys.argv[3]))
        session.rollback(transaction)
    except nupay.NotEnoughCreditError as e:
        print("You need %.02f Eur extra credit for this."%e[0][1])
    print("Your total is %.02f Eur"%session.total)
    print("Your new balance is %.02f Eur"%session.credit)

