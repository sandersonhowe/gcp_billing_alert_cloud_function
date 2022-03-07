# Google Cloud Function for billing alert - slack intergration and kill switches

This should be implimentented on all gcloud projects - **NO EXCEPTIONS!**

This cloud function will:
* Post alerts into a slack channel when billing is > the billing alert threshold
* Automatically removes the Billing Account when x1.4 > the billing alert threshold - effectivly shutting it down.

*Warning: This example removes Cloud Billing from your project, shutting down all resources. Resources might not shut down gracefully, and might be irretrievably deleted. There is no graceful recovery if you disable Cloud Billing.
You can re-enable Cloud Billing, but there is no guarantee of service recovery and manual configuration is required.*

## Docs for set up and extention:
https://cloud.google.com/billing/docs/how-to/notify#test-your-cloud-function

## NOTES!

* Make sure to run it in TEST_MODE while setting up the script.

* Make sure you create a new service account for the script, becasue after a billing account has been nuked by this script, it seems to loose the service account billing assoication you need for it to work when you rejoin the billing account to the account :( So you will need to create a new one and reset up the cloud function. You can do this by running in TEST_MODE until you get a pass before turning it back on again.

* For some reason this is not in the docs above, but you need to enable the billing API here: https://console.cloud.google.com/apis/library/cloudbilling.googleapis.com?project=xxxx to allow for the bot to drop the billing assoication and do the look up for if billing is enabled
