# -*- coding: utf-8 -*-
import argparse, socket, re, random, os, time, glob, sys, traceback, errno
from socket import error as socket_error
import socketproxy
from users import *
from messages import *
from picker import *
from environment import *
            
        

class sockpuppet:
    def __init__(self):
        random.seed()
        self.readConfig()
        self.args = self.get_args()
        self.last_reacted = {}
        self.last_triggered = {}
        Env.log = Log(self.args.logfile)
        while True:
            if self.args.proxy:
                self.sock = self.connect(self.args.server)
            else:
                print "Connect"
                host = self.args.server[:self.args.server.find(":")]
                port = int(self.args.server[self.args.server.find(":")+1:])
                print "Connect: " + host + str(port)
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print "Connect: socket"
                self.sock.connect((host, port))
                print "Connected..."
                self.out_queue = OutMessages(self.sock)
                self.reinitialize()
                self.register()
                self.ignoreOthers = False
                self.main_loop()
                Env.log.log("ERROR: Disconnected? Trying to reconnect in 10s")
                time.sleep(10)

    def substitute(self, line):
        return line.replace("%n",self.args.nick)

    def reinitialize(self):
        print "Re-loading data..."
        self.users = Users()
        self.active_channels=[]
        self.authorized_users = readFile(os.path.join(getDataFolder(), "authorized.dat"))
        self.greet_users=readFile(os.path.join(getDataFolder(), "greet_users.dat"))
        self.annoy_users=readFile(os.path.join(getDataFolder(), "annoy_users.dat"))
        self.handler = {}
        self.handler_system = {}
        for f in glob.glob(os.path.join(getDataFolder(), "trigger/*.txt")):
            word = f[len(os.path.join(getDataFolder(), "trigger/")):-4]
            self.handler[re.compile("^PRIVMSG (.+) :\s*(" + word + ")[sz]*[\s$,\.?!].*",re.I)] = self.trigger
            self.handler[re.compile("^PRIVMSG (.+) :[^^#!~]+.*\s+(" + word + ")[sz]*[\s$,\.?!].*", re.I)] = self.trigger
            self.last_triggered[word] = 0

        for f in glob.glob(os.path.join(getDataFolder(), "react/*.txt")):
            word = f[len(os.path.join(getDataFolder(), "react/")):-4]
            self.handler[re.compile("^PRIVMSG (.+) :\s*(" + word + ")[sz]*[\s$,\.?!].*",re.I)] = self.react
            self.handler[re.compile("^PRIVMSG (.+) :[^^#!~]+.*\s+(" + word + ")[sz]*[\s$,\.?!].*", re.I)] = self.react
            self.last_reacted[word] = 0
        self.handler[re.compile("^PRIVMSG ([#!&]..*) :#smake\s+([^\s]+)\s+(.*)$")] = self.smake
        self.handler[re.compile("^PRIVMSG .*")] = self.activity
        self.handler[re.compile("^PRIVMSG " + self.args.nick + " :reflect (..*)")] = self.reflect
        self.handler[re.compile("^PRIVMSG (" + self.args.nick + ") :discussNow ([!#&][^ ]*)")] = self.discussNow
        self.handler[re.compile("^PRIVMSG " + self.args.nick + " :reinit.*")] = self.reinit
        self.handler[re.compile("^PRIVMSG " + self.args.nick + " :sayto ([^:,]+)[:,](..*)")] = self.sayto
        self.handler[re.compile("^PRIVMSG " + self.args.nick + " :do ([^:,]+)[:,](..*)")] = self.do
        self.handler[re.compile("^PRIVMSG " + self.args.nick + " :join (..*)")] = self.join
        self.handler[re.compile("^PRIVMSG " + self.args.nick + " :quit.*")] = self.quit_bob
        self.handler[re.compile("^PRIVMSG ([#!&].*) :([^ ]*)\+\+.*")] = self.see_karma
        self.handler[re.compile("^PRIVMSG ([#!&].*) :([^ ]*)--.*")] = self.see_bad_karma
        self.handler[re.compile("^PRIVMSG ([#!&].*) :\s*\+\+([^ ]*)[$ ,!?\.].*")] = self.see_karma
        self.handler[re.compile("^PRIVMSG ([#!&].*) :\s--([^ ]*)[$ ,!?\.].*")] = self.see_bad_karma
        self.handler_system[re.compile("^PING (.*)")] = self.ping
        self.handler_system[re.compile("^NOTICE " + self.args.nick + " :.*identify via .*")] = self.identify

    def readConfig(self):
        conf = readFile(os.path.join(getDataFolder(), "config.dat"))
        self.conf = {}
        confRe = re.compile("^\s*([^\s=]+)\s*=\s*(.*)$")
        for l in conf:
            m = confRe.match(l.strip())
            if None != m:
                self.conf[m.group(1)]=m.group(2)

    def getConf(self, prop):
        if prop in self.conf.keys():
            return self.conf[prop]
        return "undefined"
    
    def get_args(self):
        parser = argparse.ArgumentParser(description='Helper to build a socket army in IRC chats')
        parser.add_argument('--server', default = self.getConf("server"), help='domain-name/port of IRC server')
        parser.add_argument('--host', default=self.getConf("host"), help='desired hostname')
        parser.add_argument('--client_server', default=self.getConf("client_server"), help='desired client server name')
        parser.add_argument('--user', default=self.getConf("user"), help='desired username in channel')
        parser.add_argument('--nick', default=self.getConf("nick"), help='desired nickname in channel')
        parser.add_argument('--nickservpwd', default=self.getConf("nickservpwd"), help='NickServ password for this user')
        parser.add_argument('--password', default=self.getConf("password"), help='password (if required for this server)')
        parser.add_argument('--realname', default=self.getConf("realname"), help='"Real Name" of the script')
        parser.add_argument('--logfile', default=self.getConf("logfile"), help='Logfile; should log anything sent or received')
        parser.add_argument('--proxy', dest='feature', action='store_true')
        parser.set_defaults(proxy=False)
        args = parser.parse_args()
        return args

    def activity(self, message, m):
        self.users.activity(message.nick)
    
    def ping(self, message, m):
        self.enqueue("PONG " + m.group(1),0)

    def see_karma(self, message, m):
        print "Triggered see_karma " + message.message
        i = random.randint(0,100)
        destination = m.group(1)
        if not m.group(1)[0:1] in "#&!":
            destination = message.nick
        print m.group(2)+ " " + str(i)
        result = pick_random_delayed(os.path.join(getDataFolder(), "karma/" + m.group(2).lower() + ".txt"), message, m.group(2))
        for t in result:
            (te,ti) = t
            self.enqueue("PRIVMSG " + destination + " :" + te, ti)

    def see_bad_karma(self, message, m):
        print "Triggered see_bad_karma " + message.message
        i = random.randint(0,100)
        print m.group(2)+ " " + str(i)
        destination = m.group(1)
        if not m.group(1)[0:1] in "#&!":
            destination = message.nick
        filename = m.group(2).lower()
        if filename == self.args.nick.lower():
            filename = "mynick"
            self.increase_own_karma(message, m)
        result = pick_random_delayed(os.path.join(getDataFolder(), "bad_karma/" + filename + ".txt"), message, m.group(2))
        for t in result:
            (te,ti) = t
            te = self.substitute(te)
            self.enqueue("PRIVMSG " + destination + " :" + te, ti)

    def increase_own_karma(self, message, m):
        destination = m.group(1)
        if not m.group(1)[0:1] in "#&!":
            destination = message.nick
        self.enqueue("NICK " + self.args.nick + "_" + str(random.randint(1,100000)) + "\n",1)
        self.enqueue("PRIVMSG " + destination + " :" + self.args.nick + "++\n", 1)
        self.enqueue("NICK " + self.args.nick + "\n",1)
        
    def trigger(self, message, m):
        print "Triggered trigger " + message.message
        i = random.randint(0,200)
        print m.group(2)+ " " + str(i)
        destination = m.group(1)
        if m.group(1)[0:1] in "#&!":
            if i == 1:
                self.discuss(message,m)
                return
        else:
            destination = message.nick

        word = m.group(2).lower()
        now = int(time.time())
        if word in self.last_triggered.keys():
            if now - self.last_triggered[word] < 10:
                Env.log.log("Word " + word + " was triggered already less than 7s ago. Ignore this time.")
                return
        self.last_triggered[word] = now 
                        
        result = pick_random_delayed(os.path.join(getDataFolder(), "trigger/" + m.group(2).lower() + ".txt"), message, m.group(2))
        for t in result:
            (te,ti) = t
            self.enqueue("PRIVMSG " + destination + " :" + te, ti)
        
    def react(self, message, m):
        print "Triggered react " + message.message
        print m.group(2)
        word = m.group(2).lower()
        now = int(time.time())
        if word in self.last_reacted.keys():
            if now - self.last_reacted[word] < 10:
                Env.log.log("Word " + word + " was triggered already less than 7s ago. Ignore this time.")
                return
        self.last_reacted[word] = now 
        destination = m.group(1)
        if not m.group(1)[0:1] in "#&!":
            destination = message.nick
            
        result = pick_random_delayed(os.path.join(getDataFolder(), "react/" + m.group(2).lower() + ".txt"), message, m.group(2))
        for t in result:
            (te,ti) = t
            self.enqueue("PRIVMSG " + destination + " :" + te, ti)
        
    def smake(self, message, m):
        if m.group(2)==self.args.nick:
            self.enqueue("PRIVMSG " + m.group(1) + " :" + u'\u0001' + "ACTION ducks fast" + u'\u0001',0)
            self.enqueue("PRIVMSG " + m.group(1) + " :#smake " + message.nick + " with a rotten fish of justice", 1)
            
    def reflect(self, message, m):
        if message.nick in self.authorized_users:
            self.enqueue(m.group(1),0)
            self.enqueue("PRIVMSG " + message.nick + " :Yes, my lord, certainly.", 0)
        else:
            self.enqueue("PRIVMSG " + message.nick + " :No. Not for You!", 0)

    def reinit(self, message, m):
        if message.nick in self.authorized_users:
            self.reinitialize()
            self.enqueue("PRIVMSG " + message.nick + " :Yes, my lord, certainly.", 0)
        else:
            self.enqueue("PRIVMSG " + message.nick + " :No. Not for You!", 0)

    def sayto(self, message, m):
        if message.nick in self.authorized_users:
            self.enqueue("PRIVMSG " + m.group(1) + " :" + m.group(2),0)
            self.enqueue("PRIVMSG " + message.nick + " :Yes, my lord, certainly.", 0)
        else:
            self.enqueue("PRIVMSG " + message.nick + " :No. Not for You!", 0)

    def quit_bob(self, message, m):
        if message.nick in self.authorized_users:
            print "Exiting on " + message.nick + " request..."
            exit(0)

    def do(self, message, m):
        if message.nick in self.authorized_users:
            self.enqueue("PRIVMSG " + m.group(1) + " :" + u'\u0001' + "ACTION " + m.group(2).strip() + u'\u0001' + "\n",0)
            self.enqueue("PRIVMSG " + message.nick + " :Yes, my lord, certainly.", 0)
        else:
            self.enqueue("PRIVMSG " + message.nick + " :No. Not for You!", 0)

    def join(self, message, m):
        if message.nick in self.authorized_users:
            self.enqueue("PRIVMSG " + message.nick + " :Yes, my lord, certainly.", 0)
            self.enqueue("JOIN " + m.group(1),0)
        else:
            self.enqueue("PRIVMSG " + message.nick + " :No. Not for You!", 0)
            print message.nick + " not in " + str(self.authorized_users)

    def discussNow(self, message, m):
        if message.nick in self.authorized_users:
            self.enqueue("PRIVMSG " + message.nick + " :Yes, my lord, certainly.", 0)
            self.discuss(message, m, m.group(2))
        else:
            self.enqueue("PRIVMSG " + message.nick + " :No. Not for You!", 0)

    def discuss(self, message, m, group = None):
        files = glob.glob(os.path.join(getDataFolder(), "discuss/*.txt"))
        print "Files: " + str(files)
        if len(files) <= 0:
            return
        f = files[random.randint(0,len(files)-1)]
        discuss = readFile(f)
        i = random.randint(4,6)
        if None != group:
            Env.log.log("Discuss target: " + group)
            target = group
        else:
            target = m.group(1)
            
        for l in discuss:
            l = substitute(l, message, "")
            self.enqueue("PRIVMSG " + target + " :" + l, i)
            i = i + random.randint(3,5)
        self.ignoreOthers = True
        
    def identify(self, message, m):
        if len(self.args.nickservpwd) > 0:
            self.enqueue("PRIVMSG NickServ :identify " + self.args.nickservpwd, 3)

    def connect(self,server):
        host = server[:server.find(":")]
        port = int(server[server.find(":")+1:])
        s = socketproxy.connect((host, port))
        if None == s:
            print "Failed to connect via proxy"
            exit(-1)
        print "Connected to " + str(s)
        return s

    def register(self):
        if len(self.args.password) > 0:
            self.enqueue("PASS " + self.args.password + "\n",2)
        self.enqueue("NICK " + self.args.nick + "\n",2)
        self.enqueue("USER " + self.args.nick + " " + self.args.host + " " + self.args.client_server + " :" + self.args.realname + "\n",4)
        init = readFile(os.path.join(getDataFolder(), "init.dat"))
        reInit = re.compile("^(\d*),\s*(.*)$")
        for l in init:
            m = reInit.match(l)
            if None != m:
                self.enqueue(m.group(2), int(m.group(1))+4)

    def enqueue(self, msg, countdown):
        self.out_queue.add(msg,countdown)

    def handle(self, msg):
        Env.log.log("<" + msg)
        message = Message(msg)
        if message.nick == self.args.nick:
            #ignore own messages
            return
        for k in self.handler_system.keys():
            m = k.match(message.message)
            if None != m:
                self.handler_system[k](message, m)
        if not self.ignoreOthers:
            for k in self.handler.keys():
                m = k.match(message.message)
                if None != m:
                    self.handler[k](message, m)

    def main_loop(self):
        msg = ""
        msg_new = ""
        self.sock.setblocking(0)
        self.connectionTimeout = 100 #Expect at least server PING at least once every 3 minutes
        while True:
            try:
                msg_new = self.sock.recv(100)
                self.connectionTimeout = 100 #Expect at least server PING at least once every 3 minutes
            except socket_error as serr:
                if serr.errno==11:
                    if self.connectionTimeout == 0:
                        self.enqueue("PING :SoylenBob", 0)
                    self.connectionTimeout = self.connectionTimeout - 1
                    if self.connectionTimeout < -10:
                        Env.log.log("Connection timeout? Sent PING 10s ago, nothing received ever since. Expected at least a PONG")
                        break
                    
                    time.sleep(1)
                    self.out_queue.tick()
                    if self.out_queue.empty():
                        self.ignoreOthers = False
                    continue
                else:
                    Env.log.log("Socket error:" + str(serr.errno))
                    break

            except Exception as ex:
                message = template.format(type(ex).__name__, ex.args)
                print message
                einfo = traceback.format_exc()
                Env.log.log("Exception info: " + einfo)
                break
             
            if len(msg_new) == 0:
                continue
            
            msg = msg + msg_new
            npos = msg.find("\n")
            while  npos > 0:
                self.handle(msg[:npos])
                msg = msg[npos+1:]
                npos = msg.find("\n")


sock = sockpuppet()
