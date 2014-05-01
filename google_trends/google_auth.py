#!/usr/bin/env python
# encoding: utf-8

import requests, sys, os, re, time
import colorama
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
BASE_DIR = os.path.join(os.path.expanduser("~"), "Dropbox", "gtrends-beta")




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
    print("="*60 + '\n' + 'Starting new session: [{}]'.format(red(username)))
    sess = requests.Session()
    login_response = requests.get(login_url, allow_redirects=True, verify=False)
    galx = login_response.cookies["GALX"]
    gaps = login_response.cookies["GAPS"]
    domain = urlparse(login_response.url).netloc.replace("accounts.", "")

    # now post to the auth service with this cookie and the creds
    post_data = {"Email": username, "Passwd": password,
                 "PersistentCookie": "yes", "GALX": galx,
                 "continue": "http://www.{domain}/trends".format(domain=domain)}
    post_cookies = {"GALX": galx, "GAPS": gaps}

    response = sess.post(auth_url.format(domain=domain),
                        files={"junk" : ""}, data=post_data, cookies=post_cookies,
                        allow_redirects=True, verify=False)


    if response.status_code==200:
        print("Google login successful: status code [{}]".format(green(response.status_code)))
    else:
        raise AuthException("Google login was unsuccessful, " +
                            "status code: {0}".format(response.status_code))

    # make a request to the homepage to get the pref and nid cookies
    cookie_resp = sess.get("https://www.{domain}".format(domain=domain), verify=True, allow_redirects=True)


    cookies = {"I4SUserLocale" : "en_US"}
    for key in response.cookies.keys():
        if key in ("NID", "PREF", "SID"):
            cookies[key] = response.cookies[key]

    for key in cookie_resp.cookies.keys():
        if key in ("NID", "PREF", "SID"):
            cookies[key] = cookie_resp.cookies[key]

    if "NID" not in cookies or "SID" not in cookies:
        print(red("=> Warning! Missing essential SID & NID cookies\n") +
              cyan("=> Trying selenium + phantom.js approach"))

        cookies = phone_verify_for_cookies(username=username, password=password)

    return sess, cookies, domain






def phone_verify_for_cookies(username, password):
    """Emulates browser login with selenium bindings to phantom.js.
    Gives you SID (Google User ID) cookies.

    Requires phone verification.
    This typically happens when you try to login to Google from an unusual location.
    For example, changing Amazon EC2 instances -> different IPs."""

    from selenium import webdriver

    logpath = BASE_DIR + '/phantomjs/{}.log'.format(username)
    driver = webdriver.PhantomJS(service_log_path=logpath)
    login_url = 'https://accounts.google.com/ServiceLogin'
    print("Loading login page: {}".format(login_url))
    driver.get(login_url)

    # get login forms & fill in
    email, passwd, signin = map(driver.find_element_by_id, ['Email', 'Passwd', 'signIn'])
    email.send_keys(username)
    passwd.send_keys(password)
    print(cyan('Authenticating to get SID and NID cookies...'))
    signin.click() # login

    cookies = {}
    for cookie in driver.get_cookies():
        cookies[cookie['name']] = cookie['value']

    if "NID" in cookies.keys() and "SID" in cookies.keys():
        print(green("SID and NID cookies success!"))
        return cookies

    else:
        driver.find_element_by_id("submitChallenge").click()
        driver.save_screenshot(BASE_DIR + '/phantomjs/pic_{}.png'.format(username))
        time.sleep(1)
        code = input(cyan("Enter Google mobile verification code: "))
        while len(code) != 6:
            code = input(red("Re-enter Google [6-digit] verification code: "))
        # code = '502975'
        driver.find_element_by_name("VerifySmsChallengeAnswer").send_keys(code)
        driver.find_element_by_id("submitChallenge").click()

        cookies = {}
        for cookie in driver.get_cookies():
            cookies[cookie['name']] = cookie['value']

    if "NID" in cookies.keys() and "SID" in cookies.keys():
        print(green("SID and NID cookies success!"))
        return cookies

    else:
        raise AuthException(red("=> Didn't get the required SID and NID login cookies. Aborting.\n\nAssuming that login details are correct, check that the account is allowed to login from the IP address this script is launched from.\nRemote servers (AWS EC2) will require phone authentication before Google will allow access to the account."))


