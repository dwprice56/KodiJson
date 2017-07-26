#!/usr/bin/python3
# -*- coding: utf-8 -*-

import base64
import json
import time
import unicodedata
import urllib.request

class KodiJson(object):

    VALID_DIRECTIONS = ['Up', 'Down', 'Left', 'Right']

    def __init__(self, ipAddress, port, userId, password, description):
        """Initialize the object and build the base URL."""

        self.ipAddress = ipAddress
        self.port = port
        self.userId = userId
        self.password = password
        self.description = description

        # self.debugLevel = 0
        self.url = 'http://{}:{}/jsonrpc'.format(self.ipAddress, self.port)

    def CheckResponseOK(self, response):
        """Check the response to the JSON command.

        An OK response only means the command was a valid KODI JSON command.
        It does not mean the command worked or that the command has completed."""

        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        if (response != u'OK'):
            raise RuntimeError('Kodi JSON command response was not OK: {}'.format(response))

    def SendRequest(self, method, parameters=None):
        """Send a JSON request to the url target and return the response."""

        # Serialize the data to a JSON string
        dataDict = {}

        dataDict["jsonrpc"] = "2.0"
        dataDict["method"] = method
        if parameters:
            dataDict["params"] = parameters
        dataDict["id"] = "1"

        data = json.dumps(dataDict)

        # Build the request object
        request = urllib.request.Request(self.url, data.encode('ascii'), {"Content-Type": "application/json", })
        if (self.userId and self.password):
            s = '{}:{}'.format(self.userId, self.password).replace('\n', '')
            b = bytes(s, 'utf-8')
            e = base64.b64encode(b)

            request.add_header("Authorization", "Basic " + e.decode('ascii'))

        # if (self.debugLevel >= 3):
        #     print 'DEBUG (KodiJson.SendRequest)'
        #     print 'DEBUG    method="{}", parameters="{}"'.format(method, parameters)

        try:
            response = urllib.request.urlopen(request)
            response = response.read()
            response = json.loads(response.decode('utf-8'))
            if 'result' in response:
                response = response['result']

        # This error handling is specifically to catch HTTP errors and connection
        # errors
        except urllib.request.URLError as e:
            response = str(e.reason)

        # if (self.debugLevel >= 3):
        #     print 'DEBUG (KodiJson.SendRequest)'
        #     print 'DEBUG    response="{}"'.format(response)

        return response

    def ping(self):
        """Ping the url."""

        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.ping)'

        response = self.SendRequest('JSONRPC.Ping')
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        return response

    def ApplicationVersion(self):
        """Get the KODI version."""

        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.ApplicationVersion)'

        response = self.SendRequest(u'Application.GetProperties', {u'properties': [u'name', u'version']})
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        if (type(response) is dict):
            return response['version']

        return response

        return response

    def GetInfoBooleans(self, booleans):
        """Get the boolean infor from the target machine.

        The 'booleans' parameter can be a single string or a list of strings"""

        if (type(booleans) is str):
            response = self.SendRequest(u'XBMC.GetInfoBooleans', {u'booleans': [booleans]})
        elif (type(booleans) is list):
            response = self.SendRequest(u'XBMC.GetInfoBooleans', {u'booleans': booleans})
        else:
            raise TypeError('The booleans parameter must be a string or a list.')

        return response

    def JSONRPCVersion(self):
        """Get the JSONRPC version."""

        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.JSONRPCVersion)'

        response = self.SendRequest(u'JSONRPC.Version')
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        if (type(response) is dict):
            return response['version']

        return response

    def Reboot(self):
        """Reboot the target machine."""

        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.Reboot)'

        response = self.SendRequest(u'System.Reboot')
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        self.CheckResponseOK(response)

        return response

    def VideoLibraryClean(self):
        """Send the command to clean the video library."""

        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.VideoLibraryClean)'

        response = self.SendRequest(u'VideoLibrary.Clean')
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)
        # self.ResponseOK(response)

        return response

    def VideoLibraryGetMovies(self):
        """Get a list of all movies."""

        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.VideoLibraryGetMovies)'

        # VideoLibrary.VideoLibraryGetMovies always returns the movieid & label so only ask for additional properties such as year.
        response = self.SendRequest(u'VideoLibrary.GetMovies', { u'properties' : [u'year', ], u'sort': { u'order': u'ascending', u'method': u'label', u'ignorearticle': True } } )

        # {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter": {"field": "playcount", "operator": "is", "value": "0"}, "limits": { "start" : 0, "end": 75 }, "properties" : ["art", "rating", "thumbnail", "playcount", "file"], "sort": { "order": "ascending", "method": "label", "ignorearticle": True } }
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        if (type(response) is dict):
            if (response['limits']['total'] == 0):
                return []

            return response['movies']

        return response

    def VideoLibraryGetEpisodes(self, tvshowid, season):
        """Get a list of the episodes for a TV show season."""

        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.VideoLibraryGetMovies)'

        # VideoLibrary.VideoLibraryGetMovies always returns the movieid & label so only ask for additional properties such as year.
        response = self.SendRequest(u'VideoLibrary.GetEpisodes', { u'tvshowid' : tvshowid, u'season' : season,
            # u'properties' : [u'season', u'episode', 'watchedepisodes'],
            u'sort': { u'order': u'ascending', u'method': u'label', u'ignorearticle': True } } )

        # {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter": {"field": "playcount", "operator": "is", "value": "0"}, "limits": { "start" : 0, "end": 75 }, "properties" : ["art", "rating", "thumbnail", "playcount", "file"], "sort": { "order": "ascending", "method": "label", "ignorearticle": True } }
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        if (type(response) is dict):
            if (response['limits']['total'] == 0):
                return []

            return response['episodes']

        return response

    def VideoLibraryGetSeasons(self, tvshowid):
        """Get a list of the seasons for a TV show."""

        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.VideoLibraryGetMovies)'

        # VideoLibrary.VideoLibraryGetMovies always returns the movieid & label so only ask for additional properties such as year.
        response = self.SendRequest(u'VideoLibrary.GetSeasons', { u'tvshowid' : tvshowid,  u'properties' : [u'season', u'episode', 'watchedepisodes'], u'sort': { u'order': u'ascending', u'method': u'label', u'ignorearticle': True } } )

        # {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter": {"field": "playcount", "operator": "is", "value": "0"}, "limits": { "start" : 0, "end": 75 }, "properties" : ["art", "rating", "thumbnail", "playcount", "file"], "sort": { "order": "ascending", "method": "label", "ignorearticle": True } }
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        if (type(response) is dict):
            if (response['limits']['total'] == 0):
                return []

            return response['seasons']

        return response

    def VideoLibraryGetTVShows(self):
        """Get a list of all TV shows."""

        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.VideoLibraryGetMovies)'

        # VideoLibrary.VideoLibraryGetMovies always returns the movieid & label so only ask for additional properties such as year.
        response = self.SendRequest(u'VideoLibrary.GetTVShows', { u'properties' : [u'year', ], u'sort': { u'order': u'ascending', u'method': u'label', u'ignorearticle': True } } )

        # {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter": {"field": "playcount", "operator": "is", "value": "0"}, "limits": { "start" : 0, "end": 75 }, "properties" : ["art", "rating", "thumbnail", "playcount", "file"], "sort": { "order": "ascending", "method": "label", "ignorearticle": True } }
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        if (type(response) is dict):
            if (response['limits']['total'] == 0):
                return []

            return response['tvshows']

        return response

    def VideoLibraryRefreshMovie(self, movieid):
        """Refresh the information for a single movie."""

        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.RefreshMovie), movieid={}'.format(movieid)

        response = self.SendRequest(u'VideoLibrary.RefreshMovie', { u'movieid': movieid, u'ignorenfo': False } )
        # response = self.SendRawRequest({"jsonrpc": "2.0", "method": "VideoLibrary.RefreshMovie", "params": { "movieid": movieid, "ignorenfo": False}, "id": 1 })
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        self.CheckResponseOK(response)

        return response

    def VideoLibraryRefreshTVShow(self, tvshowid, refreshepisodes = False):
        """Refresh the information for a single TV show."""

        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.RefreshMovie), movieid={}'.format(movieid)

        response = self.SendRequest(u'VideoLibrary.RefreshTVShow', { u'tvshowid': tvshowid, u'ignorenfo': False , u'refreshepisodes': refreshepisodes } )
        # response = self.SendRawRequest({"jsonrpc": "2.0", "method": "VideoLibrary.RefreshMovie", "params": { "movieid": movieid, "ignorenfo": False}, "id": 1 })
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        self.CheckResponseOK(response)

        return response

    def VideoLibraryScan(self):
        """Send the command to scan (update) the video library."""

        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.VideoLibraryScan)'

        response = self.SendRequest(u'VideoLibrary.Scan')
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)
        # self.ResponseOK(response)

        return response

    def WakeUp(self, waitTime=0.1):
        """Send a 'noop' action.  This is most often used to 'wake' the
        target machine from the screen saver."""

        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.WakeUp) waitTime={}'.format(waitTime)

        response = self.SendRequest(u'XBMC.GetInfoBooleans', {u'booleans': ['System.ScreenSaverActive']})
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.WakeUp) System.ScreenSaverActive={}'.format(response['System.ScreenSaverActive'])
        if (response['System.ScreenSaverActive']):
            response = self.SendRequest(u'Input.ExecuteAction', {u'action': 'noop'})
            self.CheckResponseOK(response)

            if (waitTime > 0.0):
                time.sleep(waitTime)
