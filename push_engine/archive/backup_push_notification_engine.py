#!/usr/bin/env python
# -*- coding: utf-8 -*-
# coding: utf8

"""
Push Notification Engine
Schedule a cron job to run me at 8,9,10pm, 1,2,3pm and 6,7,8pm
This module generates message templates which are then sent out to OneSignal for sending
Additionally it records the message components in postgresql
It then polls voluum (tracking platform) and onesignal (messaging platform)
to attach performance data to those message components
"""

__author__ = 'McHale Consulting (dmchale@mchaleconsulting.net)'
__copyright__ = 'Copyright (c) 2018 McHale Consulting'
__license__ = 'New-style BSD'
__vcs_id__ = '$Id$'
__version__ = '1.4.3'  # Versioning: http://www.python.org/dev/peps/pep-0386/

import base64
import datetime
import json
import logging
import random
import smtplib
import sys
import time
import urllib2

import psycopg2
import requests
from faker import Faker
import hashlib

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# create a file handler
handler = logging.FileHandler('/home/ubuntu/push_engine/push_engine.log')
handler.setLevel(logging.INFO)
# create a logging format
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(handler)

logger.info('Establishing database connection...')
conn = psycopg2.connect(
    database="pushengine",
    user="root",
    password="agdevil1",
    host="blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com",
    port="5432")
cur = conn.cursor()

logger.info("Database connection established.")

ttl = 2419200
priority = 5
fake = Faker('en_US')

# Selection of thumbnail to display next to message
thumbnail_list = [
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-1.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-2.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-3.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-4.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-5.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-6.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-7.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-8.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-9.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-10.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-11.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-12.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-13.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-14.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-15.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-16.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-17.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-18.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-19.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-20.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-21.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-22.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-23.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-24.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-25.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-26.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-27.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-28.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-29.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-30.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-31.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-32.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-33.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-34.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-35.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-36.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-37.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-38.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-39.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-40.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-41.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-43.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-44.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-45.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-46.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-47.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-48.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-49.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-50.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-51.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-52.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-53.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-54.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-55.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-56.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-57.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-58.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-59.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-60.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-61.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-62.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-63.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-64.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-65.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-66.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-67.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-68.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-69.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-70.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-71.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-72.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-73.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-74.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-75.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-76.jpg",
    "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-77.jpg"
]
thumbnail = random.choice(thumbnail_list)

# Selection of badge to display under message and in action bar
badge_list = [
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-1.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-2.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-3.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-4.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-5.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-6.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-7.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-8.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-9.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-10.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-11.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-12.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-13.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-14.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-15.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-16.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-17.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-18.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-19.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-20.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-21.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-22.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-23.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-24.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-25.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-26.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-27.png",
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-28.png"
    "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-29.png"
]
badge = random.choice(badge_list)
name = fake.first_name_female()
number_messages = random.randint(2, 7)
headline_types = [
    "recent",
    "latest",
    "strange",
    "unique",
    "unread",
    "urgent",
    "new",
    "special",
    "latest",
    "important",
    "sexy",
    "lusty",
]
headline_type = random.choice(headline_types)
#headline = "({}) Unread messages from {}".format(number_messages, name)

#campaigns = ['casino', 'general', 'casino', 'sweepstakes']
campaigns = ['general', 'general']
num_campaigns = len(campaigns)
campaign_num = random.randint(0, (num_campaigns - 1))
campaign = campaigns[campaign_num]

