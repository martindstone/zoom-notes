import time
import calendar
import jwt
import requests
import os

zoom_key = os.environ.get('ZOOM_KEY') or "Set your ZOOM_KEY environment variable to a Zoom REST API access key"
zoom_secret = os.environ.get('ZOOM_SECRET') or "Set your ZOOM_SECRET environment variable to your Zoom REST API client secret"

def zoom_token():
		zoom_jwt_payload = { 'iss': zoom_key, 'exp': calendar.timegm(time.gmtime()) + 36000 }
		zoom_token = jwt.encode(zoom_jwt_payload, zoom_secret)
		return zoom_token.decode("utf-8")

url = "https://api.zoom.us/v2/users"

req = requests.Request(
	method='GET',
	url=url,
	headers={"Authorization": f"Bearer {zoom_token()}"}
)

prepped = req.prepare()
response = requests.Session().send(prepped)

for user in response.json()['users']:
	print(f'{user["email"]}: {user["id"]}')
