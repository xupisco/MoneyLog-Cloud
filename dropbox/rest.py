"""
A simple JSON REST request abstraction layer that is used by the
dropbox.client and dropbox.session modules. You shouldn't need to use this
directly unless you're implementing new methods we haven't added to the SDK yet.
"""

import httplib
import json
import socket
import urllib
import urlparse
import os

SDK_VERSION = "1.2"

class RESTClient(object):
    """
    An class with all static methods to perform JSON REST requests that is used internally
    by the Dropbox Client API. It provides just enough gear to make requests
    and get responses as JSON data (when applicable). All requests happen over SSL.
    """

    @staticmethod
    def request(method, url, post_params=None, body=None, headers=None, raw_response=False):
        """Perform a REST request and parse the response.

        Args:
            method: An HTTP method (e.g. 'GET' or 'POST').
            url: The URL to make a request to.
            post_params: A dictionary of parameters to put in the body of the request.
                This option may not be used if the body parameter is given.
            body: The body of the request. Typically, this value will be a string.
                It may also be a file-like object in Python 2.6 and above. The body
                parameter may not be used with the post_params parameter.
            headers: A dictionary of headers to send with the request.
            raw_response: Whether to return the raw httplib.HTTPReponse object. [default False]
                It's best enabled for requests that return large amounts of data that you
                would want to .read() incrementally rather than loading into memory. Also
                use this for calls where you need to read metadata like status or headers,
                or if the body is not JSON.

        Returns:
            The JSON-decoded data from the server, unless raw_response is
            specified, in which case an httplib.HTTPReponse object is returned instead.

        Raises:
            dropbox.rest.ErrorResponse: The returned HTTP status is not 200, or the body was
                not parsed from JSON successfully.
            dropbox.rest.RESTSocketError: A socket.error was raised while contacting Dropbox.
        """
        post_params = post_params or {}
        headers = headers or {}
        headers['User-Agent'] = 'OfficialDropboxPythonSDK/' + SDK_VERSION

        if post_params:
            if body:
                raise ValueError("body parameter cannot be used with post_params parameter")
            body = urllib.urlencode(post_params)
            headers["Content-type"] = "application/x-www-form-urlencoded"

        host = urlparse.urlparse(url).hostname
        conn = httplib.HTTPSConnection(host, 443)

        try:

            # This code is here because httplib in pre-2.6 Pythons
            # doesn't handle file-like objects as HTTP bodies and
            # thus requires manual buffering
            if not hasattr(body, 'read'):
                conn.request(method, url, body, headers)
            else:

                #We need to get the size of what we're about to send for the Content-Length
                #Must support len() or have a len or fileno(), otherwise we go back to what we were doing!
                clen = None

                try:
                    clen = len(body)
                except (TypeError, AttributeError):
                    try:
                        clen = body.len
                    except AttributeError:
                        try:
                            clen = os.fstat(body.fileno()).st_size
                        except AttributeError:
                            # fine, lets do this the hard way
                            # load the whole file at once using readlines if we can, otherwise
                            # just turn it into a string
                            if hasattr(body, 'readlines'):
                                body = body.readlines()
                            conn.request(method, url, str(body), headers)

                if clen != None:  #clen == 0 is perfectly valid. Must explicitly check for None
                    clen = str(clen)
                    headers["Content-Length"] = clen
                    conn.request(method, url, "", headers)
                    BLOCKSIZE = 4096 #4MB buffering just because

                    data=body.read(BLOCKSIZE)
                    while data:
                        conn.send(data)
                        data=body.read(BLOCKSIZE)

        except socket.error, e:
            raise RESTSocketError(host, e)

        r = conn.getresponse()
        if r.status != 200:
            raise ErrorResponse(r)

        if raw_response:
            return r
        else:
            try:
                resp = json.loads(r.read())
            except ValueError:
                raise ErrorResponse(r)
            finally:
                conn.close()

        return resp

    @classmethod
    def GET(cls, url, headers=None, raw_response=False):
        """Perform a GET request using RESTClient.request"""
        assert type(raw_response) == bool
        return cls.request("GET", url, headers=headers, raw_response=raw_response)

    @classmethod
    def POST(cls, url, params=None, headers=None, raw_response=False):
        """Perform a POST request using RESTClient.request"""
        assert type(raw_response) == bool
        if params is None:
            params = {}

        return cls.request("POST", url, post_params=params, headers=headers, raw_response=raw_response)

    @classmethod
    def PUT(cls, url, body, headers=None, raw_response=False):
        """Perform a PUT request using RESTClient.request"""
        assert type(raw_response) == bool
        return cls.request("PUT", url, body=body, headers=headers, raw_response=raw_response)

class RESTSocketError(socket.error):
    """
    A light wrapper for socket.errors raised by dropbox.rest.RESTClient.request
    that adds more information to the socket.error.
    """

    def __init__(self, host, e):
        msg = "Error connecting to \"%s\": %s" % (host, str(e))
        socket.error.__init__(self, msg)

class ErrorResponse(Exception):
    """
    Raised by dropbox.rest.RESTClient.request for requests that return a non-200
    HTTP response or have a non-JSON response body.

    Most errors that Dropbox returns will have a error field that is unpacked and
    placed on the ErrorResponse exception. In some situations, a user_error field
    will also come back. Messages under user_error are worth showing to an end-user
    of your app, while other errors are likely only useful for you as the developer.
    """

    def __init__(self, http_resp):
        self.status = http_resp.status
        self.reason = http_resp.reason
        self.body = http_resp.read()

        try:
            body = json.loads(self.body)
            self.error_msg = body.get('error')
            self.user_error_msg = body.get('user_error')
        except ValueError:
            self.error_msg = None
            self.user_error_msg = None

    def __str__(self):
        if self.user_error_msg and self.user_error_msg != self.error_msg:
            # one is translated and the other is English
            msg = "%s (%s)" % (self.user_error_msg, self.error_msg)
        elif self.error_msg:
            msg = self.error_msg
        elif not self.body:
            msg = self.reason
        else:
            msg = "Error parsing response body: %s" % self.body

        return "[%d] %s" % (self.status, repr(msg))
