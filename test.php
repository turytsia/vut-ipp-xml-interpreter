<?php

ini_set('display_errors', 'stderr');

function printHelp_EN() {
    echo "test.php\nUsage:\n";
    echo "  --help  - Show this help\n";
    echo "  --directory=[path]  - Look for tests in specified directory\n";
    echo "  --recursive  - Look for test in specified directory and it's subdirectories\n";
    echo "  --parse-script=[file]  - File with a PHP 8.1 script for the analysis of a source code in IPPcode22\n";
    echo "  --int-script=[file]  - File with a Python 3.8 script for the interpreter of XML representation of IPPcode22\n";
    echo "  --parse-only  - Test only parser\n";
    echo "  --int-only  - Test only interpreter\n";
    echo "  --jexampath=[path]  - Path to directory containing jexamxml.jar\n";
    echo "  --noclean  - Don't remove temporary files\n";
}

//$flag_directory = true;
$flag_recursive = false;
$flag_parseScript = false;
$flag_intScript = false;
$flag_parseOnly = false;
$flag_intOnly = false;
$flag_jexampath = false;
$flag_noClean = false;
$flag_directoryPath = ".";
$flag_parseScriptFile = "parse.php";
$flag_intScriptFile = "interpret.py";
$flag_jexampathPath = "/pub/courses/ipp/jexamxml/";


/**
 * Check if flag format is correct
 */
function checkFlag($arg) {
    $flagText = explode("=", $arg, 2);
    if(sizeof($flagText) == 1 || $flagText[1] == "") {
        printHelp_EN();
        fwrite(STDERR, "Incomplete flag: " . $arg . "\n");
        exit(41);
    }
    $fileName = $flagText[1];
    
    if(!file_exists($fileName)) {
        fwrite(STDERR, "$fileName not found");
        exit(41);
    }

    return $fileName;
}

/**
 * Parse command line input flags
 */
function parseFlags($argv) {
    // global variables
    global  $flag_recursive,
            $flag_parseScript,
            $flag_intScript,
            $flag_parseOnly,
            $flag_intOnly,
            $flag_jexampath,
            $flag_noClean,
            $flag_directoryPath,
            $flag_parseScriptFile,
            $flag_intScriptFile,
            $flag_jexampathPath;

    for($i = 1; $i < sizeof($argv); $i++) {
        switch($argv[$i]) {
            case "--help":
                printHelp_EN();
                exit(0);
            case "--recursive":
                $flag_recursive = true;
                continue 2;
            case "--parse-only":
                $flag_parseOnly = true;
                continue 2;
            case "--int-only":
                $flag_intOnly = true;
                continue 2;
            case "--noclean":
                $flag_noClean = true;
                continue 2;
            default:
                break;
        }

        $flagSplit = explode("=", $argv[$i], 2);
        $flagName = $flagSplit[0];

        if($flagName == "--directory") {
            $flag_directoryPath = checkFlag($argv[$i]);
        } else if($flagName == "--parse-script") {
            $flag_parseScript = true;
            $flag_parseScriptFile = checkFlag($argv[$i]);
        } else if($flagName == "--int-script") {
            $flag_intScript = true;
            $flag_intScriptFile = checkFlag($argv[$i]);
        } else if($flagName == "--jexampath") {
            $flag_jexampath = true;
            $flag_jexampathPath = checkFlag($argv[$i]);
            if(!str_ends_with($flag_jexampathPath, "/")) {
                $flag_jexampathPath = $flag_jexampathPath."/";
            }
        } else {
            fwrite(STDERR, "Unknown flag: " . $argv[$i]);
            exit(10);
        }
    }

    // Check incorrect flag combinations and missing files
    if($flag_intOnly) {
        if($flag_parseOnly || $flag_parseScript || $flag_jexampath) {
            fwrite(STDERR, "Incorrect flag combination [--int-only && (--parse-script || --parse-only || --jexampath)]");
            exit(10);
        }
        if(!$flag_intScript && !file_exists($flag_intScriptFile)) {
            fwrite(STDERR, "File interpret.php not found");
            exit(41);
        }
    }
    if($flag_parseOnly) {
        if($flag_intOnly || $flag_intScript) {
            fwrite(STDERR, "Incorrect flag combination [--parse-only && (--int-script || --int-only)]");
            exit(10);
        }

        if(!$flag_parseScript && !file_exists($flag_parseScriptFile)) {
            fwrite(STDERR, "File parse.php not found");
            exit(41);
        }

        if(!file_exists($flag_jexampathPath."jexamxml.jar")) {
            fwrite(STDERR, $flag_jexampathPath."jexamxml.jar not found");
            exit(41);
        }

        if(!file_exists($flag_jexampathPath."options")) {
            fwrite(STDERR, $flag_jexampathPath."options not found");
            exit(41);
        }
    }
    if(!$flag_parseOnly && !$flag_intOnly) {
        if(!$flag_intScript && !file_exists($flag_intScriptFile)) {
            fwrite(STDERR, "File interpret.php not found");
            exit(41);
        }

        if(!$flag_parseScript && !file_exists($flag_parseScriptFile)) {
            fwrite(STDERR, "File parse.php not found");
            exit(41);
        }
    }
}

