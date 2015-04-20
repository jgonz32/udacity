Project Name:
Catalog Website

Installation:

Pre-requisites:
1. Python 2.7 or greater installed
2. Python path should be available as a system variable

To be able to run the catalog application you need to also install the following third party extensions:
1. pip install flask
2. pip install sqlalchemy
3. pip install requests
4. pip install oauth2client
5. pip install flask-seasurf

Google sign-in:

In order to use Google's Oath2 api to sign using a Google account you need to
1. Create a project in https://console.developers.google.com/ 
2. Generate Oauth credentials (generate a client_id and download the secret JSON file)
3. Use the client id in the html file used for login

For more detailed instructions, please go to https://developers.google.com/+/web/signin/add-button

https://developers.google.com/+/web/signin/add-button
How to execute the program:
1. Extract the .zip file anywhere in your computer:
2. Open the command prompt and run the following command
	>python application.py

History:

0.0.1 - Initial version

Credits:

Created by Jorge Gonzalez

License:

