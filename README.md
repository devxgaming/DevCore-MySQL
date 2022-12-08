# What is DevCore?
DevCore is a translate library for MySQL database to work with Python classes
* Create Python class as database table
* Set & Get data as python objects.
* Control your database table from python class
* Allow you to use custom MySQL commands
* Custom functions and variables in table class
* Stay online with MySQL server

🟡 Warning: You should import the library from main thread. don't use threading to import it


# Required library
* pip install pymysql

# Example
Create your own python script file for your database tables.

```py
from DevCore import MySQL, Table

databaseName = 'YourDatabaseName' # if not exists, new one will created

# only once for fist class, you should set mysql info.
@MySQL(databaseName, host='localhost', user='root', password='')
class Users(Table):
    id = Table.intField(auto=True) # auto (required) for each table.
    name = Table.strField(null=True) # allow column value be null, default: False
    username = Table.strField()
    password = Table.strField()


# another table on same database, not need to set mysql info for same database.
@MySQL(databaseName)
class TableName(Table):
    id = Table.intField(auto=True)
    another = Table.dictField()
```

main application

```py
# import your own file
from yourownfile import * # connect to all MySQL database. can block main thread

class MainApplication:
    def __init__(self):
        self.users = Users() # will not block main thread.
        self.other = TableName() # will not block main thread.
    
    def get_user(self, user):
        return self.users.where('username').equals(user).first()
        # return class Users or none if not found.
    
    def get_user_and_password(self, user, password):
        return self.users.where('useranme').equals(user).andWhere('password').equals(password).first()
        # return class Users or none if not found.
```


custom mysql command and functions in table
```py
@MySQL(databaseName, host='localhost', user='root', password='')
class Users(Table):
    id = Table.intField(auto=True) # auto (required) for each table.
    name = Table.strField(null=True) # allow column value be null, default: False
    username = Table.strField()
    password = Table.strField()

    # ignore variables
    # create variable that the value is not instance from Field class
    # create normal python variable types to ignore it.
    # for example
    online = False # bool
    key = 'value' # str

    # custom functions and MySQL command.

    def get_all(self):
        return self.execute(f'SELECT * FROM {self.tableName}').all()
        # return list of Users class or empty list.

    def find_user(self, user):
        return self.execute(f'SELECT * FROM {self.tableName} where username=:user', {'user': user}).first()
        # return first query as Users class or none.

    def update_user_name(self, username, name):
        self.execute(f'UPDATE {self.tableName} set name=:name where username=:user', {'user': username, 'name': name}).run()
        # if command is insert, run function will return lastrowid, else return rowcount
```

main application
```py
from yourownfile import * # connect to all MySQL database. can block main thread.

users = Users() # will not block main thread.

ls = users.get_all()
for user in ls:
    print(user.id, user.name, user.username, user.password)

user = users.find_user('username')
if user:
    users.update_user_name(user.username, 'NewName')
    # or
    user.name = 'NewName'
    user.save()
    # or delete it
    user.delete()
else:
    users.name = 'Dev'
    users.password = 'Password'
    users.username = 'Username'
    rowid = users.save() # insert new. return last row id

# not good with MySQL commands? don't warry, use where class.

user = users.where('username').equals('user').first()
if user:
    user.name = 'New name'
    user.save() # change user 'name' value to 'New name'
else:
    print('User not found')

```


# `MySQL` decorator

| args | default | type | description
--- | --- | --- | ---
host | `None` | `str` | MySQL host ip 
user | `None` | `str` | MySQL username
password | `blank` | `str`|MySQL password
charset | `utf8mb4`| `str`|MySQL database & table charset
collate | `utf8mb4_bin`| `str`|MySQL table collate
dropColumn | `False` | `bool` | drop column if variable not in your class, make sure to set it `False` after start application
addColumn | `False` | `bool` | add column if column not exists in database table and is exists as variable in your class, make sure to set it `False` after start application

<br><br>

# `Table` class + (Your Class)

| functions | args | return | description
--- | ---- | ----| ---- |
| where | variable: `str` | Where `class` | MySQL commands helper
| execute | command: `str`, args: `dict` | execute `class` | execute MySQL command
| save | `None` | `int`: rowcount or lastrowid | save changes to database table
| delete | `None` | `int`: deleted row id | delete the row from database table


# (`Table`.`where` function) -> `Where` class
| function | args | return | description | MySQL 
--- | --- | --- | --- | ---
orWherer | variable: `str` | self | `or` operator | `or columnName`
andWhere | variable: `str` | self | `and` operator | `and columnName`
equals | value: `Union[str, int, float, bool]` | self | `=` operator | `= value`
notEquals | value: `Union[str, int, float, bool]` | self | `!=` operator |`!= value`
like | value: `Union[str, int, float, bool]` | self | `LIKE` operator | `LIKE value`
notLike | value: `Union[str, int, float, bool]` | self | `NOT LIKE` operator |`NOT LIKE value`
moreThan | value: `Union[int, float]` | self | `>` operator | `> value`
moreThanOrEquals | value: `Union[int, float]` | self | `>=` operator | `>= value`
lessThan | value: `Union[int, float]` | self | `<` operator | `< value`
lessThanOrEquals | value: `Union[int, float]` | self | `<=` operator | `<= value`
notNull | `None` | self | `NOT NULL` operator | `column NOT NULL`
isNull | `None` | self | `IS NULL` operator | `column IS NULL`
iN | `value: tuple` | self | `IN` operator | `IN (tuple value, tuple value)`
between | value: `Union[str, int, float, bool]`, value2: `Union[str, int, float, bool]` | self | `between` operator | `between value and value2`
orderBy | variable: `str`, stuff=`"asc"`, limit=`0` | self | sort by variable `asc` default, limit=`0` unlimited | `ORDER BY variable ASC` or `ORDER BY variable ASC limit number`
first | `None` | Your table class or None | first row from result | `Unknown`
all | `None` | list of your table class or empty list | all row from result | `Unknown`


# (`Table`.`execute` function) -> Execute class

| function | args | return | description
--- | --- | --- | ---
all | `None` | list of your class or `empty list` | execute your command and get result as list of your class
first | `None` | Your class or `None` | execute your command and get first row result as your class or None
run | `None` | `int` last row id or row count | execute your command

# (`Table.Fields` class)

| static method | args | MYSQL | convert
--- | --- | --- | ---
intField | auto=`False` null=`False` | `integer`, auto `AUTO_INCREMENT PRIMARY KEY NOT NULL`, null `allow the value be null` | always int
strField | null=`False`, default=`None` | `longtext`, null `allow the value be null`, default `default value` | always str.
floatField | // | `REAL`, // | auto convert to python `float`
listField | // | `longtext`, // | auto convert to python `list`
dictField | // | `//`, // | auto convert to python `dict`
boolField | // | `//`, // | auto convert to python `boolean`




