<?php

/** 
 *   .IPPcode23 analyzer
 *   @author Turytsia Oleksandr (xturyt00)
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
    case ERR_PARAMETER = 10;
    case ERR_INPUT = 11; 
    case ERR_OUTPUT = 12;
    case ERR_HEADER = 21;
    case ERR_SRC_CODE = 22; 
    case ERR_SYNTAX = 23; 
    case ERR_INTERNAL = 99; 
    case EXIT_SUCCESS = 0; 
}

/**
 * ErrorHandler
 */
class ErrorHandler
{

    /**
     * exit_with_error - exits program with given error code and message
     *
     * @param  ErrorCodes $err_code
     * @param  string $message
     * @return void
     */
    static function exit_with_error(ErrorCodes $err_code, string $message)
    {
        fwrite(STDERR, "\e[31m[" . $err_code->name . "]\e[0m " . $message . "(" . $err_code->value . ")" . " \n");
        exit($err_code->value);
    }
}

/**
 * Validators - collection for validators
 */
class Validators
{
    /**
     * is_header - checks wether $line is a header
     *
     * @param  string $line
     * @return bool
     */
    public static function is_header(string $line)
    {
        return isset($line) && strtolower($line) === ".ippcode23";
    }

    /**
     * is_var - checks wether $var is a variable
     *
     * @param  string $var
     * @return bool
     */
    public static function is_var(string $var)
    {
        if (strpos($var, "@") === false) return false;
        [$frame, $name] = explode("@", $var);

        if (!in_array($frame, ["GF", "TF", "LF"])) return false;
        if (!self::is_label($name)) return false;

        return true;
    }

    /**
     * is_symb - checks wether $symb is a symbol/variable
     *
     * @param  string $symb
     * @return bool
     */
    public static function is_symb(string $symb)
    {
        if (strpos($symb, "@") === false) return false;
        [$type, $literal] = explode("@", $symb);

        if (!self::is_type($type)) return self::is_var($symb);

        switch ($type) {
            case "int":
                return preg_match("/^(([-+]?\d+)|(0[oO]?[0-7]+)|(0[xX][0-9a-fA-F]+))$/", $literal);
            case "bool":
                return preg_match("/^(true|false)$/", $literal);
            case "nil":
                return preg_match("/^nil$/", $literal);
            case "string":
                return !preg_match("/^.*(\\\\(?!\d\d\d)).*$/u", $literal);
        }
        return true;
    }


    /**
     * is_type - checks wether $type is a type
     *
     * @param  mixed $type
     * @return bool
     */
    public static function is_type(string $type)
    {
        return preg_match("/^(int|bool|string|nil)$/", $type);
    }


    /**
     * is_label - checks wether $label is a label
     *
     * @param  mixed $label
     * @return bool
     */
    public static function is_label(string $label)
    {
        return preg_match("/^[a-zA-Z_\-$&%*!?][\w\-$&%*!?]*$/", $label);
    }
}

/**
 * InstructionRule is a template for instructions
 */
class InstructionRule
{
    private array $operands;
    public function __construct(...$operand_types)
    {
        $this->operands = [];
        foreach ($operand_types as $type) {
            array_push($this->operands, $type);
        }
    }

    /**
     * get_operands - getter for $operands
     *
     * @return array
     */
    public function get_operands()
    {
        return $this->operands;
    }
    
    /**
     * has_no_operands - returns true if instruction has operands, otherwise - false
     *
     * @return bool
     */
    public function has_no_operands()
    {
        return !!count($this->operands);
    }
}

//Instruction templates
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
    "jumpifeq" => new InstructionRule(OperandTypes::LABEL, OperandTypes::SYMB, OperandTypes::SYMB),
    "jumpifneq" => new InstructionRule(OperandTypes::LABEL, OperandTypes::SYMB, OperandTypes::SYMB),
    "exit" => new InstructionRule(OperandTypes::SYMB),

    "dprint" => new InstructionRule(OperandTypes::SYMB),
    "break" => new InstructionRule(),
];

