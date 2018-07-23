

# Wait for 20 minutes
minutes = 20 * 60
time.sleep(minutes)

# TODO: Refactor to support multiple app ids
# for notificationId in notification_id_list
# Build onesignal Auth Headers
rest_authorization = "Basic {}".format(app_ids[onesignal_app_id])
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
rest_authorization = "Basic {}".format(app_ids[onesignal_app_id])
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
except:
    num_user_open = 0
    logger.exception('Error updating performance information for element.')
try:
    clicks_worth = round(num_user_open * 0.0367, 2)
except:
    clicks_worth = 0
    logger.exception('Error updating performance information for element.')
try:
    lost_users_worth = round(num_user_lost * 0.078, 2)
except:
    lost_users_worth = 0
    logger.exception('Error updating performance information for element.')
try:
    subscribers_worth = round(num_users_remaining * 0.078, 2)
except:
    subscribers_worth = 0
    logger.exception('Error updating performance information for element.')
try:
    num_time_sent = 1
except:
    num_time_sent = 0
    logger.exception('Error updating performance information for element.')
try:
    num_user_converted = round(clicks_worth / 1.5, 2)
except:
    num_user_converted = 0
    logger.exception('Error updating performance information for element.')
try:
    revenue_generated = clicks_worth
except:
    revenue_generated = 0
    logger.exception('Error updating performance information for element.')
try:
    average_churn_rate = round((num_user_lost / num_user_sent) * 100, 2)
except:
    average_churn_rate = 0
    logger.exception('Error updating performance information for element.')
try:
    average_open_rate = round((num_user_open / num_user_sent) * 100, 2)
except:
    average_open_rate = 0
    logger.exception('Error updating performance information for element.')
try:
    average_conversion_rate = round(
        (num_user_converted / num_user_open) * 100, 2)
except:
    average_conversion_rate = 0
    logger.exception('Error updating performance information for element.')


try:
    ph.update_element('headlines', 'headline', self.headline.replace("'", "''"), num_time_sent, num_user_sent, num_user_open,
                      num_user_lost, num_user_converted, revenue_generated, average_churn_rate, average_open_rate, average_conversion_rate)
    logger.info('Headline updated.')
except Exception as error:
    logger.exception('Error trying to update/insert headline.')

try:
    ph.update_element('messages', 'message', self.message.replace("'", "''"), num_time_sent, num_user_sent, num_user_open,
                      num_user_lost, num_user_converted, revenue_generated, average_churn_rate, average_open_rate,
                      average_conversion_rate)
    logger.info('Message updated.')
except Exception as error:
    logger.exception('Error trying to update/insert message.')

try:
    ph.update_element('badges', 'badge', self.badge.replace("'", "''"), num_time_sent, num_user_sent, num_user_open,
                      num_user_lost, num_user_converted, revenue_generated, average_churn_rate, average_open_rate,
                      average_conversion_rate)
    logger.info('Badge updated.')
except Exception as error:
    logger.exception('Error trying to update/insert badge.')

try:
    ph.update_element('thumbnails', 'thumbnail', self.thumbnail.replace("'", "''"), num_time_sent, num_user_sent, num_user_open,
                      num_user_lost, num_user_converted, revenue_generated, average_churn_rate, average_open_rate,
                      average_conversion_rate)
    logger.info('Thumbnail updated.')
except Exception as error:
    logger.exception('Error trying to update/insert thumbnail.')

try:
    ph.update_element('names', 'name', self.name.replace("'", "''"), num_time_sent, num_user_sent, num_user_open,
                      num_user_lost, num_user_converted, revenue_generated, average_churn_rate, average_open_rate,
                      average_conversion_rate)
    logger.info('Name updated.')
except Exception as error:
    logger.exception('Error trying to update/insert name.')

# Log Results
logger.info('Notification ID:' + str(notificationId))
logger.info('Clicks: ' + str(num_user_open))
logger.info('Clicks worth: ' + str(clicks_worth))
logger.info('Lost Users: ' + str(num_user_lost))
logger.info('Lost Users Worth: ' + str(lost_users_worth))
logger.info('Subscribers: ' + str(num_user_sent))
logger.info('Subscribers Worth: ' + str(subscribers_worth))
logger.info('Net Gain/Loss: ' + str(clicks_worth - lost_users_worth))
logger.info('Open Rate: ' + str((num_user_open / num_user_sent * 100)) + '%')


