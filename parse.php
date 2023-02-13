<?php
/*
    .IPPcode23 analyzer
    author: Turytsia Oleksandr (xturyt00)
*/

ini_set('display_errors', 'stderr');

enum ErrorCodes: int
{
    case ERR_PARAMETER = 10; // chybějící parametr skriptu (je-li třeba) nebo použití zakázané kombinace parametrů
    case ERR_INPUT = 11; //chyba při otevírání vstupních souborů (např. neexistence, nedostatečné oprávnění)
    case ERR_OUTPUT = 12; //chyba při otevření výstupních souborů pro zápis (např. nedostatečné oprávnění, chybapři zápisu);
    case ERR_HEADER = 21; //chybná nebo chybějící hlavička ve zdrojovém kódu zapsaném v IPPcode23;
    case ERR_SRC_CODE = 22; //neznámý nebo chybný operační kód ve zdrojovém kódu zapsaném v IPPcode23;
    case ERR_SYNTAX = 23; //jiná lexikální nebo syntaktická chyba zdrojového kódu zapsaného v IPPcode23
    case ERR_INTERNAL = 99; //interní chyba (neovlivněná vstupními soubory či parametry příkazové řádky; např. chyba alokace paměti).
    case EXIT_SUCCESS = 0; //OK
}

class ErrorHandler
{
    static function exit_with_error(ErrorCodes $err_code, string $message)
    {
        fwrite(STDERR, "\e[31m [" . $err_code->name . "]\e[0m " . $message . "(" . $err_code->value . ")" . " \n");
        exit($err_code->value);
    }
}

enum OperandTypes:string {
    case VAR = "var";
    case SYMB = "symb";
    case TYPE = "type";
    case LABEL = "label";
}

class InstructionRule {
    private array $operands;
    public function __construct(...$operand_types)
    {
        $this->operands = [];
        foreach($operand_types as $type){
            array_push($this->operands, $type->value);
        }
    }

    public function get_operands(){
        return $this->operands;
    }

    public function has_no_operands(){
        return !!count($this->operands);
    }
}

const INSTRUCTION_RULES = [
    "move" => "var symb",
    "createframe" => "",
    "pushframe" => "",
    "popframe" => "",
    "defvar" => "var",
    "call" => "label",
    "return" => "",

    "pushs" => "symb",
    "pops" => "var",
    "add" => "var symb symb",
    "sub" => "var symb symb",
    "mul" => "var symb symb",
    "idiv" => "var symb symb",
    "lt" => "var symb symb",
    "gt" => "var symb symb",
    "eq" => "var symb symb",
    "and" => "var symb symb",
    "or" => "var symb symb",
    "not" => "var symb",
    "int2char" => "var symb",
    "stri2int" => "var symb symb",

    "read" => "var type",
    "write" => "symb",

    "concat" => "var symb symb",
    "strlen" => "var symb",
    "getchar" => "var symb symb",
    "setchar" => "var symb symb",

    "type" => "var symb",

    "label" => "label",
    "jump" => "label",
    "jumpifeq" => "label symb symb",
    "jumpifneq" => "label symb symb",
    "exit" => "symb",

    "dprint" => "symb",
    "break" => "",
];

class ParserUtils {
    static $input = [];
}

class InputReader extends ParserUtils
{

    public function __construct()
    {
        
    }

    public function get_input()
    {
        while (($line = fgets(STDIN)) !== false) {
            if (($line = $this->format_line($line)) === NULL) continue;

            array_push(self::$input, $line);
        }

        return self::$input;
    }

    private function format_line($line)
    {
        $line = $this->remove_ending($line);
        $line = $this->remove_comments($line);
        $line = $this->remove_empty($line);

        return $line;
    }

    private function remove_ending($line)
    {
        return str_replace("\n", '', $line);
    }

    private function remove_comments($line)
    {
        if (($cut_line = strpos($line, "#")) === false)
            return trim($line);

        return trim(substr($line, 0, $cut_line));
    }

    private function remove_empty($line)
    {
        if (!preg_match("/^\S+/", $line, $match))
            return NULL;
        return $line;
    }
}

class Validators
{
    public static function verify_header(string $line)
    {
        return isset($line) && strtolower($line) === ".ippcode23";
    }

    public static function verify_var($var)
    {
        if (strpos($var, "@") === false) return false;
        [$frame, $name] = explode("@", $var);

        if (!in_array($frame, ["GF", "TF", "LF"])) return false;
        if (!self::verify_label($name)) return false;

        return true;
    }

