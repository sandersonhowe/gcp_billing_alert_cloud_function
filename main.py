import base64
import json
import os
import slack
from slack.errors import SlackApiError
from googleapiclient import discovery

# SETTINGS
# --------------------------------------------------------------------------------
# PROJECT
PROJECT_NAME = "IDENTIFY API" # name for alerts
PROJECT_ACCOUNT = "staging" # staging / production

# BOT
TEST_MODE = True # True = Will check if the script can kill the billing account without killing the billing account
KILL_BOT = True # True = kill the billing account if over THRESHOLD_KILL, otherwise it will just increase it's warning levels
THRESHOLD_WARNING = 1.2 # Increase warning level at X times the billing threshold - NOTE: this currently has only been tested with one billing threshold
THRESHOLD_KILL = 1.4 # kill billing account at or increase warning level 

# GCP
PROJECT_ID = os.getenv('GCP_PROJECT') # set this as a enviroment var in GCP
PROJECT_NAME = f'projects/{PROJECT_ID}'

# SLACK
# See https://api.slack.com/docs/token-types#bot for more info

# Your slack account
BOT_ACCESS_TOKEN = 'xoxb-2304342086610-3196957901361-b4pR4V6OhcISQavrY7ar5bIP'
CHANNEL = 'C03642N6P1N'
slack_client = slack.WebClient(token=BOT_ACCESS_TOKEN)

# Clients slack account
# CLIENT_BOT_ACCESS_TOKEN = ''
# CLIENT_CHANNEL = 'C0xxxxxxxxx'
# client_slack_client = slack.WebClient(token=CLIENT_BOT_ACCESS_TOKEN)

# SLACK NOTIFCATION AND FUNCTION ENTRY
# -------------------------------------------------------------------------------
def notify_slack(data, context):
    pubsub_message = data
    budget_notification_text = None

    # For more information, see
    # https://cloud.google.com/billing/docs/how-to/budgets-programmatic-notifications#notification_format
    try:
        notification_attr = json.dumps(pubsub_message['attributes'])
    except KeyError:
        notification_attr = "No attributes passed in"

    try:
        notification_data = base64.b64decode(data['data']).decode('utf-8')
    except KeyError:
        notification_data = "No data passed in"

    # This is just a quick dump of the budget data (or an empty string)
    # You can modify and format the message to meet your needs
    data = json.loads(notification_data)
    
    # test the account can actually delete the billing account
    if TEST_MODE:
        if data['costAmount'] > data['budgetAmount']:
            if stop_billing_test():
                budget_notification_text = f':white_check_mark: TEST MODE PASSED: ACCOUNT CAN BE LOCKED DOWN :white_check_mark:\n*Account*: {PROJECT_NAME} - {PROJECT_ACCOUNT}\n```{notification_attr}, {notification_data}```'
            else:
                budget_notification_text = f':warning: TEST MODE FAILED: CHECK LOGS :warning:\n*Account*: {PROJECT_NAME} - {PROJECT_ACCOUNT}\n```{notification_attr}, {notification_data}```'
    else: # live
        # catch over budget
        if data['costAmount'] > data['budgetAmount']:
            budget_notification_text = f':warning: BUDGET WARNING! :warning:\n*Account*: {PROJECT_NAME} - {PROJECT_ACCOUNT}\n```{notification_attr}, {notification_data}```'

        # catch over budget and almost at kill threashold
        if data['costAmount'] > data['budgetAmount'] * THRESHOLD_WARNING:
            budget_notification_text = f':rotating_light: BUDGET KILL THRESHOLD IMMINENT! :rotating_light:\n*Account*: {PROJECT_NAME} - {PROJECT_ACCOUNT}\n```{notification_attr}, {notification_data}```'

        # kill threashold hit, stop billing
        if data['costAmount'] > data['budgetAmount'] * THRESHOLD_KILL:
            if KILL_BOT:
                if stop_billing():
                    budget_notification_text = f':lock: ACCOUNT HAS BEEN LOCKED DOWN! :lock:\n*Account*: {PROJECT_NAME} - {PROJECT_ACCOUNT}\n```{notification_attr}, {notification_data}```'
                else:
                    budget_notification_text = f':boom: ACCOUNT LOCKED FAILED! :boom:\n*Account*: {PROJECT_NAME} - {PROJECT_ACCOUNT}\n```{notification_attr}, {notification_data}```'
            else:
                budget_notification_text = f':fire: BUDGET KILL THRESHOLD BREACHED! :fire:\n*Account*: {PROJECT_NAME} - {PROJECT_ACCOUNT}\n```{notification_attr}, {notification_data}```'

  
    
    # only show if there is an threshold breached
    if budget_notification_text is not None:
        # SH slack
        try:
            slack_client.api_call(
                'chat.postMessage',
                json={
                    'channel': CHANNEL,
                    'text'   : budget_notification_text
                }
            )
        except SlackApiError:
            print('Error posting to Slack')

        # client slack
        # try:
        #     client_slack_client.api_call(
        #         'chat.postMessage',
        #         json={
        #             'channel': CLIENT_CHANNEL,
        #             'text'   : budget_notification_text
        #         }
        #     )
        # except SlackApiError:
        #     print('Error posting to Slack')


