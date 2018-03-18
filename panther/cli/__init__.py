import sys

from panther.core import constants

# HACK: [Js2Py known issue](https://github.com/PiotrDabkowski/Js2Py/issues/53)
sys.setrecursionlimit(constants.RECURSION_LIMIT)
