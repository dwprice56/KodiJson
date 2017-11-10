#!/usr/bin/python3
# -*- coding: utf-8 -*-

import base64
import json
import time
import unicodedata
import urllib.request

from Exceptions import KodiJsonResponseError

class KodiJson(object):

    VALID_DIRECTIONS = ['Up', 'Down', 'Left', 'Right']

    def __init__(self, ipAddress, port, userId, password, description):
        """ Initialize the object and build the base URL.
        """

        self.ipAddress = ipAddress
        self.port = port
        self.userId = userId
        self.password = password
        self.description = description

        # self.debugLevel = 0
        self.url = 'http://{}:{}/jsonrpc'.format(self.ipAddress, self.port)

    @property
    def address(self):
        """ Returns a string with the device IP address, with port.

            Example: 192.168.4.1:8080
        """
        return ('{}:{}'.format(self.ipAddress, self.port))

    @property
    def device(self):
        """ Returns a string with the device description and IP address, with port.

            Example: Dave's PC (192.168.4.1:8080)
        """
        return ('{} ({}:{})'.format(self.description, self.ipAddress, self.port))

    def CheckResponseDict(self, command, response, entries):
        """ Check the response to the JSON command.

            The response must be a dictionary and the dictionary must contain
            the specified entry.

            Raises a KodiJsonResponseError on an error.
        """
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        if (type(response) is not dict):
            raise KodiJsonResponseError('Kodi JSON command "{}": Response was not a dictionary: {}'.format(command,
                response))

        if (type(entries) is str):
            if (entries not in response):
                raise KodiJsonResponseError('Kodi JSON command "{}": Response did not contain "{}": {}'.format(command,
                    entries, response))
        elif (type(entries) is list):
            for entry in entries:
                if (entry not in response):
                    raise KodiJsonResponseError('Kodi JSON command "{}": Response did not contain "{}": {}'.format(command,
                        entry, response))
        else:
            raise TypeError('The entries parameter must be a string or a list.')

    def CheckResponseOK(self, command, response):
        """ Check the response to the JSON command.

            An OK response only means the command was a valid KODI JSON command.
            It does not mean the command worked or that the command has completed.

            Raises a KodiJsonResponseError if the response is not "OK".
        """
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        if (response != 'OK'):
            raise KodiJsonResponseError('Kodi JSON command "{}": Response was not OK: {}'.format(command,
                response))

    def SendRequest(self, method, parameters=None):
        """ Send a JSON request to the url target and return the response.
        """

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
        """ Ping the url.
        """
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.ping)'

        response = self.SendRequest('JSONRPC.Ping')
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        return response

    def GetApplicationVersion(self):
        """ Get the KODI version.
        """
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.ApplicationVersion)'

        command = 'Application.GetProperties'
        response = self.SendRequest(command, {'properties': ['name', 'version']})
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        self.CheckResponseDict(command, response, 'version')
        return response['version']

    def GetInfoBooleans(self, booleans):
        """ Get the boolean infor from the target machine.

            The 'booleans' parameter can be a single string or a list of strings.
        """
        command = 'XBMC.GetInfoBooleans'
        if (type(booleans) is str):
            response = self.SendRequest(command, {'booleans': [booleans]})
        elif (type(booleans) is list):
            response = self.SendRequest(command, {'booleans': booleans})
        else:
            raise TypeError('The booleans parameter must be a string or a list.')

        self.CheckResponseDict(command, response, booleans)
        return response

    def GetJSONRPCVersion(self):
        """ Get the JSONRPC version.
        """
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.JSONRPCVersion)'

        command = 'JSONRPC.Version'
        response = self.SendRequest(command)
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        self.CheckResponseDict(command, response, 'version')
        return response['version']

    def Reboot(self):
        """ Reboot the target machine.
        """
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.Reboot)'

        command = 'System.Reboot'
        response = self.SendRequest(command)
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        self.CheckResponseOK(command, response)

        return response

    def AudioLibrary_Clean(self):
        """ Send the command to clean the audio library.
        """
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.AudioLibraryClean)'

        command = 'AudioLibrary.Clean'
        response = self.SendRequest(command)
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        self.CheckResponseOK(command, response)
        return response

    def AudioLibrary_Scan(self):
        """ Send the command to scan (update) the audio library.
        """
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.AudioLibraryScan)'

        command = 'AudioLibrary.Scan'
        response = self.SendRequest(command)
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)
        # self.ResponseOK(response)

        self.CheckResponseOK(command, response)
        return response

    def VideoLibrary_Clean(self):
        """ Send the command to clean the video library.
        """
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.VideoLibraryClean)'

        command = 'VideoLibrary.Clean'
        response = self.SendRequest(command)
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)
        # self.ResponseOK(response)

        self.CheckResponseOK(command, response)
        return response

    def VideoLibrary_GetMovies(self):
        """ Get a list of all movies.
        """
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.VideoLibraryGetMovies)'

        # VideoLibrary.VideoLibraryGetMovies always returns the movieid & label so only ask for additional properties such as year.
        command = 'VideoLibrary.GetMovies'
        response = self.SendRequest(command, { 'properties' : ['year', ],
            'sort': { 'order': 'ascending', 'method': 'label', 'ignorearticle': True } } )

        # {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter": {"field": "playcount", "operator": "is", "value": "0"}, "limits": { "start" : 0, "end": 75 }, "properties" : ["art", "rating", "thumbnail", "playcount", "file"], "sort": { "order": "ascending", "method": "label", "ignorearticle": True } }
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        self.CheckResponseDict(command, response, ['limits', 'movies'])
        if (response['limits']['total'] == 0):
            return []

        return response['movies']

    def VideoLibrary_GetEpisodes(self, tvshowid, season):
        """ Get a list of the episodes for a TV show season.
        """
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.VideoLibraryGetMovies)'

        # VideoLibrary.VideoLibraryGetMovies always returns the movieid & label so only ask for additional properties such as year.
        command = 'VideoLibrary.GetEpisodes'
        response = self.SendRequest(command, { 'tvshowid' : tvshowid, 'season' : season,
            # 'properties' : ['season', 'episode', 'watchedepisodes'],
            'sort': { 'order': 'ascending', 'method': 'label', 'ignorearticle': True } } )

        # {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter": {"field": "playcount", "operator": "is", "value": "0"}, "limits": { "start" : 0, "end": 75 }, "properties" : ["art", "rating", "thumbnail", "playcount", "file"], "sort": { "order": "ascending", "method": "label", "ignorearticle": True } }
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        self.CheckResponseDict(command, response, ['limits', 'episodes'])
        if (response['limits']['total'] == 0):
            return []

        return response['episodes']

    def VideoLibrary_GetSeasons(self, tvshowid):
        """ Get a list of the seasons for a TV show.
        """
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.VideoLibraryGetMovies)'

        # VideoLibrary.VideoLibraryGetMovies always returns the movieid & label so only ask for additional properties such as year.
        command = 'VideoLibrary.GetSeasons'
        response = self.SendRequest(command, { 'tvshowid' : tvshowid,  'properties' : ['season', 'episode', 'watchedepisodes'],
            'sort': { 'order': 'ascending', 'method': 'label', 'ignorearticle': True } } )

        # {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter": {"field": "playcount", "operator": "is", "value": "0"}, "limits": { "start" : 0, "end": 75 }, "properties" : ["art", "rating", "thumbnail", "playcount", "file"], "sort": { "order": "ascending", "method": "label", "ignorearticle": True } }
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        self.CheckResponseDict(command, response, ['limits', 'seasons'])
        if (response['limits']['total'] == 0):
            return []

        return response['seasons']

    def VideoLibrary_GetTVShows(self):
        """ Get a list of all TV shows.
        """
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.VideoLibraryGetMovies)'

        # VideoLibrary.VideoLibraryGetMovies always returns the movieid & label so only ask for additional properties such as year.
        command = 'VideoLibrary.GetTVShows'
        response = self.SendRequest(command, { 'properties' : ['year', ],
            'sort': { 'order': 'ascending', 'method': 'label', 'ignorearticle': True } } )

        # {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter": {"field": "playcount", "operator": "is", "value": "0"}, "limits": { "start" : 0, "end": 75 }, "properties" : ["art", "rating", "thumbnail", "playcount", "file"], "sort": { "order": "ascending", "method": "label", "ignorearticle": True } }
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        self.CheckResponseDict(command, response, ['limits', 'tvshows'])
        if (response['limits']['total'] == 0):
            return []

        return response['tvshows']

    def VideoLibrary_RefreshMovie(self, movieid):
        """ Refresh the information for a single movie.
        """
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.RefreshMovie), movieid={}'.format(movieid)

        command = 'VideoLibrary.RefreshMovie'
        response = self.SendRequest(command, { 'movieid': movieid, 'ignorenfo': False } )
        # response = self.SendRawRequest({"jsonrpc": "2.0", "method": "VideoLibrary.RefreshMovie", "params": { "movieid": movieid, "ignorenfo": False}, "id": 1 })
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        self.CheckResponseOK(command, response)
        return response

    def VideoLibrary_RefreshTVShow(self, tvshowid, refreshepisodes = False):
        """ Refresh the information for a single TV show.
        """
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.RefreshMovie), movieid={}'.format(movieid)

        command = 'VideoLibrary.RefreshTVShow'
        response = self.SendRequest(command, { 'tvshowid': tvshowid, 'ignorenfo': False,
            'refreshepisodes': refreshepisodes } )
        # response = self.SendRawRequest({"jsonrpc": "2.0", "method": "VideoLibrary.RefreshMovie", "params": { "movieid": movieid, "ignorenfo": False}, "id": 1 })
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)

        self.CheckResponseOK(command, response)
        return response

    def VideoLibrary_Scan(self):
        """ Send the command to scan (update) the video library.
        """
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.VideoLibraryScan)'

        command = 'VideoLibrary.Scan'
        response = self.SendRequest(command)
        # if (self.debugLevel >= 2):
        #     print 'DEBUG    response="{}"'.format(response)
        # self.ResponseOK(response)

        self.CheckResponseOK(command, response)
        return response

    def WakeUp(self, waitTime=0.1):
        """ Send a 'noop' action.  This is most often used to 'wake' the
            target machine from the screen saver.

            Raises a ConnectionError if the target machine does not respond.
        """
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.WakeUp) waitTime={}'.format(waitTime)

        command = 'XBMC.GetInfoBooleans'
        response = self.SendRequest(command, {'booleans': ['System.ScreenSaverActive']})
        # if (self.debugLevel >= 1):
        #     print 'DEBUG (KodiJson.WakeUp) System.ScreenSaverActive={}'.format(response['System.ScreenSaverActive'])

        self.CheckResponseDict(command, response, 'System.ScreenSaverActive')

        if (response['System.ScreenSaverActive']):
            command = 'Input.ExecuteAction'
            response = self.SendRequest(command, {'action': 'noop'})
            self.CheckResponseOK(command, response)

            if (waitTime > 0.0):
                time.sleep(waitTime)
