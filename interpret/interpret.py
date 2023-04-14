
import getopt
import sys
from enum import Enum
import xml.etree.ElementTree as XML
import re
from abc import ABCMeta, abstractmethod

USAGE = """
\bUsage: python interpret.py [-h|--help|OPTIONS]\n
\bOPTIONS:
\b--help           Show this message and exit. No other options are allowed.
\b--source=PATH    The source of the XML file.
\b--input=PATH     The input for XML source file.
\b
\bAuthor: xturyt00 (Oleksandr Turytsia)
"""


class Exceptions:
    """
        A class that contains configured custom exceptions.

        Enums:
            CodeTypes: contains error codes

        Classes:
            Usage: -h or --help options
            OptionError:  User used invalid option
            XMLFormatError: XML parsing error
            XMLUnexpectedError: Syntax error in XML
            SemanticError: Semantic error in XML
            TypeError: invalid Operand type detected
            VariableUndefinedError: Non-existing value
            OperandValueError: 0-division
            StringOperationError: Error when working with string
            InternalError: Any other errors...

        Methods:
            exit(e): Handles custom exceptions
    """
    class CodeTypes(Enum):
        SUCCESS = 0
        ERR_PARAMETER = 10
        ERR_INPUT = 11
        ERR_OUTPUT = 12
        ERR_XML_FORMAT = 31
        ERR_XML_STRUCT = 32
        ERR_SEMANTICS = 52
        ERR_TYPE = 53
        ERR_UNDEFINED = 54
        ERR_STACK = 55
        ERR_MISS = 56
        ERR_VALUE = 57
        ERR_STRING = 58
        ERR_INTERNAL = 99

    @staticmethod
    def exit(e: '_Exception'):
        """
            Handles custom exceptions, and exits the program with proper exit code.
        """
        print(e, file=sys.stderr)
        exit(e.code)

    class _Exception(Exception):
        """
            Generic class, that is configured for all types of exceptions with `code` and `message`
        """

        def __init__(self, message: str, code: 'Exceptions.CodeTypes'):
            super().__init__(message)
            self.code = code.value

    class OptionError(_Exception):
        def __init__(self, message):
            super().__init__(message, Exceptions.CodeTypes.ERR_PARAMETER)

    class XMLFormatError(_Exception):
        def __init__(self, message):
            super().__init__(message, Exceptions.CodeTypes.ERR_XML_FORMAT)

    class XMLUnexpectedError(_Exception):
        def __init__(self, message):
            super().__init__(message, Exceptions.CodeTypes.ERR_XML_STRUCT)

    class SemanticError(_Exception):
        def __init__(self, message):
            super().__init__(message, Exceptions.CodeTypes.ERR_SEMANTICS)

    class TypeError(_Exception):
        def __init__(self, message):
            super().__init__(message, Exceptions.CodeTypes.ERR_TYPE)

    class VariableUndefinedError(_Exception):
        def __init__(self, message):
            super().__init__(message, Exceptions.CodeTypes.ERR_UNDEFINED)

    class FrameError(_Exception):
        def __init__(self, message):
            super().__init__(message, Exceptions.CodeTypes.ERR_STACK)

    class ValueUndefinedError(_Exception):
        def __init__(self, message):
            super().__init__(message, Exceptions.CodeTypes.ERR_MISS)

    class OperandValueError(_Exception):
        def __init__(self, message):
            super().__init__(message, Exceptions.CodeTypes.ERR_VALUE)
            self.code = 57

    class StringOperationError(_Exception):
        def __init__(self, message):
            super().__init__(message, Exceptions.CodeTypes.ERR_STRING)

    class InternalError(_Exception):
        def __init__(self, message):
            super().__init__(message, Exceptions.CodeTypes.ERR_INTERNAL)


class FrameTypes(Enum):
    """
        Enum, represents frame types

        Types:
            LF
            GF
            TF
    """
    TF = 1
    LF = 2
    GF = 3


def deescape_str(s: str):
    try:
        res = s
        matches = re.findall(r"\\[\d]{3}", s)
        for match in matches:
            res = res.replace(match, chr(int(match[1:])))
        return res
    except ValueError as e:
        raise Exceptions.StringOperationError(e)


