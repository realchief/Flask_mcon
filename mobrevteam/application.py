# usr/env/bin
# -*- coding:utf8 -*-
"""
MobRevTeam Dashboard
Application Code for handling internal reporting dashboard and API endpoints for Push Engine Backend
"""

import ast
import copy
import datetime
import json
import logging
import os
import re
import sys
from argparse import ArgumentParser
from collections import OrderedDict, namedtuple
from contextlib import closing
from httplib import HTTPConnection  # py2
from io import BytesIO
from json import dumps as json_encode

import arrow
import boto3
import requests
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from flask import (Flask, current_app, jsonify, make_response, redirect,
                   render_template, request)
from flask_admin import Admin
from flask_admin.contrib import sqla
from flask_cors import CORS, cross_origin
from flask_mail import Mail
from flask_security import (RoleMixin, Security, SQLAlchemyUserDatastore,
                            UserMixin, current_user, login_required, utils)
from flask_sqlalchemy import SQLAlchemy, inspect
from googletrans import Translator
from werkzeug.utils import secure_filename
from wtforms.fields import PasswordField

from voluum_requester import VoluumRequester

sys.path.insert(0, '../aux_tools')

ResponseStatus = namedtuple("HTTPStatus",
                            ["code", "message"]

ResponseData = namedtuple("ResponseData",
                          ["status", "content_type", "data_stream"])

# Mapping the output format used in the client to the content type for the
# response
AUDIO_FORMATS = {"ogg_vorbis": "audio/ogg",
                 "mp3": "audio/mpeg",
                 "pcm": "audio/wave; codecs=1"}
CHUNK_SIZE = 1024
HTTP_STATUS = {"OK": ResponseStatus(code=200, message="OK"),
               "BAD_REQUEST": ResponseStatus(code=400, message="Bad request"),
               "NOT_FOUND": ResponseStatus(code=404, message="Not found"),
               "INTERNAL_SERVER_ERROR": ResponseStatus(code=500, message="Internal server error")}

if sys.version_info.major < 3:
    reload(sys)
    sys.setdefaultencoding('utf8')

HTTPConnection.debuglevel = 2

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
LOG = logging.getLogger("requests.packages.urllib3")
LOG.setLevel(logging.DEBUG)
LOG.propagate = True
# username = 'postgres'
# password = 'postgres'
# host = 'localhost'
# db = 'pushengine'
# onesignal_users_table = 'onesignal_users'
voluum_access_key = os.environ["VOLUUM_ACCESS_KEY"]
voluum_access_key_id = os.environ["VOLUUM_ACCESS_KEY_ID"]
zeropark_access_key = os.environ["ZEROPARK_ACCESS_KEY"]
# offer_details_table = 'offer_details'
# Initialize Flask and set some config values
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['DEBUG'] = True
# Replace this with your own secret key
app.config['SECRET_KEY'] = 'secretkeyyekterces'
# The database must exist (although it's fine if it's empty) before you attempt to access any page of the app
# in your browser.
# I used a PostgreSQL database, but you could use another type of database, including an in-memory SQLite database.
# You'll need to connect as a user with sufficient privileges to create tables and read and write to them.
# Replace this with your own database connection string.
# xxxxx
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://root:VK%Gu?kNdlS{@blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com/pushengine'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{0}:{1}@{2}/{3}'.format(os.environ["PUSH_DB_USER"],os.environ["PUSH_DB_PASSWD"],os.environ["PUSH_DB_HOST"],os.environ["PUSH_DB"])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Set config values for Flask-Security.
# We're using PBKDF2 with salt.
app.config['SECURITY_PASSWORD_HASH'] = 'pbkdf2_sha512'
# Replace this with your own salt.
app.config['SECURITY_PASSWORD_SALT'] = 'saltysalt'
app.config['SECURITY_EMAIL_SUBJECT_REGISTER'] = 'Welcome to MobRevMedia!'
app.config[
    'SECURITY_EMAIL_SUBJECT_CONFIRM'] = 'Please confirm your email for MobRevMedia!'
app.config['SECURITY_POST_LOGIN_VIEW'] = '/scheduled-message'
app.config['SECURITY_POST_REGISTER_VIEW'] = '/sheduled-message'
app.config['SECURITY_POST_LOGOUT_VIEW'] = '/login'
app.config['SECURITY_CONFIRMABLE'] = False
app.config['SECURITY_CHANGEABLE'] = True
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_TRACKABLE'] = True

#session = Session(profile_name="adminuser")
#polly = session.client("polly")

# Flask-Security optionally sends email notification to users upon registration, password reset, etc.
# It uses Flask-Mail behind the scenes.
# Set mail-related config values.
# Replace this with your own "from" address
app.config['SECURITY_EMAIL_SENDER'] = 'admin@mobrevteam.com'
# Replace the next five lines with your own SMTP server settings
app.config['MAIL_SERVER'] = 'email-smtp.us-west-2.amazonaws.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'AKIAIWXI5VQKK4DJSU4Q'
app.config['MAIL_PASSWORD'] = 'AtM8AJIQbdEK5Nn3ZygBp97X2Gje03AVI8wnVbyvhKjG'

# Initialize Flask-Mail and SQLAlchemy
mail = Mail(app)
db = SQLAlchemy(app)

# Create a table to support a many-to-many relationship between Users and Roles
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


# Role class
class Role(db.Model, RoleMixin):
    """
    Class representation of roles
    """
    # Our Role has three fields, ID, name and description
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    # __str__ is required by Flask-Admin, so we can have human-readable values for the Role when editing a User.
    # If we were using Python 2.7, this would be __unicode__ instead.
    def __str__(self):
        return self.name

    # __hash__ is required to avoid the exception TypeError: unhashable type:
    # 'Role' when saving a User
    def __hash__(self):
        return hash(self.name)


# User class
class User(db.Model, UserMixin):
    """
    Class representation of user role
    Our User has six fields: ID, email, password, active, confirmed_at and roles. The roles field represents a
    # many-to-many relationship using the roles_users table. Each user may
    have no role, one role, or multiple roles.
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic')
    )


class ScheduledMessage(db.Model):
    """
    Representation of ScheduledMessage model which will be used to build push notifications
    """
    id = db.Column(db.Integer, primary_key=True)
    headline = db.Column(db.String(255), unique=False, nullable=True)
    message = db.Column(db.String(255), unique=False, nullable=True)
    thumbnail = db.Column(db.String(255), unique=False, nullable=True)
    category = db.Column(db.String(255), unique=False, nullable=False)
    recurring = db.Column(db.String(255), unique=False, nullable=False)
    message_time = db.Column(db.Time(), unique=False, nullable=False)

    def __repr__(self):
        return '{"id":"%s", "headline":"%s", "message":"%s", "thumbnail":"%s", "category":"%s", "recurring":"%s", "message_time":"%s"}' % (
            self.id, self.headline, self.message, self.thumbnail, self.category, self.recurring, self.message_time)


class Killswitch(db.Model):
    """
    Representation of killswitch for defining message sending status
    """
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Boolean, unique=True, nullable=False)

    def __repr__(self):
        return '<Status %r>' % self.status


class EmailOptin(db.Model):
    """
    Representation of email opt-in user
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_time = db.Column(db.DateTime())

    def __repr__(self):
        return '<Email %r>' % self.email


class IpAddress(db.Model):
    """
    Representation of IPv4 Address records stored for filtering by IP ranges of /24 and /16
    """
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(80), unique=True, nullable=False)
    ip_type = db.Column(db.String(120), unique=False, nullable=False)
    country_code = db.Column(db.String(120), unique=False, nullable=False)
    connection_type = db.Column(db.String(120), unique=False, nullable=False)
    mobile_carrier = db.Column(db.String(120), unique=False, nullable=False)
    browser = db.Column(db.String(120), unique=False, nullable=False)
    created_time = db.Column(db.DateTime())

    def __repr__(self):
        return '<IP %r>' % self.ip


class CampaignRule(db.Model):
    """
    Representation of campaign rule records used for auto-optimizing logic
    """
    __tablename__ = 'campaign_rule'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(
        db.String(80),
        db.ForeignKey('frontend_campaigns.id'),
        unique=False,
        nullable=False)
    traffic_source = db.Column(db.String(100))
    rule_constraints = db.relationship(
        "RuleConstraint",
        back_populates="campaign_rule",
        cascade="all,delete")
    campaign = {}
    period = db.Column(db.Integer)
    action = db.Column(db.String(10))
    status = db.Column(db.Boolean)

    # def __repr__(self):
    #     return '<Rule %r>' % self.campaign_id

    def __repr__(self):
        return '{"id":%s, "status": %s, "period": %s, "action": "%s", "constraints": %s, "campaign_id": "%s", "campaign": %s}' % (
            self.id, format_boolean(self.status), self.period, self.action, sort_models_by_id(self.rule_constraints), self.campaign_id, self.campaign)


def sort_models_by_id(models):
    return sorted(models, key=lambda k: k.id)


class RuleConstraint(db.Model):
    __tablename__ = 'rule_constraint'
    id = db.Column(db.Integer, primary_key=True)
    campaign_rule_id = db.Column(db.Integer, db.ForeignKey('campaign_rule.id'))
    campaign_rule = db.relationship(
        "CampaignRule", back_populates="rule_constraints")
    metric = db.Column(db.String(13), unique=False, nullable=False)
    value = db.Column(db.Integer, unique=False, nullable=False)
    operator = db.Column(db.String(5), unique=False, nullable=False)
    conjunction = db.Column(db.String(10), unique=False)

    def __repr__(self):
        return '{"id":"%s", "metric": "%s", "value": %s, "operator": "%s", "conjunction": %s, "campaign_rule_id": %s}' % (self.id, self.metric, format_decimals(
            self.value), self.operator, ('"' + (self.conjunction) + '"' if self.conjunction is not None else "null"), self.campaign_rule_id)


def format_decimals(value):
    decimal_count = str(value)[::-1].find('.')
    if 0 < decimal_count <= 2:
        return "%.2f" % value
    elif decimal_count > 2:
        return "%.4f" % value
    else:
        return value


