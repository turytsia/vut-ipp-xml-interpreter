import getopt
import sys
from enum import Enum
import xml.etree.ElementTree as XML
import re

INSTRUCTION_DICT = {
    "MOVE": "var symb",
    "CREATEFRAME": "",
    "PUSHFRAME": "",
    "POPFRAME": "",
    "DEFVAR": "var",
    "CALL": "label",
    "RETURN": "",

    "PUSHS": "symb",
    "POPS": "var",

    "ADD": "var symb symb",
    "SUB": "var symb symb",
    "MUL": "var symb symb",
    "IDIV": "var symb symb",
    "LT": "var symb symb",
    "GT": "var symb symb",
    "EQ": "var symb symb",
    "AND": "var symb symb",
    "OR": "var symb symb",
    "NOT": "var symb",

    "INT2CHAR": "var symb",
    "STRI2INT": "var symb symb",
    "READ": "var type",
    "WRITE": "symb",

    "CONCAT": "var symb symb",
    "STRLEN": "var symb",
    "GETCHAR": "var symb symb",
    "SETCHAR": "var symb symb",

    "TYPE": "var symb",

    "LABEL": "label",
    "JUMP": "label",
    "JUMPIFEQ": "label symb symb",
    "JUMPIFNEQ": "label symb symb",
    "EXIT": "symb",

    "DPRINT": "symb",
    "BREAK": "",
}


class ErrorCodes(Enum):
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


class OperandTypes(Enum):
    VAR = "var"
    SYMB = "symb"
    TYPE = "type"
    LABEL = "label"


class SymbTypes(Enum):
    INT = 0
    STRING = 1
    BOOL = 2
    NIL = 3


class FrameTypes(Enum):
    TF = 1
    LF = 2
    GF = 3


def exit_with_message(message: str, error_code: ErrorCodes):
    print(message, file=sys.stdout if error_code == ErrorCodes.SUCCESS else sys.stderr)
    sys.exit(error_code.value)

class Types():
    def __init__(self, op_type: OperandTypes) :
        self.op_type = op_type.value


class Var(Types):
    def __init__(self, operand : XML.Element) :
            super().__init__(OperandTypes.VAR)
            scope, self.name = operand.text.strip().split('@')
            self.value = None
            self.type = None

            if scope == "TF":
                self.scope = FrameTypes.TF
            elif scope == "LF":
                self.scope = FrameTypes.LF
            elif scope == "GF":
                self.scope = FrameTypes.GF
            else:
                exit_with_message(f"Something went wrong in Var, __init__()",
                                  ErrorCodes.ERR_INTERNAL)
    def set_value(self, value, type):
        self.type = type.value
        try:
            if self.type == SymbTypes.INT:
                self.value = int(value)
            elif self.type == SymbTypes.STRING:
                self.value = value
            elif self.type == SymbTypes.BOOL:
                self.value = True if value == "true" else False
            else:
                self.value = None
        except ValueError:
            self.value = None

        


    def __repr__(self) :
        return f"VAR({self.scope}, {self.name})"
    
class Symb(Types):
    def __init__(self, operand: XML.Element) :
        super().__init__(OperandTypes.SYMB)
        self.type = operand.get("type")
        self.value = operand.text.strip()

    def __repr__(self) :
        return f"SYMB({self.type}, {self.value})"


class Type(Types):
    def __init__(self, operand: XML.Element) :
        super().__init__(OperandTypes.TYPE)
        type = operand.text.strip().upper()
        if type == "INT":
            self.value = SymbTypes.INT
        elif type == "STRING":
            self.value = SymbTypes.STRING
        elif type == "BOOL":
            self.value = SymbTypes.BOOL
        else:
            self.value = SymbTypes.NIL


    def __repr__(self) :
        return f"TYPE({self.value})"


class Label(Types):
    def __init__(self, operand: XML.Element) :
        super().__init__(OperandTypes.LABEL)
        self.value = operand.text.strip()

    def __repr__(self) :
        return f"LABEL({self.value})"

