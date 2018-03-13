# -*- coding:utf-8 -*-


class Context(object):
    def __init__(self, context_object=None):
        '''Initialize the class with a context, empty dict otherwise

        :param context_object: The context object to create class from
        :return: -
        '''
        if context_object is not None:
            self._context = context_object
        else:
            self._context = dict()

    def __repr__(self):
        '''Generate representation of object for printing / interactive use

        Most likely only interested in non-default properties, so we return
        the string version of _context.

        :return: A string representation of the object
        '''
        return "<Context %s>" % self._context

    @property
    def node(self):
        '''Get the raw AST node associated with the context

        :return: The raw AST node associated with the context
        '''
        if 'node' in self._context:
            return self._context['node']
        else:
            return None
