import sys
import upay
from decimal import Decimal
import logging

tokens = upay.read_tokens_from_file(sys.argv[1])

logging.basicConfig(level=logging.DEBUG)

with upay.SessionManager().create_session() as session:
    session.validate_tokens(tokens)
    try:
        session.cash(Decimal(sys.argv[2]))
    except upay.NotEnoughCreditError as e:
        print("You need %.02f Eur extra credit for this."%e[0][1])
    print("Your total is %.02f Eur"%session.total)
    print("Your new balance is %.02f Eur"%session.credit)

