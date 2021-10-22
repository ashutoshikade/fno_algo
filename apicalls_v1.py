from fyers_api import fyersModel
import sys

def main():
	## access_token from the redirect url
	with open('./access_token.txt', 'r') as f:
		access_token = f.read()

	## If you want to make asynchronous API calls then assign the below variable as True and then pass it in the functions, by default its value is False
	# is_async = True
	fyers = fyersModel.FyersModel()
	print(fyers.funds(token=access_token))
	# print(fyers.get_profile(token=access_token))
	# print(fyers.holdings(token=access_token))

if __name__ == '__main__':
	main()