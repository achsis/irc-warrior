import os,time

def timeStamp():
    return time.strftime("%Y-%m-%d__%H_%M_%S")

class Log:
    def __init__(self, filebasename, fileVerbosity=5, screenVerbosity=4):
        self.logfile = open(filebasename + timeStamp() + ".log","w")
        self.fileVerbosity = fileVerbosity
        self.screenVerbosity = screenVerbosity
        
    def log(self, text, priority=5):
        if text[-1] != "\n":
            text = text + "\n"
        text = timeStamp() + ":" + text
        if priority <= self.fileVerbosity:
            self.logfile.write(text)
            self.logfile.flush()
        if priority <= self.screenVerbosity:
            print text.strip()           

class Env:
    log = None

def getDataFolder():
    folders = ["data","demo-data"]
    for f in folders:
        if os.path.exists(f):
            return f
    print "No data folder exists."
    exit(1)