class PushReports(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_date = db.Column(db.Date())
    traffic_source = db.Column(db.String(255), unique=False, nullable=False)
    country = db.Column(db.String(255), unique=False, nullable=False)
    cost = db.Column(db.String(255), unique=False, nullable=True)
    subscribers = db.Column(db.String(255), unique=False, nullable=True)
    ecpa = db.Column(db.String(255), unique=False, nullable=True)
    eps = db.Column(db.String(255), unique=False, nullable=True)
    rps = db.Column(db.String(255), unique=False, nullable=True)
    profit = db.Column(db.String(255), unique=False, nullable=True)
    revenue = db.Column(db.String(255), unique=False, nullable=True)
    roi = db.Column(db.String(255), unique=False, nullable=True)


class GeosFrontendCampaigns(db.Model):
    __tablename__ = 'geos_frontend_campaigns'
    __table_args__ = (
        db.PrimaryKeyConstraint(
            'geo_id',
            'frontend_campaign_id'),
    )
    geo_id = db.Column(db.Integer, db.ForeignKey('geos.id'))
    frontend_campaign_id = db.Column(
        db.Integer, db.ForeignKey('frontend_campaigns.id'))
    geo = db.relationship("Geos", back_populates="frontend_campaigns")
    frontend_campaign = db.relationship(
        "FrontendCampaign", back_populates="geos")


class Geos(db.Model):
    __tablename__ = 'geos'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    alpha_2 = db.Column(db.String(2), unique=True, nullable=False)
    frontend_campaigns = db.relationship(
        "GeosFrontendCampaigns",
        back_populates="geo",
        cascade="all,delete")
    checked = False

    def __repr__(self):
        return '{"id":%s, "name":"%s", "checked": %s}' % (
            self.id, self.name, format_boolean(self.checked))


class MessageCategories(db.Model):
    __tablename__ = 'message_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)


class Frequencies(db.Model):
    __tablename__ = 'frequencies'
    id = db.Column(db.Integer, primary_key=True)
    interval = db.Column(db.String(255), unique=True, nullable=False)
    selected = db.Column(db.Boolean)


class GeosScheduledMessage(db.Model):
    """join table GeosScheduledMessage, creates a many to many relation between the Geos and ScheduledMessage tables"""
    __tablename__ = 'geos_scheduled_message'
    __table_args__ = (
        db.PrimaryKeyConstraint(
            'geo_id',
            'scheduled_message_id'),
    )
    geo_id = db.Column(db.Integer(), db.ForeignKey('geos.id'))
    scheduled_message_id = db.Column(
        db.Integer(), db.ForeignKey('scheduled_message.id'))


class VirusCheck(db.Model):
    __tablename__ = 'virus_checks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    status = db.Column(db.String(255))
    url = db.Column(db.String(255), unique=True, nullable=False)
    monitor_active = db.Column(db.Boolean())

    def __repr__(self):
        return '{"id":%s, "name": "%s", "status": "%s", "url": "%s", "monitor_active": %s}' % (self.id, self.name,
                                                                                               self.status, self.url, format_boolean(self.monitor_active))


class FrontendCampaign(db.Model):
    __tablename__ = 'frontend_campaigns'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    all_day_notification = db.Column(db.Boolean())
    start_at = db.Column(db.Time())
    end_at = db.Column(db.Time())
    time_zone = db.Column(db.Integer)
    frequency = db.Column(db.Integer)
    status = db.Column(db.Boolean())
    stacking = db.Column(db.String(255))
    geos = db.relationship(
        "GeosFrontendCampaigns",
        back_populates="frontend_campaign",
        cascade="all,delete")
    all_geos = []
    # campaign_rules = db.relationship("CampaignRule", back_populates="campaign", cascade="all,delete")
    # campaign_rules = []

    def set_all_geos(self, complete_geos):
        self.all_geos = []
        non_camp_geos = [
            geo for geo in complete_geos if geo not in [
                camp_geo.geo for camp_geo in self.geos]]
        for original_geo in self.geos:
            copy_geo = copy.copy(original_geo.geo)
            copy_geo.checked = True
            self.all_geos.append(copy_geo)

        self.all_geos.extend(non_camp_geos)

    def __repr__(self):
        return '{"id":%s, "name":"%s", "all_day_notification": %s, "from_time": %s, "to_time": %s, "time_zone": "%s", "locations": %s, "one_message_per_mins": %s, "status": %s, "stacking": "%s"}' % (
            self.id, self.name, format_boolean(self.all_day_notification), format_time(self.start_at), format_time(self.end_at), format_time_zone(self.time_zone), self.all_geos, self.frequency, format_boolean(self.status), self.stacking)


class FrontendCategory(db.Model):
    # @classmethod
    # def fromdict(cls, d):
    #     allowed = ('key1', 'key2')
    #     df = {k : v for k, v in d.iteritems() if k in allowed}
    #     return cls(**df)

    __tablename__ = 'frontend_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    url = db.Column(db.String(255))
    groups = db.relationship(
        "FrontendGroup",
        back_populates="category",
        cascade="all,delete")

    def __repr__(self):
        return '{"id":%s, "name":"%s", "url": "%s"}' % (
            self.id, self.name, self.url)


class FrontendGroup(db.Model):
    __tablename__ = 'frontend_groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    frontend_category_id = db.Column(
        db.Integer, db.ForeignKey('frontend_categories.id'))
    status = db.Column(db.Boolean())
    messages = db.relationship(
        "FrontendMessage",
        back_populates="frontend_group",
        cascade="all,delete")
    category = db.relationship("FrontendCategory", backref="frontend_groups")

    def __repr__(self):
        return '{"id":%s, "name":"%s", "status": %s, "cat": %s }' % (
            self.id, self.name, format_boolean(self.status), self.category)


class FrontendGroupsFrontendCampaigns(db.Model):
    """docstring for FrontendGroupsFrontendCampaigns"""
    __tablename__ = 'frontend_groups_frontend_campaigns'
    __table_args__ = (
        db.PrimaryKeyConstraint(
            'frontend_group_id',
            'frontend_campaign_id'),
    )
    frontend_group_id = db.Column(
        db.Integer(), db.ForeignKey('frontend_groups.id'))
    frontend_campaign_id = db.Column(
        db.Integer(), db.ForeignKey('frontend_campaigns.id'))
    status = db.Column(db.Boolean())
    frequency = db.Column(db.Integer)
    in_order = db.Column(db.Integer)
    sent = db.Column(db.Integer)
    frontend_group = dict()

    def __repr__(self):
        return '{"status": %s, "group": %s, "group_id": %s, "campaign_id": %s, "frequency": %s, "order": %s, "sent": %s}' % (format_boolean(
            self.status), self.frontend_group, self.frontend_group_id, self.frontend_campaign_id, self.frequency, self.in_order, self.sent)


class FrontendMessage(db.Model):
    __tablename__ = 'frontend_messages'
    id = db.Column(db.Integer, primary_key=True)
    headline = db.Column(db.String(255))
    content = db.Column(db.String(255))
    status = db.Column(db.Boolean())
    frontend_group_id = db.Column(
        db.Integer, db.ForeignKey('frontend_groups.id'))
    frontend_icon_id = db.Column(
        db.Integer, db.ForeignKey('frontend_icons.id'))
    frontend_image_id = db.Column(
        db.Integer, db.ForeignKey('frontend_images.id'))
    frontend_badge_id = db.Column(
        db.Integer, db.ForeignKey('frontend_badges.id'))
    frontend_icon = db.relationship(
        "FrontendIcon", backref="frontend_messages")
    frontend_badge = db.relationship(
        "FrontendBadge", backref="frontend_messages")
    frontend_image = db.relationship(
        "FrontendImage", backref="frontend_messages")
    frontend_group = db.relationship(
        "FrontendGroup", backref="frontend_messages")
    translations = db.relationship(
        "Translation",
        back_populates="frontend_message",
        cascade="all,delete")
    frontend_icon_tag_id = db.Column(
        db.Integer, db.ForeignKey('frontend_tags.id'))
    frontend_badge_tag_id = db.Column(
        db.Integer, db.ForeignKey('frontend_tags.id'))
    frontend_image_tag_id = db.Column(
        db.Integer, db.ForeignKey('frontend_tags.id'))
    frontend_icon_tag = db.relationship(
        "FrontendTag", foreign_keys=[frontend_icon_tag_id])
    frontend_badge_tag = db.relationship(
        "FrontendTag", foreign_keys=[frontend_badge_tag_id])
    frontend_image_tag = db.relationship(
        "FrontendTag", foreign_keys=[frontend_image_tag_id])

    def __repr__(self):
        return '{"id":%s, "headline":"%s", "content": "%s", "status": %s, "icon": %s, "badge": %s, "image": %s, "trans": %s, "languages": "%s"}' % (self.id, self.headline, self.content, format_boolean(self.status), format_media_repr(self.frontend_icon, self.frontend_icon_tag), format_media_repr(
            self.frontend_badge, self.frontend_badge_tag), format_media_repr(self.frontend_image, self.frontend_image_tag), format_translations(self.translations), str([str(translation.language) for translation in self.translations])[1:-1])


def format_media_repr(media, tag):
    if media is not None:
        return media
    elif tag is not None:
        return tag
    else:
        return "null"


class Translation(db.Model):
    __tablename__ = 'translations'
    id = db.Column(db.Integer, primary_key=True)
    headline = db.Column(db.String(255))
    content = db.Column(db.String(255))
    status = db.Column(db.Boolean())
    language = db.Column(db.String(255))
    frontend_message_id = db.Column(
        db.Integer, db.ForeignKey('frontend_messages.id'))
    frontend_message = db.relationship(
        "FrontendMessage", back_populates="translations")

    def __repr__(self):
        return '{"headline":"%s", "content": "%s", "status": %s, "lan": "%s"}' % (
            self.headline, self.content, format_boolean(self.status), self.language)


def format_translations(translations):
    output = OrderedDict()
    non_english_dict = OrderedDict()
    for translation in translations:
        if str(translation.language) == "English":
            output[str(translation.language)] = json.loads(
                translation.__repr__())
        else:
            non_english_dict[str(translation.language)] = json.loads(
                translation.__repr__())
    output.update(non_english_dict)
    return json.dumps(output)


class Thumbnail(db.Model):
    __tablename__ = 'thumbnails'
    id = db.Column(db.Integer, primary_key=True)
    creation_date = db.Column(db.DateTime())
    thumbnail = db.Column(db.Text)
    num_time_sent = db.Column(db.Numeric(precision=9, scale=1))
    num_user_sent = db.Column(db.Numeric(precision=9, scale=1))
    num_user_open = db.Column(db.Numeric(precision=9, scale=1))
    num_user_lost = db.Column(db.Numeric(precision=9, scale=1))
    num_user_converted = db.Column(db.Numeric(precision=9, scale=2))
    revenue_generated = db.Column(db.Numeric(precision=9, scale=1))
    average_churn_rate = db.Column(db.Numeric(precision=9, scale=3))
    average_open_rate = db.Column(db.Numeric(precision=9, scale=3))
    average_conversion_rate = db.Column(db.Numeric(precision=9, scale=3))
    category = db.Column(db.String(255))

    def __repr__(self):
        return '"%s"' % (self.thumbnail)


class Badge(db.Model):
    __tablename__ = 'badges'
    id = db.Column(db.Integer, primary_key=True)
    creation_date = db.Column(db.DateTime())
    badge = db.Column(db.Text)
    num_time_sent = db.Column(db.Numeric(precision=9, scale=1))
    num_user_sent = db.Column(db.Numeric(precision=9, scale=1))
    num_user_open = db.Column(db.Numeric(precision=9, scale=1))
    num_user_lost = db.Column(db.Numeric(precision=9, scale=1))
    num_user_converted = db.Column(db.Numeric(precision=9, scale=2))
    revenue_generated = db.Column(db.Numeric(precision=9, scale=1))
    average_churn_rate = db.Column(db.Numeric(precision=9, scale=3))
    average_open_rate = db.Column(db.Numeric(precision=9, scale=3))
    average_conversion_rate = db.Column(db.Numeric(precision=9, scale=3))
    category = db.Column(db.String(255))

    def __repr__(self):
        return '"%s"' % (self.badge)


class Image(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    creation_date = db.Column(db.DateTime())
    image = db.Column(db.Text)
    num_time_sent = db.Column(db.Numeric(precision=9, scale=1))
    num_user_sent = db.Column(db.Numeric(precision=9, scale=1))
    num_user_open = db.Column(db.Numeric(precision=9, scale=1))
    num_user_lost = db.Column(db.Numeric(precision=9, scale=1))
    num_user_converted = db.Column(db.Numeric(precision=9, scale=2))
    revenue_generated = db.Column(db.Numeric(precision=9, scale=1))
    average_churn_rate = db.Column(db.Numeric(precision=9, scale=3))
    average_open_rate = db.Column(db.Numeric(precision=9, scale=3))
    average_conversion_rate = db.Column(db.Numeric(precision=9, scale=3))
    category = db.Column(db.String(255))

    def __repr__(self):
        return '"%s"' % (self.image)




class FrontendTag(db.Model):
    __tablename__ = 'frontend_tags'
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(255), unique=True, nullable=False)
    checked = db.Column(db.Boolean)
    frontend_icons = db.relationship(
        "FrontendTagsFrontendIcons",
        back_populates="tag",
        cascade="all,delete")
    frontend_badges = db.relationship(
        "FrontendTagsFrontendBadges",
        back_populates="tag",
        cascade="all,delete")
    frontend_images = db.relationship(
        "FrontendTagsFrontendImages",
        back_populates="tag",
        cascade="all,delete")

    def __repr__(self):
        return '{"id":%s, "name":"%s", "checked": %s}' % (
            self.id, self.tag, format_boolean(self.checked))


class FrontendTagsFrontendIcons(db.Model):
    __tablename__ = 'frontend_tags_frontend_icons'
    __table_args__ = (
        db.PrimaryKeyConstraint(
            'frontend_tag_id',
            'frontend_icon_id'),
    )
    frontend_tag_id = db.Column(db.Integer, db.ForeignKey('frontend_tags.id'))
    frontend_icon_id = db.Column(
        db.Integer, db.ForeignKey('frontend_icons.id'))
    tag = db.relationship("FrontendTag", back_populates="frontend_icons")
    frontend_icon = db.relationship(
        "FrontendIcon", back_populates="frontend_tags")

    def __repr__(self):
        return '%s' % (self.tag)


class FrontendIcon(db.Model):
    __tablename__ = 'frontend_icons'
    id = db.Column(db.Integer, primary_key=True)
    frontend_icon_url = db.Column(db.String(255), unique=True, nullable=False)
    frontend_tags = db.relationship(
        "FrontendTagsFrontendIcons",
        back_populates="frontend_icon",
        cascade="all,delete")
    frontend_icon_filename = db.Column(
        db.String(255), unique=True, nullable=False)
    selected = db.Column(db.Boolean)

    def __repr__(self):
        return '{"id":%s, "media_type": "Icon", "name": "%s","url":"%s", "tags": %s, "selected": %s}' % (
            self.id, self.frontend_icon_filename, self.frontend_icon_url, [tag.tag for tag in self.frontend_tags], format_boolean(self.selected))


