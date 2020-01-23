#AWS2Slack

FILES INCLUDED:
===============
1. lambda_function.py:
	* Checks s3 event with handle_s3_event(event_name, bucket_name, bucket_acl) 
	* If there should be a notification, it sends the proper message to slack using hardcoded HOOK_URL
	* sends appropriate message to slack that includes bucket name, what happened (new bucket with public read, old bucket change of policy), and the date in UTC.
2. aws-to-slack-python.yaml
	* SAM file generated from aws
	* new stack uploads lambda and event triggers to cloudformation
3. cf_s3_create_template.yaml
	* automated new s3 bucket creation with public read

HOW TO DEPLOY:
===============
1. Create a slack webhook (https://api.slack.com/messaging/webhooks)
2. Edit lambda_function.py. Replace HOOK_URL variable with your slack webhook. 
3. Zip lambda_function.py
4. Create an s3 bucket edu.test43
5. Upload lambda_function.py.zip
6. Make lambda_function.py.zip publicly readable
7. Create a new stack using Cloudformation and aws-to-slack-python.yaml

HOW TO TEST:
============
Test 1: New bucket with public read policy
++++++++++++++++++++++++++++++++++++++++++
	1. Create a new stack using Cloudformation and cf_s3_create_template.yaml
	2. You should see a descriptive message on your webhook assigned channel.
Test2: Already existing bucket change policy to read
++++++++++++++++++++++++++++++++++++++++++++++++++++
	1. Create a new bucket without public read
	2. Change block to all public
	3. Go to Access policies, group, and change this to READ
	4. You will see a descriptive message on your webhook assigned channel.
