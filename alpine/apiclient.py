import os
import sys

import requests

from .alpineobject import AlpineObject
from .job import Job
from .user import User
from .workfile import Workfile
from .workspace import Workspace
from .datasource import DataSource
from .exception import *


class APIClient(AlpineObject):
    """
    The main entry point for the Alpine API. Most of the functions require a logged-in user. Begin a session by
    creating an instance of the :class:`APIClient` class.

    Example::

        >>> import alpine as AlpineAPI
        >>> session = AlpineAPI.APIClient(host, port, username, password)

    """

    user = None
    datasource = None
    workspace = None
    workfile = None
    job = None

    def __init__(self, host=None, port=None, username=None, password=None, is_secure=False, validate_certs=False,
                 ca_certs=None, token=None, logging_level='WARN'):
        """
        Sets internal values for Alpine API session. If username and password are supplied then a login is
        attempted. This is useful to check Alpine url and user login parameters.

        :param str host: Hostname or ip address of the Alpine server.
        :param str port: Port number for Alpine.
        :param str username: Username to login with.
        :param str password: Password to login with.
        :param bool is_secure: True for https else false.
        :param bool validate_certs:
        :param ca_certs:
        :param str token: Alpine API authentication token.
        :param str logging_level: Use to set the logging level.
        See https://docs.python.org/2/howto/logging.html#logging-levels.
        :return: None
        """

        super(APIClient, self).__init__(token=token)
        self._setup_logging(default_level=logging_level)
        self.is_secure = is_secure

        if is_secure:
            self.protocol = 'https'
        else:
            self.protocol = 'http'

        if not port:
            self.host = host
        if port == 80:
            self.host = host
        else:
            self.host = "{0}:{1}".format(host, port)

        self.session = requests.Session()  # instantiate a session for requests

        self.base_url = "{0}://{1}/api".format(self.protocol, self.host)

        self.ca_certs = ca_certs
        self.validate_certs = validate_certs
        self.user_id = None
        if username and password:
            self.login(username, password)

    def login(self, username, password):
        """
        Attempts a login to Alpine with provided username and password. Typically login is handled at
        session-creation time.

        :param str username: Username to login with.
        :param str password: Password to login with.
        :return: Logged-in user's metadata.
        :rtype: dict

        Example::

            >>> user_info = session.login(username, password)

        """
        # build the url string and body payload
        url = "{0}/sessions?session_id=NULL".format(self.base_url)
        # url = self.base_url + "/sessions?session_id=NULL"
        body = {"username": username, "password": password}
        # TODO login with cert.
        cert_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])),
                                 "../host_deploy/resource/ssl/certificates/test.crt")

        key_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])),
                                "../host_deploy/resource/ssl/certificates/test.key")

        self.session.headers.update({"Content-Type": "application/x-www-form-urlencoded"})

        if self.protocol == 'http':
            login_response = self.session.post(url, data=body)
        else:
            login_response = self.session.post(url, data=body,
                                               verify=self.validate_certs, cert=(cert_path, key_path),
                                               headers={'Connection': 'close'})
        if login_response.status_code == 201:
            response = login_response.json()
            self.token = response['response']['session_id']
            self.user_id = response['response']['user']['id']
            self.logger.debug("Successfully logged in with username <{0}>".format(username))
            self.logger.debug("Token ID is: {0}".format(self.token))
            self.user = User(self.base_url, self.session, self.token)
            self.datasource = DataSource(self.base_url, self.session, self.token)
            self.workspace = Workspace(self.base_url, self.session, self.token)
            self.workfile = Workfile(self.base_url, self.session, self.token)
            self.job = Job(self.base_url, self.session, self.token)
            return login_response.json()['response']['user']

        else:
            raise LoginFailureException("Login failed with status code: <{0}>.".format(login_response.status_code))

    def logout(self):
        """
        Attempts logout current user.

        :return: Request response.
        :rtype: requests.models.Response

        Example::

            >>> session.logout()
            <Response [200]>

        """
        url = "{0}/sessions?session_id={1}".format(self.base_url, self.token)
        logout_response = self.session.delete(url)
        self.logger.debug("Received response code {0} with reason {1}".format(logout_response.status_code,
                                                                              logout_response.reason))
        self.user = None
        self.datasource = None
        self.workspace = None
        self.workfile = None
        self.user = None
        self.datasource = None

        # parse status codes here:
        status = logout_response.status_code
        if logout_response.status_code == 200:
            self.logger.debug("Successfully logged-out.")
            return logout_response
        elif logout_response.status_code == 401:
            self.logger.debug("No user is logged-in.")
            return logout_response
        else:
            self.logger.debug("Failure with status code: {0}".format(status))
            return logout_response

    def get_status(self):
        """
        Returns information about the currently logged-in user. Or, if no user if logged-in, returns an empty dict.

        :return: Logged-in user's metadata.
        :rtype: dict

        Example::

            >>> session.get_status()
            {u'admin': True,
             u'auth_method': u'internal',
             u'dept': u'Development',
             u'email': u'demoadmin@alpinenow.com',
             u'entity_type': u'user',
             u'first_name': u'Demo',
             u'id': 665,
             u'image': {u'complete_json': True,
              u'entity_type': u'image',
              u'icon': u'/users/665/image?style=icon&1483606634',
              u'original': u'/users/665/image?style=original&1483606634'},
             u'is_deleted': None,
             u'last_name': u'Admin',
             u'ldap_group_id': None,
             u'notes': u'',
             u'roles': [u'admin'],
             u'subscribed_to_emails': True,
             u'tags': [],
             u'title': u'Assistant to the Regional Manager',
             u'user_type': u'analytics_developer',
             u'username': u'demoadmin',
             u'using_default_image': True}

        """
        url = "{0}/sessions".format(self.base_url)
        self.logger.debug("Checking to see if the user is still logged in....")
        response = self.session.get(url)
        self.logger.debug("Received response code {0} with reason {1}".format(response.status_code, response.reason))

        try:
            return response.json()['response']['user']
        except:
            return {}

    def get_version(self):
        """
        Returns the Alpine version.

        :return: Alpine version.
        :rtype: str

        Example::

            >>> session.get_version()
            '6.2.0.0.1-b8c02ca46'

        """
        url = "{0}/VERSION".format(self.base_url)
        response = self.session.get(url)
        return response.content.strip().decode('utf-8')

    def get_license(self):
        """
        Get the the current license information for Alpine.

        :return: Summary of Alpine license information - expiration, user limits, add-ons, etc.
        :rtype: dict

        Example::

            >>> license_info = session.get_license()

        """
        url = self.base_url + "/license"
        response = self.session.get(url)
        try:
            return response.json()['response']
        except:
            return {}
