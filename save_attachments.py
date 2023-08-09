import os
import base64
import datetime
import dateutil.parser
import requests
import json
import msal
import random
import string


# DO NOT FORGET TO CHANGE THESE VALUES
# Of course the below ones are not valid
TENANT_ID = '019c2xx0-c12xx0-4a6a-9be5-39ed220a5875'
CLIENT_ID = '0B0725d7-80sca-4acc-aba0-1821ea2ea4df'
CLIENT_SECRET = 'A6Q8QU234sK4pfdafEhGtsUh~z3trrQejlgjA4v'
USER_ID = '402e16f2-1f22-4e5a-c1dss9-91d924bde370'
FOLDER_NAME = 'Gesendete Elemente'
FILE_EXTENSION = '.pdf'
SAVE_PATH = '\Dokumente\Online_PDF'


AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
SCOPES = ['https://graph.microsoft.com/.default']
GRAPH_API_BASE_URL = 'https://graph.microsoft.com/v1.0/'
FOLDER_ID = ''
def authenticate():
    # Authenticate using MSAL
    app = msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY
    )
    result = app.acquire_token_silent(SCOPES, account=None)
    if not result:
        result = app.acquire_token_for_client(scopes=SCOPES)
    #print(result)
    return result['access_token']

def get_emails():
    # Get emails from specified folder within date range
    access_token = authenticate()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    #print(access_token)
    res_mailfolders = requests.get(f'{GRAPH_API_BASE_URL}users/{USER_ID}/mailFolders', headers=headers)
    #print(res_mailfolders.json())
    for folder in res_mailfolders.json().get('value'):
        if folder["displayName"] == FOLDER_NAME:
            # Return the folder ID if the folder name matches
            FOLDER_ID = folder["id"]
    
    # Calculate date range
    
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    query = f"receivedDateTime ge {today} and hasAttachments eq true"
    
    # Get emails matching query
    url_to_loop = f'{GRAPH_API_BASE_URL}users/{USER_ID}/mailFolders/{FOLDER_ID}/messages?$filter={query}'
    print(url_to_loop)
    while url_to_loop:
        response = requests.get(url_to_loop, headers=headers)
        data = response.json()
        url_to_loop = data.get('@odata.nextLink')
        #print(url_to_loop)
        emails =  response.json()['value']
        for email in emails:
            email_id = email['id']
            x = get_attachments(email)
            attachments = x[0]['value']
            received_date_str =x[1]
            
            for attachment in attachments:
                save_attachments(email_id, attachment,received_date_str)

def get_formatted_from_date_email(email):
    return email['receivedDateTime'][:-10] # remove the timezone offset from the receivedDateTime string

def save_attachments(email_id, attachment,email_date):
    # Save attachment to local directory
    random_char = random.choice(string.ascii_letters)
    
    attachment_name = attachment['name']
    attachment_content = attachment['contentBytes']
    filename_parts = os.path.splitext(attachment['name'])
    base_name = filename_parts[0]
    extension = filename_parts[1]
    attachment_name = base_name[:48] + extension

    attachment_content = attachment['contentBytes']
    attachment_data = base64.b64decode(attachment_content)
    
    #check for filename
    filename = attachment['name'].lower()
    print(filename)
    if filename.startswith('bestellbestätigung_') or filename.startswith('rechnung_'):
        attachment_path = os.path.join(SAVE_PATH, f'{attachment_name}')
        if attachment['contentType'] == f'application/{FILE_EXTENSION[1:]}':
            with open(attachment_path, 'wb') as f:
                f.write(attachment_data)

def get_attachments(email):
    access_token = authenticate()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    email_id = email['id']
    received_date_str = get_formatted_from_date_email(email)
    response = requests.get(f'{GRAPH_API_BASE_URL}users/{USER_ID}/messages/' + email_id + '/attachments', headers=headers)
    if response.status_code == 200:
        attachments = response.json()
        #print(attachments)
        #attachment_ids = [attachment['id'] for attachment in attachments]
        return attachments, received_date_str
    else:
        print('Failed to retrieve attachments.')


emails = get_emails()
