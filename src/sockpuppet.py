import argparse, socket, re, random, os, time, glob
import socketproxy
from users import *
from messages import *
from picker import *
from environment import *
            
        

class sockpuppet:
    def __init__(self):
        random.seed()
        self.args = self.get_args()

        if len(self.args.logfile) > 0:
            self.logfile = open(self.args.logfile,"w")
        else:
            self.logfile = open("raw.log","a")
            
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
        self.out_queue = OutMessages(self.sock, self.logfile)
        self.reinitialize()
        self.register()
        self.ignoreOthers = False
        self.main_loop()

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
            self.handler[re.compile("^PRIVMSG (.+) :.+\s+(" + word + ")[sz]*[\s$,\.?!].*", re.I)] = self.trigger
        for f in glob.glob(os.path.join(getDataFolder(), "react/*.txt")):
            word = f[len(os.path.join(getDataFolder(), "react/")):-4]
            self.handler[re.compile("^PRIVMSG (.+) :\s*(" + word + ")[sz]*[\s$,\.?!].*",re.I)] = self.react
            self.handler[re.compile("^PRIVMSG (.+) :.+\s+(" + word + ")[sz]*[\s$,\.?!].*", re.I)] = self.react
        self.handler[re.compile("^PRIVMSG .*")] = self.activity
        self.handler[re.compile("^PRIVMSG " + self.args.nick + " :reflect (..*)")] = self.reflect
        self.handler[re.compile("^PRIVMSG " + self.args.nick + " :reinit.*")] = self.reinit
        self.handler[re.compile("^PRIVMSG " + self.args.nick + " :sayto ([^:,]+)[:,](..*)")] = self.sayto
        self.handler[re.compile("^PRIVMSG " + self.args.nick + " :do ([^:,]+)[:,](..*)")] = self.do
        self.handler[re.compile("^PRIVMSG " + self.args.nick + " :join (..*)")] = self.join
        self.handler[re.compile("^PRIVMSG " + self.args.nick + " :quit.*")] = self.quit_bob
        self.handler[re.compile("^PRIVMSG ([#!&]..*) :([^ ]*)\+\+.*")] = self.see_karma
        self.handler_system[re.compile("^PING (.*)")] = self.ping
        self.handler_system[re.compile("^NOTICE " + self.args.nick + " :.*identify via .*")] = self.identify
        
    def get_args(self):
        parser = argparse.ArgumentParser(description='Helper to build a socket army in IRC chats')
        #parser.add_argument('--server', default='chat.soylentnews.org:6667', help='domain-name/port of IRC server')
        parser.add_argument('--server', default='localhost:6667', help='domain-name/port of IRC server')
        parser.add_argument('--host', default='0', help='desired hostname')
        parser.add_argument('--client_server', default='*', help='desired client server name')
        parser.add_argument('--user', default='irc-warrior', help='desired username in channel')
        parser.add_argument('--nick', default='IrcWarrior', help='desired nickname in channel')
        parser.add_argument('--nickservpwd', default='', help='NickServ password for this user')
        parser.add_argument('--password', default='', help='password (if required for this server)')
        parser.add_argument('--realname', default='Puppet Master', help='"Real Name" of the script')
        parser.add_argument('--logfile', default='', help='Logfile; should log anything sent or received')
        parser.add_argument('--proxy', dest='feature', action='store_true')
        parser.set_defaults(proxy=False)
        args = parser.parse_args()
        return args

    def activity(self, message, m):
        self.users.activity(message.nick)
    
    def ping(self, message, m):
        self.send("PONG " + m.group(1))

    def see_karma(self, message, m):
        i = random.randint(0,100)
        print m.group(2)+ " " + str(i)
        (te,ti) = pick_random_delayed(os.path.join(getDataFolder(), "karma/" + m.group(2).lower() + ".txt"), message, m.group(2))
        if len(te) > 0:
            self.enqueue("PRIVMSG " + m.group(1) + " :" + te, ti)

    def trigger(self, message, m):
        i = random.randint(0,200)
        print m.group(2)+ " " + str(i)
        destination = m.group(1)
        if m.group(1)[0:1] in "#&!":
            if i == 1:
                self.discuss(message,m)
                return
        else:
            destination = message.nick
            
        (te,ti) = pick_random_delayed(os.path.join(getDataFolder(), "trigger/" + m.group(2).lower() + ".txt"), message, m.group(2))
        if len(te) > 0:
            self.enqueue("PRIVMSG " + destination + " :" + te, ti)
        
    def react(self, message, m):
        print m.group(2)
        destination = m.group(1)
        if not m.group(1)[0:1] in "#&!":
            destination = message.nick
            
        (te,ti) = pick_random_delayed(os.path.join(getDataFolder(), "react/" + m.group(2).lower() + ".txt"), message, m.group(2))
        if len(te) > 0:
            self.enqueue("PRIVMSG " + destination + " :" + te, ti)
        
        
    def reflect(self, message, m):
        if message.nick in self.authorized_users:
            self.send(m.group(1))
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
            self.send("JOIN " + m.group(1))
            self.enqueue("PRIVMSG " + message.nick + " :Yes, my lord, certainly.", 0)
        else:
            self.enqueue("PRIVMSG " + message.nick + " :No. Not for You!", 0)
            print message.nick + " not in " + str(self.authorized_users)

    def discuss(self, message, m):
        files = glob.glob(os.path.join(getDataFolder(), "discuss/*.txt"))
        print "Files: " + str(files)
        if len(files) <= 0:
            return
        f = files[random.randint(0,len(files)-1)]
        discuss = readFile(f)
        i = random.randint(4,6)
        for l in discuss:
            l = substitute(l, message, "")
            self.enqueue("PRIVMSG " + m.group(1) + " :" + l, i)
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

    def enqueue(self, msg, countdown):
        if msg[-1:] != "\n":
            msg = msg + "\n"
        print "Enqueued: " + msg
        self.out_queue.add(msg,countdown)

    def send(self,msg):
        print msg
        if msg[-1:] != "\n":
            msg = msg + "\n"
        self.sock.send(msg)

    def handle(self, msg):
        self.logfile.write("<" + msg + "\n")
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
        while True:
            try:
                msg_new = self.sock.recv(100)
            except:
                time.sleep(1)
                self.out_queue.tick()
                if self.out_queue.empty():
                    self.ignoreOthers = False
                continue
            
            if len(msg_new) == 0:
                continue
            
            msg = msg + msg_new
            npos = msg.find("\n")
            while  npos > 0:
                self.handle(msg[:npos])
                msg = msg[npos+1:]
                npos = msg.find("\n")


sock = sockpuppet()
