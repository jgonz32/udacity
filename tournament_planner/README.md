Project Name:
Tournament planner

Installation:

Pre-requisites:
1. Python 2.7 or greater installed
2. Python path should be available as a system variable
3. Postgre database must be installed and ocnfigured.
3. A Postgre database called "tournament" must be created.

How to execute the program:
1. Extract the .zip file anywhere in your computer:
2. Connect to tournament database by running the following command
	>psql tournament
3. Once in the database prompt run the tournament.sql:
	tournament> \i tournament.sql
4 Exit the database prompt.
4. Run the following command to run the tests.
	>python tournament_test.py

History:

0.0.1 - Initial version

Credits:

Created by Jorge Gonzalez

License:

