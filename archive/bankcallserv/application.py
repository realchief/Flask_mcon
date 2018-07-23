#!/usr/env/bin
# -*- coding:utf8 -*-

# Module for handling call response xml for plivo incoming calls

from flask import Flask, Response, request, url_for
import plivo, plivoxml

app = Flask(__name__)

@app.route("/connect/", methods=['GET', 'POST'])
def connect():
    r = plivoxml.Response()
    if request.method == 'GET':
        # Generate a Dial XML with the details of the number to call
	body = "https://s3.ap-south-1.amazonaws.com/smsresource/Bankruptcy.mp3"
        prompt = "Press 1 to connect to another caller"
        no_input = "No input received. Goodbye"
        getdigits_action_url = url_for('connect', _external=True)
        getDigits = plivoxml.GetDigits(action=getdigits_action_url,
                                       method='POST', timeout=15, numDigits=1,
                                       retries=1)
	r.addPlay(body)
        r.add(getDigits)
        r.addSpeak(no_input)

        return Response(str(r), mimetype='text/xml')

    elif request.method == 'POST':
        confirmation = "Connecting your call.."

        digit = request.form.get('Digits')

        if digit == "1":
            r.addSpeak(confirmation)
            number = "13346410046"
	    callerId = request.values.get('To')
	    print('Caller ID is ' + str(callerId))
	    callerName = request.values.get('To')
	    print('Caller name is ' + str(callerName))
	    params = {
		#'callerId': '{}'.format(callerId),
		'callerId': '443-362-9016',
		#'callerName': '{}'.format(callerName)
		'callerName': '443-362-9016'
	    }
            d = r.addDial(**params)
            d.addNumber(number)
        else:
            r.addSpeak("Invalid Digit")

        print r.to_xml()
        return Response(str(r), mimetype='text/xml')

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
