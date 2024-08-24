import os
import msal
import json

# COMMENTED: NOT USED IN LOCAL
# import boto3

import requests
import datetime

from datetime import datetime
from datetime import timedelta

# COMMENTED: NOT USED IN LOCAL
# from botocore.exceptions import ClientError

class GraphConnector:
    def __init__(self):
        self.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    
    def get_secret(self):
        # COMMENTED: NOT USED IN LOCAL
        # secret_name = "innovation_lab_environment_variables"
        # region_name = "us-east-2"
    
        # # Create a Secrets Manager client
        # session = boto3.session.Session()
        # client = session.client(service_name='secretsmanager', region_name=region_name)
    
        # try:
        #     get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        #     secret = ""
        #     if get_secret_value_response:
        #         secret = get_secret_value_response['SecretString']
        #         self.print_log("INFO", "MS Graph Secret Config is Ready")
        #     else:
        #         self.print_log("ERROR", "MS Graph Secret Config Empty")
            
        #     # Decrypts secret using the associated KMS key.
        #     return json.loads(secret)
        # except ClientError as error:
        #     self.print_log("ERROR", "MS Graph Secret Config: "+error)
        
        with open(os.path.join('secret_manager.json'), 'rb') as jsonfile:
            secrets = json.load(jsonfile)

        return secrets


    def set_ms_graph_scope(self):
        aws_secrets = self.get_secret()
        self.clientId = aws_secrets['Graph_Client_ID']
        self.clientSecret = aws_secrets['Graph_Client_Secret']
        self.tenantId = aws_secrets['Graph_Tenant_ID']


    def get_ms_graph_token(self):
        GRAPH_CLIENT_ID = self.clientId
        GRAPH_CLIENT_SECRET = self.clientSecret
        GRAPH_TENANT_ID = self.tenantId
        GRAPH_AUTHORITY = 'https://login.microsoftonline.com/'+GRAPH_TENANT_ID
        GRAPH_SCOPE = ['https://graph.microsoft.com/.default']

        # Create an MSAL instance providing the client_id, authority and client_credential parameters
        client = msal.ConfidentialClientApplication(GRAPH_CLIENT_ID, authority=GRAPH_AUTHORITY, client_credential=GRAPH_CLIENT_SECRET)

        # First, try to lookup an access token in cache
        token_result = client.acquire_token_silent(GRAPH_SCOPE, account=None)

        # If the token is not available in cache, acquire a new one from Azure AD and save it to a variable
        if not token_result:
            token_result = client.acquire_token_for_client(scopes=GRAPH_SCOPE)
        
        self.print_log("INFO", "MS Graph token is ready")
        return token_result['access_token']


    def get_users_by_email_to_samaccount(self, email):
        graph_token = self.get_ms_graph_token()

        try:
            access_token = 'Bearer ' + graph_token
            url = 'https://graph.microsoft.com/v1.0/users/'+email+'?$select=Id,DisplayName,UserPrincipalName,mail,AccountEnabled,onPremisesSamAccountName'
            headers = {
                'Authorization': access_token,
                'Accept': 'application/json; odata.metadata=none'
            }

            response = requests.get(url=url, headers=headers)
            if response.status_code == 200:
                # Simplify to return only SAM Account Name
                vSamAccount = response.json().get("onPremisesSamAccountName")
                self.print_log("INFO", "MS Graph Get User By Email return: "+vSamAccount)
                return vSamAccount
            else:
                self.print_log("INFO", "MS Graph Get User By Email return: none")
                return {}
        except requests.exceptions.RequestException as e:
            self.print_log("ERROR", "MS Graph Get User By Email Error: "+e)


    def switch_corp_to_email(self, email):
        username = email.strip().split("@")[0]
        if "dev" in username.lower():
            firstLetter = username.lower().split("dev-")[1]
            email2 = firstLetter+'@email.com'
        else:
            email2 = username+'@email.com'
       
        self.print_log("INFO", "MS Graph Swith corp to email manual for "+email)
        return email2


    def print_log(self, type, message):
        print(">> {}::{}::{}".format(self.date, type, message))