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
from typing import List, Tuple, Union
import hashlib


# Class to hold the path settings
class UserPaths:
    def __init__(self, input_csv, file_directory, output_csv) -> None:
        self.input_csv = input_csv
        self.file_directory = file_directory
        self.output_csv = output_csv


# Class to hold the results of file fuzz
class FileFuzzResult:
    def __init__(
        self, path: pathlib.Path, name: str, title: str, ftype: bool, ind: int
    ) -> None:
        self.path = path
        self.name = name
        self.title = title
        self.ftype = ftype
        self.ind = ind
        self.results = []

    # Print information
    def __str__(self) -> str:
        return (
            f"Title: {self.title}\n"
            f"Results: {self.results}\n"
            f"Path: {self.path}\n"
            f"Name: {self.name}\n"
            f"Type: {self.ftype}\n"
            f"Index: {self.ind}"
        )

    # Function to update the class values
    def updateResults(
        self,
        result: List[Union[str, int]],
    ) -> None:
        # Check if it's less than 5 (desired length)
        if len(self.results) < 5:
            # Add result
            self.results.append(result)
            # Only sort for the first 5 results
            self.results.sort(key=lambda x: x[1], reverse=True)
        else:
            # Check if the score is larger than any of the existing results
            for ind, i_result in enumerate(self.results):
                if result[1] > i_result[1]:
                    # Insert the value
                    self.results.insert(ind, result)
                    # Remove the last value (since it'll be the smaller one)
                    self.results.pop()  # could also do self.results = self.results[0:5]
                    # Exit the loop
                    break  # could return too


# Class to hold the results of title fuzz
class TitleFuzzResult:
    # Initialization
    def __init__(self, title: str, ind: int) -> None:
        self.title = title
        self.ind = ind
        self.first_result = []
        self.second_result = []
        self.third_result = []

    # Print information
    def __str__(self) -> str:
        return (
            f"Title: {self.title}\n"
            f"First: {self.first_result}\n"
            f"Second: {self.second_result}\n"
            f"Third: {self.third_result}\n"
            f"Index: {self.ind}"
        )

    # Function to update the class values
    def updateResults(
        self,
        result1: List[Union[str, int]],
        result2: List[Union[str, int]],
        result3: List[Union[str, int]],
    ) -> None:
        self.first_result = result1
        self.second_result = result2
        self.third_result = result3


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


# Function to create the desired data frames
def createDesiredDataframes(
    input_file: pathlib.Path, file_path: pathlib.Path
) -> Tuple[pandas.DataFrame, pandas.DataFrame, pandas.DataFrame, pandas.DataFrame]:
    # Getting the input csv data in a data frame
    input_df = readCsv(input_file)

    # Add column names
    input_df.columns = ["Title", "Path"]

    # Creating an index column (for recombining at the end)
    input_df["Index"] = input_df.index

    # Splitting the data frame into 2 data frames (Might need to make these as deep copies later, believe these still reference the same data)
    search_df = input_df[input_df["Path"].isnull()]  # .copy()
    found_df = input_df[input_df["Path"].notnull()]  # .copy()

    # Reading all the files in the file directory
    file_titles = getFiles(file_path)

    # Removing files that are already in the found df (they've already been found :^])
    file_titles = file_titles.drop(
        file_titles[file_titles["Name"].isin(list(found_df["Path"]))].index
    )

    # Returning the data frames
    return (input_df, search_df, found_df, file_titles)


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
def findMatch(title: str, search_titles: List[str]) -> list:  # change type
    result = thefuzz.process.extract(
        title, search_titles, scorer=thefuzz.fuzz.ratio, limit=3
    )
    # Using the fuzz.ratio scorer because I shouldn't need it to tokenize or any of the
    # more advanced stuff. The titles should be mostly similar in structure. Tokenizing might
    # even make it worse because the titles often wont have any spaces.
    return result


# Function to get string similarity
def findSimilarity(
    titles: pandas.DataFrame, search: pandas.DataFrame
) -> Tuple[pandas.Series, pandas.Series]:
    # Create a series of classes to store the file results
    file_classes = createFileClasses(titles)
    # Create a series of classes to store the title results
    title_classes = createTitleClasses(search)

    # Checking each file in the search df to find the best match in the file titles df
    for index, row in search_df.iterrows():
        # Getting the fuzz results comparing the searching title to the files
        result = findMatch(row["Title"], list(file_titles["Title"]))

        # Updating the results for the titles
        title_class: TitleFuzzResult = title_classes[pathHash(row["Title"])]
        # This will update the class in the series because it's just a reference not a copy
        title_class.updateResults(result[0], result[1], result[2])

        # Updating the result for the files
        result1_class: FileFuzzResult = file_classes[pathHash(result[0][0])]
        result1_class.updateResults([row["Title"], result[0][1]])
        result2_class: FileFuzzResult = file_classes[pathHash(result[1][0])]
        result2_class.updateResults([row["Title"], result[1][1]])
        result3_class: FileFuzzResult = file_classes[pathHash(result[2][0])]
        result3_class.updateResults([row["Title"], result[2][1]])

    # Return the series
    return (file_classes, title_classes)


# Function to create a dictionary to store file fuzz results
def createFileClasses(df: pandas.DataFrame) -> pandas.Series:
    temp_list = []
    for ind, row in df.iterrows():
        temp_list.append(
            FileFuzzResult(row["Path"], row["Name"], row["Title"], row["Type"], ind)
        )
    # Create hash to store the titles because they can be key breaking
    index_hash = [pathHash(x) for x in list(df["Title"])]
    temp_series = pandas.Series(data=temp_list, index=index_hash)
    return temp_series


# Function to create a dictionary to store title fuzz results
def createTitleClasses(df: pandas.DataFrame) -> pandas.Series:
    temp_list = []
    for ind, row in df.iterrows():
        temp_list.append(TitleFuzzResult(row["Title"], ind))
    # Create hash to store the titles because they can be key breaking
    index_hash = [pathHash(x) for x in list(df["Title"])]
    temp_series = pandas.Series(data=temp_list, index=index_hash)
    return temp_series


# Function to create a hash for the path strings
def pathHash(pre: str) -> str:
    return hashlib.sha256(pre.encode("utf-8")).hexdigest()


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

# Creating the desired data frames
input_df, search_df, found_df, file_titles = createDesiredDataframes(
    user_args.input_csv, user_args.file_directory
)

# Creating series of the similarities
file_classes, title_classes = findSimilarity(file_titles, search_df)

# Deciding which file to assign to a title

# Iterating through all of the files
for ind, value in enumerate(file_classes):
    # Check each of the results to see if this file was the top match
    for ind, x_result in enumerate(value.results):
        # Checking if the highest matching result for the file was the top match for the title
        if (
            value.results[ind][0]
            == title_classes[pathHash(x_result[0])].first_result[0]
        ):
            print("YIPPIE")
            # Remove this file and that title from the pool to select from... somehow
            # ..................... #
            # ..................... #
            # ..................... #
            # ..................... #
            # ..................... #
            # Break from the loop to go onto the next file
            break
# Footer Comment
# History of Contributions:
# [2024-2024] - [Garrett Johnson (GreenBeanio) - https://github.com/greenbeanio] - [The entire document]
