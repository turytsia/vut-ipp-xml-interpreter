<?php

declare(strict_types=1);

function color(string $str, string $color)
{
    return "\033[" . $color . "m" . $str . "\033[0m";
}

function red(string $str)
{
    return color($str, "31");
}

function green(string $str)
{
    return color($str, "32");
}

function blue(string $str)
{
    return color($str, "34");
}

function indentation(int $level)
{
    return str_repeat(" ", max($level, 0) * 2);
}

class Tester
{
    private int $failed = 0;
    private int $passed = 0;
    private string $php = "php8.1";

    private function pass(string $name, int $level)
    {
        $this->passed++;
        echo indentation($level) . green($name) . "\n";
    }

    private function fail(string $name, int $level)
    {
        $this->failed++;
        echo indentation($level) . red($name) . "\n";
    }

    private function runTest(string $name, int $level = 0)
    {
        $src = "./tests/$name.src";
        $out = "./tests/$name.out";

        $cmd = "{$this->php} parse.php < $src > tmp/out.xml 2>/dev/null";
        $output = null;
        $rc = null;
        exec($cmd, $output, $rc);

        // test return code
        $expectedRc = intval(file_get_contents("./tests/$name.rc"));
        if ($rc !== $expectedRc) {
            $this->fail($name, $level);
            echo "Expected return code: $expectedRc, got: $rc\n\n";
            return;
        }
        if ($rc !== 0) {
            $this->pass($name, $level);
            return;
        }

        // test output
        $cmd = "xmldiff $out tmp/out.xml";
        $output = null;
        $rc = null;
        exec($cmd, $output, $rc);
        if ($rc === 0) {
            $this->pass($name, $level);
            return;
        } else {
            $this->fail($name, $level);
            echo "Expected:\n";
            echo file_get_contents($out) . "\n";
            echo "Got:\n";
            echo file_get_contents("tmp/out.xml") . "\n";
        }
    }

    private function testDir(string $path, int $level)
    {
        if ($path !== "") {
            echo indentation($level) . blue($path) . "\n";
        }
        $dir = opendir("./tests/$path");
        while ($file = readdir($dir)) {
            if ($file === "." || $file === "..") continue;
            $filePath = "./tests/$path/$file";
            if (is_dir($filePath)) {
                $prefix = $path === "" ? "" : "$path/";
                $this->testDir("$prefix$file", $level + 1);
            } else {
                // if file ends with .src
                if (substr($file, -4) === ".src") {
                    $this->runTest("$path/" . substr($file, 0, -4), $level + 1);
                }
            }
        }
    }

    private function setPhpExecutable()
    {
        $output = null;
        $rc = null;
        exec("which php8.1 2>/dev/null", $output, $rc);
        if ($rc !== 0) {
            $this->php = "php";
        }
    }

    function runTests()
    {
        $this->setPhpExecutable();

        exec("mkdir -p tmp");
        $this->testDir("", -1);
        echo "\n";
        $failedStr = $this->failed === 0 ? green("no failed tests") : red("{$this->failed} failed tests");
        $passedStr = $this->passed === 0 ? red("no passed tests") : green("{$this->passed} passed tests");
        echo "Tests finished with $failedStr and $passedStr";
        exec("rm -r tmp");
    }
}

$tester = new Tester();
$tester->runTests();
