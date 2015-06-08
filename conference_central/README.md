App Engine application for the Udacity training course.

## Products
- [App Engine][1]

## Language
- [Python][2]

## APIs
- [Google Cloud Endpoints][3]

## Setup Instructions
1. Update the value of `application` in `app.yaml` to the app ID you
   have registered in the App Engine admin console and would like to use to host
   your instance of this sample.
1. Update the values at the top of `settings.py` to
   reflect the respective client IDs you have registered in the
   [Developer Console][4].
1. Update the value of CLIENT_ID in `static/js/app.js` to the Web client ID
1. (Optional) Mark the configuration files as unchanged as follows:
   `$ git update-index --assume-unchanged app.yaml settings.py static/js/app.js`
1. Run the app with the devserver using `dev_appserver.py DIR`, and ensure it's running by visiting your local server's address (by default [localhost:8080][5].)
1. (Optional) Generate your client library(ies) with [the endpoints tool][6].
1. Deploy your application.


[1]: https://developers.google.com/appengine
[2]: http://python.org
[3]: https://developers.google.com/appengine/docs/python/endpoints/
[4]: https://console.developers.google.com/
[5]: https://localhost:8080/
[6]: https://developers.google.com/appengine/docs/python/endpoints/endpoints_tool


Task 1:

Session and Speaker data model:

Session 
-------
The Session model is configured as descendant of Conference. Session are part of a Conference and they 
can't belong to a different conference. The Session model contain a speakers property that holds the 
speakers for a session. The session also has typeOfSession which is of type enum. 
I created a model called SessionType that holds the types of sessions available. This will allow to have a consistent list
of allowed session types. Instead of having the user type the session type.

Speaker
-------
A Speaker object has basic information about a Session speaker. It contains name, a short biography, and an email for contact purposes. 
I decided to create a Speaker class instead of the string with  just a name because it gives flexibility to add more info about the speaker. Also, 
a Speaker is not created as a child of Session. This is because we should be able to add/remove speakers on different sessions across multiple conferences. 


Task 3:

Come up with 2 additional queries

1. get conference sessions by name and starttime - This query might be useful when the user knows the session they want to attend and want to know if they
are availablr at specific times.


2. get all speakers by conference - Useful to list speakers that will be presenting on all sessions for a conference

3. since I design the speaker to be an entity. I wrote a createSpeaker endpoint to add speakers to the database that can be later assign to a Session


--Solve the following query related problem (answer): --
The problem with this query is that we would need apply 2 inequalities filters on two different properties in the same query. One way I thought of resolving this restriction is by combining the IN and an inequality operator. Since I have predefined list of session types. I remove from the list the session type I don't want. Then use IN operator to query for all session types in the list. Then filter the result by sessions before 7pm (19:00).
My propose solution implementation is in the filterPlayground method.