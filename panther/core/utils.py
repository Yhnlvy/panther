# -*- coding:utf-8 -*-

import _ast
import ast
import logging
import os.path
import re
import sys

from panther.core import visitor
from panther.core.visitor import CallExpression
from panther.core.visitor import Identifier
from panther.core.visitor import Literal
from panther.core.visitor import MemberExpression
from panther.core.visitor import ObjectExpression

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

LOG = logging.getLogger(__name__)


"""Various helper functions."""


def _get_attr_qual_name(node, aliases):
    '''Get a the full name for the attribute node.

    This will resolve a pseudo-qualified name for the attribute
    rooted at node as long as all the deeper nodes are Names or
    Attributes. This will give you how the code referenced the name but
    will not tell you what the name actually refers to. If we
    encounter a node without a static name we punt with an
    empty string. If this encounters something more complex, such as
    foo.mylist[0](a,b) we just return empty string.

    :param node: AST Name or Attribute node
    :param aliases: Import aliases dictionary
    :returns: Qualified name referred to by the attribute or name.
    '''
    if isinstance(node, _ast.Name):
        if node.id in aliases:
            return aliases[node.id]
        return node.id
    elif isinstance(node, _ast.Attribute):
        name = '%s.%s' % (_get_attr_qual_name(node.value, aliases), node.attr)
        if name in aliases:
            return aliases[name]
        return name
    else:
        return ""


def get_call_name(node, aliases):
    if isinstance(node.func, _ast.Name):
        if deepgetattr(node, 'func.id') in aliases:
            return aliases[deepgetattr(node, 'func.id')]
        return deepgetattr(node, 'func.id')
    elif isinstance(node.func, _ast.Attribute):
        return _get_attr_qual_name(node.func, aliases)
    else:
        return ""


def get_func_name(node):
    return node.name  # TODO(tkelsey): get that qualname using enclosing scope


def get_qual_attr(node, aliases):
    prefix = ""
    if isinstance(node, _ast.Attribute):
        try:
            val = deepgetattr(node, 'value.id')
            if val in aliases:
                prefix = aliases[val]
            else:
                prefix = deepgetattr(node, 'value.id')
        except Exception:
            # NOTE(tkelsey): degrade gracefully when we can't get the fully
            # qualified name for an attr, just return its base name.
            pass

        return "%s.%s" % (prefix, node.attr)
    else:
        return ""  # TODO(tkelsey): process other node types


def deepgetattr(obj, attr):
    """Recurses through an attribute chain to get the ultimate value."""
    for key in attr.split('.'):
        obj = getattr(obj, key)
    return obj


class InvalidModulePath(Exception):
    pass


class ConfigError(Exception):
    """Raised when the config file fails validation."""

    def __init__(self, message, config_file):
        self.config_file = config_file
        self.message = "{0} : {1}".format(config_file, message)
        super(ConfigError, self).__init__(self.message)


class ProfileNotFound(Exception):
    """Raised when chosen profile cannot be found."""

    def __init__(self, config_file, profile):
        self.config_file = config_file
        self.profile = profile
        message = 'Unable to find profile (%s) in config file: %s' % (
            self.profile, self.config_file)
        super(ProfileNotFound, self).__init__(message)


def warnings_formatter(message, category=UserWarning, filename='', lineno=-1,
                       line=''):
    '''Monkey patch for warnings.warn to suppress cruft output.'''
    return "{0}\n".format(message)


def get_module_qualname_from_path(path):
    '''Get the module's qualified name by analysis of the path.

    Resolve the absolute pathname and eliminate symlinks. This could result in
    an incorrect name if symlinks are used to restructure the python lib
    directory.

    Starting from the right-most directory component look for __init__.py in
    the directory component. If it exists then the directory name is part of
    the module name. Move left to the subsequent directory components until a
    directory is found without __init__.py.

    :param: Path to module file. Relative paths will be resolved relative to
            current working directory.
    :return: fully qualified module name
    '''

    (head, tail) = os.path.split(path)
    if head == '' or tail == '':
        raise InvalidModulePath('Invalid python file path: "%s"'
                                ' Missing path or file name' % (path))

    qname = [os.path.splitext(tail)[0]]
    while head not in ['/', '.', '']:
        if os.path.isfile(os.path.join(head, '__init__.py')):
            (head, tail) = os.path.split(head)
            qname.insert(0, tail)
        else:
            break

    qualname = '.'.join(qname)
    return qualname


