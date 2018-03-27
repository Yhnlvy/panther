class Route(object):
    def __init__(self, pattern, method, entry_point_functions):
        self.pattern = pattern
        self.method = method
        self.entry_point_functions = entry_point_functions

    def __repr__(self):
        ls = []
        ls.append("Pattern: '%s'" % self.pattern)
        ls.append("Method: '%s'" % self.method)

        return '\n'.join(ls)
