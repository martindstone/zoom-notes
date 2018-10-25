# zoom-notes

This project implements two functions:

* Provides a destination for Zoom webhooks that can put participant joined / participant left notes in PagerDuty incidents when those events occur on a Zoom bridge that is being used as a PagerDuty conference bridge.
* Provides a custom action that opens a new Zoom meeting for a PagerDuty incident

To install, first you will need to get Zoom developer access. Log in at developer.zoom.us. Next, you will need to enable Zoom Webhooks V2.

Now you will need to deploy this app to Heroku (`heroku create`) and set the following config variables:

**FROM_EMAIL**: the login email of the PagerDuty user that will be seen as posting the timeline entries on PD incidents
**PD_KEY**: A read/write v2 PagerDuty API key (in PagerDuty, go to Configuration > API Access > Create New API Key)
**ZOOM_KEY**: Zoom developer credentials: "API Key"
**ZOOM_SECRET**: Zoom developer credentials: "API Secret"
**ZOOM_USERID**: Your Zoom user ID, looks like "3KsPLORiZ-u6ItjCb2vaiQ"

Sadly, it's not that easy to find your Zoom user ID, so I have written a script to list Zoom users with their ID's. To use it, set your ZOOM_KEY and ZOOM_SECRET first, like:

`heroku config:set ZOOM_KEY="YOUR_ZOOM_KEY" ZOOM_SECRET="YOUR_ZOOM_SECRET"`

and then run:

`heroku run python listusers.py`

You will get a list of user emails and Zoom ID's. Set ZOOM_USERID to the appropriate one, then set your PD_KEY and FROM_EMAIL, and you are ready to run the Heroku app.

Verify that the heroku app is up (`heroku ps`). Then, log back in to developer.zoom.com and under Webhooks, set the URL to be called to be the root URL of the Heroku deployment of the app you just deployed (You can find this by running `heroku info`)

Enable webhooks to be sent for "Meeting started", "Meeting ended", "Participant joined", and "Participant left" events

At this point, whenever a participant joins or leaves a Zoom bridge that is set as the Conference Bridge for a PagerDuty incident, an appropriate note will be recorded on the incident.

Next, configure a custom action to create a Zoom bridge on demand from a PagerDuty incident:

1. In PagerDuty, go to Configuration > Extensions > Custom Incident Actions Extension
1. In the Custom Incident Actions page, click on the green button labeled New Action
1. Set an appropriate label and description for the action, like "Start Zoom"
1. Choose the PagerDuty services where you want this action to appear
1. For the URL Endpoint, fill in the heroku app's Web URL, followed by "start" - for example, of your heroku app is deployed at https://curious-wallaby.herokuapp.com, fill in https://curious-wallaby.herokuapp.com/start

Now you will be able to create a new Zoom bridge on demand from any PagerDuty incident.
