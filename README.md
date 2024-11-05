# Match Titles to Files

A program that takes a csv of file names and attempts to match them to files

## Needed Files

- titles.csv
  - This file should have two columns with a header row.
  - The first column should hold the titles you want to match.
  - The second column should be paths (filenames) to titles you already know the location if.
- files
  - A directory filled with the files/directories that you want to match the titles to.

## CLI Arguments

- -h
  - The help command
- -i path
  - The path to the input csv file.
  - Default is the file "titles.csv" in the directory the script is ran from.
- -o path
  - The path to the output csv file.
  - Default is the file "matched.csv" in the directory the script is ran from.
- -s #
  - The desired minimum score for a match to be counted.
  - Must be 0 to 100
  - By default this is 90.
- -e #
  - The score engine to be used.
  - By default this is -1. This will run through all 6 of the engines.
  - Specific engines are:
    - 0: Ratio
      - Simple checking based on the entire strings
    - 1: Partial Ratio
      - Simple checking, but it checks substrings instead of the entire string
    - 2: Token Sort Tatio
      - Tokenizes (splits up) the strings before comparing them. Sorts them as well so the order of words doesn't matter.
    - 3: Partial Token Sort Ratio
      - Same as token sort ratio, but does it with substrings
    - 4: Token Set Ratio
      - Tokenizes (splits up) the strings before comparing them. Sorts them as well so the order of words doesn't matter. It also takes out common tokens/words.
    - 5: Partial Token Set Tatio
      - Same as token set ratio, but does it with substrings

### Linux

#### Initial Run

- cd /your/folder
- python3 -m venv env
- source env/bin/activate
- pip install -r requirements.txt
- python main.py

### Technology Used

| Package | Version | License | Link | Usage |
| --- | --- | --- | --- | --- |
| Python | 3.9.13 | Python Software Foundation License | [Link](https://www.python.org/) | Main programming language for the project |
| Pandas | 2.2.2 | BSD-3-Clause license | [Link](https://pypi.org/project/pandas/) | Dataframes and other data science data structures |
| NumPy | 2.0.1 | Modified BSD license | [Link](https://pypi.org/project/numpy/) | Mathematical operations |
| TheFuzz | 0.22.1 | MIT License | [Link](https://pypi.org/project/thefuzz/) | String Distance |