    public static function verify_symb($symb)
    {
        if (strpos($symb, "@") === false) return false;
        [$type, $literal] = explode("@", $symb);

        if (!self::verify_type($type)) return self::verify_var($symb);

        switch ($type) {
            case "int":
                return preg_match("/^[+\-]?\d+$/", $literal);
            case "bool":
                return preg_match("/^(true|false)$/", $literal);
            case "nil":
                return preg_match("/^nil$/", $literal);
            case "string":
                return !preg_match("/^.*\\\\(\d\d\D|\d\D\D|\D\D\D).*$/", $literal) &&
                    !preg_match("/^.*\\\\(\d\d\D|\d\D\D|\D\D\D)?$/", $literal);
        }
        return true;
    }


    public static function verify_type($type)
    {
        return preg_match("/^(int|bool|string|nil)$/", $type, $match);
    }

    public static function verify_label($label)
    {
        return preg_match("/^[a-zA-Z_\-$&%*!?][\w\-$&%*!?]*$/", $label, $match);
    }
}

class Operand
{
    public $type;
    public $value;
    public function __construct(string $operand, string $type)
    {
        if($type === "symb" && !Validators::verify_var($operand)){
            [$this->type, $this->value] = explode("@", $operand);
        }else{
            $this->type = $type;
            $this->value = $operand;
        }
    }
}

class Instruction
{
    private $name;
    private $operands = [];

    static $order = 0;

    public function __construct($line)
    {
        $this->name = strtolower(array_shift($line));

        if (!isset(INSTRUCTION_RULES[$this->name]))
            ErrorHandler::exit_with_error(ErrorCodes::ERR_SRC_CODE, "instruction $line[0] does not exist");


        $rule = explode(" ", INSTRUCTION_RULES[$this->name]);

        if ($rule[0] === "")
            array_pop($rule);
        if (count($line) !== count($rule))
            ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Invalid number of operands");

        foreach ($rule as $key => $operand) {
            switch ($operand) {
                case "var":
                    if (Validators::verify_var($line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Expected variable");
                case "symb":
                    if (Validators::verify_symb($line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Expected constant");
                case "type":
                    if (Validators::verify_type($line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Expected type");
                case "label":
                    if (Validators::verify_label($line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Expected label");
                default:
                    continue 2;
            }
            array_push($this->operands, new Operand($line[$key], $operand));
        }
        self::$order++;
    }

    public function get_name()
    {
        return strtoupper($this->name);
    }

    public function get_operands()
    {
        return $this->operands;
    }
}

class OutputGenerator extends ParserUtils
{
    public function parse()
    {
        if (!Validators::verify_header(self::$input[0]))
            ErrorHandler::exit_with_error(ErrorCodes::ERR_HEADER, "invalid header");

        array_shift(self::$input);

        $generator = new XMLGenerator();

        foreach (self::$input as $line) {
            $generator->generateInstruction(new Instruction(preg_split("/\s+/", $line)));
        }

        echo $generator;
    }
}

class XMLGenerator
{
    private $output;
    private $program;

    public function __construct()
    {
        $this->output = new DOMDocument("1.0", "UTF-8");
        $this->output->formatOutput = true;

        $this->program = $this->output->createElement("program");
        $this->program->setAttribute("language", "IPPcode23");
    }

    public function generateInstruction(Instruction $instruction)
    {
        $instruction_template = $this->output->createElement("instruction");
        $instruction_template->setAttribute("order", Instruction::$order);
        $instruction_template->setAttribute("opcode", $instruction->get_name());

        foreach ($instruction->get_operands() as $key => $operand) {
            $operand_template = $this->output->createElement("arg" . ($key + 1));
            $operand_template->setAttribute("type", strtolower($operand->type));
            $operand_template->nodeValue = $operand->value;
            $instruction_template->appendChild($operand_template);
        }
        $this->program->appendChild($instruction_template);
    }

    public function __toString()
    {
        $this->output->appendChild($this->program);

        return $this->output->saveXML();
    }
}

//TODO Remove tests from git
// TODO rewrite parameters handler into OOP. Create ENUM tuple with flags

/* Main here */
$shortopts = "h";

$longopts = [
    "help"
];

$options = getopt($shortopts, $longopts);

if (isset($options["help"])) {
    if (count($options) !== 1)
        ErrorHandler::exit_with_error(ErrorCodes::ERR_PARAMETER, "You can't combine other flags with' \"--help\"");

    echo "Here should be info...\n";
    exit(ErrorCodes::EXIT_SUCCESS->value);
}

$reader = new InputReader();
$input = $reader->get_input();

$output_generator = new OutputGenerator();
$output_generator->parse($input);
