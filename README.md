**Implementační dokumentace k 1. úloze do IPP 2022/2023**
**Jméno a příjmení:** Oleksandr Turytsia
**Login:** xturyt00

## PHP Parser [ENG]
**parser.php** is a script that analyzes IPPcode23.

It takes the code from input, breakes it into smaller pieces, validates its syntax and outputs valid XML representation of IPPCode23.
### Usage
```ubuntu
php8.1 parser.php <[source] [--options] [-flags] [--help]
```

### Implementation
[![](https://mermaid.ink/img/pako:eNqFVW1r2zAQ_itC9QenTUqSJmkrRmGs3QusFLoxxjAYNVYTM1sKkpzVy_Lfd5L8Iuel_eAXnZ67e-50d9rguUgYJnieUaVuU7qQNI94xL9wpWUx16ngaDC4QehOSiE_U55kTBJkAKtCv-c0KxWThyH7Vrz1Y5ExguYiX1HJFNLC4B9WTII-ivAowqAh4O8U_jy9fdBNBfpBszShWkjVdfw6zo_iNeRr2JGlCLuPjCawR1ChICZRaJAh8bzL57QJrtFs7YKnj0LmVGtYvfs3GPimI_7z_usnxiEDQMttP1g3jdDmsSvaC8yjQ9DCwZg6pOlOzSO4H1vEbfF0zx-hTcTPEGIvqY7_pHoZM7MbBvCJTc2RCv8B_lUfBTlTii6MGKilfNELEEJrkSYR33o-dirIuhkgFAhXFAr0qZS0NM5jcFTBwxoQ63LFAGVBPUtxwXRcq4e9Vh0tqYq58PfQkxBZh5B_7JZKkBoJqawMOiR6VUBn1qcFtg49o-35g8kT9GyXcZZyFgbmDfR5CQlymTJeJMvFmsWMJyCoQU0i93DQdjnjWr2NZPlKl0dh_sm0zVKffaripc1M6NRr_TqNDrKmMoTn2LYq86fQvI4BzIGG5uUDOoiMPrEstO8DGC-GarJY9oEzWYm-m6qx4jXNiiYVx6qs3u8fMtPbKaB2MrgC4jT3HIBAyMT0Xcq1Wzal3hRZ4Ho4i32oqzJjLez5hLv1TtqCtxvGgJFaE7uFXg8Bv9I9FmkbiyJH-tBrjx7ptkOrDAT2u8KffLYvAjeECLp9uL8V88KUtJWvpDD3GDEqdxlz8i6P2vdJM_58AqEfCvHPCDKzN5R2Z-bmrWQoXpPwBoJj4R_VFvdxzqD30wRuaLCKYHzrJcQTYbhfcULl7wg7HC20-FbyOSZgmvVxsYJeZNWFjskzzRRIWZICwfvqyjefPl5R_kuIvFaEJSYb_ILJ5fB8ejm6Go4nF1eT4Xg66eMSk8nsHFYXF9Pr8fByMptNJ9s-_msNAP5qfG2e69FsNrkYjbf_Ac1j7gg?type=png)](https://mermaid.live/edit#pako:eNqFVW1r2zAQ_itC9QenTUqSJmkrRmGs3QusFLoxxjAYNVYTM1sKkpzVy_Lfd5L8Iuel_eAXnZ67e-50d9rguUgYJnieUaVuU7qQNI94xL9wpWUx16ngaDC4QehOSiE_U55kTBJkAKtCv-c0KxWThyH7Vrz1Y5ExguYiX1HJFNLC4B9WTII-ivAowqAh4O8U_jy9fdBNBfpBszShWkjVdfw6zo_iNeRr2JGlCLuPjCawR1ChICZRaJAh8bzL57QJrtFs7YKnj0LmVGtYvfs3GPimI_7z_usnxiEDQMttP1g3jdDmsSvaC8yjQ9DCwZg6pOlOzSO4H1vEbfF0zx-hTcTPEGIvqY7_pHoZM7MbBvCJTc2RCv8B_lUfBTlTii6MGKilfNELEEJrkSYR33o-dirIuhkgFAhXFAr0qZS0NM5jcFTBwxoQ63LFAGVBPUtxwXRcq4e9Vh0tqYq58PfQkxBZh5B_7JZKkBoJqawMOiR6VUBn1qcFtg49o-35g8kT9GyXcZZyFgbmDfR5CQlymTJeJMvFmsWMJyCoQU0i93DQdjnjWr2NZPlKl0dh_sm0zVKffaripc1M6NRr_TqNDrKmMoTn2LYq86fQvI4BzIGG5uUDOoiMPrEstO8DGC-GarJY9oEzWYm-m6qx4jXNiiYVx6qs3u8fMtPbKaB2MrgC4jT3HIBAyMT0Xcq1Wzal3hRZ4Ho4i32oqzJjLez5hLv1TtqCtxvGgJFaE7uFXg8Bv9I9FmkbiyJH-tBrjx7ptkOrDAT2u8KffLYvAjeECLp9uL8V88KUtJWvpDD3GDEqdxlz8i6P2vdJM_58AqEfCvHPCDKzN5R2Z-bmrWQoXpPwBoJj4R_VFvdxzqD30wRuaLCKYHzrJcQTYbhfcULl7wg7HC20-FbyOSZgmvVxsYJeZNWFjskzzRRIWZICwfvqyjefPl5R_kuIvFaEJSYb_ILJ5fB8ejm6Go4nF1eT4Xg66eMSk8nsHFYXF9Pr8fByMptNJ9s-_msNAP5qfG2e69FsNrkYjbf_Ac1j7gg)

The whole implementation is just a pipe of specific parts of a parser that are connected with each other. 
- **InputReader** takes contents from *input*, formats it (removes empty lines of code, comments and eofs) and then sends it to the InputAnalyser.
- **InputAnalyser** takes array of clean lines of code, validates if header exists. If so, then generates header XML, then for each line creates instances of **Instruction**.
- Each **Instruction** validates line to which it belongs to. If given line is valid, list of **Operand**s will be created for each Instruction. Once all the instructions are created, **InputAnalyser** will send them to **OutputGenerator**.
- **OutputGenerator** is a configured object, extended from **XMLGenerator** where every instruction is being generated to XML and inserted to the whole XML structure.

To validate data during all the process, some of the objects are using collection **Validators**, where all the validation logic is stored.