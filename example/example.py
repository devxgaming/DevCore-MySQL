from DevCore import MySQL, Table

databaseName = 'ExampleDatabase'

@MySQL(databaseName, host='localhost', user='root', password='1234567x')
class MyTable(Table):
    id = Table.intField(auto=True)
    username = Table.strField()
    password = Table.strField()



class Main:
    def __init__(self) -> None:
        self.start()
        
    def start(self):
        inp = input('Select command: [insert, delete, update, close]: ')
        if inp == 'insert':
            self.insert()
        elif inp == 'delete':
            self.delete()
        elif inp == 'update':
            self.update()
        elif inp == 'close':
            return
        else:
            print('Unknown command')
            self.start()
    
    def insert(self):
        username = input('Username: ')
        password = input('Password: ')
        if not username or not password:
            print('Error, please set username or password')
            self.insert()
            return
        user = MyTable()
        find = user.where('username').equals(username).first()
        if find:
            print(f'User {username} is already registered.')
            self.start()
            return
        user.username = username
        user.password = password
        user.save()
        print(f'User {username} has successfully registered.')
        self.start()
    
    def delete(self):
        username = input('Enter username to delete: ')
        if not username:
            print('Username should not be empty.')
            self.delete()
            return
        user = MyTable()
        find = user.where('username').equals(username).first()
        if find:
            find.delete()
            print(f'User {username} has been deleted.')
            self.start()
            return
        else:
            print(f'User {username} not found.')
            self.delete()
    
    def update(self):
        username = input('Username: ')
        password = input('New password: ')
        if not username or not password:
            print('Username or password should not be empty.')
            self.update()
            return
        user = MyTable()
        find = user.where('username').equals(username).first()
        if find:
            find.password = password
            find.save()
            print(f'Password for {username} has successfully changed.')
            self.start()
            return
        else:
            print(f'user {username} not found')
        
Main()
