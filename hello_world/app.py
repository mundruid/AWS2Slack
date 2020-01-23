from __future__ import print_function

import json
import boto3
import logging
import os
import datetime

from dateutil.tz import tzlocal

from urllib.request import Request, urlopen, URLError, HTTPError

# slack hook - should be changed to your webhook
HOOK_URL = "https://hooks.slack.com/services/"

# error logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# date information will be useful for our alert
# UTC
now = datetime.datetime.now()
# convert to local - not such a good idea
# now = datetime.datetime.now(tzlocal())

# formatting datetime to look pretty
format_date_time = now.strftime('%A, %B %d, %Y - %H:%M:%S')
logger.info('format_date_time = %s' % (format_date_time))

def handle_s3_event(event, event_name, bucket_name, bucket_acl):
    if(len(bucket_acl['Grants']) > 1): # assume that Group has index [1]. Can be generalizable
        grantee = bucket_acl['Grants'][1]['Grantee']['Type']
        permission = bucket_acl['Grants'][1]['Permission']
    
    # select slack message: is it a new bucket with read policy or public access / read policy for already existent bucket?
    # create new bucket with READ everyone policy
    if(event_name == "CreateBucket"):
        # new bucket was created, but did we make the bucket public? These properties should indicate that
        if(len(bucket_acl['Grants']) > 1):
            if( grantee == "Group" and (permission == "READ" or permission == "READ_ACP")):
                slack_message = {
                    'channel': "#alerts",
                    'text': "New bucket " + bucket_name + " with public access and open READ policy created @ " + format_date_time + ' UTC'
                }
        else:
            notify = False
    # existing bucket, objects can be public, not READ yet but still...
    elif(event_name == "PutBucketPublicAccessBlock"):
        # did we make the bucket public? These properties should indicate that
        # get properties that indicate public access block, no acl policy yet 
        block_public_acl = event['detail']['requestParameters']['PublicAccessBlockConfiguration']['BlockPublicAcls']
        ignore_public_acl = event['detail']['requestParameters']['PublicAccessBlockConfiguration']['IgnorePublicAcls']
        block_public_policy = event['detail']['requestParameters']['PublicAccessBlockConfiguration']['BlockPublicPolicy']
        restrict_public_buckets = event['detail']['requestParameters']['PublicAccessBlockConfiguration']['RestrictPublicBuckets']
        
        if( block_public_acl == False and ignore_public_acl == False and block_public_policy == False and restrict_public_buckets == False):
            slack_message = {
                'channel': "#alerts",
                'text': "Existing bucket " + bucket_name + " properties changed to ""objects can be public"" @ " + format_date_time + ' UTC'
            }
        else:
            notify = False
    # existing bucket, objects can be public, AND everyone can READ
    elif(event_name == "PutBucketAcl"):
        if(len(bucket_acl['Grants']) > 1):
            if( grantee == "Group" and (permission == "READ" or permission == "READ_ACP")):
                slack_message = {
                'channel': "#alerts",
                'text': "Existing bucket " + bucket_name + " properties changed to ""open READ"" policy @ " + format_date_time + ' UTC'
            }
            else:
                notify = False
        else:
            notify = False
    else:
        # no notification
        notify = False

    return (notify, slack_message)

def lambda_handler(event, context):
    
    notify = True
    s3 = boto3.client('s3')
    
    # some logging for verification
    logger.info('## ENVIRONMENT VARIABLES')
    logger.info(os.environ)
    logger.info('## EVENT')
    logger.info(event)
    
    # get eventName
    event_name = event['detail']['eventName']
    # get bucket name
    bucket_name = event['detail']['requestParameters']['bucketName']
    
    # get the backet ACL, grantee should be group, not just owner
    # policy we are checking is READ
    bucket_acl = s3.get_bucket_acl(Bucket=bucket_name)
    logger.info("## BUCKET POLICY")
    logger.info(bucket_acl)

    # function returns true or false if the event should be notified according to specifidations
    (notify, slack_message) = handle_s3_event(event, event_name, bucket_name, bucket_acl)
    
    if(notify):    
        # create request for slack
        req = Request(HOOK_URL, json.dumps(slack_message))
        # send request
        try:
            # logging success
            response = urlopen(req)
            response.read()
            logger.info("Message posted to %s", slack_message['channel'])
        except HTTPError as e:
             # logging failed HTTP request
            logger.error("Request failed: %d %s", e.code, e.reason)
        except URLError as e:
            # logging wrong request
            logger.error("Server connection failed: %s", e.reason)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }
