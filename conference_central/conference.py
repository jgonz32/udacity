#!/usr/bin/env python
from datetime import datetime
from datetime import time
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from models import ConflictException
from models import Profile
from models import ProfileMiniForm
from models import ProfileForm
from models import StringMessage
from models import BooleanMessage
from models import Conference
from models import ConferenceForm
from models import ConferenceForms
from models import ConferenceQueryForm
from models import ConferenceQueryForms
from models import TeeShirtSize
from models import SessionType

from settings import WEB_CLIENT_ID
from settings import ANDROID_CLIENT_ID
from settings import IOS_CLIENT_ID
from settings import ANDROID_AUDIENCE

from models import Session
from models import SessionForm
from models import SessionForms

from models import Speaker
from models import SpeakerForm
from models import SpeakerForms

import time as t
import endpoints

from utils import getUserId

"""
conference.py -- Udacity conference server-side Python App Engine API;
    uses Google Cloud Endpoints

$Id: conference.py,v 1.25 2014/05/24 23:42:19 wesc Exp wesc $

created by wesc on 2014 apr 21

"""

__author__ = 'wesc+api@google.com (Wesley Chun)'

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID
MEMCACHE_ANNOUNCEMENTS_KEY = "RECENT_ANNOUNCEMENTS"
MEMCACHE_FEATURED_SPEAKER_KEY = "FEATURED_SPEAKERS"
ANNOUNCEMENT_TPL = ('Last chance to attend! The following conferences '
                    'are nearly sold out: %s')
FEATURED_SPEAKER_TPL = ('Featured speaker: %s')
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

DEFAULTS = {
    "city": "Default City",
    "maxAttendees": 0,
    "seatsAvailable": 0,
    "topics": ["Default", "Topic"],
}

OPERATORS = {
    'EQ': '=',
    'GT': '>',
    'GTEQ': '>=',
    'LT': '<',
    'LTEQ': '<=',
    'NE': '!='
}

FIELDS = {
    'CITY': 'city',
    'TOPIC': 'topics',
    'MONTH': 'month',
    'MAX_ATTENDEES': 'maxAttendees'}

CONF_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
)

CONFSPEAKER_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
)

CONF_POST_REQUEST = endpoints.ResourceContainer(
    ConferenceForm,
    websafeConferenceKey=messages.StringField(1),
)

SESSION_POST_REQUEST = endpoints.ResourceContainer(
    SessionForm,
    websafeConferenceKey=messages.StringField(1),
)

SESSIONWISHLIST_POST_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    session_websafe_key=messages.StringField(1),
)

SESSION_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
)

SESSION_GET_TYPE_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
    typeOfSession=messages.StringField(2)
)

SPEAKER_POST_REQUEST = endpoints.ResourceContainer(
    SessionForm,
    websafeSessionKey=messages.StringField(1),
    websafeSpeakerKey=messages.StringField(2)
)

SPEAKER_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    webSpeakerKey=messages.StringField(1),
)

SESSION_BY_DATESTARTTIME_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
    session_name=messages.StringField(2),
    date=messages.StringField(3),
    starttime=messages.StringField(4)
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Conference API


@endpoints.api(
    name='conference',
    version='v1',
    allowed_client_ids=[
        WEB_CLIENT_ID,
        API_EXPLORER_CLIENT_ID,
        ANDROID_CLIENT_ID,
        IOS_CLIENT_ID],
    audiences=[ANDROID_AUDIENCE],
    scopes=[EMAIL_SCOPE])
