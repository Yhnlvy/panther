
class Function(object):
    def __init__(self, file_path, identifier, node, caller=None):
        self.file_path = file_path
        self.identifier = identifier
        self.node = node
        self.caller = caller

    def __repr__(self):
        ls = []
        ls.append("File Path: '%s'" % self.file_path)
        ls.append("Identifier: '%s'" % (
            '[Anonymous]' if self.identifier is None else self.identifier))
        ls.append("Caller: '%s'" % self.caller)
        return '\n'.join(ls)
