#!/usr/bin/env python

#############################################################
# Google Trends Query Utility
# Author: Dan Garant (dgarant@cs.umass.edu)
# Modified 29/12/13 Peita Lin (peita_lin@hotmail.com)
#
# Can be used with command-line invocation or as a call from another package.
# Non-standard dependencies: argparse, requests, arrow, fuzzywuzzy
#############################################################

from __future__ import print_function
import os, sys, csv, re, random, json, argparse
import requests, arrow
from time import sleep

from fuzzywuzzy import fuzz


python3 = sys.version_info.major==3
if not python3:
    from urlparse import urlparse
else:
    from urllib.parse import urlparse

try:
    from IPython import embed
except ImportError("IPython debugging unavailable"):
    pass


DEFAULT_LOGIN_URL = "https://accounts.google.com.au/ServiceLogin"
DEFAULT_AUTH_URL = "https://accounts.{domain}/ServiceLoginAuth"
DEFAULT_TRENDS_URL = "http://www.{domain}/trends/trendsReport"
# okay to leave domain off here since it's a GET request, redirects are no problem
ENTITY_QUERY_URL = "http://www.google.com/trends/entitiesQuery"
DEFAULT_OUTPUT_PATH = "./output-file"
INTEREST_OVER_TIME_HEADER = "Interest over time"
EXPECTED_CONTENT_TYPE = "text/csv; charset=UTF-8"
NUM_KEYWORDS_PER_REQUEST = 1
### WARNING: 1 keyword per request, otherwise Google Trends returns RELATIVE search frequencies of keywords.


class AuthException(Exception):
    """ Indicates a failure occurred while logging in"""
    pass

class FormatException(Exception):
    """ Indicates that there is some problem with the format of the trends data """
    pass

class QuotaException(Exception):
    """ Indicates that the quota has been exceeded """
    pass

class KeywordData(Exception):
    """ Represents a keyword and its data """

    def __init__(self, keyword, orig_keyword=None):
        """ Creates some keyword data with the original query """
        self.keyword = keyword
        self.orig_keyword = orig_keyword if orig_keyword else keyword
        self.interest = []
        self.regional_interest = []
        # obtained by disambiguation:
        self.title = None
        self.topic = None
        self.desc = None

    def add_interest_data(self, date, count):
        self.interest.append((date, count))

    def add_regional_interest(self, date, count):
        self.regional_interest.append((date, count))

    def __unicode__(self):
        if self.topic:
            try:
                return u"{0} ({1})".format(unicode(self.title, "UTF-8"),
                                           unicode(self.desc, "UTF-8"))
            except TypeError:
                return u"{0} ({1})".format(self.title, self.desc)
        else:
            try:
                return unicode(self.keyword, "UTF-8")
            except TypeError:
                return self.keyword

    def __repr__(self):
        return self.__unicode__()