/**
 * File name, path and extension
 */
class FileName {
    private $path; // Relative path
    private $name; // Path and name
    private $ext;  // Extension

    public function __construct(string $fullName, string $fullPath) {
        $split = explode(".", $fullName);

        $this->path = $fullPath;
        $this->ext = array_pop($split);
        $this->name = implode(".", $split);
    }

    public function getName(): String { return $this->name; }
    public function getExt(): String { return $this->ext; }
    public function getPath(): String { return $this->path; }
    
    // Return file name without file path
    public function getNameNoPath(): String {
        // Linux X Windows file paths (naive hack)
        $split1 = explode("\\", $this->name);
        $split2 = explode("/", $this->name);

        if(count($split1) > count($split2)) {
            // win
            $name = array_pop($split1);
        } else {
            // linux
            $name = array_pop($split2);
        }
        return $name;
    }
}

/**
 * Represents single test file
 */
class TestFile {
    public $srcFile;
    public $inFile;
    public $outFile;
    public $rcFile;

    public function __construct() {
        $this->srcFile = NULL;
        $this->inFile = NULL;
        $this->outFile = NULL;
        $this->rcFile = NULL;
    }
}

/**
 * Wrapper for RecursiveDirectoryIterator
 * finds only src/rc/out/in files 
 */
class RecursiveDirectoryIteratorWrapper {
    private $testFiles;

    private int $current;

    public function __construct() {
        $this->current = 0;
        $this->testFiles = array();

        $this->iterateFiles();
    }

    private function iterateFiles() {
        $rdi = new RecursiveDirectoryIterator($GLOBALS["flag_directoryPath"]);
        $iterators = array();

        array_push($iterators, $rdi);

        while(!empty($iterators)) {
            $it = array_pop($iterators);
            $dirFiles = array();

            while($it->valid()) {
                // Directory
                if($it->hasChildren() && $GLOBALS["flag_recursive"]) {
                    array_push($iterators, $it->getChildren());
                } else {
                    $name = new FileName($it->getRealPath(), $it->getPath());
                    $extension = $name->getExt();

                    if($extension == "src" || $extension == "rc" || $extension == "in" || $extension == "out") {
                        array_push($dirFiles, $name);
                    }
                }
                $it->next();
            }
            $this->addTestFiles($dirFiles);
        }
    }

