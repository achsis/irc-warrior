import os

def getDataFolder():
    folders = ["data","demo-data"]
    for f in folders:
        if os.path.exists(f):
            return f
    print "No data folder exists."
    exit(1)