def main():
    """Parses arguments and initiates the trend querying process."""

    help_docs = {
        # Group 1: mutually exclusive arguments
        '--keywords': "A comma-separated list of phrases to query. Replaces --batch-input.",
        '--file': "filepath containing newline-separated trends query terms.",
        # Group 2: mutually exclusive arguments
        '--start-date': "Start date for the query in the form yyyy-mm",
        '--all-quarters': "Loops keyword through multiple quarters from a starting date: --all-quarters 2004-01. This returns daily data if available.",
        '--all-years': "Loops keyword through multiple years from a starting year: --all-years 2007. This usually returns weekly data.",
        # General Arguments
        '--end-date': "End date for the query in the form yyyy-mm",
        '--output': "Directory to write CSV files to, otherwise writes results to std out.",
        '--username': "Username of Google account to use when querying trends.",
        '--password': "Password of Google account to use when querying trends.",
        '--login-url': "Address of Google's login service.",
        '--auth-url': "Authenticate URL: Address of Google's login service.",
        '--trends-url': "Address of Google's trends querying URL.",
        '--throttle': "Number of seconds to space out requests, this is to avoid rate limiting.",
        '--category': "Category for queries, e.g 0-7-107 for category->finance->investing. See categories.txt"
    }

    command_line_args = (
        #[0]flag            [1]arg-name(dest)    [2]default
        # Group 1: mutually exclusive arguments
        ('--keywords',      "keywords",          None),
        ('--file',          "batch_input_path",  None),
        # Group 2: mutually exclusive arguments
        ('--start-date',    "start_date",        arrow.utcnow().replace(months=-2)),
        ('--all-quarters',  "all_quarters",      None),
        ('--all-years',      "all_years",        None),
        # General Arguments
        ('--end-date',      "end_date",          arrow.utcnow()),
        ('--output',        "batch_output_path", "terminal"),
        ('--username',      "username",          None),
        ('--password',      "password",          None),
        ('--login-url',     "login_url",         DEFAULT_LOGIN_URL),
        ('--auth-url',      "auth_url",          DEFAULT_AUTH_URL),
        ('--trends-url',    "trends_url",        DEFAULT_TRENDS_URL),
        ('--throttle',      "throttle",          0),
        ('--category',      "category",          None)
    )


    parser = argparse.ArgumentParser(prog="trends.py")
    arg_group1 = parser.add_mutually_exclusive_group()
    arg_group2 = parser.add_mutually_exclusive_group()
    # Mutually exclusive arguments
    list(map(lambda A: arg_group1.add_argument(A[0], help=help_docs[A[0]], dest=A[1], default=A[2]),
                                        command_line_args[:2]))
    list(map(lambda A: arg_group2.add_argument(A[0], help=help_docs[A[0]], dest=A[1], default=A[2]),
                                        command_line_args[2:5]))
    list(map(lambda A: parser.add_argument(A[0], help=help_docs[A[0]], dest=A[1], default=A[2]),
                                        command_line_args[5:]))

    def missing_args(args):
        "Makes sure essential arguments are supplied."
        if not (args.password or args.username):
            sys.stderr.write("ERROR: Use the --username and --password flags with a Google account.\n")
            sys.exit(5)
        elif not (args.keywords or args.batch_input_path):
            sys.stderr.write("ERROR: Specify --keywords or --file, try --help for details.\n")
            sys.exit(5)
        else:
            return None

    args = parser.parse_args()
    if not missing_args(args):
        if args.keywords: # Single input
            keywords = set([k.strip() for k in args.keywords.split(",")])
        else:
            with open(args.batch_input_path, 'r') as source:
                keywords = {l.strip() for l in source.readlines() if l.strip() != ""}


    def keyword_generator(keywords):
        """Shuffles keywords to avoid concurrent processes working on the same keyword.
        By default: NUM_KEYWORDS_PER_REQUEST = 1
        WARNING: Use just 1 keyword per request, otherwise Google Trends returns relative interest over time between keywords.
        """
        random.shuffle(list(keywords))
        for keyword in keywords:
            if os.path.exists(os.path.join(args.batch_output_path, csv_name(keyword))):
                continue
            yield keyword


    start_date = YYYY_MM(args.start_date)
    end_date = YYYY_MM(args.end_date)
    trend_generator = get_trends(keyword_generator(keywords), trends_url=args.trends_url,
                                 all_years=args.all_years,    all_quarters=args.all_quarters,
                                 start_date=start_date,       end_date=end_date,
                                 username=args.username,      password=args.password,
                                 throttle=args.throttle,      category=args.category)


    def csv_name(keyword, start_date=arrow.utcnow().replace(months=-2), category=""):
        """ Converts keyword into filenames: 'keyword_date_category_quarterly.csv' """
        filename = keyword + "_" + args.start_date.format("YYYY-MMM")
        if args.category:
            filename += "_" + args.category
        if args.all_quarters:
            filename += "_" + "quarterly"
        return "".join([c for c in filename if c.isalpha() or c.isdigit() or c==' ' or c=='_']).rstrip() + ".csv"


    def output_results(handle, keyword_data):
        writer = csv.writer(handle)
        writer.writerow(["Date", keyword_data.orig_keyword])
        [writer.writerow([str(s) for s in interest])
                                 for interest in keyword_data.interest]


    for keyword_data in trend_generator:
        if args.batch_output_path == "terminal":
            handle = sys.stdout
            output_results(handle, keyword_data)
        else:
            if not os.path.exists(args.batch_output_path):
                os.makedirs(args.batch_output_path)
            with open(os.path.join(args.batch_output_path, csv_name(keyword_data.orig_keyword)), 'w+') as handle:
                output_results(handle, keyword_data)





