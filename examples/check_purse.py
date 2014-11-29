import sys
import upay.common
import upay.client

tokens = upay.common.read_tokens_from_file(sys.argv[1])

token_client = upay.client.TokenClient()

tokens = token_client.validate_tokens(tokens)

value = sum([token.value for token in tokens])

print("Your balance is %.02f Eur" % value)

