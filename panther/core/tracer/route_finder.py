from panther.core.tracer.entities.function import Function
from panther.core.tracer.entities.route import Route
from panther.core.tracer.file_extractor import FileExtractor
from panther.core import utils
from panther.core.visitor import CallExpression
from panther.core.visitor import FunctionExpression
from panther.core.visitor import Identifier
from panther.core.visitor import MemberExpression


class RouteFinder(object):

    def __init__(self):
        self.methods = ['get', 'post', 'put', 'delete', 'patch']
        self.extractor = FileExtractor()

    def create_routes(self, file_path):
        '''Tries to find routes of a file.
            Supported Patterns:
            app.method() where app is a free choice.
        '''
        program = self.extractor.get_program(file_path)
        routes = []
        for node in program.traverse():
            if isinstance(node, CallExpression):
                for method in self.methods:
                    if utils.match_name_space(node, ['*', '*' + method]):
                        # Check whether we have any arguments
                        if node.arguments:
                            # First argument is a pattern.
                            first_arg = node.arguments[0]
                            found_string = utils.try_extract_string_value(
                                first_arg)
                            if found_string is not None:
                                function_list = []
                                # Loop over remaining arguments.
                                for arg in node.arguments[1:]:
                                    # If it is a function expression it is an anonymous call back.
                                    if isinstance(arg, FunctionExpression):
                                        function_list.append(
                                            Function(file_path=file_path, identifier=arg.id, node=arg))
                                    # If it is a member expression it is callback from another file.
                                    elif isinstance(arg, MemberExpression):
                                        if isinstance(arg.object, Identifier) and isinstance(arg.property, Identifier):
                                            function = self.extractor.try_fetch_function(
                                                file_path, arg.object.name, arg.property.name)
                                            if function:
                                                function.caller = '%s.%s' % (arg.object.name, arg.property.name)
                                                function_list.append(function)
                                rt = Route(pattern=found_string, method=method.upper(),
                                           entry_point_functions=function_list)
                                routes.append(rt)
        return routes