def get_trends(keyword_gen, username=None, password=None,
               trends_url=DEFAULT_TRENDS_URL, login_url=DEFAULT_LOGIN_URL, auth_url=DEFAULT_AUTH_URL,
               throttle=0, category=None, all_quarters=None, all_years=None,
               start_date=arrow.utcnow().replace(months=-2), end_date=arrow.utcnow()):
    """ Gets a collection of trends. Requires --keywords, --username and --password flags.

        Arguments:
            --keywords: The sequence of keywords to query trends on
            --trends_url: The address at which we can obtain trends
            --username: Username to provide when authenticating with Google
            --password: Password to provide when authenticating with Google
            --throttle: Number of seconds to wait between requests
            --categories: A category specification such as 0-7-37 for banking
            --start_date: The earliest records to include in the query
            --end_date: The oldest records to include in the query

        Returns a generator of KeywordData
    """

    def throttle_rate(seconds):
        """Throttles query speed in seconds. Try --throttle "random" (1~3 seconds)"""
        if str(seconds).isdigit() and seconds > 0:
            sleep(float(seconds))
        elif seconds=="random":
            sleep(float(random.randint(1,3)))

    def query_parameters(start_date, end_date, keywords, category):
        "Formats query parameters into a dictionary and passes to session.get()"
        months = int(max((end_date - start_date).days, 30) / 30) # Number of months back
        params = {"export": 1, "content": 1}
        params["date"] = "{0} {1}m".format(start_date.strftime("%m/%Y"), months)
        # combine topics into a joint query.  q: query
        params["q"] = ", ".join([k.topic for k in keywords])
        if category:
            params["cat"] = category
        return params

    def get_response(url, params, cookies):
        "Calls GET and returns a list of the reponse data."
        response = sess.get(url, params=params, cookies=cookies, allow_redirects=True, stream=True)
        # #cat=0-7-37&q=%2Fm%2F01xdn1&cmpt=q

        if response.headers["content-type"] == EXPECTED_CONTENT_TYPE:
            if sys.version_info.major==3:
                return [x.decode('utf-8') for x in response.iter_lines()]
            else:
                return list(response.iter_lines())
        elif response.headers["content-type"] == 'text/html; charset=UTF-8':
            if "quota" in response.text.strip().lower():
                raise QuotaException("The request quota has been reached. " +
                            "This may be either the daily quota (~500 queries?) or the rate limiting quota. " +
                            "Try adding the --throttle argument to avoid rate limiting problems.")
            else:
                # print(response.text.strip().lower())
                raise FormatException(("Unexpected content type {0}. " +
                    "Maybe an invalid category or date was supplied".format(response.headers["content-type"])))

    def process_response(response_data):
        "Filters raw response.get data for dates and interest over time counts."
        try:
            start_row = response_data.index(INTEREST_OVER_TIME_HEADER)
        except ValueError: # no data, just return
            return response_data

        formatted_data = []
        for line in response_data[start_row+1:]:
            if line.strip() == "":
                break # reached end of interest over time
            else:
                formatted_data.append(line.strip().split(','))
        return formatted_data

    def check_no_data(queried_data):
        "Check if query is empty. If so, format data appropriately."

        if 'Worldwide; ' in queried_data[1] and queried_data[2]=="":
            try:
                queried_data = [arrow.get(queried_data[1].replace('Worldwide; ',''), 'MMM YYYY'), 0]
            except:
                queried_data = [arrow.get(queried_data[1].replace('Worldwide; ',''), 'YYYY'), 0]
                pass
            print("No interest data found for '{0}'".format(keywords[0].title))
            return [queried_data]
        else:
            return queried_data[1:]



    sess, cookies, domain = authenticate_with_google(username, password,
                                                     login_url=login_url,
                                                     auth_url=auth_url)
    while True:
        try:         # try to get correct keywords
            keywords = disambiguate_keywords(keyword_gen, sess, cookies)
        except StopIteration:
            break
        for keyword in keywords:
            print("="*60, "\n", keyword.title, "({desc})".format(desc=keyword.desc))


        if all_quarters or all_years: # Rolling queries
            if all_quarters:
                start_range = arrow.Arrow.range('month', YYYY_MM(all_quarters), YYYY_MM(start_date))
                ended_range = arrow.Arrow.range('month', YYYY_MM(all_quarters).replace(months=+3), YYYY_MM(end_date).replace(months=+3))
                start_range = [r.datetime for r in start_range][::3]
                ended_range = [r.datetime for r in ended_range][::3]
                ended_range[-1] = YYYY_MM(arrow.utcnow()).datetime # Set last date to current month
            elif all_years:
                start_range = arrow.Arrow.range('year', YYYY_MM(all_years), YYYY_MM(start_date))
                ended_range = arrow.Arrow.range('year', YYYY_MM(all_years).replace(years=+1), YYYY_MM(end_date).replace(years=+1))
                start_range = [r.datetime for r in start_range]
                ended_range = [r.datetime for r in ended_range]
                ended_range[-1] = YYYY_MM(arrow.utcnow()).datetime # Set last date to current month

            all_data = []
            for start, end in zip(start_range, ended_range):
                print("Querying period: {start} ~ {end}".format(start=start.date(), end=end.date()))
                throttle_rate(throttle)
                params = query_parameters(start, end, keywords, category)
                queried_data = check_no_data(
                                    process_response(
                                        get_response(trends_url.format(domain=domain), params, cookies)))
                all_data.append(queried_data)
            heading = ["Date", keywords[0].title]
            all_data = [heading] + sum(all_data, [])

        else: # Single period queries
            throttle_rate(throttle)
            params = query_parameters(start_date, end_date, keywords, category)
            all_data = check_no_data(
                            process_response(
                                get_response(trends_url.format(domain=domain), params, cookies)))
            heading = ["Date", keywords[0].title]
            all_data = [heading] + all_data



        # assign (date, counts) to each KeywordData object
        for row in all_data[1:]:
            if row[1] == "":
                break
            date, counts = parse_row(row)
            for i in range(len(counts)):
                try:
                    keywords[i].add_interest_data(date, counts[i])
                except:
                    print("No interest data found for {0}, keywords: {1}".format(all_data[0][1:], keywords))
                    raise

        for kw in keywords:
            yield kw



