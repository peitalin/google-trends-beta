#!/usr/bin/env python
# encoding: utf-8

import requests, sys
from google_class import AuthException

py3 = sys.version_info[0] == 3
if not py3:
    from urlparse import urlparse
else:
    from urllib.parse import urlparse

try:
    from IPython import embed
except ImportError:
    pass

DEFAULT_LOGIN_URL = "https://accounts.google.com.au/ServiceLogin"
DEFAULT_AUTH_URL = "https://accounts.{domain}/ServiceLoginAuth"



def authenticate_with_google(username, password, login_url=DEFAULT_LOGIN_URL, auth_url=DEFAULT_AUTH_URL):
    """ Authenticates with Google using their user login portal.
        This is necessary rather than using something like OAuth since they don't have a trends API.

        Arguments:
            --username:  Username of Google account holder
            --password:  Password of Google account holder
            --login_url: Address to use for stage-1 authentication
            --auth_url:  Address to use for stage-2 authentication
        Returns a set of cookies to use for subsequent requests.
    """

    # first get the cookie from the login page
    sess = requests.Session()
    login_response = requests.get(login_url, allow_redirects=True, verify=False)
    galx, gaps = login_response.cookies["GALX"], login_response.cookies["GAPS"]
    domain = urlparse(login_response.url).netloc
    domain = domain.replace("accounts.", "")

    # now post to the auth service with this cookie and the creds
    post_data = {"Email": username, "Passwd": password, "PersistentCookie": "yes",
                 "GALX": galx, "continue": "http://www.{domain}/trends".format(domain=domain)}
    post_cookies = {"GALX": galx, "GAPS": gaps}
    response = sess.post(auth_url.format(domain=domain), files={"junk" : ""}, data=post_data,
                         cookies=post_cookies, allow_redirects=True, verify=False)


    if response.status_code==200:
        print("="*60 )
        print("Google login successful, status code: {s}".format(s=response.status_code))
    else:
        raise AuthException("Google login was unsuccessful, " +
                            "status code: {0}".format(response.status_code))


    # make a request to the homepage to get the pref and nid cookies
    cookie_resp = sess.get("https://www.{domain}".format(domain=domain), verify=False, allow_redirects=True)

    # all_requests = (login_response, response, cookie_resp, sess)
    # keyscookies = ("login_response", "response", "cookie_resp", "sess")
    # cookies_keys = dict(zip(keyscookies, map(lambda x: x.cookies.keys(), all_requests)))
    # embed()


    cookies = {"I4SUserLocale" : "en_US"}
    for key in response.cookies.keys():
        if key in ("NID", "PREF", "SID"):
            cookies[key] = response.cookies[key]

    for key in cookie_resp.cookies.keys():
        if key in ("NID", "PREF", "SID"):
            cookies[key] = cookie_resp.cookies[key]

    if "NID" not in cookies and "SID" not in cookies:
        raise AuthException("Failed to read the necessary SID & NID cookies. " +
            "This may indicate that Google has changed their login process " +
            "or the supplied google account details are incorrect.")


    return sess, cookies, domain