class FrontendTagsFrontendBadges(db.Model):
    __tablename__ = 'frontend_tags_frontend_badges'
    __table_args__ = (
        db.PrimaryKeyConstraint(
            'frontend_tag_id',
            'frontend_badge_id'),
    )
    frontend_tag_id = db.Column(db.Integer, db.ForeignKey('frontend_tags.id'))
    frontend_badge_id = db.Column(
        db.Integer, db.ForeignKey('frontend_badges.id'))
    tag = db.relationship("FrontendTag", back_populates="frontend_badges")
    frontend_badge = db.relationship(
        "FrontendBadge", back_populates="frontend_tags")

    def __repr__(self):
        return '%s' % (self.tag)


class FrontendBadge(db.Model):
    __tablename__ = 'frontend_badges'
    id = db.Column(db.Integer, primary_key=True)
    frontend_badge_url = db.Column(db.String(255), unique=True, nullable=False)
    frontend_tags = db.relationship(
        "FrontendTagsFrontendBadges",
        back_populates="frontend_badge",
        cascade="all,delete")
    frontend_badge_filename = db.Column(
        db.String(255), unique=True, nullable=False)
    selected = db.Column(db.Boolean)

    def __repr__(self):
        return '{"id":%s, "media_type": "Badge", "name": "%s","url":"%s", "tags": %s, "selected": %s}' % (
            self.id, self.frontend_badge_filename, self.frontend_badge_url, [tag.tag for tag in self.frontend_tags], format_boolean(self.selected))


class FrontendTagsFrontendImages(db.Model):
    __tablename__ = 'frontend_tags_frontend_images'
    __table_args__ = (
        db.PrimaryKeyConstraint(
            'frontend_tag_id',
            'frontend_image_id'),
    )
    frontend_tag_id = db.Column(db.Integer, db.ForeignKey('frontend_tags.id'))
    frontend_image_id = db.Column(
        db.Integer, db.ForeignKey('frontend_images.id'))
    tag = db.relationship("FrontendTag", back_populates="frontend_images")
    frontend_image = db.relationship(
        "FrontendImage", back_populates="frontend_tags")

    def __repr__(self):
        return '%s' % (self.tag)


class FrontendImage(db.Model):
    __tablename__ = 'frontend_images'
    id = db.Column(db.Integer, primary_key=True)
    frontend_image_url = db.Column(db.String(255), unique=True, nullable=False)
    frontend_tags = db.relationship(
        "FrontendTagsFrontendImages",
        back_populates="frontend_image",
        cascade="all,delete")
    frontend_image_filename = db.Column(
        db.String(255), unique=True, nullable=False)
    selected = db.Column(db.Boolean)

    def __repr__(self):
        return '{"id":%s, "media_type": "Image", "name": "%s","url":"%s", "tags": %s, "selected": %s}' % (
            self.id, self.frontend_image_filename, self.frontend_image_url, [tag.tag for tag in self.frontend_tags], format_boolean(self.selected))


def format_tags(tags):
    return json.dumps([tag.tag.tag for tag in tags])


def format_tags_associations(tags_associations):
    list_of_ids = []
    output_tags_associations = []
    for i in tags_associations:
        if i.tag.id not in list_of_ids:
            list_of_ids.append(i.tag.id)
            output_tags_associations.append(i)
    return sorted(output_tags_associations, key=lambda k: k.tag.id)


def format_boolean(boolean):
    if isinstance(boolean, tuple):
        boolean = boolean[0]
    return str(boolean).lower()


def format_time(time):
    if isinstance(time, tuple):
        time = time[0]
    return json.dumps({"hh": time.strftime(
        "%I"), "mins": time.strftime("%M"), "m": time.strftime("%p")})


def format_time_zone(time_zone):
    if isinstance(time_zone, tuple):
        time_zone = time_zone[0]
    output = "UTC "
    if time_zone < 0:
        output += "-"
    output += ("0" + str(abs(time_zone))
               ) if abs(time_zone) < 10 else (str(abs(time_zone)))
    return output


def unformat_boolean(boolean):

    return True if boolean == 'true' else False


def unformat_time(time):
    am_pm = str(time["m"])
    hh = int(time["hh"])
    mins = int(time["mins"])
    if am_pm == "PM":
        if hh == 12:
            return datetime.time(0, mins)
        else:
            return datetime.time(hh + 12, mins)

    else:
        return datetime.time(hh, mins)


def unformat_time_zone(time_zone):
    return int(time_zone[4:])


def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end + 1]
    except ValueError as error:
        print(error)
        return ""


class CampaignAlert(db.Model):
    __tablename__ = 'campaign_alert'
    id = db.Column(db.Integer, primary_key=True)
    campaignid = db.Column(db.String(255), nullable=False)
    campaignurl = db.Column(db.String(255), nullable=False)
    campaignname = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    monitor = db.Column(db.Boolean)
    metric = db.Column(db.String(20), nullable=False)
    logic = db.Column(db.String(20), nullable=False)
    value = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '{"id":%s, "campaignId": "%s", "campaignUrl": "%s","campaignName":"%s", "status": "%s", "monitor": %s, "metric": "%s","logic": "%s","value": %s}' % (
            self.id, self.campaignid, self.campaignurl, self.campaignname, self.status, format_boolean(self.monitor), self.metric, self.logic, self.value)

# Initialize the SQLAlchemy data store and Flask-Security.
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


# Executes before the first request is processed.
@app.before_first_request
def before_first_request():
    """
    Perform necessary setup steps each time flask is restarted
    """
    # Create any database tables that don't exist yet.
    db.create_all()

    # Create the Roles "admin" and "end-user" -- unless they already exist
    user_datastore.find_or_create_role(
        name='admin', description='Administrator')
    user_datastore.find_or_create_role(name='end-user', description='End user')

    # Create two Users for testing purposes -- unless they already exists.
    # In each case, use Flask-Security utility function to encrypt the
    # password.
    encrypted_password = utils.encrypt_password('#TIrKro0q5R9VC%o$3j6')
    if not user_datastore.get_user('someone@example.com'):
        user_datastore.create_user(
            email='someone@example.com',
            password=encrypted_password)
    if not user_datastore.get_user('andrew@mobrevmedia.com'):
        user_datastore.create_user(
            email='andrew@mobrevmedia.com',
            password=encrypted_password)

    # Commit any database changes; the User and Roles must exist before we can
    # add a Role to the User
    db.session.commit()

    # Give one User has the "end-user" role, while the other has the "admin" role. (This will have no effect if the
    # Users already have these Roles.) Again, commit any database changes.
    user_datastore.add_role_to_user('someone@example.com', 'end-user')
    user_datastore.add_role_to_user('andrew@mobrevmedia.com', 'admin')
    db.session.commit()


# Displays the home page.
@app.route('/')
@app.route('/index')
@login_required
def index():
    """
    Users must be authenticated to view the home page, but they don't have to have any particular role.
    Flask-Security will display a login form if the user isn't already
    authenticated.
    """
    return render_template('index.html')


@app.route("/auto-optimizer", methods=["GET", "POST"])
def auto_optimizer():
    """
    Interface for auto-optimizer tool to detect placements which should be paused based on an x and y metric defined by
    the user
    """
    # Generate and validate token for accessing voluum
    token_request = requests.post(
        'https://api.voluum.com/auth/access/session',
        json={
            "accessId": "ace793ba-7917-4013-86bd-7f888aa0caba",
            "accessKey": "7PMpMgC3kTU4cb3c9cAd3bd48mg-tkrYFgW7"})
    token = str(token_request.json()['token'])
    headers = {'content-type': 'application/json', 'cwauth-token': token}
    token_validate = requests.get(
        'https://api.voluum.com/auth/session',
        headers=headers)
    report_request = requests.get(
        'https://api.voluum.com/campaign',
        headers=headers)
    campaign_names = {}
    # Pull all campaigns from ZeroPark with active tag and use them to display
    # names for each campaign
    for campaign in report_request.json()['campaigns']:
        if '6530e6cb-9550-402c-be06-78c1bb388346' in campaign[
                'trafficSource']['id'] and 'active' in campaign['tags']:
            campaign_names[campaign['name']] = campaign['id']
    # If a form is being posted, add the new rule to the db and commit
    if request.form:
        rule = CampaignRule(campaign_id=request.form.get("campaign_id"),
                            y_metric=request.form.get("y_metric"),
                            y_metric_amount=request.form.get(
                                "y_metric_amount"),
                            y_metric_gtlt=request.form.get("y_metric_gtlt"),
                            x_metric=request.form.get("x_metric"),
                            x_metric_amount=request.form.get(
                                "x_metric_amount"),
                            x_metric_gtlt=request.form.get("x_metric_gtlt"))
        db.session.add(rule)
        db.session.commit()
    # This retrieves all campaign rules
    campaign_rules = CampaignRule.query.all()
    return render_template(
        'auto_optimizer.html',
        campaign_rules=campaign_rules,
        campaign_names=campaign_names)


@app.route("/update-optimizer-rule", methods=["POST"])
def update_optimizer_rule():
    """
    Update an existing auto optimizer rule definition
    """
    if request.form:
        LOG.info(request.form)
        id = request.form['id']
        optimizer_rule = CampaignRule.query.filter_by(id=id).first()
        campaign_id = request.form['campaign_id']
        x_metric = request.form['x_metric']
        x_metric_gtlt = request.form['x_metric_gtlt']
        x_metric_amount = request.form['x_metric_amount']
        y_metric = request.form['y_metric']
        y_metric_gtlt = request.form['y_metric_gtlt']
        y_metric_amount = request.form['y_metric_amount']
        if campaign_id is not None:
            optimizer_rule.campaign_id = campaign_id
        if y_metric is not None:
            optimizer_rule.y_metric = y_metric
        if y_metric_amount is not None:
            optimizer_rule.y_metric_amount = y_metric_amount
        if y_metric_gtlt is not None:
            optimizer_rule.y_metric_gtlt = y_metric_gtlt
        if x_metric is not None:
            optimizer_rule.x_metric = x_metric
        if x_metric_amount is not None:
            optimizer_rule.x_metric_amount = x_metric_amount
        if x_metric_gtlt is not None:
            optimizer_rule.x_metric_gtlt = x_metric_gtlt
    db.session.commit()
    return '200'


@app.route("/delete-optimizer-rule", methods=["POST"])
def delete_optimizer_rule():
    """
    Delete an existing auto optimizer rule definition
    """
    if request.form:
        id = request.form['id']
        optimizer_rule = CampaignRule.query.filter_by(id=id).first()
        db.session.delete(optimizer_rule)
    db.session.commit()
    return id


@app.route("/placement-analysis", methods=["GET", "POST"])
def placement_analysis():
    """
    Chrome Browser traffic is one of the most valuable browser types for our purposes
    Manual reporting and analysis of placements for pausing to find pockets of high percentage chrome traffic
    """
    if request.form:
        token_request = requests.post(
            'https://api.voluum.com/auth/access/session',
            json={
                "accessId": "ace793ba-7917-4013-86bd-7f888aa0caba",
                "accessKey": "7PMpMgC3kTU4cb3c9cAd3bd48mg-tkrYFgW7"})
        token = str(token_request.json()['token'])
        headers = {'content-type': 'application/json', 'cwauth-token': token}
        token_validate = requests.get(
            'https://api.voluum.com/auth/session',
            headers=headers)
        report_from_datetime = request.form[
            'from_date'] + 'T00'  # or '2018-03-18T00'
        report_to_datetime = request.form[
            'to_date'] + 'T00'  # or '2018-03-22T00'
        # or 'e029accf-d45c-4895-8d48-8c75fd58010f'
        campaign_id = request.form['campaign_id']
        report_request = requests.get(
            'https://api.voluum.com/report?include=TRAFFIC&columns=campaign&filter={}&=groupBy=campaign,customVariable1,browser&from={}&to={}&include=ACTIVE&limit=1000&sort=visits&direction=DESC'.format(
                campaign_id,
                report_from_datetime,
                report_to_datetime),
            headers=headers)
        report_rows = report_request.json()['rows']
        percent_chrome = int(request.form['percent_chrome'])  # or 65
        min_visits = int(request.form['min_visits'])
        LOG.info(report_from_datetime)
        LOG.info(report_to_datetime)
        LOG.info(percent_chrome)
        LOG.info(min_visits)
        LOG.info(campaign_id)
        placement_list = {}

        for row in report_rows:
            placement = row['customVariable1']
            browser = row['browser']
            visits = row['visits']
            ecpa = row['ecpa']
            placement_list.setdefault(placement, [])
            placement_list[placement].append((browser, visits, ecpa))

        cut_placements = []
        keep_placements = []
        for placement in placement_list:
            visits = 0
            chrome_visits = 0
            for row in placement_list[placement]:
                visits += row[1]
                if 'Chrome Mobile' in row[0]:
                    chrome_visits += row[1]
            LOG.info(visits)
            LOG.info(chrome_visits)
            if visits < min_visits:
                LOG.info('Insufficient data for cutting placement')
                continue
            amount_chrome = float(chrome_visits) / float(visits) * 100
            if amount_chrome < percent_chrome:
                cut_placements.append(placement)
                LOG.info('Less than 65% Chrome, cutting recommended.')
            else:
                keep_placements.append(placement)
            LOG.info(
                str(float(chrome_visits) / float(visits) * 100) + '% Chrome')
    else:
        cut_placements = []
    return render_template('placement_analysis.html',
                           placements=cut_placements)


