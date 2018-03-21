
from panther.core import visitor
from panther.core.visitor import CallExpression, Literal, FunctionExpression, VariableDeclarator, Identifier,MemberExpression

from panther.core import utils

class RouteFinder(object):
    def __init__(self, ast_program):
        self.ast_program = ast_program
        self.class_ast_program = visitor.objectify(self.ast_program)
        self.program_cache = {}
        self.routes = []
        self.imports = {}
        self.methods = ['get', 'post', 'put', 'delete', 'patch']

    
    def try_build_cache(file_path):
        if file_path not in program_cache:
            ## Read and write the class_ast to cache
            class_ast_program = read()
            self.program_cache[file_path] = class_ast_program
            ## Read and write imports to cache
            self.extract_imports(file_path)

    def extract_imports(self, file_path):
        class_ast_program =  self.program_cache[file_path]

        for node in class_ast_program.traverse():
            if isinstance(node, VariableDeclarator):
                if isinstance(node.id, Identifier) and isinstance(node.init, CallExpression):
                    call_expression = node.init
                    if utils.match_name_space(call_expression, ['*require']) and call_expression.arguments:
                        variable_name = node.id.name
                        candidate_module_path = call_expression.arguments[0]
                        string_module_path = RouteFinder.extract_string_value(candidate_module_path)
                        if string_module_path is not None:
                            if string_module_path.startswith((".", "/")):
                                if file_path not in self.imports:
                                    self.imports[file_path] = {} 
                                self.imports[file_path][variable_name] = string_module_path                        

    def find_routes(self, file_path):
        self.try_build_cache(file_path)
        class_ast_program = self.program_cache[file_path]

        for node in class_ast_program.traverse():
            if isinstance(node, CallExpression):
                for method in self.methods:
                    if utils.match_name_space(node, ['*', '*'+method]):
                        if node.arguments:
                            first_arg = node.arguments[0]
                            found_string = RouteFinder.extract_string_value(first_arg)
                            if found_string is not None:
                                print(found_string)
                                function_list = []
                                for arg in node.arguments[1:]:
                                    if isinstance(arg, FunctionExpression):
                                        function_list.append({'ref':'.', 'details': { 'identifier': arg.id, 'node':node }})
                                    elif isinstance(arg, MemberExpression):
                                        if isinstance(arg.object, Identifier) and isinstance(arg.property, Identifier):
                                            resolved_import = self.resolve_import(arg.object.name)
                                            if resolved_import:
                                                function_list.append({'ref':resolved_import, 'details': { 'identifier': arg.property.name, 'node':None }})
                                    # If we want to track identifier import.
                                    # elif isinstance(arg, Identifier):
                                    #         function_list.append({'ref':'../core/authHandler', 'details': { 'identifier': None, 'node':None })

                                self.routes.append({'pattern': found_string, 'method':method, 'function_list' : function_list})
    
    def find(self):
        pass

    def test(self):
        pass

    def resolve_import(self, name):
        return self.imports.get(name, None)

    def dive_all(depth=1):
        start = '.'
        self.find_routes(start)
        for route in self.routes:
            self.dive(route.function_list, [route], depth)

    def dive(stack_node, stack_trace, depth):
        depth -= 1
        for function in stack_node:
            test_result = self.test(function)
            if test_result is not None:
                print('I FOUND STH', stack_trace)
            else:
                if depth == 0:
                    print('I AM FINISHED BUT COULDNT FIND:(', stack_trace)
                else:
                    print('I AM GOING TO DIVE FOE LEVEL %d' % depth )
                    other_functions = self.find(function)
                    stack_trace.append(function)
                    self.dive(other_functions, stack_trace, depth)
            
        

    @staticmethod
    def extract_string_value(node):
        '''Tries to extract a string from a node. Supported types
        are TemplateElement and Literal.
        '''

        found_string = None

        # If it is a TemplateElement get cooked value.
        # If it is a Literal, check whether raw node starts
        # with either (') or ("").
        if isinstance(node, Literal):
            raw_literal = node.raw
            is_string = raw_literal.startswith('"') or raw_literal.startswith("'")
            if is_string:
                found_string = node.value

        return found_string           

        