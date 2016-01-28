

class User:
    def __init__(self, name):
        self.activity = 0
        self.commented_on_activity = 0

class Users:
    def __init__(self):
        self.users = {}
        
    def add(self, nickname):
        if not nickname in self.users.keys():
            self.users[nickname] = User(nickname)
            
    def delete(self, nickname):
        del self.users[nickname]

    def activity(self, nickname):
        if nickname in self.users.keys():
            self.users[nickname].activity = self.users[nickname].activity + 5
        else:
            self.add(nickname)
            
    def tick(self):
        for k in self.users.keys():
            if self.users[k].activity > 0:
                self.users[k].activity = self.users[k].activity -1