################################################
#### Selenium elements for Google login forms

### Continue Button
# <input name="submitChallenge" id="submitChallenge" class="rc-button rc-button-submit" value="Continue" type="submit">

### Verification Code form
# <input name="VerifySmsChallengeAnswer" id="VerifySmsChallengeAnswer" size="30" maxlength="6" dir="ltr" placeholder="Enter verification code" type="text">

### Enter Mobile Number form
# <input name="phoneNumber" id="phoneNumber" size="30" placeholder="Enter full phone number" dir="ltr" type="tel">

### Enter Backup Email form
# <input autocomplete="off" oldautocomplete="remove" name="emailAnswer" id="emailAnswer" size="30" placeholder="Enter full email address" dir="ltr" type="text">

### Verification Code form
# <input class="" id="verify-code-input" autocomplete="off" dir="ltr" maxlength="6" type="text">

##############################################




# clint wrapper for colorama
class ColoredString(object):
    """Enhanced string for __len__ operations on Colored output."""
    def __init__(self, color, s, always_color=False, bold=False):
        super(ColoredString, self).__init__()
        self.s = s
        self.color = color
        self.always_color = always_color
        self.bold = bold
        if os.environ.get('CLINT_FORCE_COLOR'):
            self.always_color = True

    def __getattr__(self, att):
        def func_help(*args, **kwargs):
            result = getattr(self.s, att)(*args, **kwargs)
            try:
                is_result_string = isinstance(result, basestring)
            except NameError:
                is_result_string = isinstance(result, str)
            if is_result_string:
                return self._new(result)
            elif isinstance(result, list):
                return [self._new(x) for x in result]
            else:
                return result
        return func_help

    @property
    def color_str(self):
        style = 'BRIGHT' if self.bold else 'NORMAL'
        c = '%s%s%s%s%s' % (getattr(colorama.Fore, self.color), getattr(colorama.Style, style), self.s, colorama.Fore.RESET, getattr(colorama.Style, 'NORMAL'))

        if self.always_color:
            return c
        elif sys.stdout.isatty() and 'get_ipython' not in dir():
            return c
        else:
            return self.s


    def __len__(self):
        return len(self.s)

    def __repr__(self):
        return "<%s-string: '%s'>" % (self.color, self.s)

    def __unicode__(self):
        value = self.color_str
        if isinstance(value, bytes):
            return value.decode('utf8')
        return value

    if py3:
        __str__ = __unicode__
    else:
        def __str__(self):
            value = self.color_str
            if isinstance(value, bytes):
                return value
            return value.encode('utf8')

    def __iter__(self):
        return iter(self.color_str)

    def __add__(self, other):
        return str(self.color_str) + str(other)

    def __radd__(self, other):
        return str(other) + str(self.color_str)

    def __mul__(self, other):
        return (self.color_str * other)

    def _new(self, s):
        return ColoredString(self.color, s)



def black(string, always=False, bold=False):
    return ColoredString('BLACK', string, always_color=always, bold=bold)

def red(string, always=False, bold=False):
    return ColoredString('RED', string, always_color=always, bold=bold)

def green(string, always=False, bold=False):
    return ColoredString('GREEN', string, always_color=always, bold=bold)

def yellow(string, always=False, bold=False):
    return ColoredString('YELLOW', string, always_color=always, bold=bold)

def blue(string, always=False, bold=False):
    return ColoredString('BLUE', string, always_color=always, bold=bold)

def magenta(string, always=False, bold=False):
    return ColoredString('MAGENTA', string, always_color=always, bold=bold)

def cyan(string, always=False, bold=False):
    return ColoredString('CYAN', string, always_color=always, bold=bold)

def white(string, always=False, bold=False):
    return ColoredString('WHITE', string, always_color=always, bold=bold)

