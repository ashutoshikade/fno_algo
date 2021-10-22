from fyers_api import fyersModel
import sys

# app_id = "W1RAAGH8EP"
# app_secret = "IJTNUS9VS5"
# access_token = "gAAAAABhPeVlFy-Gif0I3_CG2nqt95OEUlkKsFXN9gfcKOhXZDedT3AnhQw413t5QI3piO6PVCUI6dPxQuOosvO7mctr__rVVe21Au9mJyz9QJLaYBscJOk"

def main():
	access_token = "gAAAAABhPfCqNKmaQb9Sp4ssT3BaBxV1gFTdypWo2UQBCoaKbNgLwmaDvmBzaUwPbdTAncYaIFk71k38fYwkqruL-mlVf_acYbW9k-WI8hdO4sDoOkAX1Mw=" ## access_token from the redirect url
	## If you want to make asynchronous API calls then assign the below variable as True and then pass it in the functions, by default its value is False
	# is_async = True
	fyers = fyersModel.FyersModel()
	print(fyers.get_profile(token=access_token))
if __name__ == '__main__':
	main()