@app.route("/placement-pause", methods=["POST"])
def placement_pause():
    """
    Endpoint for pausing placements by providing:
    API Token from Voluum
    ZeroPark Campaign ID
    ZeroPark Target Hash
    """
    # Pause placements
    zp_api_token = 'AAABYk/TSanlykVoTFAznLqnNPiCJnQMM7d67kGhGJr6pIoO8YK6LizPSBh/KKWjyjg4rf5Vb7iDpOxldTIkaQ=='
    zp_headers = {
        'content-type': 'application/json',
        'api-token': zp_api_token}
    zp_campaign_id = 'cf293c30-0006-11e8-b806-0ec5f5cbb90a'
    zp_target_hash = 'whiskey-rei-r91jlH1W'
    token_request = requests.post(
        'https://api.zeropark.com/api/campaign/{}/target/pause'.format(
            zp_campaign_id),
        json={
            "campaignId": zp_campaign_id,
            "hash": zp_target_hash})
    return '200'


@app.route("/kill-switch", methods=["GET", "POST"])
@login_required
def kill_switch():
    """
    Kill switch for preventing push engine from sending in the event of a serious technical issue
    """
    # Check for request.form, set message sending status in db to form value
    killswitch = Killswitch.query.get(1)
    if not killswitch:
        killswitch = Killswitch(status=1)
        db.session.add(killswitch)
        db.session.commit()
    if request.form:
        killswitch.status = int(request.form.get("status"))
        db.session.commit()
    return render_template("kill_switch.html", send_status=killswitch)


@app.route("/kill-switch-status")
def kill_switch_status():
    """
    Endpoint which push engines poll prior to sending any push notification
    """
    killswitch = Killswitch.query.get(1)
    return str(killswitch.status)


@app.route("/push-reporting")
def push_reporting():
    push_reports = PushReports.query.all()
    return render_template(
        'push_reporting.html',
        push_reports=push_reports)


@app.route("/scheduled-message", methods=["GET", "POST"])
@login_required
def scheduled_message():
    """
    Interface for manually scheduling messages to be used by the push engines
    """

    geos_dict = [{"id": geo.id, "name": geo.name, "alpha_2": geo.alpha_2}
                 for geo in db.session.query(Geos).all()]

    message_categories_dict = [{"id": message_category.id, "name": message_category.name}
                               for message_category in db.session.query(MessageCategories).all()]

    frequencies_dict = [{"id": frequency.id, "interval": frequency.interval,
                         "selected": frequency.selected} for frequency in db.session.query(Frequencies).all()]

    if request.form:
        message = ScheduledMessage(
            headline=request.form.get("headline"),
            message=request.form.get("message"),
            thumbnail=request.form.get("thumbnail"),
            category=request.form.get("category"),
            recurring=request.form.get("recurring"),
            message_time=request.form.get("message_time"))
        db.session.add(message)
        db.session.commit()
        geo_ids_list = request.form.getlist("geos")
        last_scheduled_message_id = ScheduledMessage.query.all()[-1].id
        for geo_id in geo_ids_list:
            geos_scheduled_message = GeosScheduledMessage(
                geo_id=geo_id,
                scheduled_message_id=last_scheduled_message_id
            )
            db.session.add(geos_scheduled_message)
            db.session.commit()

    scheduled_messages = ScheduledMessage.query.all()
    return render_template("scheduled_message.html",
                           scheduled_messages=scheduled_messages)


@app.route("/get-scheduled-messages", methods=["GET"])
def get_scheduled_message():
    """
    Fetch all scheduled messages remaining for the day
    """
    current_time = arrow.now('US/Central').time()
    LOG.info(current_time)
    scheduled_messages = ScheduledMessage.query.filter(
        ScheduledMessage.message_time >= current_time).all()
    LOG.info(scheduled_messages)
    return repr(scheduled_messages)


@app.route("/update", methods=["POST"])
def update():
    """
    Endpoint to update a scheduled message
    """
    id = request.form.get("id")
    scheduled_message = ScheduledMessage.query.filter_by(id=id).first()
    headline = request.form.get("headline")
    message = request.form.get("message")
    thumbnail = request.form.get("thumbnail")
    category = request.form.get("category")
    recurring = request.form.get("recurring")
    message_time = request.form.get("message_time")
    if headline is not None:
        scheduled_message.headline = headline
    if message is not None:
        scheduled_message.message = message
    if thumbnail is not None:
        scheduled_message.thumbnail = thumbnail
    if category is not None:
        scheduled_message.category = category
    if recurring is not None:
        scheduled_message.recurring = recurring
    if message_time is not None:
        scheduled_message.message_time = message_time
    db.session.commit()
    return redirect("/scheduled-message")


@app.route("/delete", methods=["POST"])
def delete():
    """
    Endpoint to delete a scheduled message from web dashboard
    """
    message_id = request.form.get("id")
    message = ScheduledMessage.query.filter_by(id=message_id).first()
    db.session.delete(message)
    db.session.commit()
    return message_id


@app.route("/delete-push", methods=["GET", "POST"])
def delete_push():
    """
    Endpoint to delete a scheduled message programmatically from message_scheduler
    """
    message_id = request.args.get("id")
    message = ScheduledMessage.query.filter_by(id=message_id).first()
    db.session.delete(message)
    db.session.commit()
    return '200'


@app.route("/email-optin", methods=["GET", "POST"])
@login_required
def email_optin():
    if request.form:
        email = EmailOptin(name=request.form.get("name"),
                           email=request.form.get("email"),
                           created_time=arrow.utcnow().datetime)
        db.session.add(email)
        db.session.commit()
    email_optins = EmailOptin.query.all()
    return render_template("email_optin.html",
                           email_optins=email_optins)


@app.route("/add-email", methods=["POST"])
def add_email():
    if request.json:
        email = EmailOptin(name=request.json.get("name"),
                           email=request.json.get("email"),
                           created_time=arrow.utcnow().datetime)
        db.session.add(email)
        db.session.commit()
    return '200'


@app.route("/update-email", methods=["POST"])
def update_email():
    """
    Endpoint to update an opt-in email user
    """
    id = request.form.get("id")
    email_optin = EmailOptin.query.filter_by(id=id).first()
    name = request.form.get("name")
    email = request.form.get("email")
    if name is not None:
        email_optin.name = name
    if email is not None:
        email_optin.email = email
    db.session.commit()
    return redirect("/email-optin")


@app.route("/delete-email", methods=["POST"])
def delete_email():
    """
    Endpoint to delete an opt-in email user
    """
    email_id = request.form.get("id")
    email = EmailOptin.query.filter_by(id=email_id).first()
    db.session.delete(email)
    db.session.commit()
    return redirect("/email-optin")

# Customized User model for SQL-Admin


class UserAdmin(sqla.ModelView):

    # Don't display the password on the list of Users
    column_exclude_list = list = ('password',)

    # Don't include the standard password field when creating or editing a
    # User (but see below)
    form_excluded_columns = ('password',)

    # Automatically display human-readable names for the current and available
    # Roles when creating or editing a User
    column_auto_select_related = True

    # Prevent administration of Users unless the currently logged-in user has
    # the "admin" role
    def is_accessible(self):
        return current_user.has_role('admin')

    # On the form for creating or editing a User, don't display a field corresponding to the model's password field.
    # There are two reasons for this. First, we want to encrypt the password before storing in the database. Second,
    # we want to use a password field (with the input masked) rather than a
    # regular text field.
    def scaffold_form(self):

        # Start with the standard form as provided by Flask-Admin. We've already told Flask-Admin to exclude the
        # password field from this form.
        form_class = super(UserAdmin, self).scaffold_form()

        # Add a password field, naming it "password2" and labeling it "New
        # Password".
        form_class.password2 = PasswordField('New Password')
        return form_class

    # This callback executes when the user saves changes to a newly-created or edited User -- before the changes are
    # committed to the database.
    def on_model_change(self, form, model, is_created):

        # If the password field isn't blank...
        if len(model.password2):

            # ... then encrypt the new password prior to storing it in the database. If the password field is blank,
            # the existing password in the database will be retained.
            model.password = utils.encrypt_password(model.password2)


# Customized Role model for SQL-Admin
class RoleAdmin(sqla.ModelView):

    # Prevent administration of Roles unless the currently logged-in user has
    # the "admin" role
    def is_accessible(self):
        return current_user.has_role('admin')

# Initialize Flask-Admin
admin = Admin(app)

# Add Flask-Admin views for Users and Roles
admin.add_view(UserAdmin(User, db.session))
admin.add_view(RoleAdmin(Role, db.session))


def translate(phrase, language):
    translator = Translator()
    translated_phrase = translator.translate(
        '{}'.format(phrase), src='en', dest='{}'.format(language))
    return translated_phrase


@app.route('/lander_form', methods=['GET'])
def lander_form():
    return render_template('landermaker_form.html')


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


@app.route('/chat-index')
def chat_index():
    return render_template('chat_sample.html')


@app.route('/chat-voices')
def chat_voices():
    """Handles routing for listing available voices"""
    params = {}
    voices = []

    while True:
        try:
            # Request list of available voices, if a continuation token
            # was returned by the previous call then use it to continue
            # listing
            response = polly.describe_voices(**params)
        except (BotoCoreError, ClientError) as err:
            # The service returned an error
            raise HTTPStatusError(HTTP_STATUS["INTERNAL_SERVER_ERROR"],
                                  str(err))

        # Collect all the voices
        voices.extend(response.get("Voices", []))

        # If a continuation token was returned continue, stop iterating
        # otherwise
        if "NextToken" in response:
            params = {"NextToken": response["NextToken"]}
        else:
            break

    json_data = json_encode(voices)
    bytes_data = bytes(json_data, "utf-8") if sys.version_info >= (3, 0) \
        else bytes(json_data)

    return ResponseData(status=HTTP_STATUS["OK"],
                        content_type="application/json",
                        # Create a binary stream for the JSON data
                        data_stream=BytesIO(bytes_data))


@app.route('/chat-read')
def chat_read():
    """Handles routing for reading text (speech synthesis)"""
    # Get the parameters from the query string
    text = self.query_get(query, "text")
    voiceId = self.query_get(query, "voiceId")
    outputFormat = self.query_get(query, "outputFormat")

    # Validate the parameters, set error flag in case of unexpected
    # values
    if len(text) == 0 or len(voiceId) == 0 or \
            outputFormat not in AUDIO_FORMATS:
        raise HTTPStatusError(HTTP_STATUS["BAD_REQUEST"],
                              "Wrong parameters")
    else:
        try:
            # Request speech synthesis
            response = polly.synthesize_speech(Text=text,
                                               VoiceId=voiceId,
                                               OutputFormat=outputFormat)
        except (BotoCoreError, ClientError) as err:
            # The service returned an error
            raise HTTPStatusError(HTTP_STATUS["INTERNAL_SERVER_ERROR"],
                                  str(err))

        return ResponseData(status=HTTP_STATUS["OK"],
                            content_type=AUDIO_FORMATS[outputFormat],
                            # Access the audio stream in the response
                            data_stream=response.get("AudioStream"))


@app.route('/generate_lander', methods=['GET', 'POST'])
def generate_lander():
    page_title = request.form['page_title']
    header = request.form['header']
    img_src = request.form['img_src']
    sub_header = request.form['sub_header']
    paragraph_1 = request.form['paragraph_1']
    tracker_url = request.form['tracker_url']
    call_to_action = request.form['call_to_action']
    button_color = request.form['button_color']
    content = {
        'page_title': page_title,
        'header': header,
        'img_src': img_src,
        'sub_header': sub_header,
        'paragraph_1': paragraph_1,
        'tracker_url': tracker_url,
        'call_to_action': call_to_action,
        'button_color': button_color
    }
    return render_template('landermaker_test.html', **content)


