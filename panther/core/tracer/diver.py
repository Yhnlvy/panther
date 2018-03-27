import logging
from panther.core import config
from panther.core import meta_ast
from panther.core import metrics
from panther.core import node_visitor
from panther.core import test_set
from panther.core.tracer.file_extractor import FileExtractor
from panther.core import utils
from panther.core.visitor import CallExpression

LOG = logging.getLogger(__name__)


class colors(object):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Diver(object):
    def __init__(self, routes, debug=False):
        self.routes = routes
        self.extractor = FileExtractor()
        self.vulnerability_count = 0
        self.debug = debug

    def find(self, function):
        '''Find and return functions that are called in a given function.
        If the function name is an string identifier it looks for a function
        in the same document. If the caller is a member expression like
        module.fn() it looks for the module in the require call and if it can
        resolve it goes to the referenced file and fetches the function.
        '''
        file_path = function.file_path
        function_list = []
        for node in function.node.traverse():
            callee = None

            # Track call expressions
            if isinstance(node, CallExpression):
                call_expression = node

                # If we have match of an identifier function call like fn()
                if utils.match_name_space(call_expression, ['*']):
                    # Extract name space give us all names as a list.
                    # So we get the first element of the list which
                    # contains *function_name. Then we remove the star
                    # character to get the actual name.
                    identifier = utils.extract_name_space(
                        call_expression)[0][1:]
                    callee = self.extractor.try_match_function(
                        file_path, identifier)
                # Check whether we have a call like module.fn()
                elif utils.match_name_space(call_expression, ['*', '*']):
                    name_space = utils.extract_name_space(call_expression)
                    # Since we get an array of the form ['*module_name','*fn_name']
                    # we use below indexing to extract module_name and identifier.
                    module_name = name_space[0][1:]
                    identifier = name_space[1][1:]
                    callee = self.extractor.try_fetch_function(
                        file_path, module_name, identifier)
            if callee:
                function_list.append(callee)

        return function_list

    def test(self, file_path, node):
        '''Test a given function node with plugins
        and returns test results.
        '''
        nv = node_visitor.PantherNodeVisitor(
            file_path,
            meta_ast.PantherMetaAst(),
            test_set.PantherTestSet(config, profile=None),
            True,
            set(),
            metrics.Metrics()
        )
        nv.generic_visit(node)
        # TODO(izel): Do something with results.
        # if nv.tester.results:
        #     print(nv.tester.results[0].__dict__)

        # print(nv.scores)
        return nv.tester.results

    def dive_all(self, file_path, depth=1):
        '''Each route has an array of entry functions to start diving process.
        So for each entry function in each route it recursively scans for
        the vulnerabilities.
        '''
        self.vulnerability_count = 0
        for route in self.routes:
            for function in route.entry_point_functions:
                self.dive(function, [route], depth)

        return self.vulnerability_count

    def format_stack_trace(self, stack_trace):
        '''Format an array of functions with a splitter.'''
        return '\n----------------\n'.join(map(repr, stack_trace))

    def format_issues(self, results):
        '''Format an array of issues'''
        msgs = [
            "\nLine: %s - %s\n%s" % (issue.lineno, issue.text, issue.get_code())
            for issue in results
        ]
        return '----------------\n'.join(msgs)

    def dive(self, function, stack_trace, depth):
        '''Search recursively for vulnerabilities. Stop when either
        a vulnerability is encountered or depth limit is reached.
        '''
        depth -= 1
        stack_trace.append(function)
        test_result = self.test(function.file_path, function.node)
        if test_result:
            formatted_stack_trace = self.format_stack_trace(stack_trace)
            formatted_report = self.format_issues(test_result)
            header_text = colors.HEADER + '\n============================\n' + colors.ENDC
            print(
                header_text + colors.OKBLUE + formatted_stack_trace + colors.ENDC,
                colors.WARNING + formatted_report + colors.ENDC
            )
            self.vulnerability_count += 1
        else:
            if not depth:
                if self.debug:
                    formatted_stack_trace = self.format_stack_trace(stack_trace)
                    header_text = '\n\nPath search finished but nothing found. See stack trace below.\n\n'
                    print(header_text, formatted_stack_trace)
            else:
                other_functions = self.find(function)
                if other_functions:
                    for function in other_functions:
                        self.dive(function, stack_trace, depth)