message_list = [
    "Can I tell you a secret? 👀",
    "What's your dream car? 🏎️",
    "Lmaooo, have you seen r/tifu today? 😂",
    "You have a wonderful name. 😜",
    "I found you through Michael 👨",
    "Tutor me pls 🙏🏻",
    "Craziest thing? Made out with my grandpa, wbu?",
    "didnt you fuck my sister? 🤔",
    "Quick favor? 😇",
    "Help me pls? 🤗",
    "I'm outside, are you still home? 💋",
    "You know what I like? 🍆",
    "No fucking way, did you really? 😰",
    "I would have been paralyzed! 😱",
    "Please tell me you did NOT! 🤣",
    "Are you home yet? 😈",
    "I'm shook 😳",
    "Can we go out tonight? 🤠",
    "Ugh, when are you off work? 😭",
    "Plsss tell, I can keep a secret! 🤐",
    "3rd time this wk I got stood up. 😢",
    "I really can't stand Trump 🙄",
    "I can't handle more Republicans 🙄",
    "Where are we going tonite? 💃🏻",
    "You thought I was AMY? 🖕🏻",
    "Hey sexy, can you come over? 👅",
    "My ex-bf just humiliated me. 😥",
    "Look, I just want an orgasm. 💦",
    "Terrific, free for drinks later? 🍻",
    "Think you can dazzle me? 😎",
    "I was an erotic dancer, you flirt! 💃🏻",
    "I need a sexy valentine. 💞",
    "I need to be used... 👄",
    "Do you have handcuffs? 👮",
    "Are you going to spank me? 👋",
    "I just want a fuck buddy 😬",
    "wtf are you doing? 😡",
    "omg look at this pic 👀",
    "don't share this pic with anyone 😈",
    "Just bought these panties 👙",
    "Kiss, kill, or marry?🤥",
    "I'm in agony today...😕",
    "Debt-free! Drinks on me.😘 ",
    "Did you see the cancer cure?",
    "Steal a kiss? Me?😘",
    "I'm no criminal, but I'm...",
    "Your profile is killer...💀",
    "Ya get the tumor results?😬",
    "He went to PRISON for it!😵",
    "Then that pervert beat me.😢",
    "I'm in pain from jealousy.🙃",
    "The surgery was a massacre.😰",
    "in the pistol, and I panicked!😩",
    "I was in hell, bankrupt too.😦 ",
    "Jail felt like a coffin.☠️",
    "I hate worrying like this.😱 ",
    "I'm feeling lots of aggression.",
    "Malaria? The test was right?😞",
    "Cancer? For real?😞",
    "A tumor? The test was right?😞",
    "You're gravely mistaken.",
    "Look, this is a CRISIS.😡",
    "I do, I blame you.😆",
    "It was an accident, you liar.😭",
    "You filthy bastard!😑",
    "You want me to cheat? 😈",
    "Jim? He's an insane nazi.💩",
    "You're too hot-tempered for me.👎",
    "Why are you acting resentful?😫",
    "God, why are you so messy?😫",
    "I'm sorry, I didn't mean it.",
    "Why are you so intolerant?😆",
    "Fuckkk, that IS disturbing.😱",
    "That's lethal? I had no idea.🤒 ",
    "You're being ultra-critical.😭",
    "You disloyal, sick, PHONY!😭",
    "Get nasty for me.👿",
    "dtf right now?",
    "I have bad news...",
    "GOT MY DIPLOMA!😁",
    "You got ambition?😤",
    "Courage? Caught me lion.🦁",
    "Boy I'm building wealth😁",
    "My excitement is for you.😈",
    "It'd be my honor.😁",
    "YOU GOT A PROMOTION?",
    "Biggest accomplishment?",
    "I strive for excellence.😘",
    "I wanna be your achievement.😘",
    "So win me then.😈",
    "Hope I see you in heaven.😇",
    "Want a victory prize?",
    "Come treasure me.😁",
    "Fight for my freedom?🇺🇲",
    "You need a holiday.😲",
    "I respect you...😲",
    "Angel, cheer me up with love.😘",
    "My reward was the sunrise.",
    "Friends with benefits?😍",
    "You're my pleasure.😈",
    "I'm going to be a mother.😱",
    "Little love and affection?😍",
    "Your laughter was cute.",
    "All kinds of loveliness.😜",
    "Meeting you was a joy.😍",
    "Come eat my cake. 👄",
    "Vacation at my place?😜",
    "See you soon, peace.",
    "I loved your music.",
    "Yeah, your family was great.😊",
    "Christmas? I love it!😊",
    "Wow, such kindness.😘",
    "Come find paradise.",
    "You were fun!🤤",
    "You're too kind.😜",
    "You didn't hate my laugh?😱",
    "I need a hug.",
    "I need your comfort.😘",
    "Okay, with me in autumn?😊",
    "Beach house w/ me?🤤",
    "It was pure bliss.😈",
    "You never called me?",
    "I'm pregnant...",
    "Don't tell anyone...",
    "Let's hangout...",
    "I never knew this...",
    "I need a sugar daddy...",
    "I hate TRUMP!",
    "I met Trump today!!",
    "My dog died...",
    "He was bit by a snake...",
    "Sorry, I'm running late...",
    "I need a ride to the airport?",
    "The baby is yours...",
    "I need a place to crash...",
    "I like anal...",
    "My car was stolen...",
    "Let's watch a movie...",
    "You gave me a hickey...",
    "What's your sign?",
    "Did you talk to her?"
]

num_messages = len(message_list)
message_num = random.randint(0, (num_messages - 1))
headline = message_list[message_num]

message = "({}) {} messages from {}".format(
    number_messages, headline_type, name)
# Log message information prior to sending
# Construct Tracking URL
# headline = emojiRender.emojize(
#    sentence + ' ' + emoji,
#    use_aliases=True).encode('utf8')

logger.info('Campaign: ' + campaign)
logger.info('Headline: ' + headline)
logger.info('Message: ' + message)
logger.info('Thumbnail: ' + thumbnail)
logger.info('Name: ' + name)
logger.info('Number of Messages: ' + str(number_messages))
logger.info('Badge Image: ' + badge)


translations = [
    "ar",
    "bg",
    "ca",
    "cs",
    "da",
    "de",
    "el",
    "en",
    "es",
    "et",
    "fa",
    "fi",
    "fr",
    "hi",
    "hr",
    "hu",
    "id",
    "it",
    "ja",
    "ka",
    "ko",
    "lt",
    "lv",
    "ms",
    "nl",
    "pl",
    "pt",
    "ro",
    "ru",
    "sk",
    "sr",
    "sv",
    "th",
    "tr",
    "uk",
    "vi"
]

localized_name_codes = {"ar": "ar_SA",
                        "bg": "bg_BG",
                        "ca": "es_ES",
                        "cs": "cs_CZ",
                        "da": "nl_NL",
                        "de": "de_DE",
                        "el": "el_GR",
                        "en": "en_US",
                        "es": "es_ES",
                        "et": "et_EE",
                        "fa": "fa_IR",
                        "fi": "fi_FI",
                        "fr": "fr_FR",
                        "hi": "hi_IN",
                        "hr": "hr_HR",
                        "hu": "hu_HU",
                        "id": "hi_IN",
                        "it": "it_IT",
                        "ja": "ja_JP",
                        "ka": "en_US",
                        "ko": "ko_KR",
                        "lt": "lt_LT",
                        "lv": "lv_LV",
                        "ms": "en_US",
                        "nl": "nl_NL",
                        "pl": "pl_PL",
                        "pt": "pt_PT",
                        "ro": "ro_RO",
                        "ru": "ru_RU",
                        "sk": "sl_SI",
                        "sr": "sl_SI",
                        "sv": "sv_SE",
                        "th": "en_US",
                        "tr": "tr_TR",
                        "uk": "uk_UA",
                        "vi": "en_US"
                       }
contents = {}
headings = {}
"""
for translation in translations:
    translator = Translator()
    fake = Faker(localized_name_codes[translation])
    name = fake.first_name_female()
    new_headline = "({}) {} messages from {}".format(number_messages, 
                                                     headline_type, 
                                                     name.encode("utf-8"))
    translated_headline = translator.translate('{}'.format(new_headline), 
                                                           src='en', 
                                                           dest='{}'.format(translation)).text
    contents[translation] = translated_headline
    translated_message = translator.translate('{}'.format(message), 
                                              src='en',     
                                              dest='{}'.format(translation)
                                             ).text
    headings[translation] = translated_message
"""
logger.info(contents)
logger.info(headings)
offer = 'default'
placement = base64.urlsafe_b64encode(hashlib.md5(headline).digest())
placement_list = ["ZjA5MWNhZWVjMWMyMTM4ZmZlMjY0MzExNTg5OGYzODI=",
"Zjk3MTM5NDdlMGQ3NDIyZjM5MmFlZDdkMzYxZjNmODY=",
"wFMvpasJrvvO_O4zh5FNbA==",
"WKZIEqfBDHbq0B_7Xkz0Cg==",
"x7_TlURfL7w0uU9AnQAYiA==",
"Qt9xZ5sayu46amCoRrsIIw==",
"OKlfih5OwqQcW3kRAbr-qA==",
"Q7SLXebfq5GQvb0bFGGLAQ==",
"7Y36ZHPYtvfyn11zy5R4NQ==",
"BpoQ2xYeqF950A4HqTT2JA=="]

