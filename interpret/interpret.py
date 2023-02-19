import getopt
import sys
from enum import Enum
import xml.etree.ElementTree as XML
import re

# TODO rewrite it.
class InstructionTypes(Enum):
    MOVE = "var symb"
    CREATEFRAME = ""
    PUSHFRAME = ""
    POPFRAME = ""
    DEFVAR = "var"
    CALL = "label"
    RETURN = ""

    PUSHS = "symb"
    POPS = "var"
    
    ADD = "var symb symb"
    SUB = "var symb symb"
    MUL = "var symb symb"
    IDIV = "var symb symb"
    LT = "var symb symb"
    GT = "var symb symb"
    EQ = "var symb symb"
    AND = "var symb symb"
    OR = "var symb symb"
    NOT = "var symb"

    INT2CHAR = "var symb"
    STRI2INT = "var symb symb"
    READ = "var type"
    WRITE = "symb"

    CONCAT = "var symb symb"
    STRLEN = "var symb"
    GETCHAR = "var symb symb"
    SETCHAR = "var symb symb"
    
    TYPE = "var symb"

    LABEL = "label"
    JUMP = "label"
    JUMPIFEQ = "label symb symb"
    JUMPIFNEQ = "label symb symb"
    EXIT = "symb"

    DPRINT = "symb"
    BREAK = ""

class ErrorCodes(Enum):
    SUCCESS = 0
    ERR_PARAMETER = 10
    ERR_INPUT = 11
    ERR_OUTPUT = 12
    ERR_XML_FORMAT = 31
    ERR_XML_STRUCT = 32
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
            exit_with_message(f"Undefined option {opt}",
                          ErrorCodes.ERR_PARAMETER)

    return is_help, source, input


class Instruction():

    def __init__(self,element: XML.Element) -> None:
        self.opcode = ""

    @staticmethod
    def _has_opcode(element: XML.Element) -> bool:
        opcode = element.get('opcode')
        if opcode is None:
            return False
        print([opcode.name for opcode in InstructionTypes])
        return opcode in [opcode.name for opcode in InstructionTypes]
    
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
        if not Instruction._has_opcode(element) or not Instruction._has_order(element) is None:
            return False
        return True
    
class InstructionManager():
    def __init__(self):
        self._instructions = []
    def insert(self, instruction:Instruction) -> None:
        self._instructions.append(instruction)
        


def main():

    is_help, source, input = get_options("help", "source=", "input=")

    if is_help:
        exit_with_message("Help info...", ErrorCodes.SUCCESS)

    if source is None and input is None:
        exit_with_message("You must set --source or --input file",
                          ErrorCodes.ERR_PARAMETER)

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


if __name__ == "__main__":
    main()
