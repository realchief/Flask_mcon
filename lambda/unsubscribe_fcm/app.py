import json
import random
import datetime

import psycopg2
from flask import (Flask, flash, jsonify, make_response, redirect,
                   render_template, request, url_for)
from pyfcm import FCMNotification

app = Flask(__name__)


# Instantiate PyFCM With API Key
push_service = FCMNotification(
    api_key="AAAAkWfmn0k:APA91bFaHkrZQH6X7HlnUVlRXotiGOphHGsI4Uyjto0dh-cZQQsLOjhktEfKnw3niwy_6xO866KXKVyhrqEDVcFnh-Yp7uM2qnekeEiRJM-hCvJcp1zIhIR-aBQNZoYfmHyiecHd_cfG")

# Establish connection to Postgres RDS
conn = psycopg2.connect(
    database="pushengine",
    user="root",
    password="VK%Gu?kNdlS{",
    host="blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com",
    port="5432")
conn.autocommit = True
cur = conn.cursor()

@app.route('/unsubscribe_fcm/<fcm_registration_ids>', methods=['GET', 'POST'])
def unsubscribe(fcm_registration_ids):
    try:
        print('Checking for valid ids...')
        fcm_registration_ids = fcm_registration_ids.split("$H!*")
        print(fcm_registration_ids)
        valid_registration_ids = []
        valid_ids = push_service.clean_registration_ids(fcm_registration_ids)
        invalid_ids = list(set(fcm_registration_ids) - set(valid_ids))
    except Exception, error:
        conn.close()
        return make_response('Could Not get registration ids', 400)

    try:
        for item in invalid_ids:
            if item:
                print('User Invalid')
                fcm_sql = """SELECT country, sourcename from fcm_users where fcm = '{}';""".format(item)
                print(fcm_sql)
                cur.execute(fcm_sql)
                fcm_results = cur.fetchone()
                country = fcm_results[0]
                sourcename = fcm_results[1]
                today_str = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S+00')
                print(today_str)
                fcm_sql = """INSERT INTO fcm_churn VALUES ('%s', '%s', '%s');""" % (today_str, country, sourcename)
                #fcm_sql = """INSERT INTO fcm_churn VALUES ('%s', '%s');""" % (country, sourcename)
                print(fcm_sql)
                cur.execute(fcm_sql)
                fcm_sql = """DELETE from fcm_users where fcm = '{}';""".format(item)
                print(fcm_sql)
                cur.execute(fcm_sql)
            else:
                conn.close()
                return make_response('200 - OK', 200)
    except Exception, error:
        conn.close()
        return make_response('Could not delete registration id', 400)

    return make_response('200 - OK', 200)


if __name__ == '__main__':
    app.run()