def parse_row(raw_row):
    """ Parses a raw row of data into a more meaningful representation
        Arguments: raw_row -- A list of strings

        Returns a 2-tuple (date, [count1, count2, ..., countn])
        representing a date and associated counts for that date"""
    # raw_date, *counts = [x for x in raw_row] # python 3.3 feature only.

    raw_date = raw_row[0]
    if type(raw_date) == str:
        try:
            if len(raw_date) > 10: # indicates date range rather than date, grab first
                raw_date = raw_date[:10]
        except Exception:
            raise FormatException("Unable to parse data from row {0}.".format(raw_row))
    date_obj = arrow.get(raw_date).date()
    counts = [int(x) for x in raw_row[1:]]

    return (date_obj, counts)



def YYYY_MM(date_obj):
    """Removes day. Formats dates from YYYY-MM-DD to YYYY-MM. Also turns date objects into Arrow objects."""
    date_obj = arrow.get(date_obj)
    return arrow.get(date_obj.format("YYYY-MM"))



def disambiguate_keywords(keyword_generator, session, cookies, url=ENTITY_QUERY_URL,
                 keywords_to_return=NUM_KEYWORDS_PER_REQUEST):
    """ Extracts a subset of the keywords from the
        generator and maps these keywords to the most
        likely associated topic.

        Arguments:
            keyword_generator -- A generator or raw query terms
            session -- The requests session to issue HTTP calls with
            cookies -- The cookies to use when sending requests
            keywords_to_return -- The maximum number of keywords to return
            url -- The URL to request query disambiguation from

        Returns a sequence of KeywordData"""

    data = []
    try:
        for keyword in keyword_generator:
            entity_data = session.get(url, params={"q": keyword})
            try:

                entities = json.loads(entity_data.content.decode('utf-8'))["entityList"]
                types = ('investment banking company',
                         'financial services company',
                         'investment company',
                         'commercial banking company',
                         'company',
                         'corporation',
                         'conglomerate company')
                         #'consumer electronics company',
                         #'retail company',
                         #'software company',
                         #'energy company',
                         #'website',
                         #'service')

                # fuzzywuzzy import fuzz -> fuzzy string matching
                firms = [e for e in entities if e['type'].lower() in types]
                if firms:
                    common_tokens = ["Securities", "Investments"]
                    sub_keyword = list(map(lambda x: re.sub(x, "", keyword).strip(), common_tokens))
                    fuzz_scores = list(map(lambda x: fuzz.partial_ratio(sub_keyword, x), firms))
                    meanings = max(zip(fuzz_scores, firms))[1]
                else:
                    meanings = None

            except ValueError: # thrown when content is not JSON (i.e. automated queries message)
                raise QuotaException("The request quota has been reached. " +
                            "This may be either the daily quota (~500 queries?) or the rate limiting quota." +
                            "Try adding the --throttle argument to avoid rate limiting problems.")

            if not meanings:
                fixed_keyword = "".join([k for k in keyword if k.isalnum() or k==' ']).lower()
                fixed_keyword = re.sub("\s+", " ", fixed_keyword)
                cur_data = KeywordData(fixed_keyword, keyword)
                cur_data.topic = fixed_keyword
                cur_data.title = fixed_keyword
                cur_data.desc = "Search term"
            else:
                entity_dict = meanings
                cur_data = KeywordData(keyword)
                cur_data.topic = entity_dict["mid"]
                cur_data.title = entity_dict["title"]
                cur_data.desc = entity_dict["type"]
            data.append(cur_data)

            if len(data) == NUM_KEYWORDS_PER_REQUEST:
                break
    except StopIteration:
        pass
    if not data:
        raise StopIteration("No keywords left")

    return data



