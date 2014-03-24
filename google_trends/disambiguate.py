#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import
from google_class import KeywordData, QuotaException
from fuzzymatch.utils import fuzz_ratio, fuzz_partial_ratio
import json, re, sys, arrow

py3 = sys.version_info[0] == 3

try:
    from IPython import embed
except ImportError("IPython debugging unavailable"):
    pass



ENTITY_QUERY_URL = "http://www.google.com/trends/entitiesQuery"
NUM_KEYWORDS_PER_REQUEST = 1
## WARNING: 1 keyword per request, otherwise Google Trends returns
## RELATIVE search frequencies of keywords.


PRIMARY_TYPES = (
    'investment banking company',
    'financial services company',
    'finance company',
    'investment company',
    'commercial banking company',
    'commercial bank business',
    'conglomerate company',
    'consumer electronics company',
    'corporation',
    'retail company',
    'software company',
    'energy company',
    'health care company',
    'private equity company',
    'company',
    )

BACKUP_TYPES = (
    'business',
    'commercial bank business',
    'organization leader',
    'business operation',
    'restaurant',
    'brand',
    'investment',
    'website',
    'service',
    'designer',
    )


# try:
#     p = './fuzzymatch/primary-types.txt'
#     b = './fuzzymatch/backup-types.txt'

#     with open(p, 'r') as f:
#         PRIMARY_TYPES = {x.strip() for x in f.readlines()}

#     with open(b, 'r') as f:
#         BACKUP_TYPES = {x.strip() for x in f.readlines()}

# except (IOError, NameError):
#     pass



def disambiguate_keywords(keyword_generator, session, cookies,
                          url=ENTITY_QUERY_URL,
                          primary_types=PRIMARY_TYPES,
                          backup_types=BACKUP_TYPES,
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

        Returns a sequence of KeywordData Objects.
    """

    data = []
    try:
        for keyword in keyword_generator:

            # special cases: --cik-ipos, --ipo-quarters flags.
            ipo_filings = len(keyword) == 3
            if ipo_filings:
                cik, keyword, filing_date = keyword


            entity_data = session.get(url, params={"q": keyword})
            try:
                entities = json.loads(entity_data.content.decode('utf-8'))["entityList"]
                firms = [e for e in entities if e['type'].lower() in primary_types]
                if not firms:
                    firms = [e for e in entities if e['type'].lower() in backup_types]

                # fuzzy string matching to pick best match
                if firms:
                    common_tokens = ["Securities", "Investments", "Partners"]
                    sub_keyword = keyword
                    for c in common_tokens:
                        sub_keyword = re.sub(c, "", sub_keyword).strip()

                    fuzz_scores = list(map(lambda x: fuzz_ratio(sub_keyword, x['title']), firms))
                    if max(fuzz_scores) > 50:
                        meanings = max(zip(fuzz_scores, firms))[1]
                    else:
                        meanings = None
                else:
                    meanings = None

            except ValueError: # thrown when content is not JSON (i.e. automated queries message)
                raise QuotaException("The request quota has been reached. " +
                            "This may be the daily quota (~500 queries?) or the rate limiting quota. " + "Couldn't load entity data.")

            if not meanings:
                if not py3:
                    try:
                        keyword = keyword.encode('utf-8')
                    except:
                        pass
                fixed_keyword = keyword
                kw_data = KeywordData(fixed_keyword, keyword)
                kw_data.topic = fixed_keyword
                kw_data.title = fixed_keyword
                kw_data.desc = "Search term"
            else:
                entity_dict = meanings
                kw_data = KeywordData(keyword)

                if py3:
                    kw_data.topic = entity_dict["mid"]
                    kw_data.title = entity_dict["title"]
                    kw_data.desc = entity_dict["type"]
                else:
                    kw_data.topic = entity_dict["mid"].encode('utf-8')
                    kw_data.title = entity_dict["title"].encode('utf-8')
                    kw_data.desc = entity_dict["type"].encode('utf-8')

            if ipo_filings:
                kw_data.cik = cik
                kw_data.filing_date = filing_date

            data.append(kw_data)


            if len(data) == NUM_KEYWORDS_PER_REQUEST:
                break
    except StopIteration:
        pass
    if not data:
        raise StopIteration("No keywords left")

    return data








def interpolate_ioi(date, ioi):
    """ takes a list of dates and interest over time and
    interpolates the dates. Called by change_in_ioi()"""

    def linspace(start, stop, n):
        start, stop = float(start), float(stop)
        if n == 1:
            yield start
            return
        h = (stop - start) / (n - 1)
        for i in range(n):
            yield start + h * i

    def date_range(date):
        s, e = list(map(arrow.get, [list(date)[0], list(date)[-1]]))
        dates = arrow.Arrow.range('day', s, e)
        return [x.datetime for x in dates]

    date_ioi = list(zip(date, ioi))
    final_elem = []
    interp = []
    for s,e in zip(date_ioi, date_ioi[1:]):
        end_date, start_date = list(map(arrow.get, [e[0], s[0]]))
        # end_ioi, start_ioi = e[1], s[1]
        days = (end_date - start_date).days
        interp += list(linspace(s[1], e[1], days+1))[:-1]
        final_elem = e[1]

    if final_elem:
        interp += [float(final_elem)]

    date = date_range(date)
    return date, interp







def conform_interest_over_time(IoI):
    """ Removes 0's from a list of IoI to calculate percentage changes.
    Called by change_in_ioi(). """
    if not any(IoI):
        return IoI

    try:
        iIoI = iter(IoI)
        t1 = next(iIoI)
        t2 = next(iIoI)
    except StopIteration:
        return [t1]

    new_IoI = []
    new_IoI += [t1]

    for n in range(len(IoI)-2):
        if t2 != 0:
            new_IoI += [t2]
            t1 = t2
        else:
            new_IoI += [t1]
        t2 = next(iIoI)

    if t2 != 0:
        new_IoI += [t2]
    else:
        new_IoI += [t1]

    def average(list_ioi):
        return sum([float(s) for s in list_ioi])/len(list_ioi)

    avg = round(average(IoI))
    new_IoI = [avg if x==0 else x for x in new_IoI]
    return new_IoI



def change_in_ioi(date, IoI):
    """Computes changes in interest over time (IoI) (log base 10).
    date -- list of dates
    IoI  -- list of IoI values
    Returns a list of dates, and list of changes in IoI values. """

    from math import log10, log
    date, IoI = interpolate_ioi(date, IoI)
    IoI = conform_interest_over_time(IoI)
    delta_IoI = [1]

    for f1,f2 in zip(IoI, IoI[1:]):
        f1 = 1 + float(f1)
        f2 = 1 + float(f2)
        relative_effect = log10(f1/f2)
        if relative_effect < 0:
            relative_effect = 0
        delta_IoI.append(1+log10(1+relative_effect))

    return date, delta_IoI