@app.route('/frontend_campaigns', methods=['POST', 'PUT'])
def frontend_campaigns():

    if request.method == 'POST' and request.headers.get('Custom-Status') == "get_frontend_campaigns_pagination":
        try:
            request_data = json.loads(request.data)
            items_per_page = request_data['items_per_page']
            items_offset = request_data['items_offset']
            locations_loaded = request_data['locations_loaded']
            
            frontend_campaigns = FrontendCampaign.query.order_by(FrontendCampaign.id.asc()).offset(items_offset).limit(items_per_page).all()
            frontend_campaigns_length = len(frontend_campaigns)



            if locations_loaded == False:
                try:
                    geos = Geos.query.order_by(Geos.name).all()
                except Exception as error:
                    return '{ "falure": "Retrieving geos", "error": "' + \
                        str(error) + '", "status": 404, "continue_loop": false }'
            else:
                geos = request_data['locations']


            for frontend_campaign in frontend_campaigns:
                frontend_campaign.set_all_geos(geos)

            if (frontend_campaigns_length == items_per_page):
                continue_loop = True
            else:
                continue_loop = False

            # return '{ "frontend_categories": ' + frontend_categories.__repr__() + ', "success": "loading batch of frontend categories", "status": 200, "continue_loop": '+format_boolean(continue_loop)+'}'


            return '{"campaigns":' + frontend_campaigns.__repr__() + \
                ', "locations": ' + geos.__repr__() + ', "success": "loading batch of frontend campaigns", "status": 200, "continue_loop": '+format_boolean(continue_loop)+'}'

        except Exception as error:
            return '{ "falure": "loading frontend campaigns", "error": "' + \
                        str(error) + ', "status": 404, "continue_loop": false}'


    if request.method == 'PUT':
        try:
            id = json.loads(request.data)["delete_id"]
            frontend_campaign = FrontendCampaign.query.filter_by(id=id).first()
            db.session.delete(frontend_campaign)
            db.session.commit()
        except Exception as error:
            return '{ "failure": "deleting campaign (id:' + str(
                id) + ')", "error": "' + str(error) + ', "status": 404 }'

        return json.dumps(
            {"success": 'Deleting campaign id {}'.format(id), "status": 200})

    if request.method == 'POST' and request.headers.get('Custom-Status') == "save_campaign":
        json_request_campaign = json.loads(request.data)

        try:

            if json_request_campaign["id"]:
                try:
                    frontend_campaign = FrontendCampaign.query.filter_by(
                        id=json_request_campaign["id"]).first()

                except Exception as error:
                    return '{ "failure": "Retrieving campaigns", "error": "' + \
                        str(error) + ', "status": 404 }'

            else:
                try:
                    frontend_campaign = FrontendCampaign()
                except Exception as error:
                    return '{ "failure": "failure creating campaign instance", "status": 404}'

            frontend_campaign.name = json_request_campaign["name"]
            frontend_campaign.all_day_notification = json_request_campaign[
                "all_day_notification"]
            frontend_campaign.start_at = unformat_time(
                json_request_campaign["from_time"])
            frontend_campaign.end_at = unformat_time(
                json_request_campaign["to_time"])
            frontend_campaign.time_zone = unformat_time_zone(
                json_request_campaign["time_zone"])
            frontend_campaign.frequency = json_request_campaign[
                "one_message_per_mins"]
            frontend_campaign.status = json_request_campaign["status"]
            frontend_campaign.stacking = json_request_campaign['stacking']

            try:
                db.session.add(frontend_campaign)
                db.session.flush()
                db.session.commit()
            except Exception as error:
                print("THERE WAS AN ERROR SAVING CAMPAIGN: {}".format(error))
                return '{ "failure": "Saving campaign (id:' + str(
                    frontend_campaign.id) + ')", "error": "' + str(error) + ', "status": 404 }'

            true_geos = [loc for loc in json_request_campaign[
                'locations'] if loc['checked'] == True]
            for c_geo in frontend_campaign.geos:

                if c_geo.geo_id not in [true_geo["id"]
                                        for true_geo in true_geos]:
                    delete_geo = GeosFrontendCampaigns.query.filter(
                        GeosFrontendCampaigns.frontend_campaign_id == frontend_campaign.id).filter(
                        GeosFrontendCampaigns.geo_id == c_geo.geo_id)
                    db.session.delete(c_geo)
                    db.session.commit()
                else:
                    true_geos = [true_geo for true_geo in true_geos if true_geo[
                        "id"] != c_geo.geo_id]  # .remove(c_geo.geo_id)

            for true_geo in true_geos:
                gfc = GeosFrontendCampaigns()
                geo = Geos.query.filter_by(id=true_geo['id']).first()
                gfc.geo = geo
                if frontend_campaign.id:
                    gfc.frontend_campaign_id = frontend_campaign.id
                frontend_campaign.geos.append(gfc)

            try:

                db.session.flush()
                db.session.commit()
            except Exception as error:
                return '{ "failure": "Saving campaign (id:' + str(
                    frontend_campaign.id) + ')", "error": "' + str(error) + ', "status": 404 }'

            return json.dumps({"success": 'Saving campaign id {}'.format(
                frontend_campaign.id), "status": 200})

        except Exception as error:
            return '{ "failure": "Saving campaign", "error": "' + \
                str(error) + ', "status": 404 }'

    if request.method == 'POST' and request.headers.get(
            'Custom-Status') == "update_status":
        input_message = json.loads(request.data)["campaign"]
        frontend_campaign = FrontendCampaign.query.filter_by(
            id=input_message["id"]).first()
        frontend_campaign.status = input_message['status']
        db.session.add(frontend_campaign)
        db.session.flush()
        db.session.commit()
        return '{"success": "updateing status", "status": 200, "campaign_id": '+str(frontend_campaign.id)+'}'

@app.route('/virus_check', methods=['GET', 'POST', 'PUT'])
def virus_check():
    if request.method == 'GET':
        try:
            virus_checks = VirusCheck.query.all()
        except Exception as error:
            return '{ "failure": "Retrieving virus checks", "error": "' + \
                str(error) + ', "status": 404 }'
        return '{"checks":' + virus_checks.__repr__() + ', "status": 200 }'

    if request.method == 'PUT':
        try:
            id = json.loads(request.data)["delete_id"]
            virus_check = VirusCheck.query.filter_by(id=id).first()
            db.session.delete(virus_check)
            db.session.commit()
        except Exception as error:
            return '{ "failure": "Deleting virus check (id:' + str(
                id) + ')", "error": "' + str(error) + ', "status": 404 }'
        return json.dumps(
            {"success": 'Deleting virus check - id: {}'.format(id), "status": 200})

    if request.method == 'POST':
        try:
            json_request_virus_check = json.loads(request.data)
            if 'id' in json_request_virus_check.keys():
                try:
                    virus_check = VirusCheck.query.filter_by(
                        id=json_request_virus_check["id"]).first()
                except Exception as error:
                    print('Error retrieving virus checks', error)
                    return '{ "failure": "Retreiving virus checks", "error": "' + \
                        str(error) + ', "status": 404 }'
            else:
                try:
                    virus_check = VirusCheck()
                except Exception as error:
                    return '{ "failure": "Failure creating virus check", "status": 404}'
            virus_check.name = json_request_virus_check["name"]
            virus_check.status = json_request_virus_check["status"]
            virus_check.url = json_request_virus_check["url"]
            virus_check.monitor_active = json_request_virus_check[
                "monitor_active"]
            try:
                db.session.add(virus_check)
                db.session.flush()
                db.session.commit()
            except Exception as error:
                print("THERE WAS AN ERROR SAVING VIRUS CHECK: {}".format(error))
                error_representation = str(error).replace(
                    '\n',
                    '').replace(
                    '"',
                    '').replace(
                    "'",
                    "")
                return '{ "failure": "Saving virus check (id:' + str(
                    virus_check.id) + ')", "error": "' + error_representation + '", "status": 404 }'
            return json.dumps(
                {"success": 'Saving virus check - id: {}'.format(virus_check.id), "status": 200})
        except Exception as error:
            return '{ "failure": "Saving virus check", "error": "' + \
                str(error) + ', "status": 404 }'


def connect_to_s3():
    s3 = boto3.resource('s3',
         aws_access_key_id=os.environ['AWS_ACCESS_ID'],
         aws_secret_access_key=os.environ['AWS_ACCESS_KEY'])
    return s3


def upload_file_to_s3(s3_connection, file, url_root):
    try:
        s3_connection.Bucket(
            os.environ["S3_BUCKET"]).put_object(
            ACL="public-read",
            Key=url_root +
            secure_filename(
                file.filename).replace(
                " ",
                "_"),
            Body=file)
    except Exception as error:
        return {"failure": "saving to s3", "status": 404, "error": error}
    return "https://s3.{}.amazonaws.com/{}/{}{}".format(os.environ["S3_REGION"], os.environ[
                                                        "S3_BUCKET"], url_root, secure_filename(file.filename).replace(" ", "_"))


def delete_file_from_s3(s3_connection, file_url):
    response = s3_connection.Object(os.environ["S3_BUCKET"], file_url).delete()
    return response['ResponseMetadata']['HTTPStatusCode']


@app.route('/frontend_categories', methods=['POST', 'PUT'])
def frontend_categories():

    if request.method == 'POST' and request.headers.get('Custom-Status') == "get_frontend_categories_pagination":
        try:
            request_data = json.loads(request.data)
            items_per_page = request_data['items_per_page']
            items_offset = request_data['items_offset']

            
            frontend_categories = FrontendCategory.query.order_by(FrontendCategory.id.asc()).offset(items_offset).limit(items_per_page).all()
            frontend_categories_length = len(frontend_categories)

            if (frontend_categories_length == items_per_page):
                continue_loop = True
            else:
                continue_loop = False

            return '{ "frontend_categories": ' + frontend_categories.__repr__() + ', "success": "loading batch of frontend categories", "status": 200, "continue_loop": '+format_boolean(continue_loop)+'}'

        except Exception as error:
            return '{ "falure": "loading frontend categories", "error": "' + \
                        str(error) + ', "status": 404, "continue_loop": false}'





    if request.method == 'PUT':
        id = json.loads(request.data)["delete_id"]
        frontend_category = FrontendCategory.query.filter_by(id=id).first()
        db.session.delete(frontend_category)
        db.session.commit()
        return json.dumps({'success': 'Deleting category', 'status': 200})

    if request.method == 'POST' and request.headers.get('Custom-Status') == "save_frontend_category":

        json_request_category = json.loads(request.data)
        if json_request_category["id"]:
            frontend_category = FrontendCategory.query.filter(
                FrontendCategory.id == json_request_category["id"]).first()
        else:
            frontend_category = FrontendCategory()
        frontend_category.name = json_request_category["name"],
        frontend_category.url = json_request_category["url"]

        try:

            db.session.add(frontend_category)
            db.session.flush()
            db.session.commit()
        except Exception as error:
            print("THERE WAS AN ERROR SAVING Category: {}".format(error))
            return json.dumps({'error': error, "status": 404})

        return json.dumps({'success': 'creating category',
                           'status': 200, 'category_id': frontend_category.id})


@app.route('/frontend_groups', methods=['POST', 'PUT'])
def frontend_groups():


    if request.method == 'POST' and request.headers.get('Custom-Status') == "get_frontend_groups_pagination":
        try:
            request_data = json.loads(request.data)
            items_per_page = request_data['items_per_page']
            items_offset = request_data['items_offset']

            
            frontend_groups = FrontendGroup.query.order_by(FrontendGroup.id.asc()).offset(items_offset).limit(items_per_page).all()

            frontend_groups_length = len(frontend_groups)

            if (frontend_groups_length == items_per_page):
                continue_loop = True
            else:
                continue_loop = False

            return '{ "frontend_groups": ' + frontend_groups.__repr__() + ', "success": "loading batch of frontend groups", "status": 200, "continue_loop": '+format_boolean(continue_loop)+'}'

        except Exception as error:
            return '{ "falure": "loading frontend groups", "error": "' + \
                        str(error) + ', "status": 404, "continue_loop": false}'


    

    if request.method == 'PUT':
        id = json.loads(request.data)["delete_id"]
        frontend_group = FrontendGroup.query.filter_by(id=id).first()
        db.session.delete(frontend_group)
        db.session.commit()
        return json.dumps({'success': 'Deleting group', 'status': 200})

    if request.method == 'POST' and request.headers.get('Custom-Status') == "save_frontend_group":
        json_request_group = json.loads(request.data)
        if json_request_group["id"]:
            frontend_group = FrontendGroup.query.filter(
                FrontendGroup.id == json_request_group["id"]).first()
        else:
            frontend_group = FrontendGroup()

        try:
            frontend_group.name = json_request_group["name"],
            frontend_group.frontend_category_id = json_request_group[
                "cat"]["id"],
            frontend_group.status = json_request_group["status"]
        except Exception as error:
            return json.dumps({'error': error, "status": 404})

        try:

            db.session.add(frontend_group)
            db.session.flush()
            db.session.commit()
        except Exception as error:
            print("THERE WAS AN ERROR SAVING group: {}".format(error))
            return json.dumps({'error': error, "status": 404})

        return json.dumps({'success': 'Saving group',
                           'status': 200, 'group_id': frontend_group.id})


