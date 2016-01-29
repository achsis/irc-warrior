import os,re,random,time
from environment import *


def readFile(filename):
    if not os.path.exists(filename):
        print filename + " expected, but does not exist. Treat as empty file."
        return []
    f = open(filename,"r")
    lines = f.readlines()
    f.close()
    i = 0
    while i < len(lines):
        lines[i] = lines[i].strip()
        if lines[i].find("#") == 0:
            del lines[i]
            continue
        if len(lines[i]) == 0:
            del lines[i]
            continue
        i = i + 1
    return lines
    
def substitute(msg, message, word = ""):
    reSubst = re.compile("^([^,][^,]*),(\d\d*),(.*)")
    lines = readFile(getDataFolder() + "/substitutions.dat")
    for l in lines:
        m = reSubst.match(l)
        if None != m:
            p = int(m.group(2))
            i = random.randint(0,1000)
            if i > p:
                continue
            options = m.group(3).split(";")
            if len(options) == 0:
                options[0]=""
            msg = msg.replace(m.group(1), options[random.randint(0,len(options))-1])
    msg = msg.replace("%U",message.nick)
    msg = msg.replace("%u",message.nick)
    msg = msg.replace("%w",word)
    msg = msg.replace("%W",word)
    return msg

def pick_random_delayed(filename, message, word):
    if os.path.exists(filename):
        print "Opening file " + filename
        delayRe = re.compile("(\d\d*),(\d\d*)  *(.*)")
        probabilityRe = re.compile("probability:(\d\d*)")
        lines = readFile(filename)
        if len(lines) < 1:
            return []
            
        m = probabilityRe.match(lines[0])
        probability = 50
        if None != m:
            probability = int(m.group(1))
            del lines[0]
                
        i = random.randint(0, 100)
        print "probability = " + str(probability) + ", i = " + str(i)
        if i > probability:
            print "probability = " + str(probability)
            return []
            
        choice = lines[random.randint(0,len(lines)-1)]
        choice = substitute(choice, message, word)
        m = delayRe.match(choice)
        ti = 0
        if None != m:
            print "Match: " + choice
            ti = random.randint(int(m.group(1)),int(m.group(2)))
            te =  m.group(3)
        else:
            print "No Match: " +  choice
            ti = random.randint(3,6)
            te =  choice

        choices = te.split("\\n")
        result = []
        for c in choices:
            result.append((c,ti))
            ti=ti + len(te)/8 + 1
        return result
    else:
        print "Missing file " + filename
    return []

