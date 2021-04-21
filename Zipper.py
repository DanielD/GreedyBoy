##
## DEPLOYER
##

import zipfile, os
zipf = "deploy.zip"

toIgnore = [
    zipf,
    ".git",
    ".idea",
    "__pycache__",
    ".gitignore",
    "config_example.csv",
    "README.md",
    "requirements.txt"
]

def main():
    directory = r"./"
    for i in range(len(toIgnore)):
        toIgnore[i] = "./" + toIgnore[i]
    toZip(directory)

def toZip(directory):
    zippedHelp = zipfile.ZipFile(zipf, "w", compression=zipfile.ZIP_DEFLATED)

    list = os.listdir(directory)
    for file_list in list:
        file_name = os.path.join(directory,file_list)

        if os.path.isfile(file_name):
            print(file_name)
            if file_name not in toIgnore:
                zippedHelp.write(file_name)
        else:
            if file_name not in toIgnore:
                addFolderToZip(zippedHelp,file_list,directory)
            print("---------------Directory Found-----------------------")
    zippedHelp.close()

def addFolderToZip(zippedHelp,folder,directory):
    path=os.path.join(directory,folder)
    print(path)
    file_list=os.listdir(path)
    for file_name in file_list:
        file_path=os.path.join(path,file_name)
        if os.path.isfile(file_path):
            zippedHelp.write(file_path)
        elif os.path.isdir(file_name):
            print("------------------sub directory found--------------------")
            addFolderToZip(zippedHelp,file_name,path)


if __name__=="__main__":
    main()