@app.route('/frontend_messages', methods=['GET', 'POST', 'PUT'])
def frontend_messages():

    if request.method == 'POST' and request.headers.get('Custom-Status') == "load_messages":
        try:

            request_data = json.loads(request.data)
            items_per_page = request_data['items_per_page']
            items_offset = request_data['items_offset']
            media_loaded = request_data['media_loaded']
            frontend_group_id = int(request_data["group_id"])
            
            frontend_messages = FrontendMessage.query.filter(FrontendMessage.frontend_group_id == frontend_group_id).offset(items_offset).limit(items_per_page).all()
            frontend_messages_length = len(frontend_messages)


            if (frontend_messages_length == items_per_page):
                print("CONTINUE TRUE")
                continue_loop = True
            else:
                print("CONTINUE FALSE")
                continue_loop = False


            if media_loaded == False:
                try:
                    frontend_icons = FrontendIcon.query.all()
                    frontend_badges = FrontendBadge.query.all()
                    frontend_images = FrontendImage.query.all()
                    frontend_tags_frontend_icons = FrontendTagsFrontendIcons.query.all()
                    frontend_tags_frontend_badges = FrontendTagsFrontendBadges.query.all()
                    frontend_tags_frontend_images = FrontendTagsFrontendImages.query.all()
                except Exception as error:
                    return '{ "falure": "Retrieving media", "error": "' + \
                        str(error) + '", "status": 404, "continue_loop": false }'

                return '{"messages":' + frontend_messages.__repr__() + ', "images": ' + frontend_images.__repr__() + ', "icons": ' + frontend_icons.__repr__() + ', "badges": ' + frontend_badges.__repr__() + ', "images_tags": ' + format_tags_associations(frontend_tags_frontend_images).__repr__() + ', "icons_tags": ' + format_tags_associations(frontend_tags_frontend_icons).__repr__() + ', "badges_tags": ' + format_tags_associations(frontend_tags_frontend_badges).__repr__() + ',"success": "loading messages and media", "status": 200, "continue_loop":'+format_boolean(continue_loop)+'}'


            return '{"messages":' + frontend_messages.__repr__() + ',"success": "loading messages", "status": 200, "continue_loop":'+format_boolean(continue_loop)+'}'

        except Exception as error:
            return '{ "falure": "loading frontend messages", "error": "' + \
                        str(error) + ', "status": 404, "continue_loop": false}'

    if request.method == 'PUT':
        id = json.loads(request.data)["delete_id"]
        frontend_message = FrontendMessage.query.filter_by(id=id).first()
        db.session.delete(frontend_message)
        db.session.commit()
        return json.dumps({'success': 'Deleting message', 'status': 200})

    if request.method == 'POST' and request.headers.get(
            'Custom-Status') == "save_messages":

        json_request_response = json.loads(request.data)

        if json_request_response["new_message"]:
            if "headline" in [str(key) for key in json_request_response[
                    "new_message"].keys()]:

                if "content" in [str(key) for key in json_request_response[
                        "new_message"].keys()]:

                    if json_request_response["new_message"]["id"]:
                        try:
                            frontend_message = FrontendMessage.query.filter_by(
                                id=json_request_response["new_message"]["id"]).first()
                        except:
                            frontend_message = FrontendMessage()
                    else:
                        frontend_message = FrontendMessage()

                    try:
                        frontend_message.headline = str(
                            json_request_response["new_message"]["headline"]),
                    except:
                        frontend_message.headline = None
                    try:
                        frontend_message.content = str(
                            json_request_response["new_message"]["content"]),
                    except:
                        frontend_message.content = None
                    try:
                        response_icon = json_request_response[
                            "new_message"]["icon"]

                        if response_icon:
                            if "media_type" in response_icon.keys():
                                frontend_icon = FrontendIcon.query.filter_by(
                                    id=response_icon['id']).first()
                                frontend_message.frontend_icon_id = frontend_icon.id
                                frontend_message.frontend_icon = frontend_icon
                                frontend_message.frontend_icon_tag_id = None
                            elif "name" in response_icon.keys():
                                frontend_message.frontend_icon_tag_id = FrontendTag.query.filter_by(
                                    id=response_icon['id']).first().id
                                frontend_message.frontend_icon_id = None
                        else:
                            frontend_message.frontend_icon_id = None
                            frontend_message.frontend_icon_tag_id = None
                    except Exception as error:
                        return json.dumps(
                            {'falure': 'Saving icon or icon tag', 'error': str(error), "status": 404})

                    try:
                        response_badge = json_request_response[
                            "new_message"]["badge"]
                        if response_badge:
                            if "media_type" in response_badge.keys():
                                frontend_badge = FrontendBadge.query.filter_by(
                                    id=response_badge['id']).first()
                                frontend_message.frontend_badge_id = frontend_badge.id
                                frontend_message.frontend_badge = frontend_badge
                                frontend_message.frontend_badge_tag_id = None
                            elif "name" in response_badge.keys():
                                frontend_message.frontend_badge_tag_id = FrontendTag.query.filter_by(
                                    id=response_badge['id']).first().id
                                frontend_message.frontend_badge_id = None
                        else:
                            frontend_message.frontend_badge_id = None
                            frontend_message.frontend_badge_tag_id = None
                    except Exception as error:
                        return json.dumps(
                            {'falure': 'Saving badge or badge tag', 'error': str(error), "status": 404})
                    try:
                        response_image = json_request_response[
                            "new_message"]["image"]
                        if response_image:
                            if "media_type" in response_image.keys():
                                frontend_image = FrontendImage.query.filter_by(
                                    id=response_image['id']).first()
                                frontend_message.frontend_image_id = frontend_image.id
                                frontend_message.frontend_image = frontend_image
                                frontend_message.frontend_image_tag_id = None
                            elif "name" in response_image.keys():
                                frontend_message.frontend_image_tag_id = FrontendTag.query.filter_by(
                                    id=response_image['id']).first().id
                                frontend_message.frontend_image_id = None
                        else:
                            frontend_message.frontend_image_id = None
                            frontend_message.frontend_image_tag_id = None
                    except Exception as error:
                        return json.dumps(
                            {'falure': 'Saving image or image tag', 'error': str(error), "status": 404})

                    if isinstance(json_request_response[
                                  "new_message"]["status"], tuple):
                        frontend_message.status = json_request_response[
                            "new_message"]["status"][0]
                    elif isinstance(json_request_response["new_message"]["status"], bool):
                        frontend_message.status = json_request_response[
                            "new_message"]["status"]

                    frontend_message.frontend_group_id = json_request_response[
                        "group_id"]

                    # GET AWS TRANSLATIONS:
                    if not frontend_message.translations:
                        if frontend_message.headline:
                            headline_response = requests.post(
                                "https://f78jpgj8ij.execute-api.eu-central-1.amazonaws.com/prod/mobrev-translator",
                                headers={
                                    "Content-Type": "application/json"},
                                json={
                                    "translation_text": frontend_message.headline[0]}).json()
                        if frontend_message.content:
                            content_response = requests.post(
                                "https://f78jpgj8ij.execute-api.eu-central-1.amazonaws.com/prod/mobrev-translator",
                                headers={
                                    "Content-Type": "application/json"},
                                json={
                                    "translation_text": frontend_message.content[0]}).json()

                        frontend_message.translations.extend((
                            Translation(
                                language="English",
                                status=True,
                                headline=frontend_message.headline[0],
                                content=frontend_message.content[0]),
                            Translation(language="French", status=True, headline=headline_response[
                                        'translations']['fr'], content=content_response['translations']['fr']),
                            Translation(language="Chinese", status=True, headline=headline_response[
                                        'translations']['zh'], content=content_response['translations']['zh']),
                            Translation(language="German", status=True, headline=headline_response[
                                        'translations']['de'], content=content_response['translations']['de']),
                            Translation(language="Portuguese", status=True, headline=headline_response[
                                        'translations']['pt'], content=content_response['translations']['pt']),
                            Translation(language="Spanish", status=True, headline=headline_response[
                                        'translations']['es'], content=content_response['translations']['es']),
                            Translation(language="Arabic", status=True, headline=headline_response[
                                        'translations']['ar'], content=content_response['translations']['ar'])
                        ))

                    else:
                        # IF TRANSLATIONS ALREADY EXIST AND ARE MODIFIED:
                        for translation in frontend_message.translations:
                            if translation.language not in json_request_response[
                                    "new_message"]["trans"].keys():
                                db.session.delete(translation)
                                db.session.commit()
                            else:
                                translation.headline = json_request_response["new_message"][
                                    "trans"][translation.language]['headline']
                                translation.content = json_request_response["new_message"][
                                    "trans"][translation.language]['content']
                                translation.status = json_request_response["new_message"][
                                    "trans"][translation.language]['status']
                                json_request_response["new_message"][
                                    "trans"].pop(translation.language, None)

                        for key, value in json_request_response[
                                'new_message']['trans'].iteritems():
                            frontend_message.translations.append(Translation(
                                headline=value['headline'],
                                content=value['content'],
                                status=value['status'],
                                language=key
                            ))

                    try:
                        db.session.add(frontend_message)
                        db.session.flush()
                        db.session.commit()
                        print("SAVED!")
                    except Exception as error:
                        print(
                            "THERE WAS AN ERROR SAVING message: {}".format(error))
                        return json.dumps({'error': error, "status": 404})

                    return '{"success": "Saving message", "status": 200, "trans": ' + format_translations(frontend_message.translations) + ', "languages": "' + str(
                        [str(translation.language) for translation in frontend_message.translations])[1:-1] + '", "message_id": ' + str(frontend_message.id) + '}'
                else:
                    return json.dumps(
                        {'failure': "Saving message", "status": 404})

    if request.method == 'POST' and request.headers.get(
            'Custom-Status') == "update_status":
        input_message = json.loads(request.data)["message"]
        frontend_message = FrontendMessage.query.filter_by(
            id=input_message["id"]).first()
        frontend_message.status = input_message['status']
        db.session.add(frontend_message)
        db.session.flush()
        db.session.commit()
        return '{"success": "updateing status", "status": 200}'


@app.route('/frontend_groups_frontend_campaigns',
           methods=['POST', 'PUT'])
def frontend_groups_frontend_campaigns():

    if request.method == 'POST' and request.headers.get('Custom-Status') == "load_frontend_groups_frontend_campaigns":
        try:

            request_data = json.loads(request.data)
            items_per_page = request_data['items_per_page']
            items_offset = request_data['items_offset']
            frontend_groups = request_data['groups']
            frontend_categories = request_data['categories']
            campaign_id = int(request_data["campaign_id"])

            frontend_campaign = FrontendCampaign.query.filter_by(id= campaign_id).first()
            frontend_groups_frontend_campaigns = FrontendGroupsFrontendCampaigns.query.filter_by(frontend_campaign_id=campaign_id).offset(items_offset).limit(items_per_page).all()
            frontend_groups_frontend_campaigns_length = len(frontend_groups_frontend_campaigns)


            if (frontend_groups_frontend_campaigns == items_per_page):
                print("CONTINUE TRUE")
                continue_loop = True
            else:
                print("CONTINUE FALSE")
                continue_loop = False

            for gp_cp in frontend_groups_frontend_campaigns:
                for frontend_group in frontend_groups:
                    frontend_group["status"] = format_boolean(frontend_group["status"])
                    if gp_cp.frontend_group_id == frontend_group["id"]:
                        for frontend_category in frontend_categories:
                            if frontend_group["cat"]["id"] == frontend_category["id"]:
                                frontend_group["category"] = frontend_category
                                gp_cp.frontend_group = json.dumps(frontend_group)

            return '{"campaign":' + frontend_campaign.__repr__() + ', "gp_cp": ' + \
                frontend_groups_frontend_campaigns.__repr__() +',"success": "loading frontend_groups_frontend_campaigns", "status": 200, "continue_loop":'+format_boolean(continue_loop)+'}'
   
        except Exception as error:

            return '{ "falure": "loading frontend_groups_frontend_campaigns", "error": "' + \
                        str(error) + ', "status": 404, "continue_loop": false}'


    if request.method == 'PUT':

        group_id = json.loads(request.data)["group_id"]
        campaign_id = json.loads(request.data)["campaign_id"]
        frontend_groups_frontend_campaigns = FrontendGroupsFrontendCampaigns.query.filter(
            FrontendGroupsFrontendCampaigns.frontend_group_id == group_id and FrontendGroupsFrontendCampaigns.frontend_campaign_id == campaign_id).first()
        db.session.delete(frontend_groups_frontend_campaigns)
        db.session.commit()
        return json.dumps({'all good in the hood': "YUP"})

    if request.method == 'POST' and request.headers.get(
            'Custom-Status') == "save_frontend_groups_frontend_campaigns":
        request_response = json.loads(request.data)
        campaign_id = request_response['campaign_id']
        group_id = request_response['group']["id"]
        group = request_response['group']
        status = request_response["status"]
        frequency = request_response["frequency"]
        in_order = request_response["order"]
        sent = request_response["sent"]
        frontend_groups_frontend_campaigns_to_save = FrontendGroupsFrontendCampaigns.query.filter_by(
            frontend_campaign_id=campaign_id).filter_by(frontend_group_id=group_id).first()

        # Update the frontend_groups_frontend_campaigns
        if frontend_groups_frontend_campaigns_to_save:
            frontend_groups_frontend_campaigns_to_save.status = status
            frontend_groups_frontend_campaigns_to_save.frequency = frequency
            frontend_groups_frontend_campaigns_to_save.in_order = in_order
            frontend_groups_frontend_campaigns_to_save.sent = sent
        else:
            frontend_groups_frontend_campaigns_to_save = FrontendGroupsFrontendCampaigns(
                frontend_group_id=group_id,
                frontend_campaign_id=campaign_id,
                status=status,
                frequency=frequency,
                in_order=in_order,
                sent=sent
            )
            db.session.add(frontend_groups_frontend_campaigns_to_save)

        # Update group if name changed
        frontend_group = FrontendGroup.query.filter_by(id=group_id).first()
        if frontend_group:
            if frontend_group.name != group['name']:
                frontend_group.name = group['name']
                db.session.add(frontend_group)

        try:
            db.session.flush()
            db.session.commit()
        except Exception as error:
            return json.dumps({'error': error, 'status': 404})

        return json.dumps({'success': "Saving group campaign association",
                           "group_id": group_id, "campaign_id": campaign_id})


