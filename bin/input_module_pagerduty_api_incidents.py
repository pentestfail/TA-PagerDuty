
# encoding = utf-8

import os
import sys
import time
import base64
import urlparse
import json
from datetime import datetime, timedelta


def validate_input(helper, definition):
    pd_api_token = definition.parameters.get('api_token', None)
    pd_pagesize = definition.parameters.get('api_limit', None)
    pd_daysago = definition.parameters.get('days_ago', None)
    pass

def collect_events(helper, ew):
    # Retrieve runtime variables
    api_key = helper.get_arg('api_token', None)
    pd_pagesize = helper.get_arg('api_limit') or 100 #Page size of results
    pd_daysago = helper.get_arg('days_ago') or 365 #Max days ago since commit
    inputname = helper.get_input_stanza_names()
    inputsource = helper.get_input_type() + ":" + inputname
    helper.log_info("input_type=pagerduty_api_incidents input={0:s} message='Collecting events.'".format(inputname))

    # Create initial time to query for commits
    initial_status = (datetime.utcnow() - timedelta(int(pd_daysago))).strftime("%Y-%m-%d")
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Create checkpoint key
    opt_checkpoint = "pagerduty_api_incidents-{0:s}".format(inputname)
    updated = now #Add meta value for troubleshooting
    
    #Check for last query execution data in kvstore & generate if not present
    try:
        last_status = helper.get_check_point(opt_checkpoint) or initial_status
        helper.log_debug("input_type=pagerduty_api_incidents input={0:s} message='Last successful checkpoint time.' last_status={1:s}".format(inputname,json.dumps(last_status)))
    except Exception as e:
        helper.log_error("input_type=pagerduty_api_incidents input={0:s} message='Unable to retrieve last execution checkpoint!'".format(inputname))
        raise e

    # Create API request parameters
    header = {
        'Authorization': 'Token token={0}'.format(api_key),
        'Content-type': 'application/json',
        'Accept': 'application/vnd.pagerduty+json;version=2'
        }
    url = "https://api.pagerduty.com/incidents"
    method = "GET"

    def get_incidents(since, until, offset):
        params = {
            'status': "acknowledged,triggered,resolved",
            'since': since,
            'until': until,
            'offset': offset,
            'limit': pd_pagesize
        }
        r = helper.send_http_request(url, method, parameters=params, payload=None, headers=header, cookies=None, verify=True, cert=None, timeout=None, use_proxy=True)
        helper.log_info("input_type=pagerduty_api_incidents input={0:s} message='Requesting incident data from Pagerduty API.' url='{1:s}' parameters='{2:s}'".format(inputname,url,json.dumps(params)))
            
        # Return API response code
        r_status = r.status_code
        # Return API request status_code
        if r_status is 429:
            helper.log_info("input_type=pagerduty_api_incidents input={0:s} message='Too many requests, API throttled. Will retry in 10 seconds.' status_code={1:d}".format(inputname,r_status))
            time.sleep(10)
            r = helper.send_http_request(url, method, parameters=params, payload=None, headers=header, cookies=None, verify=True, cert=None, timeout=None, use_proxy=True)
        elif r_status is not 200:
            helper.log_error("input_type=pagerduty_api_incidents input={0:s} message='API request unsuccessful.' status_code={1:d}".format(inputname,r_status))
            r.raise_for_status()
        return r.json()
    
    try:
        has_results = True
        offset = 0 #iterator for records returned from Pagerduty
        i = 0 #iterator for indexed records processed
        while has_results:
            pd_incidents = get_incidents(last_status, None, offset)
            
            # Get log_entries via Pagerduty API as JSON
            incidents = pd_incidents['incidents']
            has_results = pd_incidents['more']
            
            if len(incidents) == 0:
                helper.log_info("input_type=pagerduty_api_incidents input={0:s} message='No records retrieved from Pagerduty API.' offset={1:d}".format(inputname,offset))
                has_results = False
                continue
            
            for incident in incidents:
                # Write event to index
                ew.write_event(helper.new_event(source=inputsource, index=helper.get_output_index(), sourcetype=helper.get_sourcetype(), data=json.dumps(incident)))
                i += 1
                helper.log_debug("input_type=pagerduty_api_incidents input={0:s} processed={1:d} entry_id={2:s}".format(inputname,i,incident['id']))
            
            if pd_incidents['more']:
                offset += pd_incidents['limit']
                #helper.log_debug("input_type=pagerduty_api_incidents input={0:s} message='Getting next page.' link_next='{1:s}' offset='{2:s}'".format(inputname,url,offset))
                #get_entries(since, until, offset)
            else:
                helper.log_debug("input_type=pagerduty_api_incidents input={0:s} message='No additional pages.'".format(inputname))
            
        helper.log_debug("input_type=pagerduty_api_incidents input={0:s} processed={1:d}".format(inputname,i))

        #Update last completed execution time
        helper.save_check_point(opt_checkpoint,updated)
        helper.log_info("input_type=pagerduty_api_incidents input={0:s} message='Collection complete.' indexed={1:d}".format(inputname,i))
        helper.log_debug("input_type=pagerduty_api_incidents input={0:s} message='Storing checkpoint.' updated={1:s}".format(inputname,updated))

    except Exception as error:
        helper.log_error("input_type=pagerduty_api_incidents input={0:s} message='An unknown error occurred!'".format(inputname))
        raise error