popads_placements = []
popcash_placements = []
unknown_placements = []

placement = random.choice(placement_list)

requests.post(
    'https://hooks.slack.com/services/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',
    json={
        "text": "Sending push notification now..."})

tracking_chance = random.randint(1, 100)
path = 'default'
subscriber_key = '{{subscriber_key | default: "unknown" }}'

# MaxCleaner 
if tracking_chance == 0:
    tracking_url="http://trk.clickchaser.com/12da36fd-c4e8-4f52-b10f-4cdbb8e5c46a?message={}&headline={}&campaign={}&thumbnail={}&name={}&num_messages={}&badge={}&offer={}&placement={}&path={}&subscriber_key={}".format(message, headline, campaign, thumbnail, name, number_messages, badge, offer, placement, path, subscriber_key)
    logger.info('Sending MaxCleaner Link')
    logger.info('Tracking URL:')
    logger.info(tracking_url)

# MoboGamez
if tracking_chance == 0:
    tracking_url="http://trk.clickchaser.com/edc563d7-34d9-4fbc-a6cb-e200733e3347?message={}&headline={}&campaign={}&thumbnail={}&name={}&num_messages={}&badge={}&offer={}&placement={}&path={}&subscriber_key={}".format(message, headline, campaign, thumbnail, name, number_messages, badge, offer, placement, path, subscriber_key)
    logger.info('Sending MoboGamez Link')
    logger.info('Tracking URL:')
    logger.info(tracking_url)

# Affiliate Offers
if tracking_chance > 0:
    tracking_url = "http://trk.clickchaser.com/0faecec5-56de-4a85-acb9-49fa4902d071?message={}&headline={}&campaign={}&thumbnail={}&name={}&num_messages={}&badge={}&offer={}&placement={}&path={}&subscriber_key={}".format(message, headline, campaign, thumbnail, name, number_messages, badge, offer, placement, path, subscriber_key)
    logger.info('Sending Affiliate Link')
    logger.info('Tracking URL:')
    logger.info(tracking_url)


# Wait 1-5minutes before sending message to appear more natural
time_to_sleep = random.randint(30, 60)
logger.info('Sleeping for: ' + str(time_to_sleep))
time.sleep(time_to_sleep)

# for id in app_ids, loop through and send a message
onesignal_app_id = "650bceb6-cb6d-4b92-8a03-25d6c224efb1"
onesignal_rest_api_key = "MDZiMWVkNWItNzNkZC00ODY4LWJkZTMtNWViYTk0ZWE1NTA0"
app_ids = {"49db6ad5-8436-4fd6-b73d-d8b666c22865":
"ZWMxMGI5MDAtMTQ0Ni00YjVlLTg4MzAtZGNlZThmZmYwYjg3",
"106617c9-9423-4995-934e-29798ebcf78d":
"YjcxOTg0ZWItOTVhYy00NzQyLTkxY2ItNGVmMzU4NmRmYmM5",
"668921bd-2b70-4db4-86c4-3e067af25e4f":
"NzM1MjlkNDItZWI3Zi00NWQwLTgwNTgtYjE0YjEyMTc2ZTI1",
"6912f8ce-4d8f-462d-9302-4e9bff2b8cbf":
"MDAwYTM1MjktOWQ3Mi00YTRjLWI2OGYtZDc2YmU5NmE5MmQ5",
"6959f653-b568-42a8-bd0f-9026db57a8a0":
"MDgzMWVhYTQtMjkxZC00YjgyLWJjZTAtYmJhZmQ4M2ZhMjlj",
"7b114ee5-5e4e-41b5-a93d-db3853e14492":
"M2I1ZGI5ZGYtY2U3NS00NjE1LWJhYjYtYjI2YTNhY2NhNmRk",
"a39dd205-5d83-4a36-9ebc-f7422a734706":
"ODRhMzhiMjUtYTY1ZC00YWQwLTkzMTctNDc1NmNjNjkxYmFi",
"204b05c1-ab69-4005-928c-924f9b0fe31a":
"MjI4YWVlNWQtODU1Zi00MzU3LWEwNGEtYjJjYTIzYmU1MTMx",
"6deb6b65-1e54-4649-8da4-3514e9d300a7":
"ZmFlYTgzYzktZDZmMC00NjkyLTk1YTYtNzliM2U5NGY3NTQw",
"c52616a4-3e72-4396-a00b-3396523539c4":
"MmY1NDJmMjEtZTk2OS00MjhhLWE0YzEtYTVkZWZiMDE2NmY0",
"650bceb6-cb6d-4b92-8a03-25d6c224efb1":
"MDZiMWVkNWItNzNkZC00ODY4LWJkZTMtNWViYTk0ZWE1NTA0"
}

