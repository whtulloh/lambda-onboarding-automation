import os
import json
import office365

# COMMENTED: NOT USED IN LOCAL
# import boto3

import datetime

from datetime import datetime
from datetime import timedelta

from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.listitems.listitem import ListItem

# COMMENTED: NOT USED IN LOCAL
# from botocore.exceptions import ClientError

class SharePointConnector:
    def __init__(self):
        self.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.items = ""
        self.employee_id = ""


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
        #         self.print_log("INFO", "SharePoint Secret Config is Ready")
        #     else:
        #         self.print_log("ERROR", "SharePoint Secret Config Empty")
            
        #     # Decrypts secret using the associated KMS key.
        #     return json.loads(secret)
        # except ClientError as error:
        #     self.print_log("ERROR", "SharePoint Secret Config: "+error)

        with open(os.path.join('secret_manager.json'), 'rb') as jsonfile:
            secrets = json.load(jsonfile)

        return secrets


    def get_user(self, employee_id):
        firstName = employee_id.split('.')[0]
        lastName = employee_id.split('.')[1]
        
        sharepoint_site_url= 'https://sharepoint.com/sites/Lab/ManageUsers/'
        list_title = "SharedUsers"
        
        aws_secrets = self.get_secret()
        client_id = aws_secrets['spo_client_id']
        client_secret = aws_secrets['spo_client_secret']
        
        client_credentials = ClientCredential(client_id,client_secret)    
        ctx = ClientContext(sharepoint_site_url).with_credentials(client_credentials)
        list_items = ctx.web.lists.get_by_title(list_title)
        
        include_fields = ["Title","LastName","UserName","AccountNumber","User/Title","User/UserName","UserRegion"]
        expand_fields = ["User"]
        filter_text = "Title eq %27"+ firstName +"%27 and LastName eq %27"+ lastName +"%27"
        self.print_log("INFO", "SharePoint filter: "+filter_text)
        
        # sample query:
        # https://sharepoint.com/sites/Lab/ManageUsers/_api/Web/lists/GetByTitle('SharedUsers')/items?$select=Title,LastName,UserName,User/Title,User/UserName&$expand=User&$filter=Title%20eq%20%27Wahyu%27%20and%20LastName%20eq%20%27Hidayatulloh%27
        self.items = list_items.items.select(include_fields).expand(expand_fields).filter(filter_text).get().execute_query()
        self.employee_id = employee_id

    def retrieveAccNo(self):
        accNo=""
        for index, item in enumerate(self.items):  # type: int, ListItem
            accNo = item.properties['AccountNumber']
        
        if accNo:
            self.print_log("INFO", "AccountNumber for "+self.employee_id+" is "+accNo)
            return accNo
        else:
            self.print_log("WARNING", "AccountNumber for "+self.employee_id+" not found")
            return ""

    def retrieveUsername(self):
        username = ""
        for index, item in enumerate(self.items):  # type: int, ListItem
            # self.print_log("LOGGING", item.properties)
            username = item.properties['User']['UserName']
        
        if username:
            self.print_log("INFO", "UserName for "+self.employee_id+" is "+username)
            return username
        else:
            self.print_log("WARNING", "UserName for "+self.employee_id+" not found")
            return ""
            
            
    def retrieveRegion(self):
        userRegion = ""
        for index, item in enumerate(self.items):  # type: int, ListItem
            userRegion = item.properties['UserRegion']
            
        if userRegion:
            self.print_log("INFO", "UserRegion for "+self.employee_id+" is "+userRegion)
            return userRegion
        else:
            self.print_log("WARNING", "UserRegion for "+self.employee_id+" not found")
            return ""


    def print_log(self, type, message):
        print(">> {}::{}::{}".format(self.date, type, message))