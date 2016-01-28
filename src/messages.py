import socket

class OutMessage:
    def __init__(self, msg, countdown):
        self.message = msg
        self.countdown = countdown

class OutMessages:
    def __init__(self, sock, log):
        self.messages = []
        self.sock = sock
        self.logfile = log
    def add(self, msg, countdown):
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
                print "Sending: " + self.messages[i].message
                if None != self.logfile:
                    self.logfile.write(self.messages[i].message + "\n")
                self.sock.send(self.messages[i].message)
                del self.messages[i] 

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
        print "nick : " + self.nick
        print "user : " + self.user
        print "hostname : " + self.hostname
        print "server : " + self.server
        print "message : " + self.message
        
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