@app.route('/frontend_media', methods=['POST', 'PUT'])
def frontend_medias():

    if request.method == 'POST' and request.headers.get('Custom-Status') == "get_frontend_media_pagination":
        try:
            request_data = json.loads(request.data)
            items_per_page = request_data['items_per_page']
            items_offset = request_data['items_offset']
            tags_loaded = request_data['tags_loaded']

            try:
                frontend_icons = FrontendIcon.query.offset(items_offset).limit(items_per_page).all()
                frontend_icons_length = len(frontend_icons)
            except Exception as error:
                return '{ "failure": "Retrieving icons", "error": "' + \
                    str(error) + ', "status": 404 }'
            try:
                frontend_badges = FrontendBadge.query.offset(items_offset).limit(items_per_page).all()
                frontend_badges_length = len(frontend_badges)
            except Exception as error:
                return '{ "failure": "Retrieving badges", "error": "' + \
                    str(error) + ', "status": 404 }'
            try:
                frontend_images = FrontendImage.query.offset(items_offset).limit(items_per_page).all()
                frontend_images_length = len(frontend_images)
            except Exception as error:
                return '{ "failure": "Retrieving images", "error": "' + \
                    str(error) + ', "status": 404 }'

            
            output_media = dict()
            for frontend_icon in frontend_icons:
                try:
                    output_media["Icon" + str(frontend_icon.id)
                                 ] = json.loads(frontend_icon.__repr__())
                except:
                    LOG.info('Error on icon')
                    LOG.info(frontend_icon.__repr__())
            for frontend_badge in frontend_badges:
                try:
                    output_media["Badge" + str(frontend_badge.id)
                                 ] = json.loads(frontend_badge.__repr__())
                except:
                    LOG.info('Error on badge')
                    LOG.info(frontend_badge.__repr__())
            for frontend_image in frontend_images:
                try:
                    output_media["Image" + str(frontend_image.id)] = json.loads(frontend_image.__repr__())
                except:
                    LOG.info('Error on image')
                    LOG.info(frontend_image.__repr__())


            if (frontend_icons_length == items_per_page) or (frontend_badges_length == items_per_page) or (frontend_images_length == items_per_page):
                continue_loop = True
            else:
                continue_loop = False

            if tags_loaded == False:
                try:
                    frontend_tags = FrontendTag.query.all()
                except Exception as error:
                    return '{ "falure": "Retrieving tags", "error": "' + \
                        str(error) + ', "status": 404 }'

                output_tags = dict()
                for tag in frontend_tags:
                    output_tags[tag.tag] = json.loads(tag.__repr__())

                return '{"success":"loading medias and tags", "medias":' + json.dumps(output_media) + ', "tags": ' + \
                    json.dumps(output_tags) + ', "status": 200, "continue_loop":'+format_boolean(continue_loop)+'}'
            else:
                return '{"success":"loading medias", "medias":' + json.dumps(output_media) + ', "status": 200, "continue_loop":'+format_boolean(continue_loop)+'}'
        except Exception as error:
            return '{ "falure": "loading medias", "error": "' + \
                        str(error) + ', "status": 404, "continue_loop": false }'

    if request.method == 'PUT' and request.headers.get(
            'Custom-Status') == "delete_media_file":
        # DETELE FROM DATABASE:
        response = json.loads(request.data)

        for delete_media in response['delete_medias']:

            id = delete_media['id']
            media_type = delete_media['media_type']
            try:

                if media_type:
                    if media_type == 'Icon':
                        media = FrontendIcon.query.filter_by(id=id).first()
                        media_url = "Icon/" + media.frontend_icon_filename
                    if media_type == 'Badge':
                        media = FrontendBadge.query.filter_by(id=id).first()
                        media_url = "Badge/" + media.frontend_badge_filename
                    if media_type == 'Image':
                        media = FrontendImage.query.filter_by(id=id).first()
                        media_url = "Image/" + media.frontend_image_filename

                    db.session.delete(media)

                else:
                    raise "there was no media_type specified"

                db.session.commit()
            except Exception as error:
                return '{ "failure": "deleting media (id:' + str(
                    id) + ' from DB", "media_type": "' + media_type + '", "error": "' + str(error) + '", "status": 404 }'

            # DELETE FROM S3
            try:
                s3 = connect_to_s3()

                output = delete_file_from_s3(s3, media_url)
            except Exception as error:
                return '{ "failure": "deleting media (id:' + str(
                    id) + ' from S3", "error": "' + str(error) + '", "status": 404 }'

        return json.dumps({"success": 'Deleting media', "status": 200})

    if request.method == 'PUT' and request.headers.get(
            'Custom-Status') == "delete_tag":
        input_tag = request.data

        try:
            tag_to_delete = FrontendTag.query.filter_by(tag=input_tag).first()
        except Exception as error:
            return '{ "failure": "finding tag (id:' + str(
                input_tag) + ') from DB", "error": "' + str(error) + '", "status": 404 }'

        if tag_to_delete:
            try:
                db.session.delete(tag_to_delete)
                db.session.commit()
            except Exception as error:
                return '{ "failure": "Deleting tag (id: ' + str(
                    tag_to_delete.id) + ') from DB", "error": "' + str(error) + '", "status": 404 }'
        else:
            return '{ "failure": "Deleting tag from DB", "error": "no such tag exists in DB", "status": 404 }'
        return json.dumps({"success": "Deleting tag", "status": 200})

    if request.method == 'POST' and request.headers.get(
            'Custom-Status') == "save_media_file":

        if request.files:
            media_type = request.headers.get('Media-Type')

            if media_type and media_type != "null":

                try:
                    s3 = connect_to_s3()
                    print("THIS IS THE S3", s3)
                    file = request.files["file"]
                    print("THIS IS THE FILE", file)
                    print("THIS IS THE MEDIA TYPE", media_type)
                    if file:

                        file_url = upload_file_to_s3(
                            s3, file, media_type + "/")

                        if isinstance(file_url, dict) and file_url['error']:
                            print("THIS SI THE ERROR:", file_url)
                            return '{ "failure": "Saving media image to S3", "error": '+file_url['error']+', "status": 404 }'
                            
                except Exception as error:
                    return '{ "failure": "Saving media image to S3", "error": "' + \
                        str(error) + '", "status": 404 }'

                if media_type == "Icon":
                    media_to_save = FrontendIcon()
                    media_to_save.frontend_icon_filename = secure_filename(
                        file.filename).replace(" ", "_")
                    media_to_save.frontend_icon_url = file_url
                    file_name = media_to_save.frontend_icon_filename
                elif media_type == "Badge":
                    media_to_save = FrontendBadge()
                    media_to_save.frontend_badge_filename = secure_filename(
                        file.filename).replace(" ", "_")
                    media_to_save.frontend_badge_url = file_url
                    file_name = media_to_save.frontend_badge_filename
                elif media_type == "Image":
                    media_to_save = FrontendImage()
                    media_to_save.frontend_image_filename = secure_filename(
                        file.filename).replace(" ", "_")
                    media_to_save.frontend_image_url = file_url
                    file_name = media_to_save.frontend_image_filename
                else:
                    raise "NO MEDIATYPE SPECIFIED"

                try:
                    media_to_save.selected = False
                    db.session.add(media_to_save)
                    db.session.flush()
                    db.session.commit()

                except Exception as error:

                    return '{ "failure": "Saving media (id:' + str(
                        media_to_save.id) + ') to DB", "error": "' + str(error) + '", "status": 404 }'

                return json.dumps({"success": 'Saving media id {}'.format(
                    media_to_save.id), "status": 200, "id": media_to_save.id, "url": file_url, })

                return json.dumps({"success": 'Saving media id {}'.format(
                    media_to_save.id), "status": 200, "id": media_to_save.id, "url": file_url, "name": file_name})

            else:
                return '{ "failure": "Saving media image to S3", "error": "Media-Type not specified", "status": 404 }'
        else:
            return '{ "failure": "Saving media image to S3", "error": "No file present", "status": 404 }'

    if request.method == 'POST' and request.headers.get(
            'Custom-Status') == "assign_tag":

        response = json.loads(request.data)

        input_media = response['media']
        if input_media["media_type"] == 'Icon':
            media = FrontendIcon.query.filter_by(id=input_media['id']).first()
            association = FrontendTagsFrontendIcons(
                frontend_icon_id=input_media['id'])
        if input_media["media_type"] == 'Badge':
            media = FrontendBadge.query.filter_by(id=input_media['id']).first()
            association = FrontendTagsFrontendBadges(
                frontend_badge_id=input_media['id'])
        if input_media["media_type"] == 'Image':
            media = FrontendImage.query.filter_by(id=input_media['id']).first()
            association = FrontendTagsFrontendImages(
                frontend_image_id=input_media['id'])

        # CHECK IF TAG ASSOCIATION EXISTS:
        if response["tag"] not in [a.tag.tag for a in media.frontend_tags]:
            front_tag = FrontendTag.query.filter_by(
                tag=response["tag"]).first()
            association.frontend_tag_id = front_tag.id
            db.session.add(association)
            db.session.commit()

            return json.dumps({"success": "adding tag", "status": 200})
        else:
            return '{ "failure": "assigning tag to media", "error": "tag already assiged to media", "status": 404 }'

    if request.method == 'POST' and request.headers.get(
            'Custom-Status') == "remove_tag":

        response = json.loads(request.data)

        if response["medias"]:
            input_medias = response['medias']
            if response["tags"]:
                input_tags = [tag['name'] for tag in response['tags']]
                if input_medias and input_tags:
                    for input_media in input_medias:
                        id = input_media['id']
                        media_type = input_media['media_type']

                        if media_type:
                            if media_type == 'Icon':
                                media = FrontendIcon.query.filter_by(
                                    id=id).first()
                            if media_type == 'Badge':
                                media = FrontendBadge.query.filter_by(
                                    id=id).first()
                            if media_type == 'Image':
                                media = FrontendImage.query.filter_by(
                                    id=id).first()
                            try:

                                for frontend_tag in media.frontend_tags:

                                    if frontend_tag.tag.tag in input_tags:

                                        response = db.session.delete(
                                            frontend_tag)
                                        db.session.commit()

                            except Exception as error:
                                return '{ "failure": "deleting tag (id:' + str(
                                    id) + ' from DB", media_type: ' + media_type + ')", "error": "' + str(error) + '", "status": 404 }'
                return json.dumps({"success": "removing tag", "status": 200})
            return '{ "failure": "removing tags", "error": "no tags selected", "status": 404 }'
        return '{ "failure": "removing tags", "error": "no media selected", "status": 404 }'

    if request.method == 'POST' and request.headers.get(
            'Custom-Status') == "save_tag":
        input_tag = json.loads(request.data)
        try:
            tag_to_save = FrontendTag(
                tag=input_tag['name'],
                checked=input_tag['checked'])
        except Exception as error:
            return '{ "failure": "Saving tag (id:' + str(
                tag_to_save.id) + ') to DB", "error": "' + str(error) + '", "status": 404 }'

        try:
            db.session.add(tag_to_save)
            db.session.flush()
            db.session.commit()
        except Exception as error:
            return '{ "failure": "Saving tag (id:' + str(
                tag_to_save.id) + ') to DB", "error": "' + str(error) + '", "status": 404 }'

        return json.dumps({"success": "adding tag", "status": 200})


@app.route('/optimizer/<string:traffic_source>',
           methods=['POST', 'PUT'])
