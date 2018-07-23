import json

import psycopg2
import requests
import treq
from pyfcm import FCMNotification
from twisted.internet import defer, reactor, task
from twisted.internet import _sslverify
from twisted.python.log import err
_sslverify.platformTrust = lambda : None

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
cur = conn.cursor()


def fetchURL(*urls):
    dList = []
    for url in urls:
        d = treq.get(url)
        d.addCallback(treq.content)
        d.addErrback(err)
        dList.append(d)
    return defer.DeferredList(dList)


def compare(responses):
    # the responses are returned in a list of tuples
    # Ex: [(True, b'')]
    for status, content in responses:
        print(content)


def main(reactor):
    urls = []
    fcm_sql = "SELECT fcm FROM fcm_users order by random() limit 5000;"
    cur.execute(fcm_sql)
    fcm_registration_ids = list(set([item[0] for item in cur.fetchall()]))
    valid_registration_ids = []
    while len(fcm_registration_ids) > 50:
        print('Collecting queue of work items')
        work_items = fcm_registration_ids[1:50]
        fcm_compressed = ""
        for item in work_items:
            fcm_compressed += item
            fcm_compressed += "$H!*"
        print('Spinning up registration id validation lambdas, ' + str(len(fcm_registration_ids)) + ' remaining')
        fcm_registration_ids = list(set(fcm_registration_ids) - set(work_items))
        # POST fcm_registration_ids to the lambda so it can perform validation
        urls.append('https://02vrhmo9gj.execute-api.eu-central-1.amazonaws.com/dev/unsubscribe_fcm/{}'.format(fcm_compressed[:-4]))
    d = fetchURL(*urls)     # returns Deferred
    d.addCallback(compare)  # fire compare() once the URLs return w/ a response
    return d                # wait for the DeferredList to finish

task.react(main)
