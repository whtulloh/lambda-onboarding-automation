import json
import datetime

from datetime import datetime
from datetime import timedelta

# COMMENTED: NOT USED IN LOCAL
# from services import environment_variables, credentials, lambda_service

from connector.sharePointConnector import SharePointConnector
from connector.graphConnector import GraphConnector
from connector.wfeConnector import WfeConnector

# COMMENTED: NOT USED IN LOCAL
# ENV_CONSTANTS = environment_variables.get_environment_variables()
# REGION        = ENV_CONSTANTS['Region']

def lambda_handler(event):
    email = event["email"]
    employee_id = event["employee_id"]
    target_system = event["target_system"]
    
    # Graph Connection
    graphConn = GraphConnector()
    graphConn.set_ms_graph_scope()
    
    # SharePoint Connection
    spConn = SharePointConnector()
    spConn.get_user(employee_id)
    accEmail = spConn.retrieveUsername()
    userRegion = spConn.retrieveRegion()
    accountNumber = spConn.retrieveAccNo()
    
    if accEmail:
        accUser = graphConn.get_users_by_email_to_samaccount(accEmail)
    else:
        accEmail = graphConn.switch_corp_to_email(email) # try to switch email manually
        accUser = graphConn.get_users_by_email_to_samaccount(accEmail)
        
    if not accUser:
        accEmail = ""
        accUser = ""
        print_log("WARNING", "Can't found Email, even after doing manual")
    
    # WFE Connection
    wfeConn = WfeConnector()
    wfeConn.set_wfe_scope(target_system)
    wfeToken = wfeConn.set_token(wfeConn.get_token())
    
    employee = isEmployeeExistInAPI(wfeConn, email)
    allDatasourceFromAPI = wfeConn.get_data_sources()
    
    if employee:
        configDataSources(event, wfeConn, employee, accEmail, accUser, allDatasourceFromAPI)
        updateDekstopMessagingUsername(event, wfeConn, employee)
        assignUserToOrganization(wfeConn, employee, userRegion, email, accEmail)
        updateUserExtension(wfeConn,accountNumber,employee, email)

        # COMMENTED: NOT USED IN LOCAL
        # sendNotification(event)
        
        status = 200
        message = "Employee on boarding done."
    else:
        status = 404
        message = "Error!! Employee not found. Make sure Employee is Exist"

    return {
        'status': status,
        'messages': message
    }
    
    
# Check is Employee exist in API
def isEmployeeExistInAPI(wfeConn, email):
    wfeUsers = wfeConn.get_users()
    isEmployeeFromAPI = [x for x in wfeUsers.get("data") if x.get("attributes").get("person").get("contact").get("email") == email]
    
    if isEmployeeFromAPI:
        employee = isEmployeeFromAPI.pop()
        print_log("INFO", "Employee ID: "+employee["id"] +", email: "+ employee["attributes"]["person"]["contact"]["email"])
        return employee
    else:
        print_log("ERROR","Employee Not Found: "+email)
        return ""
 
        
# Config Datasource for Employee
def configDataSources(event, wfeConn, employee, accEmail, accUser, allDatasourceFromAPI):
    sources = wfeConn.get_secret_data_source().split(',')
    
    datasources = []
    for src in sources:
        source = src.strip()
        # Find datasource in allDatasourceFromAPI that contains sources
        isSourceFromAPI = [x for x in allDatasourceFromAPI["data"] if x["attributes"]["name"] == source]
        if isSourceFromAPI:
            datasources.append({"source_id" : isSourceFromAPI.pop()["id"], "source_name" : source})
        else:
            print_log("ERROR", "Datasource "+source+" not found from API")
            
    # Check in API Get All Data Source from Employee (by Id)
    sourceEmployeeFromAPI = wfeConn.get_data_source_by_employee_id(employee["id"])
    
    for datasource in datasources:
        # Find data source in sourceEmployeeFromAPI with contains datasource
        isSourceEmployeeAPI = [x for x in sourceEmployeeFromAPI["data"]["attributes"]["assets"] if str(x["dataSourceID"]) == datasource["source_id"]]
        if not isSourceEmployeeAPI:
            # set datasource login and create datasource
            template = setDatasourceLoginTemplate(event, wfeConn, datasource["source_id"], datasource["source_name"], employee["id"], accEmail, accUser)
            createDS = wfeConn.create_datasource(datasource["source_name"], employee["id"], event["email"], template)
        else:
            print_log("INFO", "Datasource " +datasource["source_name"]+ " for employee " +event["email"]+ " is already Assigned")
 
    
# set datasource login and create datasource
def setDatasourceLoginTemplate(event, wfeConn, datasourceId, datasourceName, employeeId, accEmail, accUser):
    if "DPA" == datasourceName[:3]: # Condition for only DPA Datasource
        if event["employee_id"] == accUser:
            datasourceLogin = event["employee_id"]+','+accEmail
            template = wfeConn.open_template_two(datasourceId, datasourceName, employeeId, datasourceLogin)
        else:
            datasourceLogin = event["employee_id"]+','+accEmail+','+accUser
            template = wfeConn.open_template_three(datasourceId, datasourceName, employeeId, datasourceLogin)
    elif "TextRecording_854192" == datasourceName: # Condition for only TextRecording_854192 Datasource
        datasourceLogin = event["email"] 
        template = wfeConn.open_template(datasourceId, datasourceName, employeeId, datasourceLogin)
    elif "Text" == datasourceName[:4]: # Condition for only Text Datasource except TextRecording_854192
        manualSamaccount = wfeConn.manual_sam_account(event["email"])
        datasourceLogin = event["email"]+','+manualSamaccount
        template = wfeConn.open_template_two(datasourceId, datasourceName, employeeId, datasourceLogin)
    elif "AVD Desktops" == datasourceName: # Condition for only AVD Desktops Datasource
        datasourceLogin = wfeConn.manual_avd_account(event["email"])
        template = wfeConn.open_template(datasourceId, datasourceName, employeeId, datasourceLogin)

    else: # Condition default
        datasourceLogin = event["username"] 
        template = wfeConn.open_template(datasourceId, datasourceName, employeeId, datasourceLogin)

    return template


