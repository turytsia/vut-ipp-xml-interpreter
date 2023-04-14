**Implementační dokumentace k 2. úloze do IPP 2022/2023**<br/>**Jméno a příjmení:** Oleksandr Turytsia<br/>**Login:** xturyt00<br/>

## Python XML interpret [ENG]
This program is an interpreter for files that contain programs written in the IPPcode23 language in XML representation.

### Usage
```
python3 interpret.py [[--source=[SOURCE_FILE]] [--input=[INPUT_FILE]]] [--help|-h]
```

`--source` specifies the path to the XML file that contains the program to be interpreted.

`--input` specifies the path to a file that contains the input data for the program. 

If source or input were not provided, the interpreter will wait for input from the standard input stream.


### XML Format
The input XML file must conform to the following format:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<program language="IPPcode23">
    <instruction order="[ORDER]" opcode="[OPCODE]">
        <arg1 type="[TYPE]">[VALUE]</arg1>
        <arg2 type="[TYPE]">[VALUE]</arg2>
        <arg3 type="[TYPE]">[VALUE]</arg3>
    </instruction>
    ...
</program>
```

The program element must have a `language` attribute with the value *IPPcode23*.

Each instruction element represents a single instruction in the program, and must have the following attributes:

`order`: an integer representing the order of the instruction in the program
`opcode`: a string representing the opcode of the instruction

Each instruction element may have up to three arg elements, each with the following attributes:

`type`: a string representing the type of the argument ("int", "string", "bool", "nil", "var", "type" or "nil")
`value`: the value of the argument, represented as a string


### Implementation
Click [here](https://mermaid.ink/img/pako:eNqtV21v2zYQ_iuE9sVuXcMvqd0K-bQuGQIk64AsRTEIEBiJdolIpEDRgT3P_u07HimJeon7ZfngiPcc7-W5O4o6BolMWRAGSUbL8jdOt4rmkYgErgm52Ses0FwKeD5G4j0hbM_1iIUkrqExeZU8jcTJ29egbl_OypJuYV-pFRdbIzKeQ8KFbm39irtulJKKHMmpEn9_uL-VKqd6CHkSbF-wRLO0hz6ynArNkx7w16FgPeE3qjh9ztiTSNmGiwF7t8DP0L5sd2HT14IpKlLU6keIhKDKYOZ3QjMlaOYBkfD4vf73wweftT7Y5m4Q7zDY12nx2IdrNvvQMKd9vYbZIRs9foc46LA8kMUA132tFuOR8GbgHaCNttfvJn87IgT-Wg2NUPx4yJ_tJLya-EJCxcGsNKAh6kTiF-N55HCYi3FIzDYD3GaS1tDGLDzQZlWhdsA8-Fcpswp8hmcP-oPXiOANgNF7cdclLmOoZjc1ENnMykSaZLCQCBmhgIU_9SXTcQlGR-bHOhwjETLG_SNnxaUxQKX5bVFpbDh_AxRW3A5SWIFvUFjBAxRWUI_CCoCETHFHtsIdk-8JL2OIbzS2Bp0Ew-rI7M6O0Dx2ROC9kfRIu6fPLGuxhnb9WmN3N1XvS23oXSlabtz9SVXJ6nPKl8V3AnzuEhw0jIRlLGdCh-YEmt7c48LIZWHfDU3XSJUy1RLYYS9hkJSihzNasObOBi-My9HYcQMp83TUbqb4dyaY4gkG1_TUWzFRrVsBaLbX_vrnDh0L9iRozncnxinqSW1cPbGrpnsX9BLBefXc_UwHh_qyiq39ZZ26E1wPvGsgr_QtuGfQbPcO3Ovp1JkIYbJf5YsZ8g6ObejBtkGva-ch-aIY1QZq3ql1OMeLDcerhmx3G7o4u-r6bX3RKx6M4A_STqmmIUl5gua3cCa-UgXniIr989IdF-7UtWen0_OQdpehkwcq4LKlrK_tRqFNRFCSOYlNBuVnBHRb9X-IDK55SEOMlu18FLvyR2sti2aJqaB_JNNPZ4DSR02TFwfDPHjceoXCGThXnt2Lp0GqGGrvnf7yfbzdhe1Aa61ICKkZ2cDVrRVrFOCS5G7N88IePCXJJPzIDfRe3VflNIKbxR1JWcJTlhKwCe8XQtOU6B8sB1XbsEb4wlgBnYU3ebhji4SXbBoFDWdfaJZZ57Y_EljXnc2r89MwlZmBtu9RjyM84Fhe6MPg-8Ybh7ow6MfPp3LnKaNb0GFKjzzV0Dc4djq1HRPBkKWhOtZ5e-VpzS7o9IMPyVNpC9ncdup6h2TnwEgEkyBncMvmKXxO4UUwCkxxWBSE8JhS9WKqcAI9utPy8SCSIARnbBLsCuhZ5r6-gnBDsxKkLOVaqgf3fWb-TYKCir-lzKuNsAzCY7APws-r6Wr9cbFaflyvZ_PVfBIcgnC-WE6v5svZ58XVern4BAqnSfAP7p9N11dXs9V8tl7M14vlYvXp9B_OJAro?type=png)[](https://mermaid.live/edit#pako:eNqtV21v2zYQ_iuE9sVuXcMvqd0K-bQuGQIk64AsRTEIEBiJdolIpEDRgT3P_u07HimJeon7ZfngiPcc7-W5O4o6BolMWRAGSUbL8jdOt4rmkYgErgm52Ses0FwKeD5G4j0hbM_1iIUkrqExeZU8jcTJ29egbl_OypJuYV-pFRdbIzKeQ8KFbm39irtulJKKHMmpEn9_uL-VKqd6CHkSbF-wRLO0hz6ynArNkx7w16FgPeE3qjh9ztiTSNmGiwF7t8DP0L5sd2HT14IpKlLU6keIhKDKYOZ3QjMlaOYBkfD4vf73wweftT7Y5m4Q7zDY12nx2IdrNvvQMKd9vYbZIRs9foc46LA8kMUA132tFuOR8GbgHaCNttfvJn87IgT-Wg2NUPx4yJ_tJLya-EJCxcGsNKAh6kTiF-N55HCYi3FIzDYD3GaS1tDGLDzQZlWhdsA8-Fcpswp8hmcP-oPXiOANgNF7cdclLmOoZjc1ENnMykSaZLCQCBmhgIU_9SXTcQlGR-bHOhwjETLG_SNnxaUxQKX5bVFpbDh_AxRW3A5SWIFvUFjBAxRWUI_CCoCETHFHtsIdk-8JL2OIbzS2Bp0Ew-rI7M6O0Dx2ROC9kfRIu6fPLGuxhnb9WmN3N1XvS23oXSlabtz9SVXJ6nPKl8V3AnzuEhw0jIRlLGdCh-YEmt7c48LIZWHfDU3XSJUy1RLYYS9hkJSihzNasObOBi-My9HYcQMp83TUbqb4dyaY4gkG1_TUWzFRrVsBaLbX_vrnDh0L9iRozncnxinqSW1cPbGrpnsX9BLBefXc_UwHh_qyiq39ZZ26E1wPvGsgr_QtuGfQbPcO3Ovp1JkIYbJf5YsZ8g6ObejBtkGva-ch-aIY1QZq3ql1OMeLDcerhmx3G7o4u-r6bX3RKx6M4A_STqmmIUl5gua3cCa-UgXniIr989IdF-7UtWen0_OQdpehkwcq4LKlrK_tRqFNRFCSOYlNBuVnBHRb9X-IDK55SEOMlu18FLvyR2sti2aJqaB_JNNPZ4DSR02TFwfDPHjceoXCGThXnt2Lp0GqGGrvnf7yfbzdhe1Aa61ICKkZ2cDVrRVrFOCS5G7N88IePCXJJPzIDfRe3VflNIKbxR1JWcJTlhKwCe8XQtOU6B8sB1XbsEb4wlgBnYU3ebhji4SXbBoFDWdfaJZZ57Y_EljXnc2r89MwlZmBtu9RjyM84Fhe6MPg-8Ybh7ow6MfPp3LnKaNb0GFKjzzV0Dc4djq1HRPBkKWhOtZ5e-VpzS7o9IMPyVNpC9ncdup6h2TnwEgEkyBncMvmKXxO4UUwCkxxWBSE8JhS9WKqcAI9utPy8SCSIARnbBLsCuhZ5r6-gnBDsxKkLOVaqgf3fWb-TYKCir-lzKuNsAzCY7APws-r6Wr9cbFaflyvZ_PVfBIcgnC-WE6v5svZ58XVern4BAqnSfAP7p9N11dXs9V8tl7M14vlYvXp9B_OJAro) in order to see the entire diagram.
[![](https://mermaid.ink/img/pako:eNqtV21v2zYQ_iuE9sVuXcMvqd0K-bQuGQIk64AsRTEIEBiJdolIpEDRgT3P_u07HimJeon7ZfngiPcc7-W5O4o6BolMWRAGSUbL8jdOt4rmkYgErgm52Ses0FwKeD5G4j0hbM_1iIUkrqExeZU8jcTJ29egbl_OypJuYV-pFRdbIzKeQ8KFbm39irtulJKKHMmpEn9_uL-VKqd6CHkSbF-wRLO0hz6ynArNkx7w16FgPeE3qjh9ztiTSNmGiwF7t8DP0L5sd2HT14IpKlLU6keIhKDKYOZ3QjMlaOYBkfD4vf73wweftT7Y5m4Q7zDY12nx2IdrNvvQMKd9vYbZIRs9foc46LA8kMUA132tFuOR8GbgHaCNttfvJn87IgT-Wg2NUPx4yJ_tJLya-EJCxcGsNKAh6kTiF-N55HCYi3FIzDYD3GaS1tDGLDzQZlWhdsA8-Fcpswp8hmcP-oPXiOANgNF7cdclLmOoZjc1ENnMykSaZLCQCBmhgIU_9SXTcQlGR-bHOhwjETLG_SNnxaUxQKX5bVFpbDh_AxRW3A5SWIFvUFjBAxRWUI_CCoCETHFHtsIdk-8JL2OIbzS2Bp0Ew-rI7M6O0Dx2ROC9kfRIu6fPLGuxhnb9WmN3N1XvS23oXSlabtz9SVXJ6nPKl8V3AnzuEhw0jIRlLGdCh-YEmt7c48LIZWHfDU3XSJUy1RLYYS9hkJSihzNasObOBi-My9HYcQMp83TUbqb4dyaY4gkG1_TUWzFRrVsBaLbX_vrnDh0L9iRozncnxinqSW1cPbGrpnsX9BLBefXc_UwHh_qyiq39ZZ26E1wPvGsgr_QtuGfQbPcO3Ovp1JkIYbJf5YsZ8g6ObejBtkGva-ch-aIY1QZq3ql1OMeLDcerhmx3G7o4u-r6bX3RKx6M4A_STqmmIUl5gua3cCa-UgXniIr989IdF-7UtWen0_OQdpehkwcq4LKlrK_tRqFNRFCSOYlNBuVnBHRb9X-IDK55SEOMlu18FLvyR2sti2aJqaB_JNNPZ4DSR02TFwfDPHjceoXCGThXnt2Lp0GqGGrvnf7yfbzdhe1Aa61ICKkZ2cDVrRVrFOCS5G7N88IePCXJJPzIDfRe3VflNIKbxR1JWcJTlhKwCe8XQtOU6B8sB1XbsEb4wlgBnYU3ebhji4SXbBoFDWdfaJZZ57Y_EljXnc2r89MwlZmBtu9RjyM84Fhe6MPg-8Ybh7ow6MfPp3LnKaNb0GFKjzzV0Dc4djq1HRPBkKWhOtZ5e-VpzS7o9IMPyVNpC9ncdup6h2TnwEgEkyBncMvmKXxO4UUwCkxxWBSE8JhS9WKqcAI9utPy8SCSIARnbBLsCuhZ5r6-gnBDsxKkLOVaqgf3fWb-TYKCir-lzKuNsAzCY7APws-r6Wr9cbFaflyvZ_PVfBIcgnC-WE6v5svZ58XVern4BAqnSfAP7p9N11dXs9V8tl7M14vlYvXp9B_OJAro?type=png)](https://mermaid.live/edit#pako:eNqtV21v2zYQ_iuE9sVuXcMvqd0K-bQuGQIk64AsRTEIEBiJdolIpEDRgT3P_u07HimJeon7ZfngiPcc7-W5O4o6BolMWRAGSUbL8jdOt4rmkYgErgm52Ses0FwKeD5G4j0hbM_1iIUkrqExeZU8jcTJ29egbl_OypJuYV-pFRdbIzKeQ8KFbm39irtulJKKHMmpEn9_uL-VKqd6CHkSbF-wRLO0hz6ynArNkx7w16FgPeE3qjh9ztiTSNmGiwF7t8DP0L5sd2HT14IpKlLU6keIhKDKYOZ3QjMlaOYBkfD4vf73wweftT7Y5m4Q7zDY12nx2IdrNvvQMKd9vYbZIRs9foc46LA8kMUA132tFuOR8GbgHaCNttfvJn87IgT-Wg2NUPx4yJ_tJLya-EJCxcGsNKAh6kTiF-N55HCYi3FIzDYD3GaS1tDGLDzQZlWhdsA8-Fcpswp8hmcP-oPXiOANgNF7cdclLmOoZjc1ENnMykSaZLCQCBmhgIU_9SXTcQlGR-bHOhwjETLG_SNnxaUxQKX5bVFpbDh_AxRW3A5SWIFvUFjBAxRWUI_CCoCETHFHtsIdk-8JL2OIbzS2Bp0Ew-rI7M6O0Dx2ROC9kfRIu6fPLGuxhnb9WmN3N1XvS23oXSlabtz9SVXJ6nPKl8V3AnzuEhw0jIRlLGdCh-YEmt7c48LIZWHfDU3XSJUy1RLYYS9hkJSihzNasObOBi-My9HYcQMp83TUbqb4dyaY4gkG1_TUWzFRrVsBaLbX_vrnDh0L9iRozncnxinqSW1cPbGrpnsX9BLBefXc_UwHh_qyiq39ZZ26E1wPvGsgr_QtuGfQbPcO3Ovp1JkIYbJf5YsZ8g6ObejBtkGva-ch-aIY1QZq3ql1OMeLDcerhmx3G7o4u-r6bX3RKx6M4A_STqmmIUl5gua3cCa-UgXniIr989IdF-7UtWen0_OQdpehkwcq4LKlrK_tRqFNRFCSOYlNBuVnBHRb9X-IDK55SEOMlu18FLvyR2sti2aJqaB_JNNPZ4DSR02TFwfDPHjceoXCGThXnt2Lp0GqGGrvnf7yfbzdhe1Aa61ICKkZ2cDVrRVrFOCS5G7N88IePCXJJPzIDfRe3VflNIKbxR1JWcJTlhKwCe8XQtOU6B8sB1XbsEb4wlgBnYU3ebhji4SXbBoFDWdfaJZZ57Y_EljXnc2r89MwlZmBtu9RjyM84Fhe6MPg-8Ybh7ow6MfPp3LnKaNb0GFKjzzV0Dc4djq1HRPBkKWhOtZ5e-VpzS7o9IMPyVNpC9ncdup6h2TnwEgEkyBncMvmKXxO4UUwCkxxWBSE8JhS9WKqcAI9utPy8SCSIARnbBLsCuhZ5r6-gnBDsxKkLOVaqgf3fWb-TYKCir-lzKuNsAzCY7APws-r6Wr9cbFaflyvZ_PVfBIcgnC-WE6v5svZ58XVern4BAqnSfAP7p9N11dXs9V8tl7M14vlYvXp9B_OJAro)

#### Idea
Since the interpret had to be implemented in Python, I have decided to stick with OOP approach as much as it was possible for me.

I divided task into smaller subtasks:
- Handle options, input and basic output
- Parse XML using [ETree](https://docs.python.org/3/library/xml.etree.elementtree.html).
- Implement types using classes. (Var is subset for Symb)
- Implement data stack, frame stack and call stack.
- Create error handling mechanism, that is native to Python.
- Implement static semantic analysis, variable checking. Find all the labels that are being used in the code.
- Implement instructions and operations. Start testing.

For most subtasks was created its class that would
implement all the necessary features in order to work correctly.

In the next sections I will note some of these classes and approaches I followed to ease development.

#### Error handling
Interpret has its own error codes and messages that needs to be shown to a user in some error cases.

For that I decided to customize already existing error handling in Python by extending `Exception` class with attribudes `code` and `message`.

When error occures, exception can be easily raised with custom message and the program will gracefully exit with pre-defined error code.

#### Parser
For XML parsing interpret is using not only ETree, that I mentioned earlier, but also class `Parser`. It's made to analyze correctness and validity of a language hidden behind XML representation (IFJcode23).

When implementing this class, I have noticed that most of its subclasses were sharing the same idea but with different functionalit, so I decided to created [abstract](https://docs.python.org/3/library/abc.html) class `_GenericParseType`.

#### Types

In interpret `Var` literal is a subset for `Symb`. To implement such behaviour I have used inheritance (see diagram).



