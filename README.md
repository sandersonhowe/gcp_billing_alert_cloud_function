# Google Cloud Function for billing alert - slack intergration and kill switches

This should be implimentented on all gcloud projects - **NO EXCEPTIONS!**

This cloud function will:
* Post alerts into a slack channel when billing is > the billing alert threshold
* Automatically removes the Billing Account when x1.4 > the billing alert threshold - effectivly shutting it down.

*Warning: This example removes Cloud Billing from your project, shutting down all resources. Resources might not shut down gracefully, and might be irretrievably deleted. There is no graceful recovery if you disable Cloud Billing.
You can re-enable Cloud Billing, but there is no guarantee of service recovery and manual configuration is required.*

## Docs for set up and extention:
https://cloud.google.com/billing/docs/how-to/notify#test-your-cloud-function
