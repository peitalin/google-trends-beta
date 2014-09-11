#!/usr/bin/env python
# encoding: utf-8


from google_class import KeywordData, QuotaException
import json, re, sys, string, unicodedata
import arrow
from difflib import SequenceMatcher

PY3 = sys.version_info[0] == 3
ENTITY_QUERY_URL = "http://www.google.com/trends/entitiesQuery"
NUM_KEYWORDS_PER_REQUEST = 1
## WARNING: 1 keyword per request, otherwise Google Trends returns
## RELATIVE search frequencies of keywords.



def disambiguate_keywords(keyword_generator, session, cookies,
                          primary_types, backup_types,
                          url=ENTITY_QUERY_URL,
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
            cik_filings = len(keyword) == 3
            if cik_filings:
                cik, keyword, filing_date = keyword


            entity_data = session.get(url, params={"q": keyword})
            try:
                entities = json.loads(entity_data.content.decode('utf-8'))["entityList"]
                firms = [e for e in entities
                        if e['type'].lower() in primary_types or 'company' in e['type']]
                if not firms:
                    firms = [e for e in entities if e['type'].lower() in backup_types]

                # fuzzy string matching to pick best match
                if firms:
                    fuzz_scores = [fuzz_ratio(keyword, dic['title']) for dic in firms]
                    if max(fuzz_scores) > 50:
                        # May potentially have 2 exact matches, e.g. Groupon
                        # Isolate max scores, then pick 1st entry.
                        maxfirms = [tup for tup in zip(fuzz_scores, firms)
                                    if tup[0] == max(fuzz_scores)]
                        meanings = maxfirms[0][1]
                        # select dictionary associated to 1st max entry
                    else:
                        meanings = None
                else:
                    meanings = None

            except ValueError: # thrown when content is not JSON
                raise QuotaException("The request quota has been reached. " +
                                    "This may be the daily quota (~500 queries?)" +
                                    "or the rate limiting quota.")

            if not meanings:
                fixed_keyword = keyword
                kw_data = KeywordData(fixed_keyword, keyword)
                kw_data.topic = fixed_keyword
                kw_data.title = fixed_keyword
                kw_data.desc = "Search term"
            else:
                entity_dict = meanings
                kw_data = KeywordData(keyword)
                kw_data.topic = entity_dict["mid"]
                kw_data.title = entity_dict["title"]
                kw_data.desc = entity_dict["type"]

            if cik_filings:
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





def fuzz_ratio(s1,  s2):
    "Wrapper for difflib sequence matcher"
    assert type(s1) == str
    assert type(s2) == str
    if len(s1) == 0 or len(s2) == 0:
        return 0

    sm = SequenceMatcher(None, s1, s2)
    return round(100 * sm.ratio())



