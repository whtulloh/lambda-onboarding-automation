# FLOW
- Check if the user is exist in target system
- Get all datasource in target system
- Get datasource by employee
- Compare all datasource with datasource list from Secret Manager
- Create datasource if not exist
- Update Dekstop Messaging Username for corp email
- Assign User To Organization for corp email
- Update User Extension for corp email
- Invoke Lambda Notification

# DEPENDENCIES LIST
- services              : arn:aws:lambda:us-east-2:id:layer:services:3
- requests_layer        : arn:aws:lambda:us-east-2:id:layer:requests_layer:2
- sharepoint-o365-layer : arn:aws:lambda:us-east-2:id:layer:sharepoint-o365-layer:1

# API CONNECTOR
- System Graph
- Onboarding User SharePoint
- Workforce System (define by target system)

# AWS SECRET MANAGER LIST
- onboarding-config                | us-east-2

# RUN IN LOCAL
- install dependencies to your venv
```
pip install requirement.txt
```
- if need new lib, update requirement.txt with
```
pip freeze > requirements.txt
```
- Open lambda_function.py
- Change data event in the main section