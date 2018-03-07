"""Transforms AST dictionary into a tree of Node objects."""
import abc
from collections import OrderedDict
from typing import Any, Dict, Generator, List, Union


class UnknownNodeTypeError(Exception):
    """Raised if we encounter a node with an unknown type."""
    pass


class Node(abc.ABC):
    """Abstract Node class which defines node operations"""
    @abc.abstractproperty
    def fields(self) -> List[str]:
        """List of field names associated with this node type, in canonical order."""

    def __init__(self, data: Dict[str, Any]) -> None:
        """Sets one attribute in the Node for each field (e.g. self.body)."""
        for field in self.fields:
            setattr(self, field, objectify(data.get(field)))

    def dict(self) -> Dict[str, Any]:
        """Transform the Node back into an Esprima-compatible AST dictionary."""
        result = OrderedDict({'type': self.type})  # type: Dict[str, Any]
        for field in self.fields:
            val = getattr(self, field)
            if isinstance(val, Node):
                result[field] = val.dict()
            elif isinstance(val, list):
                result[field] = [x.dict() for x in val]
            else:
                result[field] = val
        return result

    def traverse(self) -> Generator['Node', None, None]:
        """Pre-order traversal of this node and all of its children."""
        yield self
        for field in self.fields:
            val = getattr(self, field)
            if isinstance(val, Node):
                yield from val.traverse()
            elif isinstance(val, list):
                for node in val:
                    yield from node.traverse()

    @property
    def type(self) -> str:
        """The name of the node type, e.g. 'Identifier'."""
        return self.__class__.__name__


def objectify(data: Union[None, Dict[str, Any], List[Dict[str, Any]]]) -> Union[
        None, Dict[str, Any], List[Any], Node]:
    """Recursively transform AST data into a Node object."""
    if not isinstance(data, (dict, list)):
        # Data is a basic type (None, string, number)
        return data

    if isinstance(data, dict):
        if 'type' not in data:
            # Literal values can be empty dictionaries, for example.
            return data
        # Transform the type into the appropriate class.
        node_class = globals().get(data['type'])
        if not node_class:
            raise UnknownNodeTypeError(data['type'])
        return node_class(data)
    else:
        # Data is a list of nodes.
        return [objectify(x) for x in data]


# --- AST spec: https://github.com/estree/estree/blob/master/es5.md ---
# pylint: disable=missing-docstring,multiple-statements


class Identifier(Node):
    @property
    def fields(self): return ['name', 'loc']


class Literal(Node):
    @property
    def fields(self): return ['raw', 'value', 'regex', 'loc']


class Program(Node):
    @property
    def fields(self): return ['body', 'sourceType', 'loc']


# ========== Statements ==========


class ExpressionStatement(Node):
    @property
    def fields(self): return ['expression', 'loc']


class BlockStatement(Node):
    @property
    def fields(self): return ['body', 'loc']


class EmptyStatement(Node):
    @property
    def fields(self): return ['loc']


class DebuggerStatement(Node):
    @property
    def fields(self): return ['loc']


class WithStatement(Node):
    @property
    def fields(self): return ['object', 'body', 'loc']


# ----- Control Flow -----


class ReturnStatement(Node):
    @property
    def fields(self): return ['argument', 'loc']


class LabeledStatement(Node):
    @property
    def fields(self): return ['label', 'body', 'loc']


class BreakStatement(Node):
    @property
    def fields(self): return ['label', 'loc']


class ContinueStatement(Node):
    @property
    def fields(self): return ['label', 'loc']


# ----- Choice -----


class IfStatement(Node):
    @property
    def fields(self): return ['test', 'consequent', 'alternate', 'loc']


class SwitchStatement(Node):
    @property
    def fields(self): return ['discriminant', 'cases', 'loc']


class SwitchCase(Node):
    @property
    def fields(self): return ['test', 'consequent', 'loc']


# ----- Exceptions -----


class ThrowStatement(Node):
    @property
    def fields(self): return ['argument', 'loc']


class TryStatement(Node):
    @property
    def fields(self): return ['block', 'handler', 'finalizer', 'loc']


class CatchClause(Node):
    @property
    def fields(self): return ['param', 'body', 'loc']


# ----- Loops -----


class WhileStatement(Node):
    @property
    def fields(self): return ['test', 'body', 'loc']


class DoWhileStatement(Node):
    @property
    def fields(self): return ['body', 'test', 'loc']


class ForStatement(Node):
    @property
    def fields(self): return ['init', 'test', 'update', 'body', 'loc']


