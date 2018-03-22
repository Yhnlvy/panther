import logging
import os
from panther.core import visitor
from panther.core.visitor import VariableDeclaration,CallExpression, AssignmentExpression, Literal, FunctionExpression, FunctionDeclaration, VariableDeclarator, Identifier, MemberExpression
from panther.core import utils
from panther.core import config
from panther.core import manager
from panther.core.pyesprima import esprima
from panther.core import node_visitor
from panther.core import test_set
from panther.core import metrics
from panther.core import meta_ast

LOG = logging.getLogger(__name__)


class RouteFinder(object):
    def __init__(self):
        self.import_cache = {}
        self.program_cache = {}
        self.function_definition_cache = {}
        self.routes = []
        self.methods = ['get', 'post', 'put', 'delete', 'patch']

    def create_program_cache(self, file_path):
        with open(file_path, 'r') as f:
            code = f.read()
        json_program = esprima.parse(code,{'loc': True})
        ast_program = visitor.objectify(json_program.to_dict())
        self.program_cache[file_path] = ast_program

    def create_import_cache(self, file_path):

        program = self.get_program(file_path)

        imports = {}

        for node in program.traverse():
            if isinstance(node, VariableDeclarator):
                if isinstance(node.id, Identifier) and isinstance(node.init, CallExpression):
                    call_expression = node.init
                    if utils.match_name_space(call_expression, ['*require']) and call_expression.arguments:
                        variable_name = node.id.name
                        candidate_module_path = call_expression.arguments[0]
                        string_module_path = RouteFinder.extract_string_value(
                            candidate_module_path)
                        if string_module_path is not None:
                            if string_module_path.startswith((".", "/")):
                                imports[variable_name] = string_module_path

        self.import_cache[file_path] = imports

    def create_function_definition_cache(self, file_path):
        program = self.get_program(file_path)
        
        print('PROGRAM', program.dict())
        function_definitions = {}
        def check_variable_assignment_function(left_node, right_node):
            if isinstance(right_node, FunctionExpression):
                    expression = left_node
                    function_expression = right_node
                    name_space = utils.extract_name_space_from_expression(
                        expression)
                    last_name = name_space[-1]
                    if last_name.startswith('*'):
                        resolved_name = last_name[1:]
                        return (resolved_name, function_expression)
                         
            return None

        for node in program.traverse():
            if isinstance(node, FunctionDeclaration):
                function_definitions[node.id.name] = node
            elif isinstance(node, AssignmentExpression) and node.operator == '=':
                resolved_assignment = check_variable_assignment_function(node.left, node.right)
                if resolved_assignment:
                    function_definitions[resolved_assignment[0]] = resolved_assignment[1]
            elif isinstance(node, VariableDeclaration):
                for declaration in node.declarations:
                    resolved_assignment = check_variable_assignment_function(declaration.id, declaration.init)
                if resolved_assignment:
                    function_definitions[resolved_assignment[0]] = resolved_assignment[1]

        self.function_definition_cache[file_path] = function_definitions

    def get_imports(self, file_path):
        if file_path not in self.import_cache:
            self.create_import_cache(file_path)
        return self.import_cache[file_path]

    def get_program(self, file_path):
        if file_path not in self.program_cache:
            self.create_program_cache(file_path)

        return self.program_cache[file_path]

    def get_function_definitions(self, file_path):
        if file_path not in self.function_definition_cache:
            self.create_function_definition_cache(file_path)

        return self.function_definition_cache[file_path]

    def create_routes(self, file_path):
        program = self.get_program(file_path)

        for node in program.traverse():
            if isinstance(node, CallExpression):
                for method in self.methods:
                    if utils.match_name_space(node, ['*', '*'+method]):
                        if node.arguments:
                            first_arg = node.arguments[0]
                            found_string = RouteFinder.extract_string_value(
                                first_arg)
                            if found_string is not None:
                                print(found_string)
                                function_list = []
                                for arg in node.arguments[1:]:
                                    if isinstance(arg, FunctionExpression):
                                        function_list.append(
                                            {'file_path': file_path, 'identifier': arg.id, 'node': arg})
                                    elif isinstance(arg, MemberExpression):
                                        print('MEMBERR', arg.dict())
                                        if isinstance(arg.object, Identifier) and isinstance(arg.property, Identifier):
                                            function = self.try_fetch_function(
                                                file_path, arg.object.name, arg.property.name)
                                            if function:
                                                function_list.append(function)

                                self.routes.append(
                                    {'pattern': found_string, 'method': method, 'function_list': function_list})

    def resolve_path(self, file_path, relative_path):
        file_dir = os.path.dirname(file_path)
        return os.path.abspath(os.path.join(file_dir, relative_path+'.js'))

    def try_match_function(self, file_path, identifier):
        print("MATCH FUNCTION")

        function_definitions = self.get_function_definitions(file_path)
        print('FNDEF',function_definitions)
        function_node = function_definitions.get(identifier, None)
        print('NODEEE', function_node)
        if function_node is None:
            return None

        return {'file_path': file_path, 'identifier': identifier, 'node': function_node}

    def try_fetch_function(self, file_path, module_name, identifier):
        print('TRY FETCH')

        imports = self.get_imports(file_path)

        print('IMPORTS',imports, module_name)

        relative_module_path = imports.get(module_name, None)

        print('RELAT', relative_module_path)

        if relative_module_path is None:
            return None

        next_file_path = self.resolve_path(file_path, relative_module_path)

        function = self.try_match_function(next_file_path, identifier)

        if function is None:
            return None

        return function

    def find(self, function):
        file_path = function.file_path
        function_list = []
        for node in function.node:
            function = None
            if isinstance(node, CallExpression):
                if utils.match_name_space(call_expression, ['*']):
                    identifier = utils.extract_name_space(
                        call_expression)[0][1:]
                    function = self.try_match_function(file_path, identifier)
                elif utils.match_name_space(call_expression, ['*', '*']):
                    name_space = utils.extract_name_space(call_expression)
                    module_name = name_space[0][1:]
                    identifier = name_space[1][1:]
                    function = self.try_fetch_function(
                        file_path, module_name, identifier)

            if function:
                function_list.append(function)

    def test(self, file_path, node):

        nv = node_visitor.PantherNodeVisitor(
            file_path, meta_ast.PantherMetaAst(), test_set.PantherTestSet(config, profile=None), True, set(), metrics.Metrics())
        nv.generic_visit(node)
        print((nv.tester.results))
        print(nv.scores)
        return None

    def dive_all(self, file_path, depth=1):
        self.create_routes(file_path)
        print('ROUTES', self.routes)
        for route in self.routes:
            self.dive(route['function_list'], [route], depth)

    def dive(self, stack_node, stack_trace, depth):
        depth -= 1
        for function in stack_node:
            print('TESTING')
            test_result = self.test(function['file_path'], function['node'])
            print('TEST RESULT', test_result)
            if test_result is not None:
                print('I FOUND STH', stack_trace)
            else:
                if depth == 0:
                    print('I AM FINISHED BUT COULDNT FIND:(', stack_trace)
                else:
                    print('I AM GOING TO DIVE FOR LEVEL %d' % depth)
                    other_functions = self.find(function)
                    stack_trace.append(function)
                    self.dive(other_functions, stack_trace, depth)

    @staticmethod
    def extract_string_value(node):
        '''Tries to extract a string from a node.
        '''

        found_string = None

        # If it is a TemplateElement get cooked value.
        # If it is a Literal, check whether raw node starts
        # with either (') or ("").
        if isinstance(node, Literal):
            raw_literal = node.raw
            is_string = raw_literal.startswith(
                '"') or raw_literal.startswith("'")
            if is_string:
                found_string = node.value

        return found_string
