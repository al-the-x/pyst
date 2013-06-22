#!/usr/bin/python

"""
    Compatibility of different python versions.
    Goal for now is to run on 2.6, 2.7 and 3.3 onwards.
    We skip versions prior to 2.6 and 3.1, 3.2, see Armin Ronachers blog
    post at http://lucumr.pocoo.org/2013/5/21/porting-to-python-3-redux/
"""

import sys
PY2 = sys.version_info[0] == 2

# Queue in python3 has moved:
try:
    from Queue import Queue
except ImportError:
    from queue import Queue

# String types, stolen from Armin Ronacher above
if not PY2:
    text_type = str
    string_types = (str,)
    unichr = chr
else:
    text_type = unicode
    string_types = (str, unicode)
    unichr = unichr