class ForInStatement(Node):
    @property
    def fields(self): return ['left', 'right', 'body', 'loc']


class ForOfStatement(Node):
    @property
    def fields(self): return ['left', 'right', 'body', 'loc']


# ========== Declarations ==========


class FunctionDeclaration(Node):
    @property
    def fields(self): return ['id', 'params', 'body', 'loc']


class VariableDeclaration(Node):
    @property
    def fields(self): return ['declarations', 'kind', 'loc']


class VariableDeclarator(Node):
    @property
    def fields(self): return ['id', 'init', 'loc']


class ClassDeclaration(Node):
    @property
    def fields(self): return ['id', 'superClass', 'body', 'loc']


# ========== Expressions ==========


class ThisExpression(Node):
    @property
    def fields(self): return ['loc']


class ArrayExpression(Node):
    @property
    def fields(self): return ['elements', 'loc']


class ObjectExpression(Node):
    @property
    def fields(self): return ['properties', 'loc']


class ClassExpression(Node):
    @property
    def fields(self): return ['id', 'superClass', 'body', 'loc']


class ClassBody(Node):
    @property
    def fields(self): return ['body', 'loc']


class MethodDefinition(Node):
    @property
    def fields(self): return ['key', 'value', 'kind', 'loc']


class Property(Node):
    @property
    def fields(self): return ['key', 'value', 'kind', 'shorthand', 'loc']


class MetaProperty(Node):
    @property
    def fields(self): return ['meta', 'property', 'loc']


class FunctionExpression(Node):
    @property
    def fields(self): return ['id', 'params', 'body', 'loc']


class ArrowFunctionExpression(Node):
    @property
    def fields(self): return ['id', 'params', 'body', 'loc']


class AwaitExpression(Node):
    @property
    def fields(self): return ['argument', 'loc']


class UnaryExpression(Node):
    @property
    def fields(self): return ['operator', 'prefix', 'argument', 'loc']


class UpdateExpression(Node):
    @property
    def fields(self): return ['operator', 'argument', 'prefix', 'loc']


class BinaryExpression(Node):
    @property
    def fields(self): return ['operator', 'left', 'right', 'loc']


class AssignmentExpression(Node):
    @property
    def fields(self): return ['operator', 'left', 'right', 'loc']


class LogicalExpression(Node):
    @property
    def fields(self): return ['operator', 'left', 'right', 'loc']


class MemberExpression(Node):
    @property
    def fields(self): return ['object', 'property', 'computed', 'loc']


class ConditionalExpression(Node):
    @property
    def fields(self): return ['test', 'consequent', 'alternate', 'loc']


class YieldExpression(Node):
    @property
    def fields(self): return ['argument', 'delegate', 'loc']


class CallExpression(Node):
    @property
    def fields(self): return ['callee', 'arguments', 'loc']


class NewExpression(Node):
    @property
    def fields(self): return ['callee', 'arguments', 'loc']


class SequenceExpression(Node):
    @property
    def fields(self): return ['expressions', 'loc']


class TaggedTemplateExpression(Node):
    @property
    def fields(self): return ['tag', 'quasi', 'loc']


class TemplateElement(Node):
    @property
    def fields(self): return ['value', 'tail', 'loc']


class TemplateLiteral(Node):
    @property
    def fields(self): return ['quasis', 'expressions', 'loc']


class Super(Node):
    @property
    def fields(self): return ['loc']


class SpreadElement(Node):
    @property
    def fields(self): return ['argument', 'loc']


# ========== Patterns ==========


class ArrayPattern(Node):
    @property
    def fields(self): return ['elements', 'loc']


class RestElement(Node):
    @property
    def fields(self): return ['argument', 'loc']


class AssignmentPattern(Node):
    @property
    def fields(self): return ['left', 'right', 'loc']


class ObjectPattern(Node):
    @property
    def fields(self): return ['properties', 'loc']


# ========== Import/Export ==========


class Import(Node):
    @property
    def fields(self): return ['loc']


class ImportDeclaration(Node):
    @property
    def fields(self): return ['source', 'specifiers', 'loc']


class ImportSpecifier(Node):
    @property
    def fields(self): return ['local', 'imported', 'loc']


class ExportAllDeclaration(Node):
    @property
    def fields(self): return ['source', 'loc']


class ExportDefaultDeclaration(Node):
    @property
    def fields(self): return ['declaration', 'loc']


class ExportNamedDeclaration(Node):
    @property
    def fields(self): return ['declaration', 'specifiers', 'source', 'loc']


class ExportSpecifier(Node):
    @property
    def fields(self): return ['exported', 'local', 'loc']