for onesignal_app_id in app_ids:
    # Message Sending Loop
    rest_authorization = "Basic {}".format(app_ids[onesignal_app_id])
    header = {"Content-Type": "application/json; charset=utf-8",
              "Authorization": rest_authorization}
    payload = {"app_id": onesignal_app_id,
               #"included_segments": ["All"],
               "ttl": ttl,
               "url": tracking_url,
			   "filters": [
                {"field": "tag", "key": "maxcleaner", "relation": "not_exists"}
               ],  
               "contents": {"en": "{}".format(message)},
               #"contents": contents,
               "headings": {"en": "{}".format(headline)},
               #"headings": headings,
               "chrome_web_icon": thumbnail,
               "chrome_web_badge": badge,
               #"priority": priority,
               "large_icon": thumbnail,
               "small_icon": thumbnail,
               "collapse_id": "collapse"}
    logger.info('Payload:')
    logger.info(payload)


    #TODO: Refactor to support multiple app ids
    req = requests.post("https://onesignal.com/api/v1/notifications",
                        headers=header,
                        data=json.dumps(payload))
    time.sleep(5)
    logger.info(req.status_code)
    logger.info(req.reason)
    try:
        push_results = req.json()
        notificationId = push_results['id']
        num_user_sent = push_results['recipients']
    except Exception as error:
        logger.info('Error retrieving results of push notification')
        notificationId = 'unknown'
        num_user_sent = 0

    image = ""

    # Get latest message to calculate churn rate, use notification_id to retrieve
    #cur.execute("SELECT * FROM public.latest_message order by creation_date desc limit 1;")
    #last_message = cur.fetchone()

    # Insert latest message after sending
    try:
        sql = """INSERT INTO public.latest_message (creation_date, headline, thumbnail, name, message, image, badge,
        num_user_sent) VALUES (current_timestamp, '{}', '{}', '{}', '{}', '{}', '{}', {})""".format(headline.replace("'", "''"), thumbnail, name, message, image, badge,
                                                                                                    num_user_sent)
        logger.info(sql)
        cur.execute(sql)
        conn.commit()
    except Exception as error:
        logger.info('Could not update latest_message')

    logger.info('Status Code: ' + str(req.status_code))
    logger.info('Notification ID: ' + str(notificationId))
    logger.info('Users Reached: ' + str(num_user_sent))


# Wait for 20 minutes
minutes = 20 * 60
time.sleep(minutes)

#TODO: Refactor to support multiple app ids
# Build onesignal Auth Headers
rest_authorization = "Basic {}".format(onesignal_rest_api_key)
header = {"Content-Type": "application/json; charset=utf-8",
          "Authorization": rest_authorization}
# Get churn stats after 20 minutes from oneSignal + voluum
notification_request_url = "https://onesignal.com/api/v1/apps/{}".format(
    onesignal_app_id)
req = requests.post(notification_request_url, headers=header)
time.sleep(5)
try:
    results = req.json()
    num_users_remaining = results['messageable_players']
    num_users_sent = results['messageable_players']
    num_user_lost = num_user_sent - num_users_remaining
