#!/usr/bin/env python
# -*- coding: utf-8 -*-
# coding: utf8

"""
Push Helper
Contains helper functions for PushEngine
"""

__author__ = 'McHale Consulting (dmchale@mchaleconsulting.net)'
__copyright__ = 'Copyright (c) 2018 McHale Consulting'
__license__ = 'New-style BSD'
__vcs_id__ = '$Id$'
__version__ = '1.0.0'  # Versioning: http://www.python.org/dev/peps/pep-0386/

import logging
import random

# Instantiate logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a logging format
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def generateThumbnail():
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
        "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-31.jpg",
        "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-32.jpg",
        "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-33.jpg",
        "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-34.jpg",
        "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-35.jpg",
        "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-36.jpg",
        "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-37.jpg",
        "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-38.jpg",
        "https://d3e0hlhsoiviv3.cloudfront.net/thumbnails/thumbnail-39.jpg",
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
    return thumbnail


def generateBadge():
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
        "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-28.png",
        "https://d3e0hlhsoiviv3.cloudfront.net/badges/badge-29.png"
    ]
    badge = random.choice(badge_list)
    return badge


def generateHeadlineType():
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
    return headline_type


def generateCampaignType():
    #campaigns = ['casino', 'general', 'casino', 'sweepstakes']
    campaigns = ['general', 'general']
    campaign = random.choice(campaigns)
    return campaign


def generateHeadline():
    headline_list = [
        "Can I tell you a secret? 👀",
        "What's your dream car? 🏎",
        "Lmaooo, have you seen r/tifu today? 😂",
        "You have a wonderful name. 😜",
        "I found you through Michael 👨",
        "Tutor me pls 🙏",
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
        "Where are we going tonite? 💃",
        "You thought I was AMY? 🖕",
        "Hey sexy, can you come over? 👅",
        "My ex-bf just humiliated me. 😥",
        "Look, I just want an orgasm. 💦",
        "Terrific, free for drinks later? 🍻",
        "Think you can dazzle me? 😎",
        "I was an erotic dancer, you flirt! 💃",
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
        "Did you talk to her?",
        "Been thinking about you... and it hasn't all been PG.",
        "Black panties or red panties...? I'll model the winner for you tonight.",
        "Blue is definitely your color ;)",
        "Can I have you for breakfast in bed today?",
        "Come over, I have all your favorites. Pizza, beer, and of course, ME.",
        "Good morning handsome. Have a great day!",
        "Hey cutie. Haven't talked to you in awhile. Thought I'd say hello!",
        "I always wake up smiling... I think it's your fault.",
        "I smile whenever I get a message from you <3",
        "I'm in my bed, you're in your bed... One of us is in the wrong place.",
        "I'm trying on these new bras, but I need a second opinion. Care to share your thoughts?",
        "Just got out of the shower. Want to come help me dry off?",
        "Let's hang out tonight. I promise you won't regret it ;)",
        "My phone is in my hands, but I would rather be holding you.",
        "Sweet dreams... with me in them ;)",
        "Thank you for reminding me what butterflies feel like.",
        "Ugh, I have a problem. I can't stop thinking about you.",
        "You looked good in that new shirt."
    ]
    headline = random.choice(headline_list)
    return headline


def generateMessage(number_messages, headline_type, name):
    message = "({}) {} messages from {}".format(
        number_messages, headline_type, name)
    return message