class ConferenceApi(remote.Service):

    """Conference API v0.1"""

    # - - - Conference objects - - - - - - - - - - - - - - - - -

    def _copyConferenceToForm(self, conf, displayName):
        """Copy relevant fields from Conference to ConferenceForm."""
        cf = ConferenceForm()
        for field in cf.all_fields():
            if hasattr(conf, field.name):
                # convert Date to date string; just copy others
                if field.name.endswith('Date'):
                    setattr(cf, field.name, str(getattr(conf, field.name)))
                else:
                    setattr(cf, field.name, getattr(conf, field.name))
            elif field.name == "websafeKey":
                setattr(cf, field.name, conf.key.urlsafe())
        if displayName:
            setattr(cf, 'organizerDisplayName', displayName)
        cf.check_initialized()
        return cf

    def _createConferenceObject(self, request):
        """Create or update Conference object, returning
        ConferenceForm/request."""
        # preload necessary data items
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        if not request.name:
            raise endpoints.BadRequestException(
                "Conference 'name' field required")

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {
            field.name: getattr(
                request,
                field.name) for field in request.all_fields()}
        del data['websafeKey']
        del data['organizerDisplayName']

        # add default values for those missing (both data model & outbound
        # Message)
        for df in DEFAULTS:
            if data[df] in (None, []):
                data[df] = DEFAULTS[df]
                setattr(request, df, DEFAULTS[df])

        # convert dates from strings to Date objects; set month based on
        # start_date
        if data['startDate']:
            data['startDate'] = datetime.strptime(
                data['startDate'][
                    :10],
                "%Y-%m-%d").date()
            data['month'] = data['startDate'].month
        else:
            data['month'] = 0
        if data['endDate']:
            data['endDate'] = datetime.strptime(
                data['endDate'][
                    :10],
                "%Y-%m-%d").date()

        # set seatsAvailable to be same as maxAttendees on creation
        if data["maxAttendees"] > 0:
            data["seatsAvailable"] = data["maxAttendees"]
        # generate Profile Key based on user ID and Conference
        # ID based on Profile key get Conference key from ID
        p_key = ndb.Key(Profile, user_id)
        c_id = Conference.allocate_ids(size=1, parent=p_key)[0]
        c_key = ndb.Key(Conference, c_id, parent=p_key)
        data['key'] = c_key
        data['organizerUserId'] = request.organizerUserId = user_id

        # create Conference, send email to organizer confirming
        # creation of Conference & return (modified) ConferenceForm
        Conference(**data).put()
        taskqueue.add(params={'email': user.email(),
                              'conferenceInfo': repr(request)},
                      url='/tasks/send_confirmation_email'
                      )
        return request

    @ndb.transactional()
    def _updateConferenceObject(self, request):
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {
            field.name: getattr(
                request,
                field.name) for field in request.all_fields()}

        # update existing conference
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        # check that conference exists
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' %
                request.websafeConferenceKey)

        # check that user is owner
        if user_id != conf.organizerUserId:
            raise endpoints.ForbiddenException(
                'Only the owner can update the conference.')

        # Not getting all the fields, so don't create a new object; just
        # copy relevant fields from ConferenceForm to Conference object
        for field in request.all_fields():
            data = getattr(request, field.name)
            # only copy fields where we get data
            if data not in (None, []):
                # special handling for dates (convert string to Date)
                if field.name in ('startDate', 'endDate'):
                    data = datetime.strptime(data, "%Y-%m-%d").date()
                    if field.name == 'startDate':
                        conf.month = data.month
                # write to Conference object
                setattr(conf, field.name, data)
        conf.put()
        prof = ndb.Key(Profile, user_id).get()
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))

    @endpoints.method(ConferenceForm, ConferenceForm, path='conference',
                      http_method='POST', name='createConference')
    def createConference(self, request):
        """Create new conference."""
        return self._createConferenceObject(request)

    @endpoints.method(CONF_POST_REQUEST, ConferenceForm,
                      path='conference/{websafeConferenceKey}',
                      http_method='PUT', name='updateConference')
    def updateConference(self, request):
        """Update conference w/provided fields & return w/updated info."""
        return self._updateConferenceObject(request)

    @endpoints.method(CONF_GET_REQUEST, ConferenceForm,
                      path='conference/{websafeConferenceKey}',
                      http_method='GET', name='getConference')
    def getConference(self, request):
        """Return requested conference (by websafeConferenceKey)."""
        # get Conference object from request; bail if not found
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' %
                request.websafeConferenceKey)
        prof = conf.key.parent().get()
        # return ConferenceForm
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='getConferencesCreated',
                      http_method='POST', name='getConferencesCreated')
    def getConferencesCreated(self, request):
        """Return conferences created by user."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        # create ancestor query for all key matches for this user
        confs = Conference.query(ancestor=ndb.Key(Profile, user_id))
        prof = ndb.Key(Profile, user_id).get()
        # return set of ConferenceForm objects per Conference
        return ConferenceForms(
            items=[
                self._copyConferenceToForm(
                    conf,
                    getattr(
                        prof,
                        'displayName')) for conf in confs])

    def _getQuery(self, request):
        """Return formatted query from the submitted filters."""
        q = Conference.query()
        inequality_filter, filters = self._formatFilters(request.filters)

        # If exists, sort on inequality filter first
        if not inequality_filter:
            q = q.order(Conference.name)
        else:
            q = q.order(ndb.GenericProperty(inequality_filter))
            q = q.order(Conference.name)

        for filtr in filters:
            if filtr["field"] in ["month", "maxAttendees"]:
                filtr["value"] = int(filtr["value"])
            formatted_query = ndb.query.FilterNode(
                filtr["field"],
                filtr["operator"],
                filtr["value"])
            q = q.filter(formatted_query)
        return q

    def _formatFilters(self, filters):
        """Parse, check validity and format user supplied filters."""
        formatted_filters = []
        inequality_field = None

        for f in filters:
            filtr = {
                field.name: getattr(
                    f,
                    field.name) for field in f.all_fields()}

            try:
                filtr["field"] = FIELDS[filtr["field"]]
                filtr["operator"] = OPERATORS[filtr["operator"]]
            except KeyError:
                raise endpoints.BadRequestException(
                    "Filter contains invalid field or operator.")

            # Every operation except "=" is an inequality
            if filtr["operator"] != "=":
                # check if inequality operation has been used
                # in previous filters
                # disallow the filter if inequality was performed on a
                # different field before
                # track the field on which the inequality operation is
                # performed
                if inequality_field and inequality_field != filtr["field"]:
                    raise endpoints.BadRequestException(
                        "Inequality filter is allowed on only one field.")
                else:
                    inequality_field = filtr["field"]

            formatted_filters.append(filtr)
        return (inequality_field, formatted_filters)

    @endpoints.method(ConferenceQueryForms, ConferenceForms,
                      path='queryConferences',
                      http_method='POST',
                      name='queryConferences')
    def queryConferences(self, request):
        """Query for conferences."""
        conferences = self._getQuery(request)

        # need to fetch organiser displayName from profiles
        # get all keys and use get_multi for speed
        organisers = [(ndb.Key(Profile, conf.organizerUserId))
                      for conf in conferences]
        profiles = ndb.get_multi(organisers)

        # put display names in a dict for easier fetching
        names = {}
        for profile in profiles:
            names[profile.key.id()] = profile.displayName

        # return individual ConferenceForm object per Conference
        return ConferenceForms(
            items=[
                self._copyConferenceToForm(
                    conf,
                    names[
                        conf.organizerUserId]) for conf in conferences])

    # - - - Profile objects - - - - - - - - - - - - - - - - - - -

    def _copyProfileToForm(self, prof):
        """Copy relevant fields from Profile to ProfileForm."""
        # copy relevant fields from Profile to ProfileForm
        pf = ProfileForm()
        for field in pf.all_fields():
            if hasattr(prof, field.name):
                # convert t-shirt string to Enum; just copy others
                if field.name == 'teeShirtSize':
                    setattr(
                        pf,
                        field.name,
                        getattr(
                            TeeShirtSize,
                            getattr(
                                prof,
                                field.name)))
                else:
                    setattr(pf, field.name, getattr(prof, field.name))
        pf.check_initialized()
        return pf

    def _getProfileFromUser(self):
        """Return user Profile from datastore,
        creating new one if non-existent."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # get Profile from datastore
        user_id = getUserId(user)
        p_key = ndb.Key(Profile, user_id)
        profile = p_key.get()
        # create new Profile if not there
        if not profile:
            profile = Profile(
                key=p_key,
                displayName=user.nickname(),
                mainEmail=user.email(),
                teeShirtSize=str(TeeShirtSize.NOT_SPECIFIED),
            )
            profile.put()

        return profile  # return Profile

    def _doProfile(self, save_request=None):
        """Get user Profile and return to user, possibly updating it first."""
        # get user Profile
        prof = self._getProfileFromUser()

        # if saveProfile(), process user-modifyable fields
        if save_request:
            for field in ('displayName', 'teeShirtSize'):
                if hasattr(save_request, field):
                    val = getattr(save_request, field)
                    if val:
                        setattr(prof, field, str(val))
                        # if field == 'teeShirtSize':
                        #    setattr(prof, field, str(val).upper())
                        # else:
                        #    setattr(prof, field, val)
                        prof.put()

        # return ProfileForm
        return self._copyProfileToForm(prof)

    @endpoints.method(message_types.VoidMessage, ProfileForm,
                      path='profile', http_method='GET', name='getProfile')
    def getProfile(self, request):
        """Return user profile."""
        return self._doProfile()

    @endpoints.method(ProfileMiniForm, ProfileForm,
                      path='profile', http_method='POST', name='saveProfile')
    def saveProfile(self, request):
        """Update & return user profile."""
        return self._doProfile(request)

    # - - - Announcements - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def _cacheAnnouncement():
        """Create Announcement & assign to memcache; used by
        memcache cron job & putAnnouncement().
        """
        confs = Conference.query(ndb.AND(
            Conference.seatsAvailable <= 5,
            Conference.seatsAvailable > 0)
        ).fetch(projection=[Conference.name])

        if confs:
            # If there are almost sold out conferences,
            # format announcement and set it in memcache
            announcement = ANNOUNCEMENT_TPL % (
                ', '.join(conf.name for conf in confs))
            memcache.set(MEMCACHE_ANNOUNCEMENTS_KEY, announcement)
        else:
            # If there are no sold out conferences,
            # delete the memcache announcements entry
            announcement = ""
            memcache.delete(MEMCACHE_ANNOUNCEMENTS_KEY)

        return announcement

    @endpoints.method(message_types.VoidMessage, StringMessage,
                      path='conference/announcement/get',
                      http_method='GET', name='getAnnouncement')
    def getAnnouncement(self, request):
        """Return Announcement from memcache."""
        return StringMessage(
            data=memcache.get(MEMCACHE_ANNOUNCEMENTS_KEY) or "")

    # - - - Registration - - - - - - - - - - - - - - - - - - - -

    @ndb.transactional(xg=True)
    def _conferenceRegistration(self, request, reg=True):
        """Register or unregister user for selected conference."""
        retval = None
        prof = self._getProfileFromUser()  # get user Profile

        # check if conf exists given websafeConfKey
        # get conference; check that it exists
        wsck = request.websafeConferenceKey
        conf = ndb.Key(urlsafe=wsck).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % wsck)

        # register
        if reg:
            # check if user already registered otherwise add
            if wsck in prof.conferenceKeysToAttend:
                raise ConflictException(
                    "You have already registered for this conference")

            # check if seats avail
            if conf.seatsAvailable <= 0:
                raise ConflictException(
                    "There are no seats available.")

            # register user, take away one seat
            prof.conferenceKeysToAttend.append(wsck)
            conf.seatsAvailable -= 1
            retval = True

        # unregister
        else:
            # check if user already registered
            if wsck in prof.conferenceKeysToAttend:

                # unregister user, add back one seat
                prof.conferenceKeysToAttend.remove(wsck)
                conf.seatsAvailable += 1
                retval = True
            else:
                retval = False

        # write things back to the datastore & return
        prof.put()
        conf.put()
        return BooleanMessage(data=retval)

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='conferences/attending',
                      http_method='GET', name='getConferencesToAttend')
    def getConferencesToAttend(self, request):
        """Get list of conferences that user has registered for."""
        prof = self._getProfileFromUser()  # get user Profile
        conf_keys = [ndb.Key(urlsafe=wsck)
                     for wsck in prof.conferenceKeysToAttend]
        conferences = ndb.get_multi(conf_keys)

        # get organizers
        organisers = [ndb.Key(Profile, conf.organizerUserId)
                      for conf in conferences]
        profiles = ndb.get_multi(organisers)

        # put display names in a dict for easier fetching
        names = {}
        for profile in profiles:
            names[profile.key.id()] = profile.displayName

        # return set of ConferenceForm objects per Conference
        return ConferenceForms(
            items=[
                self._copyConferenceToForm(
                    conf,
                    names[
                        conf.organizerUserId]) for conf in conferences])

    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
                      path='conference/{websafeConferenceKey}',
                      http_method='POST', name='registerForConference')
    def registerForConference(self, request):
        """Register user for selected conference."""
        return self._conferenceRegistration(request)

    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
                      path='conference/{websafeConferenceKey}',
                      http_method='DELETE', name='unregisterFromConference')
    def unregisterFromConference(self, request):
        """Unregister user for selected conference."""
        return self._conferenceRegistration(request, reg=False)

    @endpoints.method(message_types.VoidMessage, SessionForms,
                      path='filterPlayground',
                      http_method='GET', name='filterPlayground')
    def filterPlayground(self, request):
        """Filter Playground"""

        # ---- Solve the following query related problem (answer) -----
        time_tuple = t.strptime("19:00", "%H:%M")
        start_time = time(time_tuple[3], time_tuple[4])

        # removed type of session not wanted from allowed typeOfSessions
        session_type_to_remove = 'LECTURE'  # or WORKSHOP as in the question

        allowed_session_types = [
            'NOT_SPECIFIED',
            'LECTURE',
            'SYMPOSIUM',
            'SEMINAR',
            'WORKSHOP',
            'ROUND_TABLE']

        allowed_session_types.remove(session_type_to_remove)
        sessions = Session.query(
            Session.typeOfSession.IN(allowed_session_types))
        sessions = sessions.filter(Session.startTime < start_time)
        return SessionForms(
            sessions=[self._copySessionToForm(session) for session in sessions]
        )

    # ------- Sessions -----------------------------------------------

    # return all sessions by specified type
    @endpoints.method(
        SESSION_GET_TYPE_REQUEST,
        SessionForms,
        path='conference/sessions/type/{websafeConferenceKey}',
        http_method='GET',
        name='getConferenceSessionsByType')
    def getConferenceSessionsByType(self, request):
        ''' Get all sessions by session type'''

        # verify of the web safe conference key was provided
        if request.websafeConferenceKey:
            conference = ndb.Key(urlsafe=request.websafeConferenceKey)
        else:
            raise endpoints.BadRequestException(
                'Conference key was not provided.')

        sessions_qry_results = []

        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' %
                request.websafeConferenceKey)

        # get sessions by conference
        sessions_qry_results = Session.query(ancestor=conference)

        if not request.typeOfSession:
            # return all sessions if typeOfSession is not provided
            return SessionForms(
                sessions=[
                    self._copySessionToForm(session)
                    for session in sessions_qry_results])

        sessions_qry_results = sessions_qry_results.filter(
            Session.typeOfSession == request.typeOfSession)

        return SessionForms(
            sessions=[
                self._copySessionToForm(session)
                for session in sessions_qry_results])

    # Get all sessions for a given conference key
    @endpoints.method(
        SESSION_GET_REQUEST,
        SessionForms,
        path='conference/sessions/{websafeConferenceKey}',
        http_method='GET',
        name='getConferenceSessions')
    def getConferenceSessions(self, request):
        ''' Get all sessions by conference key'''

        # verify of the web safe conference key was provided
        if request.websafeConferenceKey:
            conference = ndb.Key(urlsafe=request.websafeConferenceKey)
        else:
            raise endpoints.BadRequestException(
                'Conference key was not provided.')

        # verify if a conference exists for the key provided
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' %
                request.websafeConferenceKey)

        # get all sessions in a conference
        sessions = Session.query(ancestor=conference)

        return SessionForms(
            sessions=[
                self._copySessionToForm(session) for session in sessions])

    # Get all sessions by name and starttime
    @endpoints.method(
        SESSION_BY_DATESTARTTIME_REQUEST,
        SessionForms,
        path='conference/sessions',
        http_method='GET',
        name='getConfSessionsByNameDateAndStarttime')
    def getConfSessionsByDateAndStarttime(self, request):
        ''' Get all sessions by date and type'''

        # verify of the web safe conference key was provided
        if request.websafeConferenceKey:
            conference = ndb.Key(urlsafe=request.websafeConferenceKey)
        else:
            raise endpoints.BadRequestException(
                'Conference key was not provided.')

        # verify if a conference exists for the key provided
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' %
                request.websafeConferenceKey)

        # get all sessions in a conference
        sessions = Session.query(ancestor=conference)

        # if session name is not empty filter the sessions by name specified
        if request.session_name not in (None, ""):
            sessions = sessions.filter(Session.name == request.session_name)

        # if date is provided parse date and convert to compatible format to
        # query by date (format YYYY-m-d)
        if request.date not in (None, "") and sessions:
            date = datetime.strptime(request.date, "%Y-%m-%d").date()
            sessions = sessions.filter(Session.date == date)

        # if start time is provided parse the time and convert to compatible
        # format to query by time
        if request.starttime not in (None, "") and sessions:
            time_tuple = t.strptime(request.starttime, "%H:%M")
            start_time = time(time_tuple[3], time_tuple[4])
            sessions = sessions.filter(Session.startTime == start_time)

        return SessionForms(
            sessions=[
                self._copySessionToForm(session) for session in sessions])

    # Create a SessionForm object from a Session
    def _copySessionToForm(self, session):
        """Copy relevant fields from Session to SessionForm."""

        sessionForm = SessionForm()

        # iterate over fields in SessionForm
        for field in sessionForm.all_fields():
            if hasattr(session, field.name):

                # convert Date to date string
                if field.name == 'date':
                    setattr(
                        sessionForm, field.name, str(
                            getattr(
                                session, field.name)))
                # convert Time to date string
                elif field.name.endswith('Time'):
                    setattr(
                        sessionForm, field.name, str(
                            getattr(
                                session, field.name)))
                else:
                    # Verify if exists, if it exists convert to string
                    if field.name == 'typeOfSession':
                        typeOfSession = getattr(session, field.name)
                        if typeOfSession:
                            setattr(
                                sessionForm, field.name, getattr(
                                    SessionType, str(
                                        getattr(
                                            session, field.name))))
                        else:
                            setattr(sessionForm, field.name, 'NOT_SPECIFIED')
                    else:
                        # if attribute doesn't need special
                        # handling add to form
                        setattr(
                            sessionForm,
                            field.name,
                            getattr(
                                session,
                                field.name))

            elif field.name == 'webSessionKey':
                setattr(sessionForm, field.name, session.key.urlsafe())

        sessionForm.check_initialized()
        return sessionForm

    # create a session object in datastore from the SessionForm fields
    # submitted
    def _createSessionObject(self, request):
        """ Create a session object to save in datastore
        """
        conference = ndb.Key(urlsafe=request.websafeConferenceKey)

        # verify if conference key doesn't exists
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' %
                request.websafeConferenceKey)

        # verify required field is not empty
        if not request.name:
            raise endpoints.BadRequestException(
                "Session 'name' field required")

        session_fields = {
            field.name: getattr(
                request,
                field.name) for field in request.all_fields()}

        session_id = Session.allocate_ids(size=1, parent=conference)[0]
        session = ndb.Key(Session, session_id, parent=conference)

        session_fields['key'] = session

        # format time provided to compatible format
        if session_fields['startTime']:
            time_tuple = t.strptime(session_fields['startTime'], "%H:%M")
            start_time = time(time_tuple[3], time_tuple[4])
            session_fields['startTime'] = start_time

        # format date provided to compatible format
        if session_fields['date']:
            session_fields['date'] = datetime.strptime(
                session_fields['date'],
                "%Y-%m-%d").date()

        # check if session fields has a speaker
        if session_fields['speaker']:
            sessions = Session.query(ancestor=conference)
            sessions_count = sessions.filter(
                Session.speaker == session_fields['speaker']).count()

            # check if speaker already has more than presentation to add as
            # feature speaker
            if sessions_count > 0:
                # push task to add feature speaker to mem cache
                taskqueue.add(
                    params={
                        'conference': request.websafeConferenceKey,
                        'speaker': session_fields['speaker']},
                    url='/tasks/set_feature_speaker')

        del session_fields['websafeConferenceKey']
        del session_fields['webSessionKey']

        # verify if typeOfSession is None. If it is set defalt value
        if session_fields['typeOfSession']:
            session_fields['typeOfSession'] = str(
                getattr(
                    request,
                    'typeOfSession')).upper()
        else:
            session_fields['typeOfSession'] = 'NOT_SPECIFIED'

        session = Session(**session_fields).put()

        return self._copySessionToForm(session.get())

    # endpoint to create session for selected conference
    @endpoints.method(
        SESSION_POST_REQUEST,
        SessionForm,
        path='conference/session/{websafeConferenceKey}',
        http_method='POST',
        name='createSession')
    def createSession(self, request):
        ''' Create a new conference session '''
        return self._createSessionObject(request)

    # add the specified session key to user's profile wishlist
    @ndb.transactional()
    @endpoints.method(
        SESSIONWISHLIST_POST_REQUEST,
        ProfileForm,
        path='session/wishlist',
        http_method='POST',
        name='addSessionToWishlist')
    def addSessionToWishlist(self, request):
        """ Add session to users wishlist """
        # get user profile to add session to user's wish list
        user_profile = self._getProfileFromUser()

        # get session from session key provided
        session = ndb.Key(urlsafe=request.session_websafe_key).get()

        # Check if session exists, raise an exception if otherwise
        if not session:
            raise endpoints.NotFoundException(
                'No session found with key: %s' % request.session_websafe_key)

        # Check if session key already exists in wish list and raise exception
        # if it does
        if request.session_websafe_key in user_profile.sessionWishList:
            raise endpoints.ConflictException(
                'Session key %s already exists in user\'s wishlist' %
                request.session_websafe_key)

        # add session to wishlist
        user_profile.sessionWishList.append(request.session_websafe_key)

        # save updates
        user_profile.put()

        return self._copyProfileToForm(user_profile)

    # get user's wishlist
    @endpoints.method(
        message_types.VoidMessage,
        SessionForms,
        path='session/wishlist',
        http_method='GET',
        name='getSessionsInWishlist')
    def getSessionsInWishlist(self, request):
        """ get user's sessions in wishlist"""

        # get user profile
        user_profile = self._getProfileFromUser()

        # check if sessionWishList is empty, if it is return empty list
        if not user_profile.sessionWishList:
            return SessionForms(sessions=[])

        return SessionForms(
            sessions=[self._copySessionToForm(
                    ndb.Key(urlsafe=session).get())
                    for session in user_profile.sessionWishList])

    # ------- Speakers -------------------------------------------------------

    # cache speaker if speaker is presenting in more than 1 session
    @staticmethod
    def _cacheFeatureSpeaker(conferencekey, speaker):
        """Create Feature Speaker & assign to memcache.
        """

        conference = ndb.Key(urlsafe=conferencekey)
        # query for sessions presented by specified speaker
        sessions = Session.query(ancestor=conference)
        sessions_list = sessions.filter(
            Session.speaker == speaker).fetch(projection=[Session.name])

        # Make sure speaker and session list is not empty, otherwise
        # raise exception
        if speaker and sessions_list:
            speaker = ndb.Key(urlsafe=speaker).get()

            # Format string with feature speaker name and presentations
            feature_spkr = FEATURED_SPEAKER_TPL % (
                speaker.name + ' Presenting in: %s'
                % ', '.join(session.name for session in sessions_list))

            # Create memcache for feature speaker
            memcache.set(MEMCACHE_FEATURED_SPEAKER_KEY, feature_spkr)
        else:
            raise endpoints.ConflictException(
                'No speaker or sessions list provided')

        return feature_spkr

    # get feature speaker from memcache
    @endpoints.method(message_types.VoidMessage, StringMessage,
                      path='conference/featureSpeaker/get',
                      http_method='GET', name='getFeatureSpeaker')
    def getFeatureSpeaker(self, request):
        """Return Feature Speaker from memcache."""
        return StringMessage(
            data=memcache.get(MEMCACHE_FEATURED_SPEAKER_KEY) or "")

    # Return a list of sessions by speaker
    @endpoints.method(
        SPEAKER_GET_REQUEST,
        SessionForms,
        path='speaker/sessions',
        http_method='GET',
        name='getSessionBySpeaker')
    def getSessionsBySpeaker(self, request):
        ''' Get all sessions for speaker across conferences '''
        speaker = ndb.Key(urlsafe=request.webSpeakerKey)

        if not speaker:
            raise endpoints.NotFoundException(
                'No speaker found with key: %s ' % request.webSpeakerKey)

        # Create a list of sesion Key objects from the list web sesison keys
        # available in sessionsToPresentKey
        session_keys = [ndb.Key(urlsafe=session_websafe_keys)
                        for session_websafe_keys
                        in speaker.sessionsToPresentKey]

        sessions = ndb.get_multi(session_keys)

        return SessionForms(
            sessions=[
                self._copySessionToForm(session) for session in sessions])

    # Return all speakers in a conference
    @endpoints.method(
        CONFSPEAKER_GET_REQUEST,
        SpeakerForms,
        path='speakers',
        http_method='GET',
        name='getAllSpeakersByConference')
    def getAllSpeakersByConference(self, request):
        ''' Get all speakers created by conference'''

        conference = ndb.Key(urlsafe=request.websafeConferenceKey)

        # Verify conference specified exists, raise exception if otherwise
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' %
                request.websafeConferenceKey)

        # Get all sessions for the given conference key
        sessions = Session.query(ancestor=conference)

        # If the speaker in session is not empty, then add to list of speakers
        speakers = [
            session.speaker for session in sessions \
            if session.speaker is not None and session.speaker != ""]

        return SpeakerForms(
            speakers=[
                self._copySpeakerToForm(
                    ndb.Key(
                        urlsafe=speaker).get()) for speaker in speakers])

    # Return all speakers - I used to verify Speaker creation.
    @endpoints.method(
        message_types.VoidMessage,
        SpeakerForms,
        path='all/speakers',
        http_method='GET',
        name='getAllSpeakers')
    def getAllSpeakers(self, request):
        ''' Get all speakers created regardless of conference or session'''

        # query Speaker entity
        speakers = Speaker.query()

        # return all speakers
        return SpeakerForms(
            speakers=[
                self._copySpeakerToForm(speaker) for speaker in speakers])

    # Create a SessionForm object from a Session
    def _copySpeakerToForm(self, speaker):
        """Copy relevant fields from Speaker to SpeakerForm."""

        speakerForm = SpeakerForm()
        for field in speakerForm.all_fields():
            if hasattr(speaker, field.name):
                setattr(speakerForm, field.name, getattr(speaker, field.name))

            if field.name == 'webSpeakerKey':
                setattr(speakerForm, field.name, speaker.key.urlsafe())

        speakerForm.check_initialized()
        return speakerForm

    # private method to create a Speaker object and save in datastore
    def _createSpeakerObject(self, request):
        """ Create a Speaker object to save in datastore
        """
        # Verify that requires fields are provided
        if not request.name or not request.email:
            raise endpoints.BadRequestException(
                "Speaker 'name' and 'email' field(s) required")

        # Verify user is logged in
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # create a dictionary from the request to process the data
        speaker_data = {
            field.name: getattr(
                request,
                field.name) for field in request.all_fields()}

        del speaker_data['webSpeakerKey']

        speaker_id = speaker_data['email']

        # generate speaker id from email
        s_key = ndb.Key(Speaker, speaker_id)
        speaker = s_key.get()

        # save speaker in datastore
        Speaker(**speaker_data).put()

        return request

    # endpoint to create a Speaker
    @endpoints.method(
        SpeakerForm,
        SpeakerForm,
        path='session/speaker',
        http_method='POST',
        name='createSpeaker')
    def createSpeaker(self, request):
        ''' Create a new session speaker '''
        return self._createSpeakerObject(request)

# Conference API
api = endpoints.api_server([ConferenceApi])
