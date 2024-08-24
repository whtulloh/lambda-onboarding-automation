import os
import json

# COMMENTED: NOT USED IN LOCAL
# import boto3

import requests
import datetime

from datetime import datetime
from datetime import timedelta

# COMMENTED: NOT USED IN LOCAL
# from services import environment_variables, credentials, lambda_service

# COMMENTED: NOT USED IN LOCAL
# from botocore.exceptions import ClientError

class WorkforceConnector:
    def __init__(self):
        self.date          = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # COMMENTED: NOT USED IN LOCAL
        # self.env_constants = environment_variables.get_environment_variables()
        # self.region        = self.env_constants['Region']
        # self.secret_name   = "onboarding-config"


    def get_secret(self):
        # COMMENTED: NOT USED IN LOCAL
        # Create a Secrets Manager client
        # session = boto3.session.Session()
        # client = session.client(service_name='secretsmanager', region_name=self.region)
    
        # try:
        #     get_secret_value_response = client.get_secret_value(SecretId=self.secret_name)
        #     secret = ""
        #     if get_secret_value_response:
        #         secret = get_secret_value_response['SecretString']
        #         self.print_log("INFO", "Secret Config is Ready")
        #     else:
        #         self.print_log("ERROR", "Secret Config Empty")
            
        #     # Decrypts secret using the associated KMS key.
        #     return json.loads(secret)
        # except ClientError as error:
        #     self.print_log("ERROR", "Secret Config: "+error)

        with open(os.path.join('secret_manager.json'), 'rb') as jsonfile:
            secrets = json.load(jsonfile)

        return secrets
 

    def set_scope(self,target_system):
        aws_secrets = self.get_secret()
        self.workforce_hostname   = aws_secrets[target_system+"-hostname"]
        self.workforce_username   = aws_secrets[target_system+"-username"]
        self.workforce_password   = aws_secrets[target_system+"-password"]
        self.workforce_datasource = aws_secrets[target_system+"-datasource"]
        self.workforce_extension = aws_secrets[target_system+"-extension"]


    def get_secret_data_source(self):
        return self.workforce_datasource
        

    def get_secret_extension(self):
        return self.workforce_extension
        

    def set_token(self, token):
        self.token = token


    def get_token(self):
        try:
            url = self.workforce_hostname+'/workforce/rest/core-api/auth/token'
            
            headers = {
                'Accept': '*/*',
                'Content-Type': 'application/json'
            }

            data = {
                'user': self.workforce_username,
                'password': self.workforce_password
            }

            response = requests.post(url=url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                self.print_log("INFO", "Auth Token Generated")
                return response.json().get("AuthToken").get("token")
            else:   
                self.print_log("ERROR", "Auth Token from API: "+response.text)
                return {}
        except requests.exceptions.RequestException as e:
            self.print_log("ERROR", "Exception_Auth Token: "+e)
            return {}
    
    
    def get_users(self):
        try:
            url = self.workforce_hostname+'/workforce/user-mgmt-api/v1/employees'
            headers = {
                'Content-type': 'application/json',
                'Impact360AuthToken': self.token
            }

            response = requests.get(url=url, headers=headers)
            if response.status_code == 200:
                self.print_log("INFO", "Employee from API is Ready")
                return response.json()
            else:
                self.print_log("ERROR", "Employee from API: "+response.text)
                return {}
        except requests.exceptions.RequestException as e:
            self.print_log("ERROR", "Exception_Employee: "+e)
            return {}


    def get_data_sources(self):
        try:
            url = self.workforce_hostname+'/api/workforce/v2/datasources'
            headers = {
                'Content-type': 'application/json',
                'Impact360AuthToken': self.token
            }

            response = requests.get(url=url, headers=headers)
            if response.status_code == 200:
                self.print_log("INFO", "Datasource from API is Ready")
                return response.json()
            else:
                self.print_log("ERROR", "Datasource from API: "+response.text)
                return {}
        except requests.exceptions.RequestException as e:
            self.print_log("ERROR", "Exception_Datasource: "+e)
            return {}
            
        
    def get_datasource_by_name(self, datasource_name):
        try:
            url = self.workforce_hostname+'/api/workforce/v2/datasources?name='+datasource_name
            headers = {
                'Content-type': 'application/json',
                'Impact360AuthToken': self.token
            }
            
            response = requests.get(url=url, headers=headers)
            if (response.status_code == 200): 
                dtsId = json.loads(response.text)
                return dtsId["data"][0]["id"]
            else:
                self.print_log("ERROR", "Datasource by Name from API: "+response.text)
                return ""
        except requests.exceptions.RequestException as e:
            self.print_log("ERROR", "Exception_Datasource by Name: "+e)
            return ""


    def get_data_source_by_employee_id(self, employeeId):
        try:
            url = self.workforce_hostname+'workforce/user-mgmt-api/v1/employees/'+employeeId+'/workspace'
            headers = {
                'Content-type': 'application/vnd.api+json',
                'Accept': 'application/vnd.api+json',
                'Impact360AuthToken': self.token
            }

            response = requests.get(url=url, headers=headers)
            if response.status_code == 200:
                self.print_log("INFO", "Datasource by Employee "+employeeId+" from API is Ready")
                return response.json()
            else:
                self.print_log("ERROR", "Datasource by Employee "+employeeId+" from API: "+response.text)
                return {}
        except requests.exceptions.RequestException as e:
            self.print_log("ERROR", "Exception_Datasource by Employee: "+e)
            return {}


    def create_datasource(self, datasourceName, employeeId, email, template):
        try:
            url = self.workforce_hostname+'workforce/user-mgmt-api/v1/employees/'+employeeId+'/workspace'
            headers = {
                'Content-type': 'application/vnd.api+json',
                'Accept': 'application/vnd.api+json',
                'Impact360AuthToken': self.token
            }

            response = requests.post(url=url, data=json.dumps(template), headers=headers)
            if response.status_code == 201:
                self.print_log("INFO", "Datasource " +datasourceName+ " for employee " +email+ " is Assigned")
                return True
            else:
                self.print_log("ERROR", "Datasource failed to set: "+response.text)
                return False
        except requests.exceptions.RequestException as e:
            self.print_log("ERROR", "Exception_Datasource: "+e)
            return False


    def manual_sam_account(self, email):
        username = email.strip().split("@")[0]
        firstLetter = username.split(".")[0]
        if "dev" in firstLetter.lower():
            firstLetter = firstLetter.split("-")[1][0]
        else:
            firstLetter = firstLetter[0]
       
        self.print_log("INFO", "Manual Sam Account name "+firstLetter+username.split(".")[1])
        return firstLetter+username.split(".")[1]
        
        
    def manual_avd_account(self, email):
        emailsplit = email.split("@")
        avdUsername = ""
        if emailsplit[1].lower() == "email.corp":
            nameSplit = emailsplit[0].lower().split(".")
            frontName = nameSplit[0]
            backName = nameSplit[1]
            avdUsername = frontName + backName
       
        self.print_log("INFO", "Manual AVD Account name "+avdUsername)
        return avdUsername
 

    def update_desktop_messaging_username(self, email, employeeId, template):
        try:
            url = self.workforce_hostname+'/workforce/user-mgmt-api/v1/employees'
            headers = {
                'Content-type': 'application/json',
                'Impact360AuthToken': self.token
            }

            response = requests.put(url=url, data=json.dumps(template), headers=headers)
            if response.status_code == 204:
                self.print_log("INFO", "Desktop Messaging Username " +email+ " for employee " +str(employeeId)+ " is Assigned")
                return True
            else:
                self.print_log("ERROR", "Desktop Messaging Username failed to set: "+response.text)
                return False
        except requests.exceptions.RequestException as e:
            self.print_log("ERROR", "Exception_Desktop Messaging Username: "+e)
            return False
        
        
    def get_all_organization(self):
        try:
            url = self.workforce_hostname+'workforce/user-mgmt-api/v1/organizations?sort=-id'
            headers = {
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'Impact360AuthToken': self.token
            }

            response = requests.get(url=url, headers=headers)
            if response.status_code == 200:
                self.print_log("INFO", "Retrieved Organization: Success")
                return response.json()
            else:
                self.print_log("ERROR", "Retrieved Organization: Failed - "+response.text)
                return {}
        except requests.exceptions.RequestException as e:
            self.print_log("ERROR", "Exception_Datasource failed to set: "+e)
            return {}
            
            
    def assign_employee_to_organization(self, organizationId, organizationName, email, template):
        try:
            url = self.workforce_hostname+'workforce/user-mgmt-api/v1/organizations/'+ str(organizationId) +'/employees'
            headers = {
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'Impact360AuthToken': self.token
            }

            response = requests.put(url=url, data=json.dumps(template), headers=headers)
            if response.status_code == 204:
                self.print_log("INFO", "Organization Assignment to Employee " + email + " has been assigned: "+ organizationName)
                return True
            elif response.status_code == 409:
                self.print_log("INFO", "Organization Assignment to Employee " + email + " already assigned to: "+ organizationName + ". Nothing changed!!")
                return True
            else:
                self.print_log("ERROR", "Organization Assignment " + email + " failed to set. Response code: " + str(response.status_code))
                return False
        except requests.exceptions.RequestException as e:
            self.print_log("ERROR", "Exception_Organization Employee Assignment: "+e)
            return False
            
    
    def check_extension(self, dsId, extensionId, email):
        try:
            url = self.workforce_hostname+'/api/workforce/v2/datasources/'+dsId+'/extensions?extensionValue='+extensionId
            headers = {
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'Impact360AuthToken': self.token
            }
            
            result = requests.get(url, headers=headers)
            if (result.status_code == 200): 
                extension = result.json()
                if extension["details"]:
                    if "employee" in extension["details"][0]:
                        self.print_log("INFO", "Check Extension "+extensionId+" has been associated with employee")
                        return "Not Allowed"
                    else:
                        self.print_log("INFO", "Check Extension "+extensionId+" ready to be associated")
                        return "UPDATE"
                else:
                    self.print_log("INFO", "Check Extension "+extensionId+" not created yet.")
                    return "CREATE"
            else:
                self.print_log("ERROR", "Check Extension for "+email+": Failed - "+result.text)
        except requests.exceptions.RequestException as e:
            self.print_log("ERROR", "Exception_Check Extension: "+e)
            return ""
            

    def assign_extension(self, dsId, template, email):
        try:
            headers = {"Content-type": "application/json","Impact360AuthToken":""+self.token}
            result = requests.post(self.workforce_hostname+'/api/workforce/v2/datasources/'+dsId+'/extension', data=json.dumps(template), headers=headers)
            
            if (result.status_code == 201): 
                self.print_log("INFO","Extension Assignment for "+email+" success")
            else:
                self.print_log("ERROR", "Extension Assignment failed: " + result.text)
        except requests.exceptions.RequestException as e:
            self.print_log("ERROR", "Exception_Extension Assignment: "+e)
            return False
            
    
    def update_extension(self, dsId, template, email):
        try:
            headers = {"Content-type": "application/json","Impact360AuthToken":""+self.token}
            result = requests.put(self.workforce_hostname+'/api/workforce/v2/datasources/'+dsId+'/extension', data=json.dumps(template), headers=headers)
            
            if (result.status_code == 200): 
                self.print_log("INFO","Extension Update for "+email+" success")
            else:
                self.print_log("ERROR", "Extension Update failed: " + result.text)
        except requests.exceptions.RequestException as e:
            self.print_log("ERROR", "Exception_Extension Update: "+e)
            return False
            
    
    def open_template(self, datasourceId, datasourceName, employeeId, datasourceLogin):
        with open(os.path.join('template/datasource.json'), 'rb') as jsonfile:
            template = json.load(jsonfile)
            
        # Replace place holder
        template = json.loads(json.dumps(template).replace('"DATASOURCE_ID"', '"'+datasourceId+'"'))
        template = json.loads(json.dumps(template).replace('"DATASOURCE_EMPLOYEEID"', '"'+employeeId+'"'))
        template = json.loads(json.dumps(template).replace('"DATASOURCE_LOGINNAME"', '"'+datasourceLogin+'"'))
        self.print_log("INFO", "Datasource "+datasourceName+" template is Ready for "+datasourceLogin)
        
        return template
 

    def open_template_two(self, datasourceId, datasourceName, employeeId, datasourceLogin):
        with open(os.path.join('template/datasource_two.json'), 'rb') as jsonfile:
            template = json.load(jsonfile)
        
        dsLogin = datasourceLogin.split(',')
        
        # Replace place holder
        template = json.loads(json.dumps(template).replace('"DATASOURCE_ID"', '"'+datasourceId+'"'))
        template = json.loads(json.dumps(template).replace('"DATASOURCE_EMPLOYEEID"', '"'+employeeId+'"'))
        template = json.loads(json.dumps(template).replace('"DATASOURCE_LOGINNAME_0"', '"'+dsLogin[0]+'"'))
        template = json.loads(json.dumps(template).replace('"DATASOURCE_LOGINNAME_1"', '"'+dsLogin[1]+'"'))
        self.print_log("INFO", "Datasource "+datasourceName+" template is Ready for "+datasourceLogin)
        
        return template
    
    
    def open_template_three(self, datasourceId, datasourceName, employeeId, datasourceLogin):
        with open(os.path.join('template/datasource_three.json'), 'rb') as jsonfile:
            template = json.load(jsonfile)
        
        dsLogin = datasourceLogin.split(',')
        
        # Replace place holder
        template = json.loads(json.dumps(template).replace('"DATASOURCE_ID"', '"'+datasourceId+'"'))
        template = json.loads(json.dumps(template).replace('"DATASOURCE_EMPLOYEEID"', '"'+employeeId+'"'))
        template = json.loads(json.dumps(template).replace('"DATASOURCE_LOGINNAME_0"', '"'+dsLogin[0]+'"'))
        template = json.loads(json.dumps(template).replace('"DATASOURCE_LOGINNAME_1"', '"'+dsLogin[1]+'"'))
        template = json.loads(json.dumps(template).replace('"DATASOURCE_LOGINNAME_2"', '"'+dsLogin[2]+'"'))
        self.print_log("INFO", "Datasource "+datasourceName+" template is Ready for "+datasourceLogin)
        
        return template


    def open_template_user_dmu(self, employeeID, email, firstName, lastName, organizationId):
        with open(os.path.join('template/user_dmu.json'), 'rb') as jsonfile:
            template = json.load(jsonfile)
        
        # Replace place holder
        template = json.loads(json.dumps(template).replace('"EMPLOYEE_ID"', '"'+employeeID+'"'))
        template = json.loads(json.dumps(template).replace('"EMPLOYEE_DMU"', '"'+email+'"'))
        template = json.loads(json.dumps(template).replace('"EMPLOYEE_FIRSTNAME"', '"'+firstName+'"'))
        template = json.loads(json.dumps(template).replace('"EMPLOYEE_LASTNAME"', '"'+lastName+'"'))
        template = json.loads(json.dumps(template).replace('"ORG_ID"', '"'+str(organizationId)+'"'))
        self.print_log("INFO", "Desktop Messaging Username "+email+" template is Ready")
        
        return template
            
            
    def open_template_employee_organization(self, employeeID, organizationName):
        with open(os.path.join('template/employee_org.json'), 'rb') as jsonfile:
            template = json.load(jsonfile)
        
        # Replace place holder
        template = json.loads(json.dumps(template).replace('"EMPLOYEE_ID"', '"'+employeeID+'"'))
        self.print_log("INFO", "Organization "+organizationName+" template is Ready")
        
        return template 
            
            
    def open_template_extension(self, datasourceId, datasourceName, employeeId, extension):
        with open(os.path.join('template/extension.json'), 'rb') as jsonfile:
            template = json.load(jsonfile)
            
        # Replace place holder
        template = json.loads(json.dumps(template).replace('"EMPLOYEEID"', '"'+employeeId+'"'))
        template = json.loads(json.dumps(template).replace('"EXTENSION"', '"'+extension+'"'))
        self.print_log("INFO", "Extension "+datasourceName+" template is Ready for "+extension)
        
        return template
        

    def print_log(self, type, message):
        print(">> {}::{}::{}".format(self.date, type, message))