class Operand():
    # TODO argument order
    def __init__(self, inst_name: str, operand: XML.Element) :
        if not Operand._is_operand(operand):
            exit_with_message(f"Invalid operands in {inst_name}",
                              ErrorCodes.ERR_XML_STRUCT)
        parsed_operand = Operand._parse_operand(operand)
        self.type = parsed_operand.op_type
        self.target = parsed_operand

    @staticmethod
    def _parse_operand(operand: XML.Element) -> Types:
        if not Operand._is_operand(operand):
            exit_with_message("Unknown argument",
                              ErrorCodes.ERR_XML_STRUCT)
        if Operand._is_var(operand):
            return Var(operand)
        elif Operand._is_symb(operand):
            return Symb(operand)
        elif Operand._is_type(operand):
            return Type(operand)
        elif Operand._is_label(operand):
            return Label(operand)
        else:
            exit_with_message("Unexpected type",
                              ErrorCodes.ERR_TYPE)

    @staticmethod
    def _is_operand(operand: XML.Element):
        if not re.search(r"^arg[1-3]$", operand.tag):
            return False
        if not operand.get("type"):
            return False
        return True

    @staticmethod
    def _is_var(operand: XML.Element):
        if operand.get("type") != "var":
            return False
        if not re.search(r"^(GF|LF|TF)@[a-zA-Z_\-$&%*!?][\w\-$&%*!?]*$", operand.text.strip()):
            return False
        return True

    @staticmethod
    def _is_symb(operand: XML.Element):
        if not re.search(r"^(int|bool|string|nil)", operand.get("type")):
            return Operand._is_var(operand)
        return True

    @staticmethod
    def _is_type(operand: XML.Element):
        if operand.get("type") != "type":
            return False
        if not re.search(r"^(int|bool|string|nil)$", operand.text.strip()):
            return False
        return True

    @staticmethod
    def _is_label(operand: XML.Element):
        if operand.get("type") != "label":
            return False
        if not re.search(r"^[a-zA-Z_\-$&%*!?][\w\-$&%*!?]*$", operand.text.strip()):
            return False
        return True

    def __repr__(self) :
        return f"{self.target}"


class Instruction():
    def __init__(self, element: XML.Element) :
        self.opcode = element.get('opcode')
        self.order = int(element.get('order'))
        self.operands = []

        # REVIEW this could check number of args
        expected_operands = INSTRUCTION_DICT[self.opcode].split(" ")
        try:
            for idx, child in enumerate(element):
                operand = Operand(self.opcode, child)
                self.operands.append(operand)

                #TODO here is an error where comparing symb and var
                if not Instruction._compare_types(operand.type, expected_operands[idx]):
                    exit_with_message("Unexpected type",ErrorCodes.ERR_TYPE)
        except IndexError:
            exit_with_message(f"Too many arguments for {self.opcode}", ErrorCodes.ERR_TYPE)

    @staticmethod
    def _has_opcode(element: XML.Element):
        opcode = element.get('opcode')
        if opcode is None:
            return False
        return opcode in dict.keys(INSTRUCTION_DICT)

    @staticmethod
    def _has_order(element: XML.Element):
        opcode = element.get('order')
        if opcode is None:
            return False
        if int(opcode) <= 0:
            return False
        return True

    @staticmethod
    def is_instruction(element: XML.Element):
        if element.tag != 'instruction':
            return False
        if not Instruction._has_opcode(element) or not Instruction._has_order(element):
            return False
        return True
    
    @staticmethod
    def _compare_types(t1: str, t2: str):
        if t1 == 'var':
            return t1 == t2 or t2 == 'symb'
        else:
            return t1 == t2

    def __repr__(self) :
        return f"(order={self.order},instruction={self.opcode},operands={self.operands})"


class InstructionManager():
    def __init__(self):
        self._instructions = []

    def insert(self, instruction: Instruction) :
        self._instructions.append(instruction)

    def get_instructions(self):
        return sorted(self._instructions, key=lambda i: i.order)


class Frame():
    def __init__(self):
        self._data = {}
    
    def get_var(self,var_name):
        return self._data.get(var_name)
    
    def set_var (self, var: Var):
        if self.get_var(var.name) is not None:
            exit_with_message(f"Variable {var.name} is already defined at {var.scope}",
                              ErrorCodes.ERR_SEMANTICS)

        self._data[var.name] = var

    def __repr__(self):
        return repr(self._data)