def namespace_path_join(base, name):
    '''Extend the current namespace path with an additional name

    Take a namespace path (i.e., package.module.class) and extends it
    with an additional name (i.e., package.module.class.subclass).
    This is similar to how os.path.join works.

    :param base: (String) The base namespace path.
    :param name: (String) The new name to append to the base path.
    :returns: (String) A new namespace path resulting from combination of
              base and name.
    '''
    return '%s.%s' % (base, name)


def namespace_path_split(path):
    '''Split the namespace path into a pair (head, tail).

    Tail will be the last namespace path component and head will
    be everything leading up to that in the path. This is similar to
    os.path.split.

    :param path: (String) A namespace path.
    :returns: (String, String) A tuple where the first component is the base
              path and the second is the last path component.
    '''
    return tuple(path.rsplit('.', 1))


def escaped_bytes_representation(b):
    '''PY3 bytes need escaping for comparison with other strings.

    In practice it turns control characters into acceptable codepoints then
    encodes them into bytes again to turn unprintable bytes into printable
    escape sequences.

    This is safe to do for the whole range 0..255 and result matches
    unicode_escape on a unicode string.
    '''
    return b.decode('unicode_escape').encode('unicode_escape')


def linerange(node):
    """Get line number range from a node."""
    strip = {"body": None, "orelse": None,
             "handlers": None, "finalbody": None}
    for key in strip.keys():
        if hasattr(node, key):
            strip[key] = getattr(node, key)
            setattr(node, key, [])

    lines_min = 9999999999
    lines_max = -1
    for n in visitor.objectify(node).traverse():
        if hasattr(n, 'lineno'):
            lines_min = min(lines_min, n.lineno)
            lines_max = max(lines_max, n.lineno)

    for key in strip.keys():
        if strip[key] is not None:
            setattr(node, key, strip[key])

    if lines_max > -1:
        return list(range(lines_min, lines_max + 1))
    return [0, 1]


def linerange_fix(node):
    """Try and work around a known Python bug with multi-line strings."""
    # deal with multiline strings lineno behavior (Python issue #16806)
    lines = linerange(node)
    if hasattr(node, 'sibling') and hasattr(node.sibling, 'lineno'):
        start = min(lines)
        delta = node.sibling.lineno - start
        if delta > 1:
            return list(range(start, node.sibling.lineno))
    return lines


def concat_string(node, stop=None):
    '''Builds a string from a ast.BinOp chain.

    This will build a string from a series of ast.Str nodes wrapped in
    ast.BinOp nodes. Something like "a" + "b" + "c" or "a %s" % val etc.
    The provided node can be any participant in the BinOp chain.

    :param node: (ast.Str or ast.BinOp) The node to process
    :param stop: (ast.Str or ast.BinOp) Optional base node to stop at
    :returns: (Tuple) the root node of the expression, the string value
    '''
    def _get(node, bits, stop=None):
        if node != stop:
            bits.append(
                _get(node.left, bits, stop)
                if isinstance(node.left, ast.BinOp)
                else node.left)
            bits.append(
                _get(node.right, bits, stop)
                if isinstance(node.right, ast.BinOp)
                else node.right)

    bits = [node]
    while isinstance(node.parent, ast.BinOp):
        node = node.parent
    if isinstance(node, ast.BinOp):
        _get(node, bits, stop)
    return (node, " ".join([x.s for x in bits if isinstance(x, ast.Str)]))


