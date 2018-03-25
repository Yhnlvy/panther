import logging
from panther.core import utils
from panther.core.tracer.entities.function import Function
from panther.core.tracer.entities.route import Route
from panther.core.visitor import (CallExpression, FunctionExpression,
                                  Identifier, MemberExpression)
from panther.core.tracer.file_extractor import FileExtractor
LOG = logging.getLogger(__name__)


class RouteFinder(object):

    def __init__(self):
        self.methods = ['get', 'post', 'put', 'delete', 'patch']
        self.extractor = FileExtractor()

    def create_routes(self, file_path):
        program = self.extractor.get_program(file_path)
        routes = []
        for node in program.traverse():
            if isinstance(node, CallExpression):
                for method in self.methods:
                    if utils.match_name_space(node, ['*', '*'+method]):
                        if node.arguments:
                            first_arg = node.arguments[0]
                            found_string = utils.try_extract_string_value(
                                first_arg)
                            if found_string is not None:
                                function_list = []
                                for arg in node.arguments[1:]:
                                    if isinstance(arg, FunctionExpression):
                                        function_list.append(
                                            Function(file_path=file_path, identifier=arg.id, node=arg))
                                    elif isinstance(arg, MemberExpression):
                                        if isinstance(arg.object, Identifier) and isinstance(arg.property, Identifier):
                                            function = self.extractor.try_fetch_function(
                                                file_path, arg.object.name, arg.property.name)
                                            if function:
                                                function_list.append(function)

                                routes.append(
                                    Route(pattern=found_string, method=method, entry_point_functions=function_list))
        return routes
