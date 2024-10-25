# Header Comment
# Project: [Garrett's Split Tracker] [https://github.com/GreenBeanio/Match-Titles-to-Files]
# Copyright: Copyright (c) [2024]-[2024] [Match Titles to Files] Contributors
# Version: [0.1]
# Status: [Development]
# License(s): [MIT]
# Author(s): [Garrett Johnson (GreenBeanio) - https://github.com/greenbeanio]
# Maintainer: [Garrett Johnson (GreenBeanio) - https://github.com/greenbeanio]
# Project Description: [This project is used to try to match titles to corresponding files. ]
# File Description: This is the main file for the project.

# Imports
import pandas
import thefuzz
import pathlib
import logging
import sys
import argparse
import numpy
import thefuzz.fuzz
import thefuzz.process
from typing import List


# Class to hold the path settings
class UserPaths:
    def __init__(self, input_csv, file_directory, output_csv) -> None:
        self.input_csv = input_csv
        self.file_directory = file_directory
        self.output_csv = output_csv


# Class to hold the results of file fuzz
class FileFuzzResult:
    def __init__(self, path: pathlib.Path, name: str, title: str, ftype: bool) -> None:
        self.path = path
        self.name = name
        self.title = title
        self.ftype = ftype
        self.first_results = []
        self.second_results = []
        self.third_results = []


# Class to hold the results of title fuzz
class TitleFuzzResult:
    def __init__(self, title: str) -> None:
        self.title = title
        self.first_result = []
        self.second_result = []
        self.third_result = []


# Function to check if a path exists
def checkPath(test_path: pathlib.Path) -> bool:
    if pathlib.Path.exists(test_path):
        return True
    else:
        return False


# Function to get the arguments
def checkArguments() -> UserPaths:
    # Get the current directory
    cwd = pathlib.Path().resolve()
    # Getting path options
    if cli_args.csv_path is None:
        input_csv = pathlib.Path.joinpath(cwd, "titles.csv")
    else:
        input_csv = cli_args.csv_path
    if cli_args.files_path is None:
        files_path = pathlib.Path.joinpath(cwd, "files")
    else:
        files_path = cli_args.files_path
    if cli_args.output_path is None:
        output_csv = pathlib.Path.joinpath(cwd, "matched.csv")
    else:
        output_csv = cli_args.output_path
    # Checking the the input csv exists and that the file directory exists
    good_paths = True
    if not checkPath(input_csv):
        good_paths = False
        logger.error(f'The input file at "{input_csv}" does not exist')
    if not checkPath(files_path):
        good_paths = False
        logger.error(f'The input directory at "{files_path}" does not exist')
    elif not any(files_path.iterdir()):
        # Check that the directory isn't empty
        good_paths = False
        logger.error(f'The input directory at "{files_path}" is empty')
    # Checking that the output file is in a directory that exists
    if not checkPath(output_csv.parent):
        good_paths = False
        logger.error(f'The output directory at "{output_csv.parent}" does not exist')
    # Close if there was an invalid path
    if not good_paths:
        logger.critical("Fix the errors in your files")
        sys.exit()
    # Create the class to store the files
    return UserPaths(input_csv, files_path, output_csv)


# Function to read the csv
def readCsv(csv_path: pathlib.Path) -> pandas.DataFrame:
    # Try to open the csv file
    try:
        # try to read the csv
        df = pandas.read_csv(csv_path, header=None, usecols=[0, 1])
        return df
    except:
        logger.error(f'The file at "{csv_path}" couldn\'t be read')
        sys.exit()


# Function to get the file names
def getFiles(file_path: pathlib.Path) -> pandas.DataFrame:
    # Creating an empty list
    temp_list = []
    # Iterate through every item in the path
    for item in file_path.iterdir():
        # Add the file to a numpy array
        if item.is_file():
            temp_list.append([item, item.name, item.stem, True])
        else:
            temp_list.append([item, item.stem, item.stem, False])
    # Create a data frame
    temp_df = pandas.DataFrame(
        data=temp_list, columns=["Path", "Name", "Title", "Type"]
    )
    return temp_df


# Function to find the best match
def find_match(title: str, search_titles: List[str]) -> list:  # change type
    result = thefuzz.process.extract(
        title, search_titles, scorer=thefuzz.fuzz.ratio, limit=3
    )
    print(result)


# Function to create a dictionary to store results for each file
def createResultDict(titles: str) -> dict:
    temp_dict = {}
    for title in titles:
        temp_dict[title] = {1: [], 2: [], 3: []}
    return temp_dict


# Creating a logger
# Create a logger
logger = logging.getLogger("Title Matcher")
logger.setLevel(logging.INFO)

# Creating the cli arguments
parser = argparse.ArgumentParser(
    prog="Match Titles to Files",
    description="Attempts to match titles to files.",
    epilog="Garrett Johnson (GreenBeanio) - https://github.com/greenbeanio",
)
parser.add_argument(
    "-csv",
    "--csv_path",
    help="Path to the csv file. Default: ./titles.csv",
    type=pathlib.Path,
)
parser.add_argument(
    "-files",
    "--files_path",
    help="Path to the directory with the files to attempt to match the titles to. Default: ./files",
    type=pathlib.Path,
)
parser.add_argument(
    "-o",
    "--output_path",
    help="Path to where you want to new (or overwritten) csv to go. Default: ./matched.csv",
    type=pathlib.Path,
)
cli_args = parser.parse_args()

# Get the user arguments
user_args = checkArguments()

# Getting the input csv data in a data frame
input_df = readCsv(user_args.input_csv)

# Add column names
input_df.columns = ["Title", "Path"]

# Creating an index column (for recombining at the end)
input_df["Index"] = input_df.index

# Splitting the data frame into 2 data frames (Might need to make these as deep copies later, believe these still reference the same data)
search_df = input_df[input_df["Path"].isnull()]  # .copy()
found_df = input_df[input_df["Path"].notnull()]  # .copy()

# Reading all the files in the file directory
file_titles = getFiles(user_args.file_directory)

# Removing files that are already in the found df (they've already been found :^])
file_titles = file_titles.drop(
    file_titles[file_titles["Name"].isin(list(found_df["Path"]))].index
)

print(search_df)

# Create a dictionary to store the file results
file_results = createResultDict(list(file_titles["Name"]))

# Create a dictionary to store the title results
title_results = createResultDict(list(search_df["Title"]))

# Checking each file in the search df to find the best match in the file titles df
for index, row in search_df.iterrows():
    find_match(row["Title"], list(file_titles["Name"]))
    input()
# Footer Comment
# History of Contributions:
# [2024-2024] - [Garrett Johnson (GreenBeanio) - https://github.com/greenbeanio] - [The entire document]
