import time
import calendar
import jwt
import requests
import re
import os
from flask import Flask, request, Response
import json
from dotmap import DotMap
import pd

import pprint
pp = pprint.PrettyPrinter(indent=4)

pd_key = os.environ.get('PD_KEY') or "Set your PD_KEY environment variable to a PD API token"
from_email = os.environ.get('FROM_EMAIL') or "Set your FROM_EMAIL environment variable to the login email of a PD user"
zoom_key = os.environ.get('ZOOM_KEY') or "Set your ZOOM_KEY environment variable to a Zoom REST API access key"
zoom_secret = os.environ.get('ZOOM_SECRET') or "Set your ZOOM_SECRET environment variable to your Zoom REST API client secret"
zoom_userid = os.environ.get('ZOOM_USERID') or "Set your ZOOM_USERID environment variable to your Zoom REST User ID"

app = Flask(__name__)

def zoom_token():
		zoom_jwt_payload = { 'iss': zoom_key, 'exp': calendar.timegm(time.gmtime()) + 36000 }
		zoom_token = jwt.encode(zoom_jwt_payload, zoom_secret)
		return zoom_token.decode("utf-8")

@app.route("/", methods=['POST'])
def index():
	req = DotMap(request.json)
	if req.event == 'meeting.participant_joined' or req.event == 'meeting.participant_left' or req.event == 'meeting.started' or req.event == 'meeting.ended':

		meeting_id = req.payload.object.id
		meeting_topic = req.payload.object.topic
		action = req.event.split('.')[1]
		if "_" in action:
			action = action.split('_')[1]
		user_name = req.payload.object.participant.user_name
		user_id = req.payload.object.participant.user_id
		zoom_req = requests.Request(method="get", 
			url=f"https://api.zoom.us/v2/users/{user_id}", 
			headers={"Authorization": f"Bearer {zoom_token()}"})
		prepped = zoom_req.prepare()
		response = requests.Session().send(prepped)

		user_email = response.json().get("email");
		if action == 'started' or action == 'ended':
			note = f'Zoom meeting {meeting_id} ({meeting_topic}) {action}'
		else:
			note = f'{user_name} ({user_email}) {action} Zoom meeting {meeting_id} ({meeting_topic})'

		incidents = pd.fetch(api_key=pd_key, endpoint="incidents", params={"statuses[]": ["triggered", "acknowledged"], "include[]": ["metadata"]})
		conf_bridges = [{"id": incident.get("id"), "metadata": incident.get("metadata")} for incident in incidents if incident.get("metadata")]

		for bridge in conf_bridges:
			if bridge["metadata"].get("conference_number"):
				conf = re.findall("[\d]+", bridge["metadata"]["conference_number"].replace('-', ''))[-1]
				if (meeting_id == conf):
					print(f'I should put this note on incident {bridge["id"]} because conference number is {bridge["metadata"]["conference_number"]}')
					r = pd.add_note(api_key=pd_key, incident_id=bridge["id"], from_email=from_email, note=note)
			elif bridge["metadata"].get("conference_url"):
				conf = re.findall("[\d]+", bridge["metadata"]["conference_url"].replace('-', ''))[-1]
				if (meeting_id == conf):
					print(f'I should put this note on incident {bridge["id"]} because conference url is {bridge["metadata"]["conference_url"]}')
					r = pd.add_note(api_key=pd_key, incident_id=bridge["id"], from_email=from_email, note=note)


	return "", 200

@app.route("/start", methods=['POST'])
def start_zoom():
	req = DotMap(request.json)
	incident_id = req.messages[0].incident.id
	incident_title = req.messages[0].incident.title
	incident_number = req.messages[0].incident.incident_number
	requester_id = req.messages[0].log_entries[0].agent.id
	requester_name = req.messages[0].log_entries[0].agent.summary
	url = f"https://api.zoom.us/v2/users/{zoom_userid}/meetings"

	topic = f'[{incident_number}] {incident_title}'
	print(f'start zoom requested on {topic} by {requester_id} ({requester_name})')

	data = {
		"type": 1,
		"topic": topic
	}
	req = requests.Request(
		method='POST',
		url=url,
		headers={"Authorization": f"Bearer {zoom_token()}"},
		json=data
	)

	prepped = req.prepare()
	response = requests.Session().send(prepped)
	res = DotMap(response.json())
	join_url = res.join_url
	print(f'created meeting {join_url} for incident {topic}')
	add_conf = {
		"requester_id": requester_id,
		"incidents": [
			{
				"id": incident_id,
				"type": "incident_reference",
				"metadata":  {
					"conference_url": join_url
				}
			}
		]
	}
	response = pd.request(api_key=pd_key, endpoint="/incidents", method="PUT", data=add_conf, addheaders={"From": from_email})

	return "", 200