def authenticate_with_google(username, password, login_url=DEFAULT_LOGIN_URL, auth_url=DEFAULT_AUTH_URL):
    """ Authenticates with Google using their user login portal.
        This is necessary rather than using something like OAuth since they don't have a trends API.

        Arguments:
            --username:  Username of Google account holder
            --password:  Password of Google account holder
            --login_url: Address to use for stage-1 authentication
            --auth_url:  Address to use for stage-2 authentication
        Returns a set of cookies to use for subsequent requests."""

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
        print("="*60)
        print("Google login successful, status code: %s" % response.status_code)
    else:
        raise AuthException("Google login was unsuccessful, " +
                            "status code: {0}".format(response.status_code))
    # make a request to the homepage to get the pref and nid cookies
    cookie_resp = sess.get("https://www.{domain}".format(domain=domain), verify=False, allow_redirects=True)

    try:
        cookies = {"SID" : response.cookies["SID"],
                   "NID" : response.cookies["NID"],
                   "PREF" : cookie_resp.cookies["PREF"],
                   "I4SUserLocale" : "en_US"}
    except KeyError:
        raise AuthException("Failed to read the necessary cookies. " +
                    "This may indicate that Google has changed their login process " +
                    "or the supplied account information is incorrect.")
    return sess, cookies, domain




if __name__ == "__main__":
    main()
    print("="*60)
    print("OK. Done.")

