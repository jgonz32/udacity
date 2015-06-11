Configuration Details:
----------------------
Login username: grader

Server IP: 
52.25.95.234

Configuration Steps:
--------------------
1. Create a new user an gave sudo access ("grader") using the following commands/steps :
	>adduser grader
	>visudo   #to edit sudoers file
	
	# Added the following line in the sudoers file
	grader ALL=(ALL:ALL) ALL
	
2. Updated all currently installed packages:
	>apt-get update #to update the source list
	>apt-get upgrade #this updates all install packages
	>apt-get dist-upgrade  #I ran this just in case for smart update. Good for package conflict resolution.
	
3. Change the SSH port from 22 to 2200
	1. Created a backup of sshd_config and ssh_config files
	2. On both sshd_config and ssh config files changes the Port field to 2200
	3. Restart the ssh service
		> /etc/init.d/ssh restart
	
	*Note: I had to do this a couple of times since I got myself locked out. The first couple if times I just changes the sshd_config file, 
	but when I changed both (the ssh server and client) files it worked.
	
4. Configure the Uncomplicated Firewall (UFW) to only allow incoming connections for SSH (port 2200), HTTP (port 80), and NTP (port 123)
	1. To use the UFW I had to enable it first:
		>ufw enable
	2. Updated the rules to accept incoming connections for 2200,80,123
		
		>ufw allow 2200
		>ufw allow 123
		>ufw allow 80
		
		#verify changes
		>ufw status
		
		#Restarted the server
		>reboot
		
5. Configure the local timezone to UTC
	I ran the following command to verify its current set up and it appeared that it was already set up to UTC
		>dpkg-reconfigure --frontend noninteractive tzdata

6. Install and configure Apache to serve a Python mod_wsgi application
	1. Installed apache2 and mod_wsgi for Python:
		>apt-get install apache2
		>apt-get install python-setuptools libapache2-mod-wsgi
		
		*Note: More detaild about the configuration in the configuration steps to deploy Catalog web app
		
7. Install and configure PostgreSQL:

	Install:
		> apt-get install postgresql
	Configure
		>sudo -u postgres createuser -D -A -P catalog  # create user catalog
		>sudo -u postgres createdb -O catalog phonecatalog # create database
		>psql phonecatalog catalog #to verify it was created successfully

		# Added the following line to enable password authentication for the catalog app in the pg_hba.conf file
		# TYPE  DATABASE        USER            ADDRESS                 METHOD
		local   phonecatalog    catalog                                 password
		
8. Git Installation and Catalog deployment/config

	a. Installed git:
		>apt-get install git
	
	b. Cloned udacity folder to get catalog app
		> git clone https://github.com/jgonz32/udacity.git
	
	c. Copied the catalog folder to the catalog root folder under /var/www/catalog/
		At this point the structure of the directory is as follows:
		/var/www/catalog/catalog/
								/static
								/templates
								/db
								*.py files
	d. Created a new virtual host config for the catalog app under /etc/apache2/sites-available/catalog.conf . In the catalog.conf 
	file added the following:
		<VirtualHost *:80>
        ServerName localhost
        ServerAdmin jorgeagd81@gmail.com
		
		#this rewrites the IP address to hostname if user specifies in browser. This is needed in order to allow Oauth2 authentication. 
		#Google doesn't allow IP in the config
        RewriteEngine On
        RewriteCond %{HTTP_HOST} ^52\.25\.95\.234$
        RewriteRule ^/(.*)$ http://ec2-52-25-95-234.us-west-2.compute.amazonaws$

        WSGIScriptAlias / /var/www/catalog/catalog.wsgi
        <Directory /var/www/catalog/catalog/>
                Order allow,deny
                Allow from all
        </Directory>
        Alias /static /var/www/catalog/catalog/static
        <Directory /var/www/catalog/catalog/static/>
                Order allow,deny
                Allow from all
        </Directory>
        ErrorLog ${APACHE_LOG_DIR}/error.log
        LogLevel warn
	e. Enabled the site 
		> a2ensite catalog
	f. Restart apache
		>service restart apache2
	
	8. Under /var/www/catalog/ I created a catalog.wsgi that initialise the catalog app:
		#!/usr/bin/python
		import sys
		import logging
		logging.basicConfig(stream=sys.stderr)
		sys.path.insert(0,"/var/www/catalog/")

		from catalog import app as application
		application.secret_key="super_secre_key"
		

	9. I renamed application.py to __init__.py so it gets initialised when catalog gets imported in the step above
	
	10. Installed missing libraries needed to run the catalog app:
		apt-get install python-pip #Used pip to install some python libs since they gave me errors when using apt-get
		apt-get install python-psycopg2
		apt-get install python-flask-sqlalchemy
		pip install flask
		apt-get install python-oauth2client
		pip install flask-seasurf
	
	11. I experienced issues accessing the catalog app at first until realised that had to disabled the the default site:
		> a2dissite 000-default
		> service apache2 reload	#reload apache
	
	12. Also updated the connection string to connect to postgresql instead of sqlite

