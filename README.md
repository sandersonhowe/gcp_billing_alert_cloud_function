# Google Cloud Function for slack billing alert and optional kill switch
This fuction extends on the function coded provided by google here: https://cloud.google.com/billing/docs/how-to/notify

# What it does
Monitors your billing alerts and posts warnings to Slack when you breach these thresholds.
Optionallay locks down your GCP account if you go over a set threshold, effectivly trying to save you from billing run aways.

## Warning!
If you use the kill switch, this script will remove the associated Cloud Billing from your project, therefor shutting down all paid resources. Resources might not shut down gracefully, and might be irretrievably deleted. There is no graceful recovery if you disable Cloud Billing.
You can re-enable Cloud Billing, but there is no guarantee of service recovery and manual configuration is required.*
# Quotas
We where going to set up a quotas script, but at the time of writing this, the quotas API was still quite Alpha and it's quicker to just set up it in the gui, I strongly suggest you start there by:

1. Open your GCP console and make sure your in the right project
2. Search for “quotas” in the search bar
3. Select “All quotas”
4. Search for any item that has “Unlimited” set in the “limit” column and change them to something more cost effective.

## Set up
You will need a billing monitor in place, a slack bot and a cloud function.

### Billing monitor

1. Search for “billing” in the search bar or select it from the menu on the left hand side
2. Select ‘Budgets and alerts’ from the menu on the left hand side
3. Click on ‘Create budget’
4. Give it a name, fill in the details (we used a monthly budget of $100) and then set it to email the admins and users - which will then send an email notification when your account hits thresholds of 50%, 90% and 100% respectively.

### Set up a Slack bot
Docs: https://cloud.google.com/billing/docs/how-to/notify#send_notifications_to_slack

### Cloud fucntion
Docs: https://cloud.google.com/billing/docs/how-to/notify#cap_disable_billing_to_stop_usage

**Note:** You need to enable the billing API here: https://console.cloud.google.com/apis/library/cloudbilling.googleapis.com?project=xxxx to allow for the bot to drop the billing assoication and do the look up for if billing is enabled.

**Note:** Make sure you create a new service account for the script, becasue after a billing account has been nuked by this script, it seems to loose the service account billing assoication you need for it to work when you rejoin the billing account to the account :( So you will need to create a new one and reset up the cloud function. You can do this by running in TEST_MODE until you get a pass before turning it back on again.

### Testing permissions
Run it in TEST_MODE while setting up the script to test if your kill script will work with out killing your billing account.

# Provided as is, use at your own risk
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.