#FIXME
class FrameManager():
    def __init__(self) :
        self._gframe = Frame()
        self._lframe = []
        self._tframe = None
    
    def set_var(self, var:Var):
        if var.scope == FrameTypes.GF:
            self._gframe.set_var(var)
        elif var.scope == FrameTypes.TF:
            if self._tframe is None:
                exit_with_message(f"TF is not defined",
                                  ErrorCodes.ERR_STACK)
            self._tframe.set_var(var)
        elif var.scope == FrameTypes.LF:
            pass
        else:
            exit_with_message(f"Something went wrong. Checkout set_var() in FrameManager",
                              ErrorCodes.ERR_INTERNAL)
    
    def get_var(self, var: Var):
        _var = self._tframe.get_var(var.name)

        if var.scope == FrameTypes.TF:
            _var = self._tframe.get_var(var.name)
        elif var.scope == FrameTypes.LF:
            _var = self._lframe[-1].get_var(var.name)
        elif var.scope == FrameTypes.GF:
            _var = self._gframe.get_var(var.name)
        
        if _var is None:
            exit_with_message(f"Variable '{var.name}' is not defined at {var.scope}",
                              ErrorCodes.ERR_MISS)
        else:
            return _var

    def create_frame(self): 
        self._tframe = Frame()

    def push_frame(self):
        if self._tframe is None:
            exit_with_message(f"Unable to push undefined TF to LF",
                              ErrorCodes.ERR_STACK)
        self._lframe.append(self._tframe)
        self._tframe = None

    def pop_frame(self):
        if len(self._lframe) == 0:
            exit_with_message(f"Unable to pop LF when it is empty",
                              ErrorCodes.ERR_STACK)
        self._tframe = self._lframe.pop()

    def __repr__(self):
        return f"GF: {self._gframe}\nTF: {self._tframe}\nLF: {self._lframe}"
    

def read_lines(filename=None):
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

def main():

    is_help = False
    source = None
    input = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["help", "source=", "input="])
    except:
        exit_with_message(f"Unknown options. Use --help.",
                          ErrorCodes.ERR_PARAMETER)

    for opt, arg in opts:
        if opt == '--help':
            is_help = True
        elif opt == '--source':
            source = arg
        elif opt == '--input':
            input = arg
        else:
            exit_with_message(f"Unknown option {opt}",
                              ErrorCodes.ERR_PARAMETER)

    if is_help:
        exit_with_message(
        """
        \bUsage: python interpret.py [OPTIONS]

        \bInterpret an XML file.

        \bOptions:
        \b--help           Show this message and exit.
        \b--source=PATH    The source of the XML file.
        \b--input=PATH     The input for XML source file.
        """, ErrorCodes.SUCCESS)


    if source is None:
        source = sys.stdin

    input = read_lines(input)

    try:
        tree = XML.parse(source)
    except FileNotFoundError:
        exit_with_message("Unknown path to a file. File not found",
                          ErrorCodes.ERR_PARAMETER)
    except:
        exit_with_message("Invalid XML format",
                          ErrorCodes.ERR_XML_FORMAT)

    root = tree.getroot()

    # TODO validate <?xml version="1.0" encoding="UTF-8"?>
    if root.tag != "program":
        exit_with_message("Expected <program> element",
                          ErrorCodes.ERR_XML_STRUCT)

    inst_manager = InstructionManager()
    for instruction_element in root:
        if not Instruction.is_instruction(instruction_element):
            exit_with_message("Expected <instruction> element with \"opcode\" and \"order\"",
                              ErrorCodes.ERR_XML_STRUCT)
        inst_manager.insert(Instruction(instruction_element))

    frame_manager = FrameManager()
    
    #REVIEW at this point instructions are validated
    for instruction in inst_manager.get_instructions():
        print(instruction)
        if instruction.opcode == "CREATEFRAME":
            frame_manager.create_frame()
        elif instruction.opcode == "PUSHFRAME":
            frame_manager.push_frame()
        elif instruction.opcode == "POPFRAME":
            frame_manager.pop_frame()
        elif instruction.opcode == "DEFVAR":
            frame_manager.set_var(instruction.operands[0].target)
        elif instruction.opcode == "WRITE":
            op = instruction.operands[0].target
            if isinstance(op, Var):
                var = frame_manager.get_var(op)
                print(var.value)
            elif isinstance(op, Symb):
                print(var.value)
            else:
                exit_with_message(f"Something went wrong. Checkout main(). Instruction WRITE",
                                  ErrorCodes.ERR_INTERNAL)
        elif instruction.opcode == "READ":
            target = instruction.operands[0].target
            type = instruction.operands[1].target
            try:
                var = frame_manager.get_var(target)
                var.set_value(next(input), type)
            except StopIteration:
                var.set_value(None, type)




    print(frame_manager)


if __name__ == "__main__":
    main()
