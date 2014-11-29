import upay
import time
import logging

logging.basicConfig(level=logging.DEBUG)
token_reader = upay.USBTokenReader()


while True:
    print("Waiting for purse")
    
    while True: 
        try:
            tokens = token_reader.read_tokens()
            break
        except upay.NoTokensAvailableError:
            time.sleep(1)

    print("Read %d tokens"%len(tokens))

    print("Waiting for medium to vanish")

    while token_reader.medium_valid:
        pass

   
