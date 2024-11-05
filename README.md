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
    - 2: Token Sort Ratio
      - Tokenizes (splits up) the strings before comparing them. Sorts them as well so the order of words doesn't matter.
    - 3: Partial Token Sort Ratio
      - Same as token sort ratio, but does it with substrings
    - 4: Token Set Ratio
      - Tokenizes (splits up) the strings before comparing them. Sorts them as well so the order of words doesn't matter. It also takes out common tokens/words.
    - 5: Partial Token Set Ratio
      - Same as token set ratio, but does it with substrings

### Note About the Engines

    The engines are listed from low to high in the selection by how exact they are. You should keep that in mind when examining the results. The Ratio [0] and Partial Ratio [1] engines from my testing seem to be accurate with most of my files. The Token Sort Ratio [2] and Partial Token Sort Ratio [3] seem to be fairly accurate. The Token Set Ratio [4] and Partial Token Set Ratio [6] are very hit or miss and I would check every match manually. 
    
    Note that my results are from using -1 which will iterate though all of the engines in order. This method is intended to use the closest to exact matching engines first and removing the files and titles that are found to match from subsequent iterations. In theory this should result in more accurate findings as only the files and titles that need less exact engines are scored by the less exact engines. 

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
