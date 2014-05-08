"""
Forked from fuzzywuzzy module

Copyright (c) 2011 Adam Cohen

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from __future__ import unicode_literals
import sys, re, string, unicodedata

PY3 = sys.version_info[0] == 3

try:
    from StringMatcher import StringMatcher as SequenceMatcher
except:
    from difflib import SequenceMatcher

try:
    from IPython import embed
except ImportError:
    print("IPython debugging unavailable")
    pass



#########################################
# Scoring Functions for String Matching #
#########################################


def fuzz_ratio(s1,  s2):

    if s1 is None: raise TypeError("s1 is None")
    if s2 is None: raise TypeError("s2 is None")
    s1, s2 = make_type_consistent(s1, s2)
    if len(s1) == 0 or len(s2) == 0:
        return 0

    m = SequenceMatcher(None, s1, s2)
    return intr(100 * m.ratio())

# todo: skip duplicate indexes for a little more speed
def fuzz_partial_ratio(s1,  s2):

    if s1 is None: raise TypeError("s1 is None")
    if s2 is None: raise TypeError("s2 is None")
    s1, s2 = make_type_consistent(s1, s2)
    if len(s1) == 0 or len(s2) == 0:
        return 0

    if len(s1) <= len(s2):
        shorter = s1; longer = s2;
    else:
        shorter = s2; longer = s1

    m = SequenceMatcher(None, shorter, longer)
    blocks = m.get_matching_blocks()

    # each block represents a sequence of matching characters in a string
    # of the form (idx_1, idx_2, len)
    # the best partial match will block align with at least one of those blocks
    #   e.g. shorter = "abcd", longer = XXXbcdeEEE
    #   block = (1,3,3)
    #   best score === ratio("abcd", "Xbcd")
    scores = []
    for block in blocks:
        long_start   = block[1] - block[0] if (block[1] - block[0]) > 0 else 0
        long_end     = long_start + len(shorter)
        long_substr  = longer[long_start:long_end]

        m2 = SequenceMatcher(None, shorter, long_substr)
        r = m2.ratio()
        if r > .995: return 100
        else: scores.append(r)

    return int(100 * max(scores))


def make_type_consistent(s1, s2):
    if not PY3:
        if isinstance(s1, str) and isinstance(s2, str):
            return s1, s2
        elif isinstance(s1, unicode) and isinstance(s2, unicode):
            return s1, s2
        else:
            return unicode(s1), unicode(s2)
    else:
        return s1, s2

def intr(n):
    '''Returns a correctly rounded integer'''
    return int(round(n))