class Types:
    """
        Class, that implements all the typing dependencies and methods.

        Nested classes represent literal of specific types, class inheritance represents their subtype (or more specific literals).

        Classes:
            Symb
            Var
            Type
            Label
    """
    class Symb:
        """
            Class, represents Symb literal with its value and type

            Methods:
                Special methods, that define behaviour for various operators/built-in methods.

            Classmethods:
                Int(): Creates instance of Symb with type integer
                Float(): Creates instance of Symb with type float
                String(): Creates instance of Symb with type string
                Bool(): Creates instance of Symb with type boolean
                Nil(): Creates instance of Symb with type nil
        """

        def __init__(self, value, _type: 'Types.Type'):
            self.type = Types.Type.to_type(_type)
            try:
                if self.type.is_int():
                    self.value = int(value)
                elif self.type.is_bool():
                    if type(value) == bool:
                        self.value = value
                    else:
                        if value.lower() == "true":
                            self.value = True
                        else:
                            self.value = False
                elif self.type.is_float():
                    self.value = float.fromhex(value) if type(
                        value) == str else value
                elif self.type.is_string():
                    self.value = "" if value is None else value
                else:
                    self.value = value
            except ValueError:
                raise Exceptions.XMLUnexpectedError(
                    f"{value} is not valid int")

        @classmethod
        def Int(cls, value):
            """
                Creates instance of Symb with type integer
            """
            return cls(value, Types.Type.Int())

        @classmethod
        def Float(cls, value):
            """
                Creates instance of Symb with type float
            """
            return cls(value, Types.Type.Float())

        @classmethod
        def String(cls, value):
            """
                Creates instance of Symb with type string
            """
            return cls(value, Types.Type.String())

        @classmethod
        def Bool(cls, value):
            """
                Creates instance of Symb with type bool
            """
            return cls(value, Types.Type.Bool())

        @classmethod
        def Nil(cls, value):
            """
                Creates instance of Symb with type nil
            """
            return cls(value, Types.Type.Nil())

        @classmethod
        def Undef(cls, value):
            """
                Creates instance of Symb with type nil
            """
            return cls(value, Types.Type.Undef())

        def __gt__(self, other: 'Types.Symb'):
            if isinstance(other, (Types.Var, Types.Symb)):
                if self.type.is_nil() or other.type.is_nil():
                    raise Exceptions.TypeError("GT doesn't support NIL")
                if self.type != other.type:
                    raise Exceptions.TypeError("Incompatible types in LT")
                if self.type.is_string():
                    return Types.Symb.Bool(deescape_str(str(self.value)) > deescape_str(str(other.value)))
                else:
                    return Types.Symb.Bool(self.value > other.value)
            return NotImplemented

        def __lt__(self, other: 'Types.Symb'):
            if isinstance(other, (Types.Var, Types.Symb)):
                if self.type.is_nil() or other.type.is_nil():
                    raise Exceptions.TypeError("LT doesn't support NIL")
                if self.type != other.type:
                    raise Exceptions.TypeError("Incompatible types in LT")
                if self.type.is_string():
                    return Types.Symb.Bool(deescape_str(str(self.value)) < deescape_str(str(other.value)))
                else:
                    return Types.Symb.Bool(self.value < other.value)
            return NotImplemented

        def __bool__(self):
            return bool(self.value)

        def __eq__(self, other: 'Types.Symb'):
            if isinstance(other, (Types.Var, Types.Symb)):
                if (self.type != other.type and
                        not self.type.is_nil() and not other.type.is_nil()):
                    raise Exceptions.TypeError(
                        "Operands must be of the same type")
                if self.type.is_string():
                    return Types.Symb.Bool(deescape_str(str(self.value)) == deescape_str(str(other.value)))
                else:
                    return Types.Symb.Bool(self.value == other.value)
            return NotImplemented

        def __invert__(self):
            if not self.type.is_bool():
                raise Exceptions.TypeError("AND/OR/NOT supports bool only")
            return Types.Symb.Bool(not self.value)

        def __and__(self, other: 'Types.Symb'):
            if isinstance(other, (Types.Var, Types.Symb)):
                if not self.type.is_bool() or not other.type.is_bool():
                    raise Exceptions.TypeError(
                        "AND/OR/NOT supports bool only")
                return Types.Symb.Bool(self.value and other.value)
            return NotImplemented

        def __or__(self, other: 'Types.Symb'):
            if isinstance(other, (Types.Var, Types.Symb)):
                if not self.type.is_bool() or not other.type.is_bool():
                    raise Exceptions.TypeError(
                        "AND/OR/NOT supports bool only")
                return Types.Symb.Bool(self.value or other.value)
            return NotImplemented

        def __add__(self, other: 'Types.Symb'):
            if isinstance(other, (Types.Var, Types.Symb)):

                if other.type.is_nil() and isinstance(other, Types.Var):
                    raise Exceptions.ValueUndefinedError("Missing value")
                if not (self.type.is_int() and other.type.is_int()
                        or self.type.is_float() and other.type.is_float()):
                    raise Exceptions.TypeError(
                        f"Incompatible types of {other} and {self}")
                if self.type.is_int():
                    return Types.Symb.Int(int(self.value + other.value))
                else:
                    return Types.Symb.Float(self.value + other.value)
            return NotImplemented

        def __sub__(self, other: 'Types.Symb'):
            if isinstance(other, (Types.Var, Types.Symb)):

                if other.type.is_nil() and isinstance(other, Types.Var):
                    raise Exceptions.ValueUndefinedError("Missing value")
                if not (self.type.is_int() and other.type.is_int()
                        or self.type.is_float() and other.type.is_float()):
                    raise Exceptions.TypeError(
                        f"Incompatible types of {other} and {self}")
                if self.type.is_int():
                    return Types.Symb.Int(int(self.value - other.value))
                else:
                    return Types.Symb.Float(self.value - other.value)
            return NotImplemented

        def __mul__(self, other: 'Types.Symb'):
            if isinstance(other, (Types.Var, Types.Symb)):

                if other.type.is_nil() and isinstance(other, Types.Var):
                    raise Exceptions.ValueUndefinedError("Missing value")
                if not (self.type.is_int() and other.type.is_int()
                        or self.type.is_float() and other.type.is_float()):
                    raise Exceptions.TypeError(
                        f"Incompatible types of {other} and {self}")
                if self.type.is_int():
                    return Types.Symb.Int(int(self.value * other.value))
                else:
                    return Types.Symb.Float(self.value * other.value)
            return NotImplemented

        def __floordiv__(self, other: 'Types.Symb'):
            if isinstance(other, (Types.Var, Types.Symb)):
                if other.type.is_nil() and isinstance(other, Types.Var):
                    raise Exceptions.ValueUndefinedError("Missing value")
                if not (self.type.is_int() and other.type.is_int()):
                    raise Exceptions.TypeError(
                        f"Incompatible types of {other} and {self}")
                if other.value == 0:
                    raise Exceptions.OperandValueError(
                        "0 division is not allowed")
                return Types.Symb.Int(self.value // other.value)
            return NotImplemented

        def __truediv__(self, other: 'Types.Symb'):
            if isinstance(other, (Types.Var, Types.Symb)):

                if other.type.is_nil() and isinstance(other, Types.Var):
                    raise Exceptions.ValueUndefinedError("Missing value")
                if not (self.type.is_int() and other.type.is_int()
                        or self.type.is_float() and other.type.is_float()):
                    raise Exceptions.TypeError(
                        f"Incompatible types of {other} and {self}")
                if other.value == 0:
                    raise Exceptions.OperandValueError(
                        "0 division is not allowed")
                if self.type.is_int():
                    return Types.Symb.Int(int(self.value / other.value))
                else:
                    return Types.Symb.Float(self.value / other.value)
            return NotImplemented

        def __getitem__(self, arg: 'Types.Symb'):
            if not arg.type.is_int():
                raise Exceptions.TypeError(
                    "Invalid index type")
            if not self.type.is_string():
                raise Exceptions.TypeError(
                    "Expected string")
            if arg.value < 0:
                raise Exceptions.StringOperationError(
                    "Index can't be negative")
            try:
                return Types.Symb.String(self.value[arg.value])
            except IndexError:
                raise Exceptions.StringOperationError("Index out of range")

        def __str__(self):
            if self.type.is_bool():
                return "true" if self.value else "false"
            if self.type.is_float():
                return float.hex(float(self.value))

            return str(self.value) if not self.type.is_nil() and not self.type.is_undef() else ""

        def __repr__(self):
            return f"SYMB({self.type}, {self.value})"

    class Var(Symb):
        """
            Class, represents literal for variables.

            Methods:
                set_symb(symb): Assigns given Symb to a variable.
                to_scope(scope): Converts 'TF'|'LF'|'GF' to a specific type.
        """

        def __init__(self, name, scope):
            super().__init__(None, None)
            self.name = name
            self.scope = self.to_scope(scope)

        def set_symb(self, symb: 'Types.Symb'):
            """
                Assigns given Symb to a variable.
            """
            self.type = symb.type
            self.value = symb.value

        def to_scope(self, scope: str):
            """
                Converts 'TF'|'LF'|'GF' to a specific type.

                Raise:
                    InternalError: if given type of frame is not valid.

                Return:
                    constant of type FrameTypes.
            """
            if scope == "TF":
                return FrameTypes.TF
            elif scope == "LF":
                return FrameTypes.LF
            elif scope == "GF":
                return FrameTypes.GF
            else:
                raise Exceptions.InternalError(f"Scope {scope} is undefined")

        def __repr__(self):
            return f"VAR({self.name}, {self.value})"

    class Type:
        """
        Class, represents type literal, and type of Var and Symb.

        Classmethods:
            Int(): Creates instance of Type integer.
            Float(): Creates instance of Type float.
            String(): Creates instance of Type string.
            Bool(): Creates instance of Type bool.
            Nil(): Creates instance of Type nil.

        Methods:
            is_int(): Checks if type is integer
            is_float(): Checks if type is float
            is_string(): Checks if type is string
            is_bool(): Checks if type is bool
            is_nil(): Checks if type is nil
            to_type(): converts 'var'|'int'|'float'|'string'|'bool'|'nil' to a specific type. Calls methods above.
        """
        class _SymbTypes(Enum):
            INT = "int"
            STRING = "string"
            BOOL = "bool"
            FLOAT = "float"
            NIL = "nil"
            UNDEF = "undef"

        def __init__(self, value: 'Types.Type._SymbTypes'):
            self.value = value

        def __repr__(self):
            return f"TYPE({self.value})"

        def __eq__(self, other: 'Types.Type'):
            if isinstance(other, Types.Type):
                return self.value == other.value
            return False

        def __ne__(self, other: 'Types.Type'):
            if isinstance(other, Types.Type):
                return self.value != other.value
            return False

        def __str__(self):
            return str(self.value.value)

        @classmethod
        def Int(cls):
            """
                Creates instance of Type integer
            """
            return cls(cls._SymbTypes.INT)

        @classmethod
        def Float(cls):
            """
                Creates instance of Type float
            """
            return cls(cls._SymbTypes.FLOAT)

        @classmethod
        def String(cls):
            """
                Creates instance of Type string
            """
            return cls(cls._SymbTypes.STRING)

        @classmethod
        def Bool(cls):
            """
                Creates instance of Type bool
            """
            return cls(cls._SymbTypes.BOOL)

        @classmethod
        def Nil(cls):
            """
                Creates instance of Type nil
            """
            return cls(cls._SymbTypes.NIL)

        @classmethod
        def Undef(cls):
            """
                Creates instance of Type nil
            """
            return cls(cls._SymbTypes.UNDEF)

        def is_int(self):
            """
                Checks if type is integer
            """
            return self.value == Types.Type._SymbTypes.INT

        def is_float(self):
            """
                Checks if type is float
            """
            return self.value == Types.Type._SymbTypes.FLOAT

        def is_string(self):
            """
                Checks if type is string
            """
            return self.value == Types.Type._SymbTypes.STRING

        def is_bool(self):
            """
                Checks if type is bool
            """
            return self.value == Types.Type._SymbTypes.BOOL

        def is_nil(self):
            """
                Checks if type is nil
            """
            return self.value == Types.Type._SymbTypes.NIL

        def is_undef(self):
            """
                Checks if type is nil
            """
            return self.value == Types.Type._SymbTypes.UNDEF

        @staticmethod
        def to_type(_type: str) -> 'Types.Type':
            if isinstance(_type, Types.Type):
                return _type

            if _type == "int":
                return Types.Type.Int()
            elif _type == "string":
                return Types.Type.String()
            elif _type == "bool":
                return Types.Type.Bool()
            elif _type == "float":
                return Types.Type.Float()
            else:
                return Types.Type.Nil()

    class Label:
        """
            Class, represents labels
        """

        def __init__(self, value):
            self.value = value

        def __repr__(self):
            return f"LABEL({self.value})"


class Parser:
    """
        A class that contains nested classes that parse XML to a specific abstract object.

        Classes:
            Instruction
            _GenericParseType
            Symb
            Var
            Type
            Label
    """

    class Instruction:
        """
            Parses XML object into Instruction.

            Methods:
                parse(): parses XML object that represents instruction in XML and returns instance of `Instruction`.
                is_valid(): checks wether the XML is valid instruction object.
        """

        def __init__(self, element: XML.Element):
            self.element = element
            self.opcode = element.get('opcode')
            self.order = element.get('order')
            self.operands = list(element)

        def parse(self):
            """
                returns instance of Types.Instruction

                Raise:
                    XMLUnexpectedError: instruction object is not valid XML.

                Return:
                    Instance of Types.Instruction
            """
            if not self.is_valid():
                raise Exceptions.XMLUnexpectedError("Instruction is not valid")

            return Instruction(self.opcode, self.order, self.operands)

        def is_valid(self):
            """
                Checks if XML object is a valid instruction

                Return:
                    True if object is valid, othewise - False
            """
            return (self.opcode is not None
                    and self.order is not None
                    and self.opcode.upper() in dict.keys(EXPECTED_TYPES)
                    and self.order.isnumeric() and int(self.order) > 0
                    and self.element.tag == 'instruction')

    class _GenericParseType(metaclass=ABCMeta):
        """
            Abstract class that defines behaviour for methods that parse XML.

            Methods definitions:
                parse()
                is_valid()
        """

        def __init__(self, element: XML.Element):
            self.element = element
            self.attr = element.get("type")
            try:
                self.text = element.text.strip()
            except AttributeError:
                self.text = None

        @abstractmethod
        def parse(self):
            pass

        @abstractmethod
        def is_valid(self):
            pass

    class Symb(_GenericParseType):
        """
            Class that is configured to parse `Symb` literals out of XML

            Methods:
                parse(): Returns instance of Symb in case if XML object is a symb
                is_valid(): Returns true if XML object is valid `Symb`
        """

        def __init__(self, element: XML.Element):
            super().__init__(element)

        def parse(self):
            """
                Returns instance of `Symb` in case if XML object is a symb

                Return:
                    Instance of `Types.Symb`, otherwise it checks for `Types.Var`
            """
            if not self.is_valid():
                return Parser.Var(self.element).parse()

            return Types.Symb(self.text, self.attr.lower())

        def is_valid(self):
            """
                Returns true if XML object is valid `Symb`. There is also
                extra check for a specific type of a literal. Just in case.

                Return:
                    true if object is valid XML symb literal, otherwise false
            """
            if re.search(r"^(int|bool|string|float|nil)$", self.attr) is None:
                return False
            return True

    class Var(_GenericParseType):
        """
            Class that is configured to parse XML objects representing `Var` literals.

            Methods:
                parse(): Parses and returns an instance of `Types.Var`
                is_valid(): Checks whether XML object is valid `Types.Var` literal
        """

        def __init__(self, element: XML.Element):
            super().__init__(element)

        def parse(self):
            """
                Parses and returns an instance of Types.Var

                Raise:
                    TypeError: Unexpected type

                Return:
                    Instance of a Types.Var if XML is valid Var.
            """
            if not self.is_valid():
                raise Exceptions.TypeError("Unexpected type")

            scope, name = self.text.split('@')

            return Types.Var(name, scope)

        def is_valid(self):
            """
                Checks whether XML object is valid Types.Var literal.

                Return:
                    true in case if XML object is valid
            """
            return (self.attr == "var"
                    and re.search(r"^(GF|LF|TF)@[a-zA-Z_\-$&%*!?][\w\-$&%*!?]*$", self.text))

    class Type(_GenericParseType):
        """
            Class that is configured to parse types out of XML objects

            Methods:
                parse(): parses and returns instance of a Types.Type
                is_valid(): checks if XML object is valud Type
        """

        def __init__(self, element: XML.Element):
            super().__init__(element)

        def parse(self):
            """
                Parses and returns instance of a Types.Type

                Raise:
                    TypeError: Unexpected type

                Return:
                    Instance of a Types.Type
            """
            if not self.is_valid:
                raise Exceptions.TypeError("Unexpected type")

            return Types.Type.to_type(self.text.lower())

        def is_valid(self):
            """
                Checks if XML object is valid Type.

                Return:
                    True if object is valid XML
            """
            return (self.attr == "type"
                    and re.search(r"^(int|bool|string|float|nil)$", self.text))

    class Label(_GenericParseType):
        """
            Class that is configured to parse labels.

            Methods:
                parse(): parses XML object and returns instance of Types.Label
                is_valid(): checks whether XML object is valid Label

        """

        def __init__(self, element: XML.Element):
            super().__init__(element)

        def parse(self):
            """
                Parses XML object and returns instance of Types.Label

                Raise:
                    TypeError: Unexpected type

                Return:
                    Instance of Types.Label
            """
            if not self.is_valid():
                raise Exceptions.TypeError("Unexpected type")

            return Types.Label(self.text)

        def is_valid(self):
            """
                Checks whether XML object is valid Label

                Return:
                    true if the object is valid Label, otherwise - false
            """
            return (self.attr == "label"
                    and re.search(r"^[a-zA-Z_\-$&%*!?][\w\-$&%*!?]*$", self.text))


EXPECTED_TYPES = {
    "MOVE": [Parser.Var, Parser.Symb],
    "CREATEFRAME": None,
    "PUSHFRAME": None,
    "POPFRAME": None,
    "DEFVAR": [Parser.Var],
    "CALL": [Parser.Label],
    "RETURN": None,

    "PUSHS": [Parser.Symb],
    "POPS": [Parser.Var],

    "ADD": [Parser.Var, Parser.Symb, Parser.Symb],
    "SUB": [Parser.Var, Parser.Symb, Parser.Symb],
    "MUL": [Parser.Var, Parser.Symb, Parser.Symb],
    "IDIV": [Parser.Var, Parser.Symb, Parser.Symb],
    "DIV": [Parser.Var, Parser.Symb, Parser.Symb],
    "LT": [Parser.Var, Parser.Symb, Parser.Symb],
    "GT": [Parser.Var, Parser.Symb, Parser.Symb],
    "EQ": [Parser.Var, Parser.Symb, Parser.Symb],
    "AND": [Parser.Var, Parser.Symb, Parser.Symb],
    "OR": [Parser.Var, Parser.Symb, Parser.Symb],
    "NOT": [Parser.Var, Parser.Symb],

    "CLEARS": None,
    "ADDS": None,
    "SUBS": None,
    "MULS": None,
    "DIVS": None,
    "IDIVS": None,
    "LTS": None,
    "GTS": None,
    "EQS": None,
    "ANDS": None,
    "ORS": None,
    "NOTS": None,
    "INT2CHARS": None,
    "STRI2INTS": None,
    "INT2FLOATS": None,
    "FLOAT2INTS": None,

    "JUMPIFEQS": [Parser.Label],
    "JUMPIFNEQS": [Parser.Label],

    "INT2CHAR": [Parser.Var, Parser.Symb],
    "STRI2INT": [Parser.Var, Parser.Symb, Parser.Symb],
    "INT2FLOAT": [Parser.Var, Parser.Symb],
    "FLOAT2INT": [Parser.Var, Parser.Symb],
    "READ": [Parser.Var, Parser.Type],
    "WRITE": [Parser.Symb],

    "CONCAT": [Parser.Var, Parser.Symb, Parser.Symb],
    "STRLEN": [Parser.Var, Parser.Symb],
    "GETCHAR": [Parser.Var, Parser.Symb, Parser.Symb],
    "SETCHAR": [Parser.Var, Parser.Symb, Parser.Symb],

    "TYPE": [Parser.Var, Parser.Symb],

    "LABEL": [Parser.Label],
    "JUMP": [Parser.Label],
    "JUMPIFEQ": [Parser.Label, Parser.Symb, Parser.Symb],
    "JUMPIFNEQ": [Parser.Label, Parser.Symb, Parser.Symb],
    "EXIT": [Parser.Symb],

    "DPRINT": [Parser.Symb],
    "BREAK": None,
}


class Instruction:
    """
        Class, that represents instruction. Its instances are created when parsing XML.

        Raise:
            XMLUnexpectedError: any operand errors
    """

    def __init__(self, opcode: str, order: str, operands: list):
        self.opcode = opcode.upper()
        self.order = int(order)
        self.operands = []

        expectTypeList = EXPECTED_TYPES[self.opcode]

        if len(operands) != len(expectTypeList or []):
            raise Exceptions.XMLUnexpectedError(
                f"Invalid number of arguments in {self.opcode}")

        try:
            for idx, child in enumerate(sorted(operands, key=lambda child: child.tag)):
                if child.tag != f"arg{idx+1}":
                    raise Exceptions.XMLUnexpectedError(
                        f"Invalid operand at {self.opcode}, order={self.order}")
                TypeParser = expectTypeList[idx]
                self.operands.append(TypeParser(child).parse())
        except IndexError:
            raise Exceptions.XMLUnexpectedError(
                f"Too many arguments for {self.opcode}")

    def __repr__(self):
        return f"(order={self.order},instruction={self.opcode},operands={self.operands})"


class Frame():
    """
        Class that represents frames in IFJcode23.

        Raise:
            SemanticError: variable is already defined

        Methods:
            get_var(var_name): Gets variable by its name.
            set_var(var): Declares variable in specific frame.
    """

    def __init__(self):
        self._data = {}

    def get_var(self, var_name):
        """
            Gets variable by its name.

            Params:
                var_name: name of the variable

            Return: 
                Object of type `Types.Var`
        """
        return self._data.get(var_name)

    def set_var(self, var: Types.Var):
        """
            Declares variable in specific frame

            Params:
                var: Object of type `Types.Var` that needs to be declared in frame
        """
        if self.get_var(var.name) is not None:
            raise Exceptions.SemanticError(
                f"Variable {var.name} is already defined at {var.scope}")

        var.type = Types.Type.Undef()
        self._data[var.name] = var

    def __repr__(self):
        return repr(self._data)


class FrameManager():
    """
        Class for managing memory model in IFJcode23.

        Methods:
            set_var(var): Declares variable in specific frame
            get_var(var): Returns var out of specific frame
            create_frame(): Creates frame TF
            push_frame(): Moves TF onto LF
            pop_frame(): Moves LF onto TF
    """

    def __init__(self):
        self._gframe = Frame()
        self._lframe = []
        self._tframe = None

    def set_var(self, var: Types.Var):
        """
            Declares variable in specific frame.

            Raise:
                FrameError: frame is not defined
                InternalError: undefined frame
        """
        if var.scope == FrameTypes.GF:
            self._gframe.set_var(var)
        elif var.scope == FrameTypes.TF:
            if self._tframe is None:
                raise Exceptions.FrameError(f"TF is not defined")
            self._tframe.set_var(var)
        elif var.scope == FrameTypes.LF:
            if len(self._lframe) == 0:
                raise Exceptions.FrameError(f"LF is not defined")
            self._lframe[-1].set_var(var)
        else:
            raise Exceptions.InternalError(
                f"Something went wrong. Checkout set_var() in FrameManager")

    def get_var(self, var: Types.Var) -> Types.Var:
        """
            Returns var out of specific frame.

            Raise:
                FrameError: Frame does not exist.
                VariableUndefinedError: Variable is not defined.

            Return:
                Instance of `Types.Var`
        """

        if var.scope == FrameTypes.TF:
            if self._tframe is None:
                raise Exceptions.FrameError("Frame TF does not exist.")
            _var = self._tframe.get_var(var.name)
        elif var.scope == FrameTypes.LF:
            if len(self._lframe) == 0:
                raise Exceptions.FrameError("Frame LF does not exist.")
            _var = self._lframe[-1].get_var(var.name)
        elif var.scope == FrameTypes.GF:
            _var = self._gframe.get_var(var.name)

        if _var is None:
            raise Exceptions.VariableUndefinedError(
                f"Variable '{var.name}' is not defined at {var.scope}")
        else:
            return _var

    def create_frame(self):
        """
            Creates frame TF
        """
        self._tframe = Frame()

    def push_frame(self):
        """
            Moves TF onto LF

            Raise:
                FrameError: TF is not defined
        """
        if self._tframe is None:
            raise Exceptions.FrameError(f"Unable to push undefined TF to LF")
        self._lframe.append(self._tframe)
        self._tframe = None

    def pop_frame(self):
        """
            Moves LF onto TF

            Raise:
                FrameError: LF is not defined
        """
        if len(self._lframe) == 0:
            raise Exceptions.FrameError(f"Unable to pop LF when it is empty")
        self._tframe = self._lframe.pop()

    def __repr__(self):
        return f"GF: {self._gframe}\nTF: {self._tframe}\nLF: {self._lframe}"


class StackManager():
    """
        Class for managing data stack

        Methods:
            Instruction implementation.
    """

    def __init__(self):
        self._data = []

    def push(self, symb: Types.Symb):
        self._data.append(symb)

    def pop(self) -> Types.Symb:
        if self.is_empty():
            raise Exceptions.ValueUndefinedError("Data stack is empty")
        return self._data.pop()

    def get_symb(self):
        if len(self._data) < 1:
            raise Exceptions.ValueUndefinedError("Data stack is empty")
        return self._data[-1]

    def get_symb_symb(self):
        if len(self._data) < 2:
            raise Exceptions.ValueUndefinedError("Data stack is empty")
        return self._data[-2], self._data[-1]

    def pop_symb_symb(self):
        symb2 = self.pop()
        symb1 = self.pop()
        return symb1, symb2

    def clear(self):
        self._data = []

    def add(self):
        symb1, symb2 = self.pop_symb_symb()
        self.push(symb1+symb2)

    def sub(self):
        symb1, symb2 = self.pop_symb_symb()
        self.push(symb1-symb2)

    def mul(self):
        symb1, symb2 = self.pop_symb_symb()
        self.push(symb1*symb2)

    def div(self):
        symb1, symb2 = self.pop_symb_symb()
        self.push(symb1/symb2)

    def idiv(self):
        symb1, symb2 = self.pop_symb_symb()
        self.push(symb1//symb2)

    def lt(self):
        symb1, symb2 = self.pop_symb_symb()
        self.push(symb1 < symb2)

    def gt(self):
        symb1, symb2 = self.pop_symb_symb()
        self.push(symb1 > symb2)

    def eq(self):
        symb1, symb2 = self.pop_symb_symb()
        self.push(symb1 == symb2)

    def ands(self):
        symb1, symb2 = self.pop_symb_symb()
        self.push(symb1 & symb2)

    def ors(self):
        symb1, symb2 = self.pop_symb_symb()
        self.push(symb1 | symb2)

    def nots(self):
        symb1 = self.pop()
        self.push(~symb1)

    def int2char(self):
        symb = self.pop()
        if not symb.type.is_int():
            raise Exceptions.TypeError(
                "Invalid type in INT2CHARS")
        try:
            self.push(Types.Symb.String(chr(symb.value)))
        except ValueError:
            raise Exceptions.StringOperationError(
                f"{symb} is not valid unicode")

    def stri2int(self):
        symb1, symb2 = self.pop_symb_symb()
        self.push(Types.Symb.Int(ord(symb1[symb2].value)))

    def int2float(self):
        symb1 = self.pop()
        if symb1.type.is_nil():
            raise Exceptions.ValueUndefinedError(
                "Cannot convert NIL to FLOAT")
        if not symb1.type.is_int():
            raise Exceptions.TypeError(
                "Invalid type in convert")

        self.push(Types.Symb.Float(symb1.value))

    def float2int(self):
        symb1 = self.pop()

        if symb1.type.is_nil():
            raise Exceptions.ValueUndefinedError(
                "Cannot convert NIL to INT")
        if not symb1.type.is_float():
            raise Exceptions.TypeError(
                "Invalid type in convert")

        self.push(Types.Symb.Int(int(symb1.value)))

    def is_empty(self):
        return len(self._data) == 0

    def __repr__(self):
        return str(self._data)


def read_input_generator(filename=None):
    if filename is None:
        file = sys.stdin
    else:
        file = open(filename, 'r')
    try:
        for line in file:
            yield line.rstrip('\n')
    finally:
        if file is not sys.stdin:
            file.close()


def _write(symb: Types.Symb, file=sys.stdout):
    if symb.type.is_string():
        print(deescape_str(str(symb.value)), end="", file=file)
    else:
        print(symb, end="", file=file)


class InstructionManager():

    def __init__(self):
        self._instructions = []

    def insert(self, instruction: Instruction):
        self._instructions.append(instruction)

    def instructions(self):
        return sorted(self._instructions, key=lambda i: i.order)


class CallStack():
    """
        Class for managing CALL and RETURN instructions. It stores indexes of Calls.

        Methods:
            push(label): Saves index of specific label in order to return back to it
            pop(): Pops saved index
            is_empty(): Checks if call stack is empty
    """

    def __init__(self):
        self._calls = []

    def push(self, label):
        """
            Saves index of specific label in order to return back to it
        """
        self._calls.append(label)

    def pop(self):
        """
            Pops saved index.

            Raise:
                ValueUndefinedError: Call stack is empty
        """
        if self.is_empty():
            raise Exceptions.ValueUndefinedError("Call stack is empty")
        return self._calls.pop()

    def is_empty(self):
        """
            Checks if call stack is empty
        """
        return len(self._calls) == 0

    def __repr__(self):
        return f"Call stack: {self._calls}"


def main():

    source = None  # XML file with source code
    input = None  # input file

    try:

        try:
            opts, args = getopt.getopt(
                sys.argv[1:], "hs:i:", ["help", "source=", "input="])
        except getopt.GetoptError as err:
            raise Exceptions.OptionError(err)

        for opt, arg in opts:
            if opt in ('-h', '--help'):
                if len(opts) > 1:
                    raise Exceptions.OptionError(
                        "Option --help(-h) can only be used without any other options)")
                print(USAGE)
                exit(0)
            elif opt in ('-s', '--source'):
                source = arg
            elif opt in ('-i', '--input'):
                input = arg

        if source is None:
            source = sys.stdin

        input = read_input_generator(input)

        try:
            tree = XML.parse(source)
        except FileNotFoundError:
            raise Exceptions.OptionError(
                f"{source}: No such file or directory")
        except XML.ParseError:
            raise Exceptions.XMLFormatError("Invalid XML format")

        root = tree.getroot()

        # TODO validate <?xml version="1.0" encoding="UTF-8"?>
        if root.tag != "program":
            raise Exceptions.XMLUnexpectedError("Expected <program> element")

        IManager = InstructionManager()

        for child in root:
            IManager.insert(Parser.Instruction(child).parse())

        instructions = IManager.instructions()

        # dublicate order check
        orders = list(map(lambda i: i.order, instructions))
        if len(orders) != len(set(orders)):
            raise Exceptions.XMLUnexpectedError("Duplicate order")

        FManager = FrameManager()
        SManager = StackManager()
        CStack = CallStack()
        labels = {}

        for idx, i in enumerate(instructions):
            if i.opcode == "LABEL":
                label, = i.operands
                if labels.get(label.value) is None:
                    labels[label.value] = idx
                else:
                    raise Exceptions.SemanticError(
                        f"Label {label.value} is already defined")

        idx = 0

        while idx < len(instructions):
            instruction = instructions[idx]

            if instruction.opcode == "CREATEFRAME":
                FManager.create_frame()
            elif instruction.opcode == "PUSHFRAME":
                FManager.push_frame()
            elif instruction.opcode == "POPFRAME":
                FManager.pop_frame()
            elif instruction.opcode == "DEFVAR":
                var, = instruction.operands
                FManager.set_var(var)
            elif instruction.opcode == "WRITE":
                symb, = instruction.operands
                if isinstance(symb, Types.Var):
                    symb = FManager.get_var(symb)
                    if symb.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                _write(symb)
            elif instruction.opcode == "DPRINT":
                symb, = instruction.operands
                if isinstance(symb, Types.Var):
                    symb = FManager.get_var(symb)
                _write(symb, file=sys.stderr)
            elif instruction.opcode == "BREAK":
                print(instruction.order, end="", file=sys.stderr)
                print(FManager, end="", file=sys.stderr)
                print(SManager, end="", file=sys.stderr)
                print(CStack, end="", file=sys.stderr)
            elif instruction.opcode == "READ":
                var, _type = instruction.operands
                
                try:
                    var = FManager.get_var(var)
                    value = next(input)
                    if _type.is_int():
                        int(value)
                        
                    var.set_symb(Types.Symb(value, _type))
                except (ValueError, StopIteration):
                    var.set_symb(Types.Symb.Nil(None))
            elif instruction.opcode == "MOVE":
                var, symb = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb, Types.Var):
                    symb = FManager.get_var(symb)
                    if symb.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                var.set_symb(symb)
            elif instruction.opcode == "ADD":
                var, symb1, symb2 = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb1.type.is_nil():
                        raise Exceptions.ValueUndefinedError("Missing value")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb2.type.is_nil():
                        raise Exceptions.ValueUndefinedError("Missing value")

                var.set_symb(symb1 + symb2)
            elif instruction.opcode == "SUB":
                var, symb1, symb2 = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb1.type.is_nil():
                        raise Exceptions.ValueUndefinedError("Missing value")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb2.type.is_nil():
                        raise Exceptions.ValueUndefinedError("Missing value")

                var.set_symb(symb1 - symb2)
            elif instruction.opcode == "MUL":
                var, symb1, symb2 = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb1.type.is_nil():
                        raise Exceptions.ValueUndefinedError("Missing value")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb2.type.is_nil():
                        raise Exceptions.ValueUndefinedError("Missing value")

                var.set_symb(symb1 * symb2)
            elif instruction.opcode == "IDIV":
                var, symb1, symb2 = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb1.type.is_nil():
                        raise Exceptions.ValueUndefinedError("Missing value")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb2.type.is_nil():
                        raise Exceptions.ValueUndefinedError("Missing value")

                var.set_symb(symb1 // symb2)
            elif instruction.opcode == "DIV":
                var, symb1, symb2 = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb1.type.is_nil():
                        raise Exceptions.ValueUndefinedError("Missing value")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb2.type.is_nil():
                        raise Exceptions.ValueUndefinedError("Missing value")

                var.set_symb(symb1 / symb2)
            elif instruction.opcode == "EXIT":
                symb, = instruction.operands
                if isinstance(symb, Types.Var):
                    symb = FManager.get_var(symb)
                    if symb.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if not symb.type.is_int():
                    raise Exceptions.TypeError(
                        "EXIT accepts only integer")
                if symb.value < 0 or symb.value > 49:
                    raise Exceptions.OperandValueError(
                        "EXIT code must be in interval <0, 49>")
                exit(symb.value)
            elif instruction.opcode == "TYPE":
                var, symb = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb, Types.Var):
                    symb = FManager.get_var(symb)
                if symb.type.is_undef():
                    var.set_symb(Types.Symb.Nil(None))
                else:
                    var.set_symb(Types.Symb.String(str(symb.type)))
            elif instruction.opcode == "LT":
                var, symb1, symb2 = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                var.set_symb(symb1 < symb2)

            elif instruction.opcode == "GT":
                var, symb1, symb2 = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                var.set_symb(symb1 > symb2)

            elif instruction.opcode == "EQ":
                var, symb1, symb2 = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                var.set_symb(symb1 == symb2)

            elif instruction.opcode == "AND":
                var, symb1, symb2 = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb1.type.is_nil():
                        raise Exceptions.ValueUndefinedError("Missing value")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb2.type.is_nil():
                        raise Exceptions.ValueUndefinedError("Missing value")
                var.set_symb(symb1 & symb2)

            elif instruction.opcode == "OR":
                var, symb1, symb2 = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb1.type.is_nil():
                        raise Exceptions.ValueUndefinedError("Missing value")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb2.type.is_nil():
                        raise Exceptions.ValueUndefinedError("Missing value")
                var.set_symb(symb1 | symb2)

            elif instruction.opcode == "NOT":
                var, symb1 = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb1.type.is_nil():
                        raise Exceptions.TypeError("Missing value")
                var.set_symb(~symb1)

            elif instruction.opcode == "INT2CHAR":
                var, symb = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb, Types.Var):
                    symb = FManager.get_var(symb)
                    if symb.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if not symb.type.is_int():
                    raise Exceptions.TypeError(
                        "Invalid type in INT2CHAR")
                try:
                    var.set_symb(Types.Symb.String(chr(symb.value)))
                except ValueError as e:
                    raise Exceptions.StringOperationError(e)
            elif instruction.opcode == "STRI2INT":
                var, symb1, symb2 = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")

                var.set_symb(Types.Symb.Int(ord(symb1[symb2].value)))

            elif instruction.opcode == "INT2FLOAT":
                var, symb = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb, Types.Var):
                    symb = FManager.get_var(symb)
                    if symb.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb.type.is_nil():
                        raise Exceptions.ValueUndefinedError(
                            "Cannot convert NIL to FLOAT")
                if not symb.type.is_int():
                    raise Exceptions.TypeError(
                        "Invalid type in convert")

                var.set_symb(Types.Symb.Float(symb.value))
            elif instruction.opcode == "FLOAT2INT":
                var, symb = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb, Types.Var):
                    symb = FManager.get_var(symb)
                    if symb.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                    if symb.type.is_nil():
                        raise Exceptions.ValueUndefinedError(
                            "Cannot convert NIL to INT")
                if not symb.type.is_float():
                    raise Exceptions.TypeError(
                        "Invalid type in convert")

                var.set_symb(Types.Symb.Int(int(symb.value)))
            elif instruction.opcode == "LABEL":
                pass
            elif instruction.opcode == "CALL":
                label, = instruction.operands
                jump_to = labels.get(label.value)
                if jump_to is None:
                    raise Exceptions.SemanticError(
                        f"Label {label.value} is undefined")
                CStack.push(idx)
                idx = jump_to
            elif instruction.opcode == "RETURN":
                jump_to = CStack.pop()
                if jump_to is None:
                    raise Exceptions.SemanticError(
                        f"Label {label.value} is undefined")
                idx = jump_to
            elif instruction.opcode == "JUMP":
                label, = instruction.operands
                jump_to = labels.get(label.value)
                if jump_to is None:
                    raise Exceptions.SemanticError(
                        f"Label {label.value} is undefined")
                idx = jump_to
            elif instruction.opcode == "JUMPIFEQ":
                label, symb1, symb2 = instruction.operands

                jump_to = labels.get(label.value)
                if jump_to is None:
                    raise Exceptions.SemanticError(
                        f"Label {label.value} is undefined")

                if not symb1.type.is_nil and not symb2.type.is_nil():
                    if symb1.type != symb2.type:
                        raise Exceptions.TypeError(
                            "Incompatible types in JUMPIFEQ")

                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")

                if bool(symb1 == symb2):
                    idx = jump_to

            elif instruction.opcode == "JUMPIFNEQ":
                label, symb1, symb2 = instruction.operands
                jump_to = labels.get(label.value)
                if jump_to is None:
                    raise Exceptions.SemanticError(
                        f"Label {label.value} is undefined")

                if not symb1.type.is_nil() and not symb2.type.is_nil():
                    if symb1.type != symb2.type:
                        raise Exceptions.TypeError(
                            "Incompatible types in JUMPIFNEQ")

                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")

                if bool(symb1 != symb2):
                    idx = jump_to
            elif instruction.opcode == "JUMPIFEQS":
                label, = instruction.operands

                jump_to = labels.get(label.value)
                if jump_to is None:
                    raise Exceptions.SemanticError(
                        f"Label {label.value} is undefined")

                symb1, symb2 = SManager.get_symb_symb()

                if not symb1.type.is_nil() and not symb2.type.is_nil():
                    if symb1.type != symb2.type:
                        raise Exceptions.TypeError(
                            "Incompatible types in JUMPIFEQS")

                if bool(symb1 == symb2):
                    idx = jump_to
            elif instruction.opcode == "JUMPIFNEQS":
                label, = instruction.operands
                jump_to = labels.get(label.value)
                if jump_to is None:
                    raise Exceptions.SemanticError(
                        f"Label {label.value} is undefined")

                symb1, symb2 = SManager.get_symb_symb()

                if not symb1.type.is_nil() and not symb2.type.is_nil():
                    if symb1.type != symb2.type:
                        raise Exceptions.TypeError(
                            "Incompatible types in JUMPIFNEQ")

                if bool(symb1 != symb2):
                    idx = jump_to
            elif instruction.opcode == "PUSHS":
                symb, = instruction.operands
                if isinstance(symb, Types.Var):
                    symb = FManager.get_var(symb)
                    if symb.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                SManager.push(symb)
            elif instruction.opcode == "POPS":
                var, = instruction.operands
                var = FManager.get_var(var)
                var.set_symb(SManager.pop())
            elif instruction.opcode == "CLEARS":
                SManager.clear()
            elif instruction.opcode == "ADDS":
                SManager.add()
            elif instruction.opcode == "SUBS":
                SManager.sub()
            elif instruction.opcode == "MULS":
                SManager.mul()
            elif instruction.opcode == "DIVS":
                SManager.div()
            elif instruction.opcode == "IDIVS":
                SManager.idiv()
            elif instruction.opcode == "LTS":
                SManager.lt()
            elif instruction.opcode == "GTS":
                SManager.gt()
            elif instruction.opcode == "EQS":
                SManager.eq()
            elif instruction.opcode == "ANDS":
                SManager.ands()
            elif instruction.opcode == "ORS":
                SManager.ors()
            elif instruction.opcode == "NOTS":
                SManager.nots()
            elif instruction.opcode == "INT2CHARS":
                SManager.int2char()
            elif instruction.opcode == "STRI2INTS":
                SManager.stri2int()
            elif instruction.opcode == "FLOAT2INTS":
                SManager.float2int()
            elif instruction.opcode == "INT2FLOATS":
                SManager.int2float()
            elif instruction.opcode == "CONCAT":
                var, symb1, symb2 = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if not symb1.type.is_string() or not symb2.type.is_string():
                    raise Exceptions.TypeError(
                        "Both operands must be of type string in CONCAT")
                var.set_symb(Types.Symb.String(symb1.value + symb2.value))
            elif instruction.opcode == "STRLEN":
                var, symb1 = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if not symb1.type.is_string():
                    raise Exceptions.TypeError(
                        "Operand must be of type string in STRLEN")
                var.set_symb(Types.Symb.Int(len(symb1.value or "")))
            elif instruction.opcode == "GETCHAR":
                var, symb1, symb2 = instruction.operands
                var = FManager.get_var(var)
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if not symb1.type.is_string():
                    raise Exceptions.TypeError(
                        "Second operand in GETCHAR must be string")
                if not symb2.type.is_int():
                    raise Exceptions.TypeError(
                        "Third operand in GETCHAR must be integer")
                if symb2.value < 0:
                    raise Exceptions.StringOperationError(
                        "Second operand in GETCHAR must be >= 0")
                var.set_symb(Types.Symb.String(symb1[symb2]))
            elif instruction.opcode == "SETCHAR":
                var, symb1, symb2 = instruction.operands
                var = FManager.get_var(var)
                if var.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if isinstance(symb1, Types.Var):
                    symb1 = FManager.get_var(symb1)
                    if symb1.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if isinstance(symb2, Types.Var):
                    symb2 = FManager.get_var(symb2)
                    if symb2.type.is_undef():
                        raise Exceptions.ValueUndefinedError(
                            "Var's value is undefined")
                if not var.type.is_string():
                    raise Exceptions.TypeError(
                        "First operand in SETCHAR must be string")
                if not symb1.type.is_int():
                    raise Exceptions.TypeError(
                        "Second operand in SETCHAR must be integer")
                if symb1.value < 0:
                    raise Exceptions.StringOperationError(
                        "Second operand in SETCHAR must be >= 0")
                if not symb2.type.is_string():
                    raise Exceptions.TypeError(
                        "Third operand in SETCHAR must be string")
                try:
                    val1 = deescape_str(var.value)
                    val2 = deescape_str(symb2.value)
                    listValue = list(val1)
                    listValue[symb1.value] = val2[0]
                    var.set_symb(Types.Symb.String("".join(listValue)))
                except IndexError as e:
                    raise Exceptions.StringOperationError(e)
            idx += 1

    except (Exceptions.OptionError,
            Exceptions.XMLFormatError,
            Exceptions.XMLUnexpectedError,
            Exceptions.TypeError,
            Exceptions.SemanticError,
            Exceptions.FrameError,
            Exceptions.OperandValueError,
            Exceptions.StringOperationError,
            Exceptions.ValueUndefinedError,
            Exceptions.VariableUndefinedError,
            Exceptions.InternalError) as e:
        Exceptions.exit(e)


if __name__ == "__main__":
    main()