    private function addTestFiles($dirFiles) {
        $found = array();

        // Go through each file found in directory and add them
        foreach($dirFiles as $file) {
            $extension = $file->getExt();
            $name = $file->getName();

            if(!array_key_exists($name, $found)) {
                $found[$name] = new TestFile();
            }

            if($extension == "src") {
                $found[$name]->srcFile = $file;
            } else if($extension == "in") {
                $found[$name]->inFile = $file;
            } else if($extension == "out") {
                $found[$name]->outFile = $file;
            } else if($extension == "rc") {
                $found[$name]->rcFile = $file;
            }
        }

        // Go through each test and create .in, .out or .rc files as needed
        foreach($found as &$testFile) {
            if($testFile->srcFile == NULL) {
                continue;
            }

            if($testFile->inFile == NULL) {
                $inFileName = $testFile->srcFile->getName().".in";
                $f = fopen($inFileName, "w");
                fclose($f);

                $testFile->inFile = new FileName($inFileName, $testFile->srcFile->getPath());
            }

            if($testFile->outFile == NULL) {
                $outFileName = $testFile->srcFile->getName().".out";
                $f = fopen($outFileName, "w");
                fclose($f);

                $testFile->outFile = new FileName($outFileName, $testFile->srcFile->getPath());
            }

            if($testFile->rcFile == NULL) {
                $rcFileName = $testFile->srcFile->getName().".rc";
                $f = fopen($rcFileName, "w");
                fwrite($f, "0");
                fclose($f);

                $testFile->rcFile = new FileName($rcFileName, $testFile->srcFile->getPath());
            }
            array_push($this->testFiles, $testFile);
        }
    }

    public function next() {
        if($this->current == count($this->testFiles)) {
            return NULL;
        }
        return $this->testFiles[$this->current++];
    }
}

/**
 * Represents single test
 */
class Test {
    public $isOk;
    public $testName;
    public $testPath;
    public $output;
    public $returnCode;

    public $expectedOut;
    public $expectedRc;

    public function __construct($testName, $testPath, $output, $returnCode, $expectedOut, $expectedRc) {
        $this->testName = $testName;
        $this->testPath = $testPath;
        $this->output = $output;
        $this->returnCode = $returnCode;

        $this->expectedOut = $expectedOut;
        $this->expectedRc = $expectedRc;
    }
}

/**
 * Holds all the test results
 */
class TestEnv {
    private $tests;
    private $okTestCount;
    private $failedTestCount;

    public function __construct() {
        $this->tests = array();
        $this->okTestCount = 0;
        $this->failedTestCount = 0;
    }

    public function add($testName, $testPath, $out, $rc, $expectedOut, $expectedRc, $forceResult = NULL) {
        $t = new Test($testName, $testPath, $out, $rc, $expectedOut, $expectedRc);

        if(!array_key_exists($testPath, $this->tests)) {
            $this->tests[$testPath] = array();
        }

        if($forceResult == NULL) {
            // Check output and return codes
            if($out == $expectedOut && strval($rc) == $expectedRc) {
                $t->isOk = True;
                $this->okTestCount++;
            } else {
                $t->isOk = False;
                $this->failedTestCount++;
            }
        } else {
            if($forceResult == True) {
                $t->isOk = True;
                $this->okTestCount++;
            } else {
                $t->isOk = False;
                $this->failedTestCount++;
            }
        }
        array_push($this->tests[$testPath], $t);
    }
    
