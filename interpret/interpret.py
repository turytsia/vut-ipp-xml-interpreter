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
    ERR_SEMANTICS = 52,
    ERR_TYPE = 53,
    ERR_UNDEFINED = 54,
    ERR_STACK = 55,
    ERR_MISS = 56,
    ERR_VALUE = 57,
    ERR_STRING = 58,
    ERR_INTERNAL = 99


def exit_with_message(message: str, error_code: ErrorCodes):
    if error_code == ErrorCodes.SUCCESS:
        print(message, file=sys.stdout)
        sys.exit(0)
    else:
        print(message, file=sys.stderr)
        sys.exit(error_code.value)


def get_options(*args):
    is_help = False
    source = None
    input = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", args)
    except:
        print("Invalid options.", file=sys.stderr)

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

    return is_help, source, input


class Operand():
    # TODO argument order
    def __init__(self, inst_name: str, operand: XML.Element) -> None:
        if not Operand._is_operand(operand):
            exit_with_message(f"Invalid operands in {inst_name}",
                              ErrorCodes.ERR_XML_STRUCT)
        self.type = Operand._get_operand_type(operand)
        print(self.type)

    @staticmethod
    def _get_operand_type(operand: XML.Element) -> str:
        if not Operand._is_operand(operand):
            exit_with_message("Unknown argument",
                              ErrorCodes.ERR_XML_STRUCT)
        if Operand._is_var(operand):
            return "var"
        elif Operand._is_symb(operand):
            return "symb"
        elif Operand._is_type(operand):
            return "type"
        elif Operand._is_label(operand):
            return "label"
        else:
            print(operand.text)
            exit_with_message("Unexpected type",
                              ErrorCodes.ERR_TYPE)

    @staticmethod
    def _is_operand(operand: XML.Element) -> bool:
        if not re.search(r"^arg[1-3]$", operand.tag):
            return False
        if not operand.get("type"):
            return False
        return True

    @staticmethod
    def _is_var(operand: XML.Element) -> bool:
        if operand.get("type") != "var":
            return False
        if not re.search(r"^(GF|LF|TF)@[a-zA-Z_\-$&%*!?][\w\-$&%*!?]*$", operand.text):
            return False
        return True

    @staticmethod
    def _is_symb(operand: XML.Element) -> bool:
        if not re.search(r"^(int|bool|string|nil)", operand.get("type")):
            return Operand._is_var(operand)
        return True

    @staticmethod
    def _is_type(operand: XML.Element) -> bool:
        if operand.get("type") != "type":
            return False
        if not re.search(r"^(int|bool|string|nil)$", operand.text):
            return False
        return True

    @staticmethod
    def _is_label(operand: XML.Element) -> bool:
        if operand.get("type") != "label":
            return False
        if not re.search(r"^[a-zA-Z_\-$&%*!?][\w\-$&%*!?]*$", operand.text):
            return False
        return True

    def __repr__(self) -> str:
        return f"(\"{self.type}\" : value)"


class Instruction():
    def __init__(self, element: XML.Element) -> None:
        self.opcode = element.get('opcode')
        self.order = element.get('order')
        self.operands = []

        # REVIEW this could check number of args
        expected_operands = INSTRUCTION_DICT[self.opcode].split(" ")

        for idx, child in enumerate(element):
            operand = Operand(self.opcode, child)
            self.operands.append(operand)

            #TODO here is an error where comparing symb and var
            if operand.type != expected_operands[idx]:
                exit_with_message("Unexpected type",ErrorCodes.ERR_TYPE)

    @staticmethod
    def _has_opcode(element: XML.Element) -> bool:
        opcode = element.get('opcode')
        if opcode is None:
            return False
        return opcode in dict.keys(INSTRUCTION_DICT)

    @staticmethod
    def _has_order(element: XML.Element) -> bool:
        opcode = element.get('order')
        if opcode is None:
            return False
        if int(opcode) <= 0:
            return False
        return True

    @staticmethod
    def is_instruction(element: XML.Element) -> bool:
        if element.tag != 'instruction':
            return False
        if not Instruction._has_opcode(element) or not Instruction._has_order(element):
            return False
        return True

    def __repr__(self) -> str:
        return f"(order={self.order},instruction={self.opcode},operands={self.operands})\n"


class InstructionManager():
    def __init__(self):
        self._instructions = []

    def insert(self, instruction: Instruction) -> None:
        self._instructions.append(instruction)

    def get_instructions(self):
        return self._instructions


def main():

    is_help, source, input = get_options("help", "source=", "input=")

    if is_help:
        exit_with_message("Help info...", ErrorCodes.SUCCESS)

    if source is None and input is None:
        exit_with_message("You must set --source or --input file",
                          ErrorCodes.ERR_PARAMETER)
    # TODO fix this
    if source is None:
        source = sys.stdin
    if input is None:
        input = sys.stdin

    try:
        tree = XML.parse(source)
    except FileNotFoundError:
        exit_with_message("You must define --source or --input file",
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
    for child_element in root:
        if not Instruction.is_instruction(child_element):
            exit_with_message("Expected <instruction> element with \"opcode\" and \"order\"",
                              ErrorCodes.ERR_XML_STRUCT)
        inst_manager.insert(Instruction(child_element))

    print(inst_manager.get_instructions())


if __name__ == "__main__":
    main()
