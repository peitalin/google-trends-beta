#!/usr/bin/env python
# encoding: utf-8


from sys import version_info
py3 = version_info.major == 3

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
        # obtained only from cik-file argument
        self.cik = None
        self.filing_date = None
        self.querycounts = None

    def add_interest_data(self, date, count):
        self.interest.append((date, count))

    def add_regional_interest(self, date, count):
        self.regional_interest.append((date, count))


    def __unicode__(self):
        # Returns query to stdout
        if self.topic:
            return "{0} ({1})".format(self.title, self.desc)
        else:
            return self.keyword

    def __repr__(self):
        return self.__unicode__()