def get_called_name(node):
    '''Get a function name from an ast.Call node.

    An ast.Call node representing a method call with present differently to one
    wrapping a function call: thing.call() vs call(). This helper will grab the
    unqualified call name correctly in either case.

    :param node: (ast.Call) the call node
    :returns: (String) the function name
    '''
    func = node.func
    try:
        return func.attr if isinstance(func, ast.Attribute) else func.id
    except AttributeError:
        return ""


def get_path_for_function(f):
    '''Get the path of the file where the function is defined.

    :returns: the path, or None if one could not be found or f is not a real
        function
    '''

    if hasattr(f, "__module__"):
        module_name = f.__module__
    elif hasattr(f, "im_func"):
        module_name = f.im_func.__module__
    else:
        LOG.warning("Cannot resolve file where %s is defined", f)
        return None

    module = sys.modules[module_name]
    if hasattr(module, "__file__"):
        return module.__file__
    else:
        LOG.warning("Cannot resolve file path for module %s", module_name)
        return None


def parse_ini_file(f_loc):
    config = configparser.ConfigParser()
    try:
        config.read(f_loc)
        return {k: v for k, v in config.items('panther')}

    except (configparser.Error, KeyError, TypeError):
        LOG.warning("Unable to parse config file %s or missing [panther] "
                    "section", f_loc)

    return None


def check_ast_node(name):
    'Check if the given name is that of a valid AST node.'
    return name
    # try:
    #     node = getattr(ast, name)
    #     if issubclass(node, ast.AST):
    #         return name
    # except AttributeError:  # nosec(tkelsey): catching expected exception
    #     pass

    # raise TypeError("Error: %s is not a valid node type in AST" % name)


def clean_code(buffer):
    '''Trims the shebang at the beginning of JS file

    Example: #!/usr/bin/env node
    '''
    return re.sub(r'^#!([^\r\n]+)', '', buffer)


def extract_name(node, disable_conversion=False):
    '''Tries to extract the name from a node.
    If disable_conversion is True it does not resolve
    the name. If a value is extracted it contains '*'
    sign at the start then the extracted value itself.
    If it cannot be extracted then the first character
    becomes '?' and the remaining part becomes the name of
    the class.
    '''

    found_name = None

    if isinstance(node, Identifier) and not disable_conversion:
        found_name = '*' + node.name
    elif isinstance(node, Literal) and not disable_conversion:
        found_name = '*' + str(node.value)
    else:
        found_name = '?' + node.__class__.__name__

    return found_name


def extract_name_space_from_expression(expression):
    ''''Extracts a name space from an expression.
        Returns an array of names where each name starts
        with '*' if it can be resolved '?' otherwise.

        Example: returns ['*x','?Identifier','?MemberExpression'] for x.Identifier.MemberExpression

        Handles cases below:

            x() => x
            x.y.z() => x.y.z
            x[y][z]() => x.Identifier.Identifier
            x[y][z.j]() => x.Identifier.MemberExpression
            x['y'][3]() => x.y.3
            x['y'][3+2]() => x.y.BinaryExpression
            x[y()][z()]() => x.CallExpression.CallExpression
            [].x() => ArrayExpression.x
            []['x']() => ArrayExpression.x
            [][x]() => ArrayExpression.Identifier
            ''.x() => Literal.x
            ''['x']() => Literal.x
            ''[x]() => Literal.Identifier
            fn()() => CallExpression
            (x=2)() => AssignmentExpression
            Identifier.Identifier() => Identifier.Identifier
    '''
    name_space = []

    # If it is a member expression recursively evaluate the expression.
    if isinstance(expression, MemberExpression):
        def read_property(member):
            '''Reads the property of member and extracts the name.'''
            prop_node = member.property

            # SPECIAL CASE: (x[y][z]() => x.Identifier.Identifier)
            # For above case to work we should disable conversion.
            # If not engine gives x.y.z which we do not want.

            disable_conversion = member.computed and isinstance(
                prop_node, Identifier)
            return extract_name(prop_node, disable_conversion)

        # Recursively evaluate expressions
        name_space.insert(0, read_property(expression))
        member = expression.object
        while isinstance(member, MemberExpression):
            name_space.insert(0, read_property(member))
            member = member.object

        # SPECIAL CASE: (''.x() => Literal.x)
        # For above case to work we should disable conversion.
        # If not engine gives .x which we do not want.
        disable_conversion = isinstance(member, Literal)
        name_space.insert(0, extract_name(member, disable_conversion))

        return name_space
    else:
        return [extract_name(expression)]


