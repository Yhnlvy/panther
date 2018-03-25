
class Function(object):
    def __init__(self, file_path, identifier, node):
        self.file_path = file_path
        self.identifier = identifier
        self.node = node

    def __repr__(self):
        ls = []
        ls.append("File Path: '%s'" % self.file_path)
        ls.append("Identifier: '%s'" % '[Anonymous]' if self.identifier is None else self.identifier)
        # ls.append("Node: '%s'" % self.node.dict())

        return '\n'.join(ls)
