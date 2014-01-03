
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

