import upay.common
import upay.client
import time
import logging

logging.basicConfig(level=logging.DEBUG)

token_reader = upay.common.USBTokenReader()
session_manager = upay.client.SessionManager()

while True:
    print("Waiting for purse")
    
    while True: 
        try:
            tokens = token_reader.read_tokens()
            break
        except upay.common.NoTokensAvailableError:
            time.sleep(1)

    print("Read %d tokens"%len(tokens))

    with session_manager.create_session() as session:
        session.validate_tokens(tokens)
        print("Your balance is %.02f Eur"%session.credit)

    print("Waiting for medium to vanish")

    while token_reader.medium_valid:
        time.sleep(1)

   