    // Generate html from the test results
    public function getHtml() {
        $testCount = $this->okTestCount + $this->failedTestCount;

        // Generate html page
        // Beginning of HTML Page
        $html = "<!DOCTYPE html>
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"description\" content=\"Test results\">
    <style>
    th, td { padding-left:10px; padding-right:10px; color:white; }
    h1,h2,h3,h4 { color:white; }
    textarea { background-color: rgb(18, 18, 18); color:white; }
    body { padding-left: 1em; padding-right: 1em; background-color: rgb(18, 18, 18); }
    </style>
</head>

<body>
    <h1 style=\"text-align: center;\">Test result</h1>
    <h2>Tests run: ". $testCount ."</h2>
    <h2>Passed: ". $this->okTestCount ." </h2>
    <h2>Failed: ". $this->failedTestCount ." </h2>
    <hr>
    <h3 style=\"text-align: center; color:red\">Failed tests</h3>";

        // Go through each directory and find failed tests
        foreach ($this->tests as $testPath => $arr) {
            $first = True;
            // Go through each test in a directory
            foreach ($arr as $val) {
                if($val->isOk) {
                    continue;
                }
                // Only add new table, when a failed test exists
                if($first) {
                    $first = False;
                    $html = $html."<hr><h4>".$testPath."</h4>".
                    "<table>".
                    "<tr>".
                    "<th>Test name</th>".
                    "<th>Return code</th>".
                    "<th>Expected return code</th>".
                    "<th>Output</th>".
                    "<th>Expected output</th>".
                    "</tr>";
                }

                $html = $html.
                "\n<tr>".
                "<td>".$val->testName."</td>".
                "<td>".$val->returnCode."</td>".
                "<td>".$val->expectedRc."</td>".
                "<td><textarea readonly rows=5 cols=50>".$val->output."</textarea></td>".
                "<td><textarea readonly rows=5 cols=50>".$val->expectedOut."</textarea></td>".
                "</tr>\n";
            }
            if(!$first) {
                $html = $html."\n</table>\n";
            }
        }

        $html = $html."<hr><h3 style=\"text-align: center; color:green\">Passed tests</h3>";

        // Go through each directory and find passed tests
        foreach ($this->tests as $testPath => $arr) {
            $first = True;
            // Go through each test in a directory
            foreach ($arr as $val) {
                if(!$val->isOk) {
                    continue;
                }
                // Only add new table, when a successful test exists
                if($first) {
                    $first = False;
                    $html = $html."<hr><h4>".$testPath."</h4><table>".
                    "<tr>".
                    "<th>Test name</th>".
                    "<th>Return code</th>".
                    "<th>Output</th>".
                    "</tr>";
                }

                $html = $html.
                "\n<tr>".
                "<td>".$val->testName."</td>".
                "<td>".$val->returnCode."</td>".
                "<td><textarea readonly rows=5 cols=50>".$val->expectedOut."</textarea></td>".
                "</tr>\n";
            }
            if(!$first) {
                $html = $html."\n</table>\n";
            }
        }

        return $html."</body></html>";
    }
}

/**
 * Read a file and return its contents
 */
function getFileContent(string $name) {
    $size = filesize($name);
    if($size == 0) {
        return NULL;
    }
    $f = fopen($name, "r");
    $out = fread($f, $size);
    fclose($f);
    return $out;
}

/**
 * Invoke diff and return true, if the 2 files have the same content
 */
function diff2files(string $fileName1, string $fileName2) {
    // Setup diff
    $diffOutput = NULL;
    $diffRc = NULL;
    if (strtoupper(substr(PHP_OS, 0, 3)) === 'WIN') {
        $diffCmd = "FC ".$fileName1." ".$fileName2; // Windows "diff"
    } else {
        $diffCmd = "diff ".$fileName1." ".$fileName2; // diff
    }

    exec($diffCmd, $diffOutput, $diffRc);

    return ($diffRc == 0);
}

// Parse command line arguments
parseFlags($argv);

// Init directory iterator
$rdi = new RecursiveDirectoryIteratorWrapper();
$file = $rdi->next();

$testEnv = new TestEnv();
$filesToRemove = array();

