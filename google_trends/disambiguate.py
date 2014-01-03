
import json, re
from fuzzywuzzy import fuzz
from g_classes import KeywordData

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



def disambiguate_keywords(keyword_generator, session, cookies, url=ENTITY_QUERY_URL,
                          primary_types=PRIMARY_TYPES , backup_types=BACKUP_TYPES,
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

        Returns a sequence of KeywordData
    """

    data = []
    try:
        for keyword in keyword_generator:
            entity_data = session.get(url, params={"q": keyword})
            try:
                entities = json.loads(entity_data.content.decode('utf-8'))["entityList"]
                firms = [e for e in entities if e['type'].lower() in primary_types]
                if not firms:
                    firms = [e for e in entities if e['type'].lower() in backup_types]

                # fuzzywuzzy import fuzz -> fuzzy string matching to analyst string match
                if firms:
                    common_tokens = ["Securities", "Investments", "Partners"]
                    sub_keyword = list(map(lambda x: re.sub(x, "", keyword).strip(), common_tokens))
                    fuzz_scores = list(map(lambda x: fuzz.ratio(sub_keyword, x), firms))
                    if max(zip(fuzz_scores, firms))[1] > 50:
                        meanings = max(zip(fuzz_scores, firms))[1]
                    else:
                        meanings = None
                else:
                    meanings = None

            except ValueError: # thrown when content is not JSON (i.e. automated queries message)
                raise QuotaException("The request quota has been reached. " +
                            "This may be the daily quota (~500 queries?) or the rate limiting quota." +
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


