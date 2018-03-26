import os
from panther.core.pyesprima import esprima
from panther.core.tracer.entities.function import Function
from panther.core import utils
from panther.core import visitor
from panther.core.visitor import AssignmentExpression
from panther.core.visitor import CallExpression
from panther.core.visitor import FunctionDeclaration
from panther.core.visitor import FunctionExpression
from panther.core.visitor import Identifier
from panther.core.visitor import VariableDeclaration
from panther.core.visitor import VariableDeclarator


class FileExtractor(object):

    def __init__(self):
        self.import_cache = {}
        self.program_cache = {}
        self.function_definition_cache = {}

    def create_program_cache(self, file_path):
        '''Create an AST of a program from a file path
        and saves to cache with file_path as key.
        '''
        with open(file_path, 'r') as f:
            code = f.read()
        json_program = esprima.parse(code, {'loc': True})
        ast_program = visitor.objectify(json_program.to_dict())
        self.program_cache[file_path] = ast_program

    def create_import_cache(self, file_path):
        '''Extract all imports using the AST of a program and
        builds a dictionary of the form <variable_name, module_path> and
        saves to cache with file_path as key.
        Supported Patterns:
            var x = require(...)
        '''
        program = self.get_program(file_path)
        imports = {}
        for node in program.traverse():
            if isinstance(node, VariableDeclarator):
                if isinstance(node.id, Identifier) and isinstance(node.init, CallExpression):
                    call_expression = node.init
                    if utils.match_name_space(call_expression, ['*require']) and call_expression.arguments:
                        variable_name = node.id.name
                        candidate_module_path = call_expression.arguments[0]
                        string_module_path = utils.try_extract_string_value(
                            candidate_module_path)
                        if string_module_path is not None:
                            if string_module_path.startswith((".", "/")):
                                imports[variable_name] = string_module_path

        self.import_cache[file_path] = imports

    def create_function_definition_cache(self, file_path):
        '''Extract all function definitions using the AST of a program and
        builds a dictionary of the form <variable_name, (FunctionDeclaration | FunctionExpression)>
        and saves to cache file_path as key.
        Supported Patterns:
            1) var x = fn(...):
            2) var x = fn(...), y = fn2(...)
            3) function x(){}
        '''

        program = self.get_program(file_path)

        function_definitions = {}

        def check_variable_assignment_function(left_node, right_node):
            if isinstance(right_node, FunctionExpression):
                expression = left_node
                function_expression = right_node
                name_space = utils.extract_name_space_from_expression(
                    expression)
                last_name = name_space[-1]

                # Check whether it is resolved.
                if last_name.startswith('*'):
                    resolved_name = last_name[1:]
                    return (resolved_name, function_expression)

            return None

        for node in program.traverse():
            # Check for function x(){}
            if isinstance(node, FunctionDeclaration):
                function_definitions[node.id.name] = node
            # Check for var x = function(){}
            elif isinstance(node, AssignmentExpression) and node.operator == '=':
                resolved_assignment = check_variable_assignment_function(
                    node.left, node.right)
                if resolved_assignment:
                    function_definitions[resolved_assignment[0]] = resolved_assignment[1]
            # Check for var x = function(){}, y = function(){}
            elif isinstance(node, VariableDeclaration):
                for declaration in node.declarations:
                    resolved_assignment = check_variable_assignment_function(
                        declaration.id, declaration.init)
                if resolved_assignment:
                    function_definitions[resolved_assignment[0]] = resolved_assignment[1]

        self.function_definition_cache[file_path] = function_definitions

    def get_imports(self, file_path):
        '''Serve extracted imports. If the imports are present in the cache
        it returns the cached entry else it builds the cache and returns.
        '''
        if file_path not in self.import_cache:
            self.create_import_cache(file_path)
        return self.import_cache[file_path]

    def get_program(self, file_path):
        '''Serve the AST of the program. If the AST is present in the cache
        it returns the cached entry else it builds the cache and returns.
        '''
        if file_path not in self.program_cache:
            self.create_program_cache(file_path)

        return self.program_cache[file_path]

    def get_function_definitions(self, file_path):
        '''Serve the function definitions of a program. If function declarations are
        in the cache it returns the cached entry else it builds the cache and returns.
        '''
        if file_path not in self.function_definition_cache:
            self.create_function_definition_cache(file_path)

        return self.function_definition_cache[file_path]

    def resolve_path(self, file_path, relative_path):
        '''Resolve the next file path using the current file path
        and relative import path.
        '''
        file_dir = os.path.dirname(file_path)
        return os.path.abspath(os.path.join(file_dir, relative_path + '.js'))

    def try_match_function(self, file_path, identifier):
        '''Search for a function definition that matches the
        identifier and returns if a match is found.
        '''
        function_definitions = self.get_function_definitions(file_path)
        function_node = function_definitions.get(identifier, None)
        if function_node is None:
            return None

        return Function(file_path=file_path, identifier=identifier, node=function_node)

    def try_fetch_function(self, file_path, module_name, identifier):
        '''Try to jump to a module name and tries to fetch a function
        using the identifier. If it can fetch it returns.
        '''

        # Check whether we have an import registered.
        imports = self.get_imports(file_path)
        relative_module_path = imports.get(module_name, None)
        if relative_module_path is None:
            return None

        # Jump to next file and search for the function.
        next_file_path = self.resolve_path(file_path, relative_module_path)
        function = self.try_match_function(next_file_path, identifier)
        if function is None:
            return None

        function.caller = '%s.%s' % (module_name, identifier)
        return function
