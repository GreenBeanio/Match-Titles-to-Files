# Header Comment
# Project: [Match Titles to Files] [https://github.com/GreenBeanio/Match-Titles-to-Files]
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
    def __init__(
        self,
        input_csv: pathlib.Path,
        file_directory: pathlib.Path,
        output_csv: pathlib.Path,
        score_limit: int,
        score_engine: int,
    ) -> None:
        self.input_csv = input_csv
        self.file_directory = file_directory
        self.output_csv = output_csv
        self.score_limit = score_limit
        self.score_engine = score_engine


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
        self.match_result = []

    # Print information
    def __str__(self) -> str:
        return (
            f"Title: {self.title}\n"
            f"First: {self.first_result}\n"
            f"Second: {self.second_result}\n"
            f"Third: {self.third_result}\n"
            f"Index: {self.ind}\n"
            f"Match: {self.match_result}"
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

    # Function to assign the match value
    def updateMatch(self, result: List[Union[str, int]]) -> None:
        self.match_result = result

    # Function to check if there is already a match
    def checkMatch(self) -> bool:
        if len(self.match_result) == 0:
            return False
        else:
            return True


# Function to check if a path exists
def checkPath(test_path: pathlib.Path) -> bool:
    if pathlib.Path.exists(test_path):
        return True
    else:
        return False


# Function to get the arguments
def checkArguments(cli_args: argparse.Namespace) -> UserPaths:
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
    return UserPaths(
        input_csv, files_path, output_csv, cli_args.score_limit, cli_args.score_engine
    )


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


# Function to create the initial data frame
def createInitialDataframes(
    input_file: pathlib.Path, file_path: pathlib.Path
) -> Tuple[pandas.DataFrame, pandas.DataFrame]:
    # Getting the input csv data in a data frame
    input_df = readCsv(input_file)

    # Add column names
    input_df.columns = ["Title", "Path"]

    # Creating an index column (for recombining at the end)
    input_df["Index"] = input_df.index

    # Reading all the files in the file directory
    file_df = getFiles(file_path)

    # # Removing files that are already in the found df (they've already been found :^])
    # file_df = file_df.drop(
    #     file_df[
    #         file_df["Name"].isin(list(input_df.loc[input_df["Path"].notna(), "Path"]))
    #     ].index
    # )  # TEMP: I forsee an issue if there are 2 entries with the same title... I might need to think about that

    # Returning the data frames
    return (input_df, file_df)


# Function to create the desired data frames
def createDesiredDataframes(
    input_df: pandas.DataFrame, file_df: pandas.DataFrame
) -> Tuple[pandas.DataFrame, pandas.DataFrame]:

    # Splitting the data frame into 2 data frames (Might need to make these as deep copies later, believe these still reference the same data)
    search_df = input_df[input_df["Path"].isna()]  # .copy()
    # found_df = input_df[input_df["Path"].notna()]  # .copy()

    # Removing files that are already in the found df (they've already been found :^])
    file_df = file_df.drop(
        file_df[
            file_df["Name"].isin(list(input_df.loc[input_df["Path"].notna(), "Path"]))
        ].index
    )  # TEMP: I forsee an issue if there are 2 entries with the same title... I might need to think about that

    # Returning the data frames
    return (search_df, file_df)


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
def findMatch(
    title: str, search_titles: List[str], matching: numpy.ndarray, token_engine: int
) -> list:
    # Use the desired engine
    if token_engine == 0:
        result = thefuzz.process.extract(
            title, search_titles, scorer=thefuzz.fuzz.ratio, limit=3
        )
        # Simple checking based on the entire strings
    elif token_engine == 1:
        result = thefuzz.process.extract(
            title, search_titles, scorer=thefuzz.fuzz.partial_ratio, limit=3
        )
        # Simple checking, but it checks substrings instead of the entire string
    elif token_engine == 2:
        result = thefuzz.process.extract(
            title, search_titles, scorer=thefuzz.fuzz.token_sort_ratio, limit=3
        )
        # Tokenizes (splits up) the strings before comparing them. Sorts them as well so the order of words doesn't matter.
    elif token_engine == 3:
        result = thefuzz.process.extract(
            title, search_titles, scorer=thefuzz.fuzz.partial_token_sort_ratio, limit=3
        )
        # Same as token sort ratio, but does it with substrings
    elif token_engine == 4:
        result = thefuzz.process.extract(
            title, search_titles, scorer=thefuzz.fuzz.token_set_ratio, limit=3
        )
        # Tokenizes (splits up) the strings before comparing them. Sorts them as well so the order of words doesn't matter. It also takes out common tokens/words.
    elif token_engine == 5:
        result = thefuzz.process.extract(
            title, search_titles, scorer=thefuzz.fuzz.partial_token_set_ratio, limit=3
        )
        # Same as token set ratio, but does it with substrings
    # For matching files you probably want it to be as similar as possible (i.e. the smaller integer options)
    # Modifying the results to use the original path instead of lower case
    new_result = [list(x) for x in result]
    for x in range(0, len(new_result)):
        ibx = numpy.where(matching[1] == new_result[x][0])
        new_result[x][0] = matching[0][ibx].item()

    return new_result


# Function to create the classes
def createClasses(titles: pandas.DataFrame, search: pandas.DataFrame):
    # Create a series of classes to store the file results
    file_classes = createFileClasses(titles)
    # Create a series of classes to store the title results
    title_classes = createTitleClasses(search)
    return (file_classes, title_classes)


# Function to get string similarity
def findSimilarity(
    file_classes: pandas.Series,
    title_classes: pandas.Series,
    titles: pandas.DataFrame,
    search_df: pandas.DataFrame,
    token_engine: int,
) -> None:
    # Create a list of files in lower case to compare to (I believe making it lower case will make them closer)
    file_titles = [x.lower() for x in list(titles["Title"])]
    # Create a numpy array with both
    file_np = numpy.array([list(titles["Title"]), file_titles])

    # Checking each file in the search df to find the best match in the file titles df
    for index, row in search_df.iterrows():
        # Getting the fuzz results comparing the searching title to the files
        result = findMatch(row["Title"].lower(), file_titles, file_np, token_engine)

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


# Function to create a dictionary to store file fuzz results
def createFileClasses(df: pandas.DataFrame) -> pandas.Series:
    temp_list = []
    for ind, row in df.iterrows():
        temp_list.append(
            FileFuzzResult(row["Path"], row["Name"], row["Title"], row["Type"], ind)
        )
    # Create hash to store the titles because they can be key breaking (I don't think they actually are, but I already implemented before I realized the true error)
    index_hash = [pathHash(x) for x in list(df["Title"])]
    temp_series = pandas.Series(data=temp_list, index=index_hash)
    return temp_series


# Function to create a dictionary to store title fuzz results
def createTitleClasses(df: pandas.DataFrame) -> pandas.Series:
    temp_list = []
    for ind, row in df.iterrows():
        temp_list.append(TitleFuzzResult(row["Title"], ind))
    # Create hash to store the titles because they can be key breaking (I don't think they actually are, but I already implemented before I realized the true error)
    index_hash = [pathHash(x) for x in list(df["Title"])]
    temp_series = pandas.Series(data=temp_list, index=index_hash)
    return temp_series


# Function to create a hash for the path strings
def pathHash(pre: str) -> str:
    return hashlib.sha256(pre.encode("utf-8")).hexdigest()


# Function to get the title results for a certain type
def getCheckValue(title_value: str, search: int) -> List[Union[str, int]]:
    # Would like to use a case statement instead of if, but I need it to work on older python
    if search == 0:
        return title_value.first_result
    elif search == 1:
        return title_value.second_result
    elif search == 2:
        return title_value.third_result


# Function to check for matching titles
def checkValue(
    file_value: str, title_value: str, search: int, score_criteria: int
) -> bool:
    # Get the result
    result = getCheckValue(title_value, search)
    # Check that file names match
    if file_value == result[0]:
        # Check that the file is above a certain score (could do this in the first conditional statement, but too bad never nesters)
        if result[1] >= score_criteria:
            return True
        else:
            return False
    else:
        return False


# Function to check if the title and files are matching
def checkMatching(
    files: pandas.Series,
    titles: pandas.Series,
    search: int,
    score_criteria: int,
    token_engine: int,
) -> pandas.Series:
    results = {"yes": 0, "no": 0}
    # Iterating through all of the files
    for ind, value in enumerate(files):
        found_file = False
        # Check each of the results to see if this file was the top match
        for ind, x_result in enumerate(value.results):
            # Check the different location depending on the search argument
            if checkValue(
                value.title, titles[pathHash(x_result[0])], search, score_criteria
            ):
                # Make sure that the title hasn't already been assigned a file
                if not titles[pathHash(x_result[0])].checkMatch():
                    # Update the title item
                    found_file = True
                    results["yes"] = results["yes"] + 1
                    # Remove the file from series (so that it wont be used in further results)
                    files = files.drop(
                        pathHash(value.title)
                    )  # Probably not the most efficient, but it's this or an if statement on every class to check if it's been used or not
                    # Add match information to to the title
                    titles[pathHash(x_result[0])].updateMatch(
                        [
                            value.path,
                            value.name,
                            value.title,
                            value.ftype,
                            getCheckValue(titles[pathHash(x_result[0])], search),
                            search,
                            score_criteria,
                            token_engine,
                        ]
                    )
                    # Could also probably save the entire class object of the file into the title, but I don't want to do that
                    # You also really only need the path and get the other name aspects from that, but I'm saving them
                    # Break from the loop to go onto the next file (don't break if the file was already used!)
                    break
        if not found_file:
            results["no"] = results["no"] + 1
    # Return the unmatched files
    print(results)
    return files


# Function to update the input dataframe with the title information
def updateInputDataframe(
    title_classes: pandas.Series, input_df: pandas.DataFrame
) -> pandas.Series:
    found_list = []
    print(len(title_classes))
    # Go through all of the titles
    for title in title_classes:
        # If the title has a match
        if len(title.match_result) != 0:
            # Update the input data frame
            input_df.loc[title.ind, "Path"] = title.match_result[1]
            # Drop the title
            found_list.append(pathHash(title.title))
    # Drop the titles when we're not iterating through the list (could be problematic)
    title_classes = title_classes.drop(found_list)
    return title_classes


# Function to check all 3 levels of matching
def checkAllMatching(
    files: pandas.Series, titles: pandas.Series, score_criteria: int, token_engine: int
) -> pandas.Series:
    files = checkMatching(files, titles, 0, score_criteria, token_engine)
    files = checkMatching(files, titles, 1, score_criteria, token_engine)
    files = checkMatching(files, titles, 2, score_criteria, token_engine)
    return files


# Function to create the logger
def createLogger(logger_name: str) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    return logger


# Function to set up CLI arguments
def createCliArgs() -> UserPaths:
    # Creating the cli arguments
    parser = argparse.ArgumentParser(
        prog="Match Titles to Files",
        description="Attempts to match titles to files.",
        epilog="Garrett Johnson (GreenBeanio) - https://github.com/greenbeanio",
    )
    parser.add_argument(
        "-i",
        "--csv_path",
        help="Path to the csv file. Default: ./titles.csv",
        type=pathlib.Path,
    )
    parser.add_argument(
        "-f",
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
    parser.add_argument(
        "-s",
        "--score_limit",
        help="What the score must be for a title and file to match. Default: 0. Must be 0 to 100",
        type=int,
        choices=range(0, 101),
        metavar="0-100",
        default=90,  # No reason for this specific limit, just a starting point
    )
    parser.add_argument(
        "-e",
        "--score_engine",
        help="What score engine to use. Default: 0. Must be 0 to 5.\n0: Ratio\n1: Partial Ratio\n2: Token Sort Ratio\n3: Partial Token Sort Ratio\n4: Token Set Ratio\n5: Partial Token Set Ratio",
        type=int,
        choices=range(0, 6),
        metavar="0-5",
        default=0,
    )
    # Getting cli arguments
    cli_args = parser.parse_args()
    # Checking the arguments
    user_args = checkArguments(cli_args)
    return user_args


# Creating the global variables (so I don't have to pass them into every function)
# Creating a logger
logger = createLogger("Title Matcher")
# Get the command line (user) arguments
user_args = createCliArgs()

################ NEW

# Create the initial data frame (source data frames)
o_input_df, o_file_df = createInitialDataframes(
    user_args.input_csv, user_args.file_directory
)


# I want to loop all of this for every score engine type...
for stage in range(0, 6):
    # If it's the first stage create the starting variables from the original inputs
    if stage == 0:
        # Creating the desired data frames
        search_df, file_titles = createDesiredDataframes(o_input_df, o_file_df)
        # Create the classes to store the data
        file_classes, title_classes = createClasses(file_titles, search_df)
    # If not create the files from the previous iterations
    else:  # NOT SURE WHAT TO CHANGE YET (MIGHT NOT EVEN HAVE TO ACTUALLY...)
        # Creating the desired data frames
        search_df, file_titles = createDesiredDataframes(o_input_df, o_file_df)
        # Create the classes to store the data
        file_classes, title_classes = createClasses(file_titles, search_df)

    # Check if there are any more files AND titles to connect
    if len(file_classes) != 0 and len(title_classes) != 0:
        # Creating series of the similarities  (I could just get the file titles from the title_classes...)
        findSimilarity(file_classes, title_classes, file_titles, search_df, stage)
        # Check if the file and titles match (returns remaining files)
        file_classes = checkAllMatching(
            file_classes, title_classes, user_args.score_limit, stage
        )
        # Update the input dataframe with the title results
        title_classes = updateInputDataframe(title_classes, o_input_df)

# Prints all matches
for x in title_classes:
    if len(x.match_result) != 0:
        print(
            f"Title: {x.title}, File: {x.match_result[1]}, Score: {x.match_result[4][1]}, Engine: {x.match_result[7]}, Limit: {x.match_result[6]}, Search: {x.match_result[5]}"
        )
input("DONE WITH NEW")

# Testing
print("FOR THE LOVE OF GOD I'M ON FIRE")
print(len(file_classes))
print(len(title_classes))
print(title_classes[1])
print(o_input_df.iloc[36])

############### OLD

# Creating the desired data frames
search_df, file_titles = createDesiredDataframes(o_input_df, o_file_df)

# Create the classes to store the data
file_classes, title_classes = createClasses(file_titles, search_df)

# Creating series of the similarities
findSimilarity(
    file_classes, title_classes, file_titles, search_df, user_args.score_engine
)

# Check if the file and titles match (returns remaining files)
file_classes = checkAllMatching(
    file_classes, title_classes, user_args.score_limit, user_args.score_engine
)

# Prints all matches
for x in title_classes:
    if len(x.match_result) != 0:
        print(
            f"Title: {x.title}, File: {x.match_result[1]}, Score: {x.match_result[4][1]}, Engine: {x.match_result[7]}, Limit: {x.match_result[6]}, Search: {x.match_result[5]}"
        )


# Footer Comment
# History of Contributions:
# [2024-2024] - [Garrett Johnson (GreenBeanio) - https://github.com/greenbeanio] - [The entire document]