except Exception as error:
    logger.info('Could not retrieve app data')
    num_users_remaining = 0
    num_users_sent = 0
    num_user_lost = 0
# Update churn using last message before updating latest_message


# Build onesignal Auth Headers
rest_authorization = "Basic {}".format(onesignal_rest_api_key)
header = {"Content-Type": "application/json; charset=utf-8",
          "Authorization": rest_authorization}
# Get message stats after 20 minutes from oneSignal + voluum
notification_request_url = "http://onesignal.com/api/v1/notifications/{}?app_id={}".format(
    str(notificationId), onesignal_app_id)
req = requests.post(notification_request_url, headers=header)
time.sleep(5)
results = req.json()

try:
    num_user_open = round(results['converted'], 2)
    clicks_worth = round(num_user_open * 0.0367, 2)
    lost_users_worth = round(num_user_lost * 0.078, 2)
    subscribers_worth = round(num_users_remaining * 0.078, 2)
    num_time_sent = 1
    num_user_converted = round(clicks_worth / 1.5, 2)
    revenue_generated = clicks_worth
    average_churn_rate = round((num_user_lost / num_user_sent) * 100, 2)
    average_open_rate = round((num_user_open / num_user_sent) * 100, 2)
    average_conversion_rate = round(
        (num_user_converted / num_user_open) * 100, 2)
except Exception as error:
    logger.info('Error updating performance information for element.')

logger.info(headline)
logger.info(message)
logger.info(num_time_sent)
logger.info(num_user_sent)
logger.info(num_user_open)
logger.info(num_user_lost)
logger.info(num_user_converted)
logger.info(revenue_generated)
logger.info(average_churn_rate)
logger.info(average_open_rate)
logger.info(average_conversion_rate)
conn.close()


def update_element(table, column, element, num_time_sent, num_user_sent, num_user_open, num_user_lost, num_user_converted,
                   revenue_generated, average_churn_rate, average_open_rate, average_conversion_rate):
    """
    Update or insert arbitrary elements into db w/ tracking data for each
    """
    logger.info('Establishing database connection...')
    conn = psycopg2.connect(
        database="pushengine",
        user="root",
        password="agdevil1",
        host="blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com",
        port="5432")
    cur = conn.cursor()
    logger.info("Database connection established.")
    sql = """SELECT * from public.{table} where {column} = '{element}';""".format(table=table, column=column,
                                                                                  element=element)
    logger.info(sql)
    cur.execute(sql)
    rows = cur.fetchall()
    logger.info(rows)
    if len(rows) > 0:
        original_num_user_sent = float(rows[0][4])
        original_num_user_open = float(rows[0][5])
        original_num_user_lost = float(rows[0][6])
        original_num_user_converted = float(rows[0][7])
        original_revenue_generated = float(rows[0][8])
        original_average_churn_rate = float(rows[0][9])
        original_average_open_rate = float(rows[0][10])
        original_average_conversion_rate = float(rows[0][11])
        num_user_sent = num_user_sent + original_num_user_sent
        num_user_open = num_user_open + original_num_user_open
        num_user_lost = num_user_lost + original_num_user_lost
        num_user_converted = num_user_converted + original_num_user_converted
        revenue_generated = revenue_generated + original_revenue_generated
        average_churn_rate = round((num_user_lost / num_user_sent * 100), 2)
        average_open_rate = round((num_user_open / num_user_sent) * 100, 2)
        average_conversion_rate = round(
            (num_user_converted / num_user_open) * 100, 2)
        sql = """UPDATE public.{table} SET num_time_sent=num_time_sent + 1, num_user_sent={num_user_sent},
        num_user_open={num_user_open}, num_user_lost={num_user_lost}, num_user_converted={num_user_converted}, revenue_generated={revenue_generated},
        average_churn_rate={average_churn_rate}, average_open_rate={average_open_rate},
        average_conversion_rate={average_conversion_rate} WHERE
        {column} ='{element}';""".format(table=table,
                                         num_user_sent=num_user_sent,
                                         num_user_open=num_user_open,
                                         num_user_lost=num_user_lost,
                                         num_user_converted=num_user_converted,
                                         revenue_generated=revenue_generated,
                                         average_churn_rate=average_churn_rate,
                                         average_open_rate=average_open_rate,
                                         average_conversion_rate=average_conversion_rate,
                                         column=column,
                                         element=element)
        logger.info(sql)
        cur.execute(sql)
        conn.commit()
    else:
        # Insert element if none found
        sql = """INSERT INTO public.{table} (creation_date, {column}, num_time_sent, num_user_sent, num_user_open,
        num_user_lost, num_user_converted, revenue_generated, average_churn_rate, average_open_rate, average_conversion_rate)
        VALUES (current_timestamp, '{element}', {num_time_sent}, {num_user_sent}, {num_user_open}, {num_user_lost},
        {num_user_converted}, {revenue_generated}, {average_churn_rate}, {average_open_rate},
        {average_conversion_rate});""".format(table=table,
                                              column=column,
                                              element=element,
                                              num_time_sent=num_time_sent,
                                              num_user_sent=num_user_sent,
                                              num_user_open=num_user_open,
                                              num_user_lost=num_user_lost,
                                              num_user_converted=num_user_converted,
                                              revenue_generated=revenue_generated,
                                              average_churn_rate=average_churn_rate,
                                              average_open_rate=average_open_rate,
                                              average_conversion_rate=average_conversion_rate)
        logger.info(sql)
        cur.execute(sql)
        conn.commit()
        conn.close()
        logger.info('Update/Insert Complete')


