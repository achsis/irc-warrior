import socket
from environment import *

class OutMessage:
    def __init__(self, msg, countdown):
        self.message = msg
        self.countdown = countdown

class OutMessages:
    def __init__(self, sock):
        self.messages = []
        self.sock = sock
    def add(self, msg, countdown):
        if msg[-1:] != "\n":
            msg = msg + "\n"
        if countdown == 0:
            self.__send(msg)
        else:
            Env.log.log("|" + msg)
            self.messages.append(OutMessage(msg,countdown))

    def empty(self):
        return len(self.messages) == 0
    
    def tick(self):
        i = 0
        while i < len(self.messages):
            if self.messages[i].countdown > 0:
                self.messages[i].countdown = self.messages[i].countdown - 1
                i = i + 1
            else:
                self.__send(self.messages[i].message)
                del self.messages[i]
                
    def __send(self, message):
        Env.log.log(">" + message)
        self.sock.send(message)
        

class Message:
    def __init__(self, msg):
        self.user = ""
        self.nick = ""
        self.hostname = ""
        self.server = ""
        self.message = ""
        self._parse(msg)
        self.dump()

    def dump(self):
        prio = 6
        Env.log.log("nick : " + self.nick, prio)
        Env.log.log("user : " + self.user, prio)
        Env.log.log("hostname : " + self.hostname, prio)
        Env.log.log("server : " + self.server, prio)
        Env.log.log("message : " + self.message, prio)
        
    def _parse(self, msg):
        if msg.find(":") == 0 and msg.find(" ") > 0:
            #There is a prefix present (usually is...)
            prefix = msg[1:msg.find(" ")]
            if prefix.find("@") > 0:
                self.hostname = prefix[prefix.find("@") + 1:]
                prefix = prefix[:prefix.find("@")]
            if prefix.find("!") > 0:
                self.user = prefix[prefix.find("!") + 1:]
                prefix = prefix[:prefix.find("!")]
            if prefix.find(".") > 0:
                self.server = prefix
            else:
                self.nick = prefix
            self.message = msg[msg.find(" ") + 1:]
        else:
            self.message = msg
