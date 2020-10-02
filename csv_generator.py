import pandas as pd
from datetime import datetime, timedelta
import requests
 
url = 'https://api.cloudflare.com/client/v4/graphql/'
# Customize these variables
file_dir = ''  # Must include trailing slash, if left blank csv will be created in current directory
api_email = '[your email here]'
api_key = '[your API key here]'
api_account = '[your account ID here]'
# Setting most recent day as yesterday
offset_days = 1
# How many days worth of data do we want? By default 7.
historical_days = 7

 
 
def get_date(num_days):
    today = datetime.utcnow().date()
    return today - timedelta(days=num_days)
 
 
def get_cf_graphql():
    headers = {'content-type': 'application/json', 'X-Auth-Email': api_email, 'X-Auth-Key': api_key}
    # This variable replacement requires python3.6 or higher
    payload = f'''{{"query":
        "query ipFlowEventLog($accountTag: string, $filter: AccountIpFlows1mAttacksGroupsFilter_InputObject) {{viewer {{accounts(filter: {{ accountTag: $accountTag }}) {{ipFlows1mAttacksGroups(limit: 10000, filter: $filter, orderBy: [min_datetimeMinute_ASC]) {{dimensions {{attackId, attackDestinationIP, attackDestinationPort, attackMitigationType, attackSourcePort, attackType}}, avg {{bitsPerSecond, packetsPerSecond}}, min {{datetimeMinute, bitsPerSecond, packetsPerSecond}}, max {{datetimeMinute, bitsPerSecond, packetsPerSecond}}, sum {{bits, packets}}}}}}}}}}",
         "variables": {{
         "accountTag":"{api_account}",
         "filter": {{"AND":[{{"date_geq":"{min_date}"}},{{"date_leq": "{max_date}"}}]}}}}}}'''

    r = requests.post(url, data=payload, headers=headers)
    return r.text
 
 
def convert_to_csv():
    # Parse JSON response in Pandas
    network_analytics = pd.read_json(raw_data)['data']['viewer']['accounts']
    # Flatten nested JSON data first
    network_analytics_normalized = pd.json_normalize(network_analytics, 'ipFlows1mAttacksGroups')
    # Only select the columns we're interested in
    network_analytics_abridged = network_analytics_normalized[['dimensions.attackId','min.datetimeMinute','max.datetimeMinute','dimensions.attackMitigationType', 'dimensions.attackType','dimensions.attackDestinationIP','max.packetsPerSecond']] # Selecting only the data we want
    # Rename the columns to visually friendly names
    network_analytics_abridged.columns = ['Attack ID','Start date/time', 'End date/time', 'Action taken', 'Attack type', 'Destination IP', 'Max packets/second'] #Renaming columns
    network_analytics_abridged.to_csv("{}network-analytics-{}.csv".format(file_dir,min_date))
 
max_date = get_date(offset_days)
min_date = get_date(historical_days)
 
raw_data = get_cf_graphql()
convert_to_csv()