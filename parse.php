<?php
/*
    .IPPcode23 analyzer
    author: Turytsia Oleksandr (xturyt00)
*/

ini_set('display_errors', 'stderr');

//TODO rewrite descriptions
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

const INSTRUCTION_RULES = [
    "move" => "VAR SYMB",
    "createframe" => "",
    "pushframe" => "",
    "popframe" => "",
    "defvar" => "VAR",
    "call" => "LABEL",
    "return" => "",

    "pushs" => "SYMB",
    "pops" => "VAR",
    "add" => "VAR SYMB SYMB",
    "sub" => "VAR SYMB SYMB",
    "mul" => "VAR SYMB SYMB",
    "idiv" => "VAR SYMB SYMB",
    "lt" => "VAR SYMB SYMB",
    "gt" => "VAR SYMB SYMB",
    "eq" => "VAR SYMB SYMB",
    "and" => "VAR SYMB SYMB",
    "or" => "VAR SYMB SYMB",
    "not" => "VAR SYMB",
    "int2char" => "VAR SYMB",
    "stri2int" => "VAR SYMB SYMB",

    "read" => "VAR TYPE",
    "write" => "SYMB",

    "concat" => "VAR SYMB SYMB",
    "strlen" => "VAR SYMB",
    "getchar" => "VAR SYMB SYMB",
    "setchar" => "VAR SYMB SYMB",

    "type" => "VAR SYMB",

    "label" => "LABEL",
    "jump" => "LABEL",
    "jumpifeq" => "LABEL SYMB SYMB",
    "jumpifneq" => "LABEL SYMB SYMB",
    "exit" => "SYMB",

    "dprint" => "SYMB",
    "break" => "",
];

class InputReader
{
    private $input;

    public function __construct()
    {
        $this->input = [];
    }

    public function get_input()
    {
        while (($line = fgets(STDIN)) !== false) {
            if (($line = $this->format_line($line)) === NULL) continue;

            array_push($this->input, $line);
        }

        return $this->input;
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
    public static function verify_header($line)
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
    public function __construct($operand, $type)
    {
        switch ($type) {
            case "SYMB":
                if (!Validators::verify_var($operand)) {
                    [$this->type, $this->value] = explode("@", $operand);
                    break;
                }
            case "VAR":
                $this->type = "var";
                $this->value = $operand;
                break;
            case "LABEL":
                $this->type = "label";
                $this->value = $operand;
            case "TYPE":
                $this->type = "type";
                $this->value = $operand;
                break;
            default:
                ErrorHandler::exit_with_error(ErrorCodes::ERR_INTERNAL, "undefined operand's type");
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
                case "VAR":
                    if (Validators::verify_var($line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Expected variable");
                case "SYMB":
                    if (Validators::verify_symb($line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Expected constant");
                case "TYPE":
                    if (Validators::verify_type($line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Expected type");
                case "LABEL":
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

class InputAnalyzer
{
    public function analyze(array $input)
    {
        if (!Validators::verify_header($input[0]))
            ErrorHandler::exit_with_error(ErrorCodes::ERR_HEADER, "invalid header");

        array_shift($input);

        $generator = new XMLGenerator();

        foreach ($input as $line) {
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

// TODO rewrite parameters handler into OOP. Create ENUM tuple with flags
$shortopts = "h";

$longopts = [
    "help"
];

$options = getopt($shortopts, $longopts);

if (isset($options["help"])) {
    if ($argc > 2)
        ErrorHandler::exit_with_error(ErrorCodes::ERR_PARAMETER, "You can't combine other flags with' \"--help\"");

    echo "Here should be info...\n";
    exit(ErrorCodes::EXIT_SUCCESS->value);
}

$reader = new InputReader();
$input = $reader->get_input();

$analyzer = new InputAnalyzer();
$analyzer->analyze($input);
