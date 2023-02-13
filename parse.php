<?php
/*
    .IPPcode23 analyzer
    author: Turytsia Oleksandr (xturyt00)
*/

ini_set('display_errors', 'stderr');

enum OperandTypes: string
{
    case VAR = "var";
    case SYMB = "symb";
    case TYPE = "type";
    case LABEL = "label";
}

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

enum OptionTypes : string {
    case LOC = "loc";
    case COMMENTS = "comments";
    case LABELS = "labels";
    case JUMPS = "jumps";
    case FWJUMPS = "fwjumps";
    case BACKJUMPS = "backjumps";
    case FREQUENT = "frequent";
    case PRINT = "print";
    case EOLS = "eols";
}

class StatsEntity {
    public function __construct(array $options)
    {
        
    }
}

class Stats {
    
    static private $order = 1;

    protected function increase_order(){
        self::$order++;
    }

    protected function get_order(){
        return self::$order;
    }

}

class ErrorHandler
{
    static function exit_with_error(ErrorCodes $err_code, string $message)
    {
        fwrite(STDERR, "\e[31m[" . $err_code->name . "]\e[0m " . $message . "(" . $err_code->value . ")" . " \n");
        exit($err_code->value);
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

class InstructionRule {
    private array $operands;
    public function __construct(...$operand_types)
    {
        $this->operands = [];
        foreach($operand_types as $type){
            array_push($this->operands, $type);
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
    "move" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB),
    "createframe" => new InstructionRule(),
    "pushframe" => new InstructionRule(),
    "popframe" => new InstructionRule(),
    "defvar" => new InstructionRule(OperandTypes::VAR),
    "call" => new InstructionRule(OperandTypes::LABEL),
    "return" => new InstructionRule(),

    "pushs" => new InstructionRule(OperandTypes::SYMB),
    "pops" => new InstructionRule(OperandTypes::VAR),
    "add" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB, OperandTypes::SYMB),
    "sub" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB, OperandTypes::SYMB),
    "mul" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB, OperandTypes::SYMB),
    "idiv" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB, OperandTypes::SYMB),
    "lt" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB, OperandTypes::SYMB),
    "gt" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB, OperandTypes::SYMB),
    "eq" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB, OperandTypes::SYMB),
    "and" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB, OperandTypes::SYMB),
    "or" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB, OperandTypes::SYMB),
    "not" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB),
    "int2char" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB),
    "stri2int" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB, OperandTypes::SYMB),

    "read" => new InstructionRule(OperandTypes::VAR, OperandTypes::TYPE),
    "write" => new InstructionRule(OperandTypes::SYMB),

    "concat" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB, OperandTypes::SYMB),
    "strlen" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB),
    "getchar" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB, OperandTypes::SYMB),
    "setchar" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB, OperandTypes::SYMB),

    "type" => new InstructionRule(OperandTypes::VAR, OperandTypes::SYMB),

    "label" => new InstructionRule(OperandTypes::LABEL),
    "jump" => new InstructionRule(OperandTypes::LABEL),
    "jumpifeq" => new InstructionRule(OperandTypes::LABEL,OperandTypes::SYMB, OperandTypes::SYMB),
    "jumpifneq" => new InstructionRule(OperandTypes::LABEL, OperandTypes::SYMB, OperandTypes::SYMB),
    "exit" => new InstructionRule(OperandTypes::SYMB),

    "dprint" => new InstructionRule(OperandTypes::SYMB),
    "break" => new InstructionRule(),
];

