#!/usr/env/python
"""
## Zipper.py
##
## Description:
## Script to launch to zip every needed file for AWS Lambda, to deploy it faster.
##
"""

__author__      = "Kevin Pruvost"
__copyright__   = "Copyright 2021, GreedyBoy"
__credits__     = ["Kevin Pruvost", "Hugo Matthieu-Steinbach"]
__license__     = "Proprietary"
__version__     = "1.0.0"
__maintainer__  = "Kevin Pruvost"
__email__       = "pruvostkevin0@gmail.com"
__status__      = "Test"

import zipfile, os
zipf = "deploy.zip"

toIgnore = [
    zipf,
    ".git",
    ".idea",
    ".gitignore",
    "config_example.csv",
    "README.md",
    "logo",
    "docs",
    "docsrc",
    "logo",
    "make.bat",
    "Makefile",
    "LayersAWSLambda",
    "AOT_Compile.py",
    "AOT_Test.py",
    "JIT_Test.py",
    "GraphViewer.py",
    "GraphViewerDataMachine.py",
    "Zipper.py",
    "temp.csv",
    "data.csv",
    "candlestick_python_data.csv",
    "XDGEUR.csv",
    "XDGUSD.csv",
    # "*__pycache__",
    # "*.pyc"
]

def main():
    directory = r"./"
    wildcard_toIgnore = []
    for i in range(len(toIgnore)): 
        toIgnore[i] = r"./" + toIgnore[i]
        if "*" in toIgnore[i]:
            wildcard_toIgnore.append(toIgnore[i].split("*")[1])
    toZip(directory, wildcard_toIgnore)

def toZip(directory, wildcard_toIgnore):
    zippedHelp = zipfile.ZipFile(zipf, "w", compression=zipfile.ZIP_DEFLATED)
    addToZip(zippedHelp, directory, wildcard_toIgnore)
    zippedHelp.close()

def addToZip(zippedHelp, directory, wildcard_toIgnore):
    list = os.listdir(directory)
    for file_list in list:
        file_name = os.path.join(directory, file_list)

        if os.path.isfile(file_name):
            if file_name not in toIgnore and not any(wildcard in file_name for wildcard in wildcard_toIgnore):
                zippedHelp.write(file_name)
        elif os.path.isdir(file_name):
            if file_name not in toIgnore and not any(wildcard in file_name for wildcard in wildcard_toIgnore):
                print("Adding directory '" + file_name + "'...")
                addToZip(zippedHelp, file_name, wildcard_toIgnore)

if __name__=="__main__":
    main()