# KILL BOT SCRIPTS
# NOTE: test this function works as intended with stop_billing_test()
# -------------------------------------------------------------------------------
def stop_billing_test():
    if PROJECT_ID is None:
        print('TEST: No project specified with environment variable')
        return False
    
    billing = discovery.build(
        'cloudbilling',
        'v1',
        cache_discovery=False,
    )

    projects = billing.projects()
    
    billing_enabled = __is_billing_enabled(PROJECT_NAME, projects)

    if billing_enabled:
        print('TEST: Billing enabled')
        return True
    else:
        print('TEST: Billing already disabled or not found')
    
    return False

# real deal
def stop_billing():
    if PROJECT_ID is None:
        print('No project specified with environment variable')
        return False

    billing = discovery.build(
        'cloudbilling',
        'v1',
        cache_discovery=False,
    )

    projects = billing.projects()

    billing_enabled = __is_billing_enabled(PROJECT_NAME, projects)

    if billing_enabled:
        disabled = __disable_billing_for_project(PROJECT_NAME, projects)
        if disabled:
            return True
        
        return False
    else:
        print('Billing already disabled')
    
    return False


def __is_billing_enabled(project_name, projects):
    """
    Determine whether billing is enabled for a project
    @param {string} project_name Name of project to check if billing is enabled
    @return {bool} Whether project has billing enabled or not
    """
    print('look up billing for: ', project_name)
    try:
        res = projects.getBillingInfo(name=project_name).execute()
        return res['billingEnabled']
    except KeyError:
        # If billingEnabled isn't part of the return, billing is not enabled
        return False
    except Exception as e:
        print('Unable to determine if billing is enabled on specified project, assuming billing is enabled but unreachabe. DANGER: Check Bot permissions, it might not be able to disable the account.')
        print('Check you have the Billing API turned on: https://console.cloud.google.com/apis/library/cloudbilling.googleapis.com?project='+PROJECT_ID)
        print('You may also need to recreate the service account as it can stop working after the script has locked your acocunt.')
        print(e)

        # return False for test mode so you can try and fix the permission errors
        if TEST_MODE:
            return False

        # if LIVE, presume it might work and try to shut down service anyway.
        return True


def __disable_billing_for_project(project_name, projects):
    """
    Disable billing for a project by removing its billing account
    @param {string} project_name Name of project disable billing on
    """
    body = {'billingAccountName': ''}  # Disable billing
    try:
        res = projects.updateBillingInfo(name=project_name, body=body).execute()
        print(f'Billing disabled: {json.dumps(res)}')
        return True
    except Exception as e:
        print('Failed to disable billing, possibly check permissions')
        print(e)
        return False