def optimizer(traffic_source):

    if request.method == 'POST' and request.headers.get('Custom-Status') == "get_optimizer_media_pagination":
        try:
            request_data = json.loads(request.data)
            items_per_page = request_data['items_per_page']
            items_offset = request_data['items_offset']
            traffic_source_campaigns_loaded = request_data['traffic_source_campaigns_loaded']



            if traffic_source_campaigns_loaded == False:
                vc = VoluumRequester(voluum_access_key, voluum_access_key_id)
                traffic_source_campaigns = vc.get_traffic_source_campaigns(
                    traffic_source, ['trafficSourceName', 'campaignName', 'campaignId'], ['traffic_source', 'name', 'id'])

                #DELETE VOLUUM REQUESTER INSTANCE
                del vc

            else:
                traffic_source_campaigns = request_data['traffic_source_campaigns']
            campaign_rules = CampaignRule.query.filter_by(
                traffic_source=traffic_source).offset(items_offset).limit(items_per_page).all()
            campaign_rules_length = len(campaign_rules)
            for campaign_rule in campaign_rules:
                try:
                    campaign_rule.campaign = json.dumps([item for item in traffic_source_campaigns if item[
                                                        "id"] == campaign_rule.campaign_id][0])
                except:
                    pass
            if (campaign_rules_length == items_per_page):
                continue_loop = True
            else:
                continue_loop = False

            return '{ "traffic_source_campaigns": ' + json.dumps(traffic_source_campaigns) + ', "campaign_rules": ' + campaign_rules.__repr__() + ', "success": "loading batch of campaign_rules", "status": 200, "continue_loop": '+format_boolean(continue_loop)+'}'
        except Exception as error:
            return '{ "falure": "loading optimizer campaign_rules", "error": "' + \
                        str(error) + ', "status": 404 }'

    if request.method == 'PUT':
        id = json.loads(request.data)["delete_id"]
        campaign_rule = CampaignRule.query.filter_by(id=id).first()
        db.session.delete(campaign_rule)
        db.session.commit()
        return json.dumps({'success': 'Deleting campaign rule', 'status': 200})

    if request.method == 'POST' and request.headers.get('Custom-Status') == "save_rule":

        request_response = json.loads(request.data)
        if request_response["id"]:
            campaign_rule = CampaignRule.query.filter_by(
                id=request_response["id"]).first()

        if campaign_rule is None:
            campaign_rule = CampaignRule()
        try:
            campaign_rule.status = request_response['status']
            campaign_rule.campaign_id = request_response['campaign']['id']
            campaign_rule.period = request_response['period']
            campaign_rule.action = request_response['action']
            campaign_rule.traffic_source = request_response[
                'campaign']['traffic_source'].lower()
        except Exception as error:
            return json.dumps({'error': str(
                error), "falure": "Saving rule, make sure all the fields are in the correct formats", "status": 404})

        try:
            db.session.add(campaign_rule)
            db.session.flush()
            db.session.commit()
        except Exception as error:
            return json.dumps(
                {'error': str(error), "falure": "Saving rule", "status": 404})

        for constraint in request_response['constraints']:
            constraint_to_save = RuleConstraint.query.filter_by(
                id=constraint['id']).first()
            if constraint_to_save is None:
                constraint_to_save = RuleConstraint()

            try:
                constraint_to_save.campaign_rule_id = campaign_rule.id
                constraint_to_save.operator = constraint['operator']
                constraint_to_save.conjunction = constraint['conjunction']
                constraint_to_save.metric = constraint['metric']
                constraint_to_save.traffic_source = traffic_source
                if constraint["value"]:
                    constraint_to_save.value = float(constraint['value'])
            except Exception as error:
                return json.dumps(
                    {'error': str(error), "falure": "Saving constriant", "status": 404})

            try:
                db.session.add(constraint_to_save)
                db.session.flush()
                db.session.commit()
            except Exception as error:
                return json.dumps(
                    {'error': str(error), "falure": "Saving constriant", "status": 404})

        return '{"success": "Saving rule", "status": 200, "campaign_rule_id": ' + \
            str(campaign_rule.id) + ', "constraints": ' + \
            campaign_rule.rule_constraints.__repr__() + '}'


@app.route('/get_voluum_landers', methods=['POST'])
def get_voluum_landers():
    if request.method == 'POST':
        json_response = json.loads(request.data)

        # Must be in format YYYY-MM-DD
        if json_response['start_date']:
            start_date = json_response['start_date']
        else:
            start_date = None
        # Must be in format YYYY-MM-DD
        if json_response['end_date']:
            end_date = json_response['end_date']
        else:
            end_date = None
        # Columns you request. Array of strings ['landerId','landerName',
        # 'landerUrl']
        if json_response['report_columns']:
            report_columns = json_response['report_columns']
        else:
            report_columns = []
        # Names to rename columns (must be in same order). Array of strings
        # ['lander_id', 'lander_name', 'lander_url']
        if json_response['fieldnames']:
            field_names = json_response['fieldnames']
        else:
            field_names = []
        if start_date:
            vc = VoluumRequester(
                voluum_access_key,
                voluum_access_key_id,
                start_date)
            if end_date:
                vc = VoluumRequester(
                    voluum_access_key,
                    voluum_access_key_id,
                    start_date,
                    end_date)
        else:
            if end_date:
                vc = VoluumRequester(
                    voluum_access_key,
                    voluum_access_key_id,
                    start_date,
                    end_date)
            else:
                vc = VoluumRequester(voluum_access_key, voluum_access_key_id)

        #DELETE VOLUUM REQUESTER INSTANCE
        del vc
   
        return json.dumps(vc.get_landers(report_columns, field_names))


@app.route('/get_voluum_offers', methods=['POST'])
def get_voluum_offers():
    if request.method == 'POST':
        json_response = json.loads(request.data)

        # Must be in format YYYY-MM-DD
        if json_response['start_date']:
            start_date = json_response['start_date']
        else:
            start_date = None
        # Must be in format YYYY-MM-DD
        if json_response['end_date']:
            end_date = json_response['end_date']
        else:
            end_date = None
        # Columns you request. Array of strings ['offerId','offerName',
        # 'offerUrl']
        if json_response['report_columns']:
            report_columns = json_response['report_columns']
        else:
            report_columns = []
        # Names to rename columns (must be in same order). Array of strings
        # ['offer_id', 'offer_name', 'offer_url']
        if json_response['fieldnames']:
            field_names = json_response['fieldnames']
        else:
            field_names = []
        if start_date:
            vc = VoluumRequester(
                voluum_access_key,
                voluum_access_key_id,
                start_date)
            if end_date:
                vc = VoluumRequester(
                    voluum_access_key,
                    voluum_access_key_id,
                    start_date,
                    end_date)
        else:
            if end_date:
                vc = VoluumRequester(
                    voluum_access_key,
                    voluum_access_key_id,
                    start_date,
                    end_date)
            else:
                vc = VoluumRequester(voluum_access_key, voluum_access_key_id)

        #DELETE VOLUUM REQUESTER INSTANCE
        del vc
   
        return json.dumps(vc.get_offers(report_columns, field_names))

@app.route('/reporting_overview', methods=['POST'])
def overview_report():
    if request.method == 'POST':
        json_response = json.loads(request.data)
        try:
            if json_response['period']:
                period = json_response['period']
                if period == 'today':
                    start_date = (datetime.datetime.today() - datetime.timedelta(1)).date()
                    end_date = datetime.datetime.today().date()
                elif period == 'yesterday':
                    start_date = (datetime.datetime.today() - datetime.timedelta(2)).date()
                    end_date = (datetime.datetime.today() - datetime.timedelta(1)).date()
                elif period == '3':
                    start_date = (datetime.datetime.today() - datetime.timedelta(3)).date()
                    end_date = datetime.datetime.today().date()
                elif period == '7':
                    start_date = (datetime.datetime.today() - datetime.timedelta(7)).date()
                    end_date = datetime.datetime.today().date()
                elif period == 'this_month':
                    start_date = datetime.datetime.today().date().replace(day=1)
                    end_date = datetime.datetime.today().date()
                elif period == 'last_month':
                    start_date = (datetime.datetime.today() - datetime.timedelta(weeks=4)).date()
                    end_date = datetime.datetime.today().date()
                elif period == 'this_year':
                    start_date = datetime.datetime.today().date().replace(day=1, month=1)
                    end_date = datetime.datetime.today().date()
                elif period == 'custom_date':
                    start_date = json_response['from_date']
                    end_date = json_response['to_date']
        except Exception as error:
            LOG.info("there was an error {}".format(error))
            return json.dumps({"failure": "getting time span", "status":200})

        frontend_categories = FrontendCategory.query.all()
        vc = VoluumRequester(voluum_access_key, voluum_access_key_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        report = vc.prepare_overview_report(frontend_categories)
        
        # #DELETE VOLUUM REQUESTER INSTANCE
        del vc
   
        # return json.dumps({"success": "getting response", "status":200})
        return json.dumps({"success": "getting response", "status":200, "report": report})


@app.route('/campaign_alerts', methods=['GET','POST', 'PUT'])
def campaign_alerts():
    if request.method == 'GET':

        vc = VoluumRequester(voluum_access_key, voluum_access_key_id)
        voluum_campaigns = vc.get_all_campaigns()
        campaign_alerts = CampaignAlert.query.all()
        for index, row in enumerate(voluum_campaigns['campaigns']):
            voluum_campaigns['campaigns'][index] = vc.keep_keys_in_dict(row, ['trafficSourceName','campaignName', 'campaignId', "campaignCountry", "campaignUrl"])

        del vc
        return json.dumps({"success": "doing whatever", "status":200, 'voluum_campaigns': voluum_campaigns['campaigns'], "campaign_alerts": json.loads(campaign_alerts.__repr__())})

    if request.method == 'POST' and request.headers.get('Custom-Status') == "get_campaign_alerts_pagination":
        try:
            request_data = json.loads(request.data)
            items_per_page = request_data['items_per_page']
            items_offset = request_data['items_offset']
            voluum_campaigns_loaded = request_data['voluum_campaigns_loaded']

            if voluum_campaigns_loaded == False:
                vc = VoluumRequester(voluum_access_key, voluum_access_key_id)
                voluum_campaigns = vc.get_all_campaigns()
                for index, row in enumerate(voluum_campaigns['campaigns']):
                    voluum_campaigns['campaigns'][index] = vc.keep_keys_in_dict(row, ['trafficSourceName','campaignName', 'campaignId', "campaignCountry", "campaignUrl"])

                #DELETE VOLUUM REQUESTER INSTANCE
                del vc

            else:
                voluum_campaigns = request_data['voluum_campaigns']


            campaign_alerts = CampaignAlert.query.offset(items_offset).limit(items_per_page).all()
            campaign_alerts_length = len(campaign_alerts)

            if (campaign_alerts_length == items_per_page):
                continue_loop = True
            else:
                continue_loop = False

            return '{ "voluum_campaigns": ' + json.dumps(voluum_campaigns['campaigns']) + ', "campaign_alerts": ' + campaign_alerts.__repr__() + ', "success": "loading batch of campaign_alerts", "status": 200, "continue_loop": '+format_boolean(continue_loop)+'}'
        except Exception as error:
            return '{ "falure": "loading campaign alerts", "error": "' + \
                        str(error) + ', "status": 404 }'


    if request.method == 'POST' and request.headers.get('Custom-Status') == "save_campaign_alert":
        request_response = json.loads(request.data)

        if request_response["id"]:
            campaign_alert = CampaignAlert.query.filter_by(
                id=request_response["id"]).first()
        else:
            campaign_alert = CampaignAlert(
                status = 'normal',
                campaignid = "",
                campaignurl = "",
                campaignname = "",
                monitor = True,
                metric = "",
                logic = "",
                value = 0
                )
        try:
            campaign_alert.status = request_response['status'].title()
            campaign_alert.campaignid = request_response['campaignId']
            campaign_alert.campaignurl = request_response['campaignUrl']
            campaign_alert.campaignname = request_response['campaignName']
            campaign_alert.monitor = request_response['monitor']
            campaign_alert.metric = request_response['metric']
            campaign_alert.logic = request_response['logic']
            campaign_alert.value = request_response['value']
        except Exception as error:
            return json.dumps({'error': str(
                error), "falure": "Saving campaign alert, make sure all the fields are in the correct formats", "status": 404})

        try:
            db.session.add(campaign_alert)
            db.session.flush()
            db.session.commit()
        except Exception as error:
            return json.dumps(
                {'error': str(error), "falure": "Saving campaign alert", "status": 404})

        return json.dumps({"success": "saving campaign alert", "status":200, 'camp_alert_id': campaign_alert.id})

    if request.method == 'PUT':
        id = json.loads(request.data)["delete_id"]
        campaign_alert = CampaignAlert.query.filter_by(id=id).first()
        db.session.delete(campaign_alert)
        db.session.commit()
        return json.dumps({'success': 'Deleting campaign alert', 'status': 200})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
