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
    "MOVE" => "VAR SYMB",
    "CREATEFRAME" => "",
    "PUSHFRAME" => "",
    "POPFRAME" => "",
    "DEFVAR" => "VAR",
    "CALL" => "LABEL",
    "RETURN" => "",

    "PUSHS" => "SYMB",
    "POPS" => "VAR",
    "ADD" => "VAR SYMB SYMB",
    "SUB" => "VAR SYMB SYMB",
    "MUL" => "VAR SYMB SYMB",
    "IDIV" => "VAR SYMB SYMB",
    "LT" => "VAR SYMB SYMB",
    "GT" => "VAR SYMB SYMB",
    "EQ" => "VAR SYMB SYMB",
    "AND" => "VAR SYMB SYMB",
    "OR" => "VAR SYMB SYMB",
    "NOT" => "VAR SYMB SYMB",
    "INT2CHAR" => "VAR SYMB",
    "STRI2INT" => "VAR SYMB SYMB",

    "READ" => "VAR TYPE",
    "WRITE" => "SYMB",

    "CONCAT" => "VAR SYMB SYMB",
    "STRLEN" => "VAR SYMB",
    "GETCHAR" => "VAR SYMB SYMB",
    "SETCHAR" => "VAR SYMB SYMB",

    "TYPE" => "VAR SYMB",

    "LABEL" => "LABEL",
    "JUMP" => "LABEL",
    "JUMPIFEQ" => "LABEL SYMB SYMB",
    "JUNPIFNEQ" => "LABEL SYMB SYMB",
    "EXIT" => "SYMB",

    "DPRINT" => "SYMB",
    "BREAK" => "",
];

// TODO rewrite parameters handler into OOP. Create ENUM tuple with flags
$shortopts = "h";

$longopts = [
    "help"
];

$options = getopt($shortopts, $longopts);

if (isset($options["help"])) {
    if ($argc > 2) ErrorHandler::exit_with_error(ErrorCodes::ERR_PARAMETER, "use just \"--help\"");

    echo "Here should be info...\n";
    exit(ErrorCodes::EXIT_SUCCESS->value);
}

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
                return preg_match("/^-?\d+$/", $literal, $match);
            case "bool":
                return preg_match("/^(true|false)$/", $literal, $match);
            case "nil":
                return preg_match("/^nil$/", $literal, $match);
            case "string":
                return !preg_match("/^.*\\\\(\d\d\D|\d\D|\D]).*$/", $literal, $match);
        }
        return true;
    }


    public static function verify_type($type)
    {
        return preg_match("/(int|bool|string|nil)/", $type, $match);
    }

    public static function verify_label($label)
    {
        return preg_match("/^[a-zA-Z_\-$&%*!?][\w\-$&%*!?]*$/", $label, $match);
    }
}

class Instruction
{
    private $name;
    private $operands = [];

    static $order = 0;

    public function __construct($line)
    {
        if (!isset(INSTRUCTION_RULES[$line[0]]))
            ErrorHandler::exit_with_error(ErrorCodes::ERR_SRC_CODE, "instruction does not exist");
        $rule = INSTRUCTION_RULES[$line[0]];

        $this->name = array_shift($line);

        foreach (explode(" ", $rule) as $key => $operand) {
            switch ($operand) {
                case "VAR":
                    if (Validators::verify_var($line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "var");
                case "SYMB":
                    if (Validators::verify_symb($line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "symb");
                case "TYPE":
                    if (Validators::verify_type($line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "type");
                case "LABEL":
                    if (Validators::verify_label($line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "label");
                default:
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_INTERNAL, "unknown operand type");
            }
            array_push($this->operands, $line[$key]);
        }
        self::$order++;
    }

    public function get_name()
    {
        return $this->name;
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
            $generator->generateInstruction(new Instruction(explode(" ", $line)));
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

        $operands = explode(" ", INSTRUCTION_RULES[$instruction->get_name()]);

        foreach ($instruction->get_operands() as $key => $operand) {
            $operand_template = $this->output->createElement("arg" . ($key + 1));
            $operand_template->setAttribute("type", strtolower($operands[$key]));
            $operand_template->nodeValue = $operand;
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

$reader = new InputReader();
$input = $reader->get_input();

$analyzer = new InputAnalyzer();
$analyzer->analyze($input);