try:
    update_element('headlines', 'headline', headline.replace("'", "''"), num_time_sent, num_user_sent, num_user_open,
                   num_user_lost, num_user_converted, revenue_generated, average_churn_rate, average_open_rate, average_conversion_rate)
    logger.info('Headline updated.')
except Exception as error:
    logger.info('Error trying to update/insert headline.')
    logger.info(error)

try:
    update_element('messages', 'message', message.replace("'", "''"), num_time_sent, num_user_sent, num_user_open,
                   num_user_lost, num_user_converted, revenue_generated, average_churn_rate, average_open_rate,
                   average_conversion_rate)
    logger.info('Message updated.')
except Exception as error:
    logger.info('Error trying to update/insert message.')
    logger.info(error)

try:
    update_element('badges', 'badge', badge.replace("'", "''"), num_time_sent, num_user_sent, num_user_open,
                   num_user_lost, num_user_converted, revenue_generated, average_churn_rate, average_open_rate,
                   average_conversion_rate)
    logger.info('Badge updated.')
except Exception as error:
    logger.info('Error trying to update/insert badge.')
    logger.info(error)

try:
    update_element('thumbnails', 'thumbnail', thumbnail.replace("'", "''"), num_time_sent, num_user_sent, num_user_open,
                   num_user_lost, num_user_converted, revenue_generated, average_churn_rate, average_open_rate,
                   average_conversion_rate)
    logger.info('Thumbnail updated.')
except Exception as error:
    logger.info('Error trying to update/insert thumbnail.')
    logger.info(error)

try:
    update_element('names', 'name', name.replace("'", "''"), num_time_sent, num_user_sent, num_user_open,
                   num_user_lost, num_user_converted, revenue_generated, average_churn_rate, average_open_rate,
                   average_conversion_rate)
    logger.info('Name updated.')
except Exception as error:
    logger.info('Error trying to update/insert name.')
    logger.info(error)


# Log Results
logger.info('Notification ID:' + str(notificationId))
logger.info('Clicks: ' + str(num_user_open))
logger.info('Clicks worth: ' + str(clicks_worth))
logger.info('Lost Users: ' + str(num_user_lost))
logger.info('Lost Users Worth: ' + str(lost_users_worth))
logger.info('Subscribers: ' + str(subscribers))
logger.info('Subscribers Worth: ' + str(subscribers_worth))
logger.info('Net Gain/Loss: ' + str(clicks_worth - lost_users_worth))
logger.info('Open Rate: ' + str((num_user_open / subscribers * 100)) + '%')


def test():
    """ Testing Docstring"""
    pass

if __name__ == '__main__':
    test()