def extract_name_space(call_expression):
    ''''Extracts a name space from a call expression.
        Returns an array of names where each name starts
        with '*' if it can be resolved '?' otherwise.

        Example: returns ['*x','?Identifier','?MemberExpression'] for x.Identifier.MemberExpression

        See extract_name_space_from_expression to see handled cases.
    '''

    if not isinstance(call_expression, CallExpression):
        raise Exception('Please supply a call expression.')

    expression = call_expression.callee

    return extract_name_space_from_expression(expression)


def match_pattern(name, pattern):
    '''This is a helper function for matching
    patterns in a name space search. So if a '*' is
    passed as a parameter it checks whether a name
    is a resolved name. If '*{name}' is given it looks
    for an exact match. Similarly if a '?' is
    passed as a parameter it checks whether a name
    is not a resolved name. If '?{name}' is given it looks
    for an exact match.
    '''
    pattern_len = len(pattern)

    # Check whether they are both question mark or star
    if pattern_len == 1 and name[0] != pattern[0]:
        return False

    # Check for an exact match
    if pattern_len > 1 and name != pattern:
        return False

    return True


def match_name_space(expression, pattern_list):
    '''Gets a pattern array and a function (or expression) then searches for the specific
    pattern in the function (or expression). If it finds it returns True.

    Examples of pattern_list:

    1) ['*db', '*', 'find']

    Matches => db.mytable.find(...) since namespace is db.mytable.find

    2) ['*x', '?', '?Identifier']

    Matches => x[y][z](...) since namespace is x.Identifier.Identifier

    3) ['*','?','?']

    Matches => x[y][z.j](...) since namespace is x.Identifier.MemberExpression

    '''

    if isinstance(expression, CallExpression):
        name_space_list = extract_name_space(expression)
    else:
        name_space_list = extract_name_space_from_expression(expression)

    # If pattern_list contains no element or there is
    # length mismatch return False.
    if not pattern_list or len(name_space_list) != len(pattern_list):
        return False

    # If there is any mismatch in the pattern arrays then
    # return False.
    for name, pattern in zip(name_space_list, pattern_list):
        if not match_pattern(name, pattern):
            return False

    return True


def match_argument_with_object_key(call_expression, pattern_key):
    ''''It checks whether a call expression has one argument and
        this argument is an object and has a specific pattern of
        key. (pattern_key)

        pattern_key can either start with a question mark or a star.

        For more information see the test functions.
    '''
    node = call_expression

    # Check whether there is only one argument and it is an object.
    if len(node.arguments) == 1 and isinstance(node.arguments[0], ObjectExpression):
        object_expression = node.arguments[0]

        # Loop over each property if there is match in the name return True.
        for prop in object_expression.properties:
            # If the property is computed and the type is identifier
            # we cannot know the name. So in that case disable conversion.
            #
            # Example:
            #   var o = {[prop]: 'hey'};
            #
            # *prop should not match the above statement but ?Identifier
            # should match.

            disable_conversion = prop.computed and isinstance(
                prop.key, Identifier)

            name = extract_name(prop.key, disable_conversion)
            if match_pattern(name, pattern_key):
                return True

    return False


def try_extract_string_value(node):
    '''Tries to extract a string from a node.'''

    found_string = None

    # Check whether raw node starts with either (') or ("").
    if isinstance(node, Literal):
        raw_literal = node.raw
        is_string = raw_literal.startswith('"') or raw_literal.startswith("'")
        if is_string:
            found_string = node.value

    return found_string