/**
 * Formatter - provides any class with functions to work with string
 */
trait Formatter
{
    /**
     * format_line - is a pipe of remove_ending, remove_comments, remove_empty. Returns false if $line is not a string
     *
     * @param  mixed $line
     * @return bool/string
     */
    protected function format_line($line)
    {
        if (gettype($line) !== "string")
            return false;

        $line = $this->remove_ending($line);
        $line = $this->remove_comments($line);
        $line = $this->remove_empty($line);

        return $line;
    }

    /**
     * remove_ending - removes \n at the end of the $line
     *
     * @param  string $line
     * @return string
     */
    private function remove_ending(string $line)
    {
        return str_replace("\n", '', $line);
    }

    /**
     * remove_comments - removes comments from the code (exm. #blabla will be removed)
     *
     * @param  string $line
     * @return string
     */
    private function remove_comments(string $line)
    {
        if (($cut_line = strpos($line, "#")) === false)
            return trim($line);

        return trim(substr($line, 0, $cut_line));
    }

    /**
     * remove_empty - returns null if $line is empty
     *
     * @param  string $line
     * @return string/null
     */
    private function remove_empty($line)
    {
        if (!preg_match("/^\S+/", $line, $match))
            return NULL;

        return $line;
    }
}

/**
 * InputReader - class to read from STDIN
 */
class InputReader
{
    use Formatter;
    private $input;
    public function __construct()
    {
        $this->input = [];
    }

    /**
     * get_input - returns array of formatted lines of code 
     *
     * @return array
     */
    public function get_input()
    {
        while (($line = $this->format_line(fgets(STDIN))) !== false) {
            if ($line === NULL) continue;

            array_push($this->input, $line);
        }

        return $this->input;
    }
}


/**
 * Operand - class to group all the information about given operand in one place
 */
class Operand
{
    public $type;
    public $value;
    public function __construct(string $operand, OperandTypes $type) //It will set needed information for generator of code 
    {
        switch ($type) {
            case OperandTypes::SYMB:
                if (Validators::is_var($operand)) {
                    [$this->type, $this->value] = ["var", $operand];
                }else if(Validators::is_symb($operand)){
                    [$this->type, $this->value] = explode("@", $operand);
                }else{
                    
                }
                break;
            case OperandTypes::VAR:
            case OperandTypes::TYPE:
            case OperandTypes::LABEL:
                $this->type = $type->value;
                $this->value = $operand;
        }
    }
}

/**
 * Instruction - class to group all the information about given instruction in one place
 */
class Instruction
{
    private $name;
    private $order;
    private $operands;

    private static $general_order = 1;
    