class Formatter {
    protected function format_line($line)
    {
        if (gettype($line) !== "string") 
            return false;

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

class InputReader extends Formatter
{
    private $input;
    public function __construct()
    {
        $this->input = [];
    }

    public function get_input()
    {
        while (($line = $this->format_line(fgets(STDIN))) !== false) {
            if ($line === NULL) continue;

            array_push($this->input, $line);
        }

        return $this->input;
    }
}

class Operand
{
    public $type;
    public $value;
    public function __construct(string $operand, OperandTypes $type)
    {
        switch($type){
            case OperandTypes::SYMB:
                if (!Validators::verify_var($operand)) {
                    [$this->type, $this->value] = explode("@", $operand);
                    break;
                }
            case OperandTypes::VAR:
            case OperandTypes::TYPE:
            case OperandTypes::LABEL:
                $this->type = $type->value;
                $this->value = $operand;
        }
    }
}

class Instruction extends Stats
{
    private $name;
    private $order;
    private $operands;

    public function __construct($line)
    {
        
        $this->name = strtolower(array_shift($line));
        $this->operands = [];

        if (!isset(INSTRUCTION_RULES[$this->name]))
            ErrorHandler::exit_with_error(ErrorCodes::ERR_SRC_CODE, "instruction does not exist");

        $instruction_rule = INSTRUCTION_RULES[$this->name];

        //check number of arguments
        if (count($line) !== count($instruction_rule->get_operands()))
            ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Invalid number of operands");

        foreach ($instruction_rule->get_operands() as $key => $operand) {
            switch ($operand) {
                case OperandTypes::VAR:
                    if (Validators::verify_var($line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Expected variable");
                case OperandTypes::SYMB:
                    if (Validators::verify_symb($line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Expected constant");
                case OperandTypes::TYPE:
                    if (Validators::verify_type($line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Expected type");
                case OperandTypes::LABEL:
                    if (Validators::verify_label($line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Expected label");
                default:
                    continue 2;
            }
            array_push($this->operands, new Operand($line[$key], $operand));
        }
        $this->order = parent::get_order();
        parent::increase_order();
    }

    public function get_name()
    {
        return strtoupper($this->name);
    }

    public function get_operands()
    {
        return $this->operands;
    }

    public function get_order(){
        return $this->order;
    }
}

class InputAnalyzer
{
    private $input;
    private $instructions;

    public function __construct($input)
    {
        $this->input = $input;
        $this->instructions = [];
    }

    public function get_instructions(){
        if (!Validators::verify_header($this->input[0]))
            ErrorHandler::exit_with_error(ErrorCodes::ERR_HEADER, "invalid header");
        
        array_shift($this->input);

        foreach($this->input as $line){
            array_push($this->instructions, new Instruction(preg_split("/\s+/", $line)));
        }

        return $this->instructions;
    }


}

class XMLGenerator
{
    protected $output;
    protected $program;

    public function __construct()
    {
        $this->output = new DOMDocument("1.0", "UTF-8");
        $this->output->formatOutput = true;

        $this->program = $this->output->createElement("program");
        $this->program->setAttribute("language", "IPPcode23");
    }

    protected function generate_instruction(Instruction $instruction)
    {
        $instruction_template = $this->output->createElement("instruction");
        $instruction_template->setAttribute("order", $instruction->get_order());
        $instruction_template->setAttribute("opcode", $instruction->get_name());

        foreach ($instruction->get_operands() as $key => $operand) {
            $operand_template = $this->output->createElement("arg" . ($key + 1));
            $operand_template->setAttribute("type", strtolower($operand->type));
            $operand_template->nodeValue = $operand->value;
            $instruction_template->appendChild($operand_template);
        }
        $this->program->appendChild($instruction_template);
    }
}

class OutputGenerator extends XMLGenerator
{
    private $instructions;
    public function __construct($instructions)
    {
        parent::__construct();
        $this->instructions = $instructions;
    }

    public function generate()
    {
        foreach ($this->instructions as $instruction) {
            $this->generate_instruction($instruction);
        }

        $this->output->appendChild($this->program);
        
        return $this->output->saveXML();
    }
}

// TODO rewrite parameters handler into OOP. Create ENUM tuple with flags

/* Main here */


$shortopts = "h";

$longopts = [
    "help",
    "comments",
    "labels",
    "jumps",
    "fwjumps",
    "backjumps",
    "frequent",
    "print:",
    "stats:",
    "eols",


];

$options = getopt($shortopts, $longopts);

print_r($options);

if (isset($options["help"])) {
    if (count($options) !== 1)
        ErrorHandler::exit_with_error(ErrorCodes::ERR_PARAMETER, "You can't combine other flags with' \"--help\"");

    echo "
   \rWelcome to IPPCode23 parser!\n
   \rScript takes IPPCode23 as input, creates XML representation (encoding UTF-8)\nand sends it to output.

   \rUsage: php parser.php [options] <[file]

   \rDefault options:
   \r  --help or -h\tprints help info

   \rIn case if you want to display IFJCode23 statistics, you must\nset output file for statistics --stats=<file>.

   \rStats options:
   \r  --loc\t\t\toutputs number of lines with instructions (no header, blank lines or comment lines)
   \r  --comments\t\toutputs number of lines with comments
   \r  --labels\t\toutputs number of labels
   \r  --jumps\t\toutputs number of jumps
   \r  --fwjumps\t\toutputs number of forward jumps
   \r  --backjumps\t\toutputs number of back jumps
   \r  --frequent\t\toutputs instructions by their frequency
   \r  --print=<string>\toutputs <string> to stats
   \r  --eols\t\tadds breaks to stats
   \r\n";
    exit(ErrorCodes::EXIT_SUCCESS->value);
}

$reader = new InputReader();
$input = $reader->get_input();

$inputAnalyzer = new InputAnalyzer($input);
$instructions = $inputAnalyzer->get_instructions();

$output_generator = new OutputGenerator($instructions);
$output = $output_generator->generate();

echo $output;

exit(0);
