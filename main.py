import base64
import json
import os
import slack
from slack.errors import SlackApiError
from googleapiclient import discovery

# budget id: fc1f3a9f-9df0-45f1-8cd2-b68e58174e03
# topic: buget-trigger

# See https://api.slack.com/docs/token-types#bot for more info
# SH internal slack account
BOT_ACCESS_TOKEN = 'xoxb-2304342086610-3196957901361-b4pR4V6OhcISQavrY7ar5bIP'
CHANNEL = 'C03642N6P1N'

slack_client = slack.WebClient(token=BOT_ACCESS_TOKEN)

# Clients slack account
# CLIENT_BOT_ACCESS_TOKEN = ''
# CLIENT_CHANNEL = 'C0xxxxxxxxx'
# client_slack_client = slack.WebClient(token=CLIENT_BOT_ACCESS_TOKEN)

# slack notifcation
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
    
    # catch over budget
    if data['costAmount'] > data['budgetAmount']:
        budget_notification_text = f':warning: BUDGET WARNING! :warning:\nAccount: IDENTIFY API\n```{notification_attr}, {notification_data}```'

    # catch over budget and almost at kill threashold
    if data['costAmount'] > data['budgetAmount'] * 1.2:
        budget_notification_text = f':rotating_light: BUDGET KILL THRESHOLD IMMINENT! :rotating_light:\nAccount: IDENTIFY API\n```{notification_attr}, {notification_data}```'

    # kill threashold hit, stop billing
    if data['costAmount'] > data['budgetAmount'] * 1.4:
        # stopped = stop_billing_test() # test
        stopped = stop_billing() # live
        if stopped:
            budget_notification_text = f':boom: ACCOUNT HAS BEEN LOCKED DOWN! :boom:\nAccount: IDENTIFY API\n```{notification_attr}, {notification_data}```'
  
    
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


# KILL EVERYTHING SWITCH
# NOTE: test the kill function works as intended
# -------------------------------------------------------------------------------
PROJECT_ID = os.getenv('GCP_PROJECT')
PROJECT_NAME = f'projects/{PROJECT_ID}'

def stop_billing_test():
    if PROJECT_ID is None:
        print('TEST: No project specified with environment variable')
    
    billing = discovery.build(
        'cloudbilling',
        'v1',
        cache_discovery=False,
    )

    projects = billing.projects()
    
    billing_enabled = __is_billing_enabled(PROJECT_NAME, projects)

    if billing_enabled:
        print('TEST: Billing enabled - stop it')
        return True
    else:
        print('TEST: Billing already disabled')
    
    return False

# real deal
def stop_billing(data, context):
    pubsub_data = base64.b64decode(data['data']).decode('utf-8')
    pubsub_json = json.loads(pubsub_data)
    cost_amount = pubsub_json['costAmount']
    budget_amount = pubsub_json['budgetAmount']
    if cost_amount <= budget_amount:
        print(f'No action necessary. (Current cost: {cost_amount})')
        return

    if PROJECT_ID is None:
        print('No project specified with environment variable')
        return

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
    try:
        res = projects.getBillingInfo(name=project_name).execute()
        return res['billingEnabled']
    except KeyError:
        # If billingEnabled isn't part of the return, billing is not enabled
        return False
    except Exception:
        print('Unable to determine if billing is enabled on specified project, assuming billing is enabled')
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
    except Exception:
        print('Failed to disable billing, possibly check permissions')
        return False