    /**
     * __construct - creates and validates instruction for code generation
     *
     * @param  array $destructured_line
     * @return void
     */
    public function __construct(array $destructured_line)
    {
        $this->name = strtolower(array_shift($destructured_line));
        $this->operands = [];

        if (!isset(INSTRUCTION_RULES[$this->name]))
            ErrorHandler::exit_with_error(ErrorCodes::ERR_SRC_CODE, "instruction does not exist");

        $instruction_rule = INSTRUCTION_RULES[$this->name];

        if (count($destructured_line) !== count($instruction_rule->get_operands()))
            ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Invalid number of operands");

        foreach ($instruction_rule->get_operands() as $key => $operand) {
            switch ($operand) {
                case OperandTypes::VAR:
                    if (Validators::is_var($destructured_line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Invalid variable");
                case OperandTypes::SYMB:
                    if (Validators::is_symb($destructured_line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Invalid constant");
                case OperandTypes::TYPE:
                    if (Validators::is_type($destructured_line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Invalid type");
                case OperandTypes::LABEL:
                    if (Validators::is_label($destructured_line[$key])) break;
                    ErrorHandler::exit_with_error(ErrorCodes::ERR_SYNTAX, "Invalid label");
                default:
                    continue 2;
            }

            array_push($this->operands, new Operand($destructured_line[$key], $operand));
        }

        $this->order = self::$general_order++;
    }
    
    /**
     * get_name - getter for $name
     *
     * @return string
     */
    public function get_name()
    {
        return strtoupper($this->name);
    }

    /**
     * get_name - getter for $operands
     *
     * @return Operand[]
     */
    public function get_operands()
    {
        return $this->operands;
    }

    /**
     * get_name - getter for $order
     *
     * @return int
     */
    public function get_order()
    {
        return $this->order;
    }
}

/**
 * InputAnalyzer - class for code analysis before generating XML
 */
class InputAnalyser
{
    private $input;
    private $instructions;

    public function __construct($input)
    {
        $this->input = $input;
        $this->instructions = [];
    }

    /**
     * get_instructions - validates header and returns validated instances of instructions
     *
     * @return Instruction[]
     */
    public function get_instructions()
    {
        if(count($this->input) == 0)
            ErrorHandler::exit_with_error(ErrorCodes::ERR_HEADER, "invalid header");
        if (!Validators::is_header($this->input[0]))
            ErrorHandler::exit_with_error(ErrorCodes::ERR_HEADER, "invalid header");

        array_shift($this->input);

        foreach ($this->input as $line) {
            array_push($this->instructions, new Instruction(preg_split("/\s+/", $line)));
        }

        return $this->instructions;
    }
}

/**
 * XMLGenerator - configured XML Generator to generate code in a way *instruction by instruction*
 */
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

    /**
     * generate_instruction - generates $instruction as XML
     *
     * @param  Instruction $instruction
     * @return void
     */
    protected function generate_instruction(Instruction $instruction)
    {
        $instruction_template = $this->output->createElement("instruction");
        $instruction_template->setAttribute("order", $instruction->get_order());
        $instruction_template->setAttribute("opcode", $instruction->get_name());

        foreach ($instruction->get_operands() as $key => $operand) {
            $operand_template = $this->output->createElement("arg" . ($key + 1));
            $operand_template->setAttribute("type", strtolower($operand->type));
            $valueNode = $this->output->createTextNode($operand->value);
            $operand_template->appendChild($valueNode);
            $instruction_template->appendChild($operand_template);
        }
        $this->program->appendChild($instruction_template);
    }
}


/**
 * OutputGenerator - extended layer for XML generator that iterates through the instructions, generates them and returns XML
 */
class OutputGenerator extends XMLGenerator
{
    private $instructions;
    public function __construct(array $instructions)
    {
        parent::__construct();
        $this->instructions = $instructions;
    }
    
    /**
     * generate - generates XML code out of valid instructions and returns it
     *
     * @return string
     */
    public function generate()
    {
        foreach ($this->instructions as $instruction) {
            $this->generate_instruction($instruction);
        }

        $this->output->appendChild($this->program);

        return $this->output->saveXML();
    }
}

/* Main here */

$shortopts = "h";

$longopts = [
    "help",
];

$options = getopt($shortopts, $longopts);

if (isset($options["help"])) {
    if (count($options) !== 1)
        ErrorHandler::exit_with_error(ErrorCodes::ERR_PARAMETER, "You can't combine other flags with' \"--help\"");

    echo "
   \rWelcome to IPPCode23 parser!\n
   \rScript takes IPPCode23 as input, creates XML representation (encoding UTF-8)\nand sends it to output.

   \rUsage: php parser.php [options] <[file]

   \rDefault options:
   \r  --help or -h\tprints help info
   \r\n";
    exit(0);
}

$reader = new InputReader();
$input = $reader->get_input();

$inputAnalyser = new InputAnalyser($input);
$instructions = $inputAnalyser->get_instructions();

$output_generator = new OutputGenerator($instructions);
$output = $output_generator->generate();

echo $output;

exit(0);