// Go through each testfile
while($file != NULL) {
    if($flag_intOnly) {
        // Setup
        $output = NULL;
        $rc = NULL;
        $srcFile = $file->srcFile->getName();
        $outputFile = $srcFile."_tempOut.temp";
        
        $cmd = "python3 " . $flag_intScriptFile . " --source=" . $srcFile . ".src --input="
                . $file->inFile->getName() . ".in";

        // Execute interpreter
        exec($cmd, $output, $rc);
        $output = implode("\n", $output);

        // Write it to the temporary file
        $f = fopen($outputFile, "w");
        fwrite($f, $output);
        fclose($f);

        // Get expected output and return code
        $expectedOut = getFileContent($file->outFile->getName().".out");
        $expectedRc = getFileContent($file->rcFile->getName().".rc");

        // Add the test
        $testName = $file->srcFile->getNameNoPath();
        $testPath = $file->srcFile->getPath();
        $testEnv->add($testName, $testPath, $output, $rc, $expectedOut, $expectedRc);

        // Cleanup
        if(!$flag_noClean) {
            if(file_exists($outputFile)) {
                array_push($filesToRemove, $outputFile);
            }
        }
    } else if($flag_parseOnly) {
        // Setup
        $output = NULL;
        $rc = NULL;
        $srcFile = $file->srcFile->getName();
        $outputFile = $srcFile."_tempOut.xml";
        $deltaFile = $srcFile."_tempDelta.xml";

        $cmd = "php ". $flag_parseScriptFile ." < ". $srcFile .".src";

        // Execute parser
        exec($cmd, $output, $rc);
        $output = implode("\n", $output);

        // Write it to the temporary file
        $f = fopen($outputFile, "w");
        fwrite($f, $output);
        fclose($f);

        // Get expected output and return code
        $expectedOut = getFileContent($file->outFile->getName().".out");
        $expectedRc = getFileContent($file->rcFile->getName().".rc");

        if($expectedRc != "0") {
            // Add the test
            $testName = $file->srcFile->getNameNoPath();
            $testPath = $file->srcFile->getPath();
            $testEnv->add($testName, $testPath, $output, $rc, $expectedOut, $expectedRc);
        } else {
            // Setup
            $jexamxmlOut = NULL;
            $jexamxmlRc = NULL;
            $jexamxmlCmd = "java -jar ".$flag_jexampathPath."jexamxml.jar ".
                            $outputFile." ".
                            $srcFile.".out ".
                            $deltaFile." -D ".
                            $flag_jexampathPath."options";

            // Execute jexamxml.jar
            exec($jexamxmlCmd, $jexamxmlOut, $jexamxmlRc);
            
            // Add the test
            $testName = $file->srcFile->getNameNoPath();
            $testPath = $file->srcFile->getPath();
            // Check if files are different using the return code
            if($jexamxmlRc == 0) {
                $testEnv->add($testName, $testPath, $output, $rc, $expectedOut, $expectedRc, True);
            } else {
                $testEnv->add($testName, $testPath, $output, $rc, $expectedOut, $expectedRc, False);
            }
        }

        // Cleanup
        if(!$flag_noClean) {
            if(file_exists($outputFile)) {
                array_push($filesToRemove, $outputFile);
            }
            if(file_exists($outputFile.".log")) {
                array_push($filesToRemove, $outputFile.".log");
            }
            if(file_exists($deltaFile)) {
                array_push($filesToRemove, $deltaFile);
            }
        }
    } else {
        $testName = $file->srcFile->getNameNoPath();
        $testPath = $file->srcFile->getPath();

        // Setup parser
        $output = NULL;
        $rc = NULL;
        $srcFile = $file->srcFile->getName();
        $outputFile = $srcFile."_tempOut.temp";

        $cmd = "php ".$flag_parseScriptFile." < ".$srcFile.".src | python3 ".$flag_intScriptFile." --input=".$srcFile.".in > ".$outputFile;

        // Execute parser and interpreter
        exec($cmd, $output, $rc);

        // Get expected output and return code
        $expectedOut = getFileContent($file->outFile->getName().".out");
        $expectedRc = getFileContent($file->rcFile->getName().".rc");
        $output = getFileContent($outputFile);

        if(diff2files($outputFile, $srcFile.".out") && $expectedRc == strval($rc)) {
            // Outputs and return codes are equal
            $testEnv->add($testName, $testPath, $output, $rc, $expectedOut, $expectedRc, True);
        } else {
            $testEnv->add($testName, $testPath, $output, $rc, $expectedOut, $expectedRc, False);
        }
    }

    $file = $rdi->next();
}

print($testEnv->getHtml());

// Clean up
if(!$flag_noClean) {
    foreach($filesToRemove as $f) {
        unlink($f);
    }
}
