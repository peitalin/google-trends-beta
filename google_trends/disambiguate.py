#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import
from google_class import KeywordData, QuotaException
from fuzzymatch.utils import fuzz_ratio, fuzz_partial_ratio
from entity_types import PRIMARY_TYPES, BACKUP_TYPES
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

PRIMARY_TYPES = {
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
    'company'
}

BACKUP_TYPES = {
    'business',
    'commercial bank business',
    'organization leader',
    'business operation',
    'restaurant',
    'brand',
    'investment',
    'website',
    'service',
    'designer'
}

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
                    fuzz_scores = list(map(lambda x: fuzz_ratio(keyword, x['title']), firms))
                    if max(fuzz_scores) > 60:
                        meanings = max(zip(fuzz_scores, firms))[1]
                    else:
                        meanings = None
                else:
                    meanings = None

            except ValueError: # thrown when content is not JSON (i.e. automated queries message)
                raise QuotaException("The request quota has been reached. " +
                            "This may be the daily quota (~500 queries?) or the rate limiting quota. " + "Couldn't load entity data.")

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