# Update Dekstop Messaging Username
def updateDekstopMessagingUsername(event, wfeConn, employee):
    employeeID = employee["id"]
    email = employee["attributes"]["person"]["contact"]["email"]
    firstName = employee["attributes"]["person"]["firstName"]
    lastName = employee["attributes"]["person"]["lastName"]
    organizationId = employee["attributes"]["organizationId"]

    if email:
        emailsplit=email.split("@")
        if emailsplit[1].lower() == "email.corp":
            desktopMessagingUsername = employee["attributes"]["person"]["contact"]["desktopMessagingUsername"]
            if not desktopMessagingUsername:
                # set template and send update
                template = wfeConn.open_template_user_dmu(employeeID, email, firstName, lastName, organizationId)
                updateDmu = wfeConn.update_desktop_messaging_username(email, employeeID, template)
            else:
                print_log("INFO", "Desktop Messaging Username is already Assigned")
        else:
            print_log("ERROR", "Desktop Messaging Username "+email+" not in email.corp") 
    else:
        print_log("ERROR", "Desktop Messaging Username "+email+" not found") 


#Get Organization Id by Organization Name with format: "Enterprise Users - {{Region}}"
def getOrganizationIdByRegion(organizations, userRegion, email):
    filterUserOrg = [x for x in organizations.get("data") if x.get("attributes").get("name") == "Enterprise Users - " + userRegion]
    
    if filterUserOrg:
        userOrg = filterUserOrg.pop()
        print_log("INFO", "Organization ID: " + userOrg["id"] + " found for User " + email)
        return userOrg["id"]
        

# Assign Employee to Organization using Organization ID and Employee ID
def assignUserToOrganization(wfeConn, employee, usrRegion, email, accEmail):
    # Change Region AMER for corp only
    emailsplit = email.split("@")
    
    if emailsplit[1].lower() == "email.corp" and accEmail != "Portal_Services@email.com":
        if usrRegion == "AMER":
            usrRegion = usrRegion + " Eastern"
            
        organizationName = "Enterprise Users - " + usrRegion
        organizations = wfeConn.get_all_organization()
        organizationId = getOrganizationIdByRegion(organizations, usrRegion, email)
        organizationTemplate = wfeConn.open_template_employee_organization(employee["id"], organizationName)
        assignEmployee = wfeConn.assign_employee_to_organization(organizationId, organizationName, email, organizationTemplate)
    else:
        print_log("INFO", email + " is not in email.corp or maybe email was Portal_Services, organization not changed")
    
    
def updateUserExtension(wfeConn, extension, employee, email):
    firstName = employee["attributes"]["person"]["firstName"]
    lastName = employee["attributes"]["person"]["lastName"]
    employeeId = employee["id"]
    
    emailsplit = email.split("@")
    if emailsplit[1].lower() == "email.corp":
        extensions= wfeConn.get_secret_extension().split(',') # convert datasource name for extension to array, if the extension number for datasources on here is same, then no need to refactor
        for src in extensions:
            dsName = src.strip()
            dsId= wfeConn.get_datasource_by_name(dsName)
            template = wfeConn.open_template_extension(dsId, dsName, employeeId, extension)
            checkExt = wfeConn.check_extension(dsId,extension, email)
            
            if checkExt == "Not Allowed":
                print_log("ERROR","Set extension for "+email+ " Not Allowed")
            elif checkExt == "CREATE":
                wfeConn.assign_extension(dsId, template, email)
            elif checkExt == "UPDATE":
                wfeConn.update_extension(dsId, template, email)
            else:
                print_log("ERROR","Unable to set extension for "+email)
    else:
        print_log("ERROR", "Extension Assignment for "+email+" failed, not in email.corp") 
        
        
# COMMENTED: NOT USED IN LOCAL
# Send notification to Lambda service
# def sendNotification(event):
#     payload = {'employee_id':event['employee_id'],'target_system':event['target_system']}
#     payload = json.dumps(payload)
#     print_log("INFO", "Payload for wfe-scopeupdate-ssm "+ payload)
#     response = lambda_service.invoke_lambda_function(REGION,"wfe-scopeupdate-ssm",payload,in_invocation_type="RequestResponse")
#     result = response.decode('UTF-8')
#     print_log("INFO", "Response lambda_service.invoke_lambda_function : " + result)


def print_log(type, message):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(">> {}::{}::{}".format(date, type, message))

if __name__ == '__main__':
    event = {
                "email": "test-user@email.corp",
                "username": "test-user@email.corp",
                "employee_id": "12345",
                "target_system": "shared_env"
            }
    
    lambda_handler(event)
    