
import pymysql
import warnings
from typing import Union
import time

ConnectionWrapper = {}

class Style():
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

class Logger:
    @staticmethod
    def warning(text):
        print(Style.YELLOW + str(text) + Style.RESET)
    
    def log(text):
        print(Style.RESET + str(text) + Style.RESET)
    
    def error(text):
        print(Style.RED + str(text) + Style.RESET)
    
    def success(text):
        print(Style.GREEN + str(text) + Style.RESET)

class DatabaseException(Exception):
    ""

class FieldExecption(Exception):
    ""

class TypeError(Exception):
    ""
    
class SmartDict(dict):
    def __init__(self, *args, **kwargs):
        super(SmartDict, self).__init__()
        [self.update(arg) for arg in args if isinstance(arg, dict)]
        self.update(kwargs)
    
    def __getattr__(self, attr):
        if attr in self:
            return self.get(attr)
        return None
    
    def __getitem__(self, key):
        if key in self:
            return super().__getitem__(key)
        return None
    
    def __setattr__(self, name: str, value):
        self.__setitem__(name, value)
    

class _Instance:
    @staticmethod
    def getDatabase(table):
        for db in ConnectionWrapper:
            find = ConnectionWrapper[db]
            if table in find['Classes']:
                return find['Handler']
        return None

    @staticmethod
    def getSettings(table):
        for db in ConnectionWrapper:
            find = ConnectionWrapper[db]
            if table in find['Classes']:
                return find['Settings']
        return None

    @staticmethod
    def connect(name, **kwargs):
        try:
            conn = pymysql.connect(host=kwargs.get('host'),
                                   user=kwargs.get('user'),
                                   password=kwargs.get('password'),
                                   charset=kwargs.get('charset') or 'utf8mb4',
                                   autocommit=True,
                                   cursorclass=pymysql.cursors.DictCursor)
            with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    charset = kwargs.get('charset') or 'utf8mb4'
                    collate = kwargs.get('collate') or 'utf8mb4_bin'
                    conn.cursor().execute(f"create database if not exists {name} CHARACTER SET {charset} COLLATE {collate};")
            conn.close()
            conn = pymysql.connect(host=kwargs.get('host'),
                                   user=kwargs.get('user'),
                                   password=kwargs.get('password'),
                                   charset=kwargs.get('charset') or 'utf8mb4',
                                   autocommit=True,
                                   database=name,
                                   cursorclass=pymysql.cursors.DictCursor)
            ConnectionWrapper[name] = {
                'Classes': [],
                'Settings': kwargs,
                'Handler': conn
            }
        except pymysql.err.OperationalError as w:
            raise DatabaseException(f"Runtime error: {w}")
        except pymysql.err.InternalError as w:
            raise DatabaseException(f"Runtime error: {w}".format(error=w))
        except Exception as w:
            raise RuntimeError(f"Unable to connection your database.\nreason: {w}")
    
    @staticmethod
    def addClassToConnection(name, table):
        if name in ConnectionWrapper:
            db = ConnectionWrapper[name]
            if table not in db['Classes']:
                db['Classes'].append(table)
                return True
            return False
        return -1

class Field:
    def __init__(self, typ = None, auto = None, null = False, default = None):
        self.typ = typ
        self.auto = auto
        self.null = null
        self.def_ = default
        if auto and null:
            Logger.warning(f'intField can\'t be auto increment with null value {Style.GREEN} [auto-editor]: changed null to False {Style.RESET}')
            self.null = False
        
    def get_type(self):
        return type(eval(self.typ))
    
    def isNull(self):
        return self.null
    
    def isAuto(self):
        return self.auto
    
    def default(self):
        return self.def_
    
    def _sqlType(self):
        if self.get_type() is int:
            if self.isAuto():
                return 'INT AUTO_INCREMENT PRIMARY KEY NOT NULL'
            elif not self.isNull():
                if self.default():
                    return f'INT NOT NULL DEFAULT {self.default()}'
                else:
                    return 'INT NOT NULL'
            else:
                return 'INT'
        elif self.get_type() is float:
            if not self.isNull():
                if self.default():
                    return f'REAL NOT NULL DEFAULT {self.default()}'
                else:
                    return 'REAL NOT NULL'
            else:
                return 'REAL'
        elif self.get_type().__name__ in ['str', 'list', 'dict', 'bool']:
            if not self.isNull():
                if self.default():
                    return f'LONGTEXT NOT NULL DEFAULT {self.default()}'
                else:
                    return 'LONGTEXT NOT NULL'
            else:
                return 'LONGTEXT'
        return 'LONGTEXT'
    
    @staticmethod
    def intField(auto = False, null=False):
        return Field('int()', auto=auto, null=null)
    
    @staticmethod
    def strField(null = False, default = None):
        return Field('str()', False, null, default)
    
    @staticmethod
    def floatField(null = False, default = None):
        return Field('float()', False, null, default)
    
    @staticmethod
    def listField(null = False, default = None):
        return Field('list()', False, null, default)
    
    @staticmethod
    def dictField(null = False, default = None):
        return Field('dict()', False, null, default)
    
    @staticmethod
    def boolField(null = False, default = None):
        return Field('bool()', False, null, default)
    

class _Where:
    def __init__(self, parent, database, variable: str):
        self.__cls = parent
        self.__database = database
        self.__where = f'where {variable}'
        self.__closed = False
        self.__values = []
        self.__check(variable)

    def orWhere(self, variable: str):
        self.__check(variable)
        if not self.__closed:
            raise RuntimeError('you can do it, you should close the first')
        
        self.__where += f' or {variable}'
        self.__closed = False
        return self

    def andWhere(self, variable: str):
        self.__check(variable)
        if not self.__closed:
            raise RuntimeError('you can do it, you should close the first')
        
        self.__where += f' and {variable}'
        self.__closed = False
        return self
    
    def equals(self, value: Union[str, int, float, bool]):
        if self.__closed:
            raise TypeError('Please use andWhere or orWhere before you call this function.')
        self.__check_value(value)
        self.__where += ' = %s'
        self.__closed = True
        self.__values.append(value)
        return self

    def notEquals(self, value: Union[str, int, float, bool]):
        if self.__closed:
            raise TypeError('Please use andWhere or orWhere before you call this function.')
        self.__check_value(value)
        self.__where += f' != %s'
        self.__closed = True
        self.__values.append(value)
        return self
    
    def like(self, value: Union[str, int, float, bool], before=True, after=True):
        if self.__closed:
            raise TypeError('Please use andWhere or orWhere before you call this function.')
        self.__check_value(value)
        if after and before:
            self.__where += f'like "%{value}%"'
        elif after:
            self.__where += f'like "{value}%"'
        elif before:
            self.__where += f'like "%{value}"'
        else:
            self.__where += f'like "%{value}"'
        self.__closed = True
        return self

    def notLike(self, value: Union[str, int, float, bool], before = True, after=True):
        if self.__closed:
            raise TypeError('Please use andWhere or orWhere before you call this function.')
        self.__check_value(value)
        if after and before:
            self.__where += f'not like "%{value}%"'
        elif after:
            self.__where += f'not like "{value}%"'
        elif before:
            self.__where += f'not like "%{value}"'
        else:
            self.__where += f'not like "%{value}"'
        self.__closed = True
        return self
    
    def moreThan(self, value: Union[int, float]):
        if self.__closed:
            raise TypeError('Please use andWhere or orWhere before you call this function.')
        self.__check_value(value, force=['int', 'float'])
        self.__where += f' > %s'
        self.__closed = True
        self.__values.append(value)
        return self
    
    def moreThanOrEquals(self, value: Union[int, float]):
        if self.__closed:
            raise TypeError('Please use andWhere or orWhere before you call this function.')
        self.__check_value(value, force=['int', 'float'])
        self.__where += f' >= %s'
        self.__closed = True
        self.__values.append(value)
        return self
    
    def lessThan(self, value: Union[int, float]):
        if self.__closed:
            raise TypeError('Please use andWhere or orWhere before you call this function.')
        self.__check_value(value, fore=['int', 'float'])
        self.__where += f' < %s'
        self.__closed = True
        self.__values.append(value)
        return self
    
    def notNull(self):
        if self.__closed:
            raise TypeError('Please use andWhere or orWhere before you call this function.')
        self.__where += ' is not null'
        self.__closed = True
        return self

    def isNull(self):
        if self.__closed:
            raise TypeError('Please use andWhere or orWhere before you call this function.')
        self.__where += ' is null'
        self.__closed = True
        return self
    
    def iN(self, value: tuple):
        if self.__closed:
            raise TypeError('Please use andWhere or orWhere before you call this function.')
        self.__check_value(value, force=['tuple'])
        self.__where += ' IN %s'
        self.__closed = True
        self.__values.append(value)
        return self
    
    def between(self, value: Union[str, int, float, bool], value2: Union[str, int, float, bool]):
        if self.__closed:
            raise TypeError('Please use andWhere or orWhere before you call this function.')
        self.__check_value(value)
        self.__check_value(value2)
        self.__where += ' between %s and %s'
        self.__values.append(value)
        self.__values.append(value2)
        self.__closed = True
        return self
    
    
    def lessThanOrEquals(self, value: Union[int, float]):
        if self.__closed:
            raise TypeError('Please use andWhere or orWhere before you call this function.')
        self.__check_value(value, fore=['int', 'float'])
        self.__where += f' <= %s'
        self.__closed = True
        self.__values.append(value)
        return self

    def orderBy(self, variable: str, stuff="asc", limit = 0):
        self.__check(variable)
        if limit > 0:
            self.__where += f' order by {variable} {stuff} limit {limit}'
        else:
            self.__where += f' order by {variable} {stuff}'
        
        self.__closed = True
        return self
    
    def __check(self, variable):
        if variable in self.__cls.__class__.__dict__:
            field = self.__cls.__class__.__dict__[variable]
            if not isinstance(field, Field):
                raise FieldExecption(f'variable {variable} is not column, is ignored column. you cann\'t use it with where because is not exists on database.')
    
    def __check_value(self, value, force = None):
        if force:
            if type(value).__name__ not in force:
                raise TypeError(f'unsupported type of value, please use only {force} to check the value, you used: {type(value).__name__}')
        else:
            if type(value).__name__ not in ['int', 'str', 'float', 'bool']:
                raise TypeError(f'unsupported type of value, please use only int, str, float or bool to check the value, you used: {type(value).__name__}')
    
    def first(self, asDict = False) -> Union[classmethod, dict, None]:
        if not self.__closed:
            raise TypeError('Look like you didn\'t finish the full where command. did you use some of this functions:\n[equals, notEquals, like, notLike, moreThan, moreThanOrEquals, lessThan, lessThanOrEquals, iN, between, notNull, isNull, orderBy] before you call first()?')
        
        try:
            cursor = self.__database.cursor()
            command = f'select * from {self.__cls.tableName} {self.__where}'
            if self.__values:
                cursor.execute(command, self.__values)
            else:
                cursor.execute(command)
            fetch = cursor.fetchone()
            cursor.close()
            if not fetch:
                return None
            if asDict:
                return self.__cls._to_python(fetch)
            cls = self.__cls.__class__()
            res = self.__cls._to_python(fetch)
            for key in res:
                cls.__setattr__(key, res[key], True)
            return cls
        except pymysql.err.OperationalError as err:
            code = err.args[0]
            if code == 2013:
                    self.__database.ping(reconnect=True)
                    return self.first(asDict=asDict)
            return Logger.error(f'Error while execute command:\n{err}')
        except Exception as why:
            return Logger.error(f'Error while execute command:\n{why}')

    def all(self, asDict = False) -> Union[classmethod, list, None]:
        if not self.__closed:
            raise TypeError('Look like you didn\'t finish the full where command. did you use some of this functions:\n[equals, notEquals, like, notLike, moreThan, moreThanOrEquals, lessThan, lessThanOrEquals, iN, between, notNull, isNull, orderBy] before you call all()?')
        try:
            cursor = self.__database.cursor()
            command = f'select * from {self.__cls.tableName} {self.__where}'
            if self.__values:
                cursor.execute(command, self.__values)
            else:
                cursor.execute(command)
            fetch = cursor.fetchall()
            cursor.close()
            if not fetch:
                return []
            if asDict:
                return self.__cls._to_python(fetch)
            res = []
            for row in fetch:
                cls = self.__cls.__class__()
                topy = self.__cls._to_python(row)
                for column in topy:
                    setattr(cls, column, topy[column], True)
                res.append(cls)
            return res
        except pymysql.err.OperationalError as err:
            code = err.args[0]
            if code == 2013:
                    self.__database.ping(reconnect=True)
                    return self.all(asDict=asDict)
            return Logger.error(f'Error while execute command:\n{err}')
        except Exception as why:
            return Logger.error(f'Error while execute command:\n{why}')

class _Execute:
    def __init__(self, cls, database, command: str, args=None):
        self.__cls = cls
        self.__database = database
        self.command = command
        self.args = args
    
    def all(self, asDict = False):
        try:
            command, value = self.__excute(contine=False)
            cursor = self.__database.cursor()
            if len(value) > 1:
                cursor.execute(command, tuple(value))
            elif len(value) == 1:
                cursor.execute(command, value[0])
            else:
                cursor.execute(command)

            fetch = cursor.fetchall()
            cursor.close()
            if not fetch:
                return []
            if asDict:
                return fetch
            ls = []
            for row in fetch:
                cls = self.__cls.__class__()
                topy = self.__cls._to_python(row)
                for column in topy:
                    cls.__setattr__(column, topy[column], True)
                ls.append(cls)
            return ls
        except pymysql.err.OperationalError as err:
            code = err.args[0]
            if code == 2013:
                self.__database.ping(reconnect=True)
                return self.all(asDict=asDict)
            return Logger.error(f'Error while execute command:\n{err}')
        except Exception as why:
            return Logger.error(f'Error while execute command:\n{why}')

    def first(self, asDict = False):
        try:
            command, value = self.__excute(contine=False)
            cursor = self.__database.cursor()
            if len(value) > 1:
                cursor.execute(command, tuple(value))
            elif len(value) == 1:
                cursor.execute(command, value[0])
            else:
                cursor.execute(command)

            fetch = cursor.fetchone()
            cursor.close()
            if not fetch:
                return None
            if asDict:
                return self.__cls._to_python(fetch)
            cls = self.__cls.__class__()
            res = self.__cls._to_python(fetch)
            for key in res:
                cls.__setattr__(key, res[key], True)
            return cls
        except pymysql.err.OperationalError as err:
            code = err.args[0]
            if code == 2013:
                self.__database.ping(reconnect=True)
                return self.first(asDict=asDict)
            return Logger.error(f'Error while execute command:\n{err}')
        except Exception as why:
            return Logger.error(f'Error while execute command:\n{why}')

    def run(self):
        try:
            cursor = self.__excute()
            if self.command.lower().strip().startswith('insert'):
                res = cursor.lastrowid
            else:
                res = cursor.rowcount
            # res = cursor.rowcount
            cursor.close()
            return res
        except pymysql.err.OperationalError as err:
            code = err.args[0]
            if code == 2013:
                self.__database.ping(reconnect=True)
                return self.run()
            else:
                return Logger.error(f'Error while execute command:\nquery: {self.command}\nError msg:\n{err.args[1]}')
                
        except Exception as why:
            return Logger.error(f'Error while execute command:\nquery: {self.command}\nError msg:\n{why}')

    def __excute(self, contine = True):
        cursor = self.__database.cursor()
        command = self.command
        values = []
        if self.args:
            if type(self.args).__name__ == 'dict':
                for key in self.args:
                    command = command.replace(f":{key}", "%s")
                    values.append(self.args[key])
                if len(values) > 1:
                    if contine:
                        cursor.execute(command, tuple(values))
                else:
                    if contine:
                        cursor.execute(command, values[0])
            else:
                if contine:
                    cursor.execute(command, self.args)
        else:
            if contine:
                cursor.execute(command)
        if not contine:
            return command, values
        return cursor

class _Commandes:
    @staticmethod
    def createTableOrModify(table, fields, drop, add, setting):
        start = time.perf_counter_ns()
        charset = setting.get('charset') or 'utf8mb4'
        collate = setting.get('collate') or 'utf8mb4_bin'
        command = f'CREATE TABLE IF NOT EXISTS {table}('
        for column in fields:
            info = fields[column]
            command += f'{column} {info._sqlType()}, '
        command = command[:-2]
        command += f') CHARACTER SET {charset} COLLATE {collate};'
        if not command.count('INT AUTO_INCREMENT PRIMARY KEY NOT NULL'):
            raise FieldExecption('You should have one of auto increment field, for example: id = Table.intField(auto=True)')
        db = _Instance.getDatabase(table)
        cursor = db.cursor()
        cursor.execute(command)
        if drop or add:
            cursor.execute(f"SHOW COLUMNS FROM {table}")
            columns = cursor.fetchall()
            if drop and columns:
                for col in columns:
                    if any(col['Field'] == item for item in fields):
                        continue
                    command = f'ALTER TABLE {table} drop {col["Field"]};'
                    cursor.execute(command)
            if add and columns:
                for item in fields:
                    if any(item == col['Field'] for col in columns):
                        continue
                    command = f'ALTER TABLE {table} add COLUMN {item} {fields[item]._sqlType()};'
                    cursor.execute(command)
        cursor.close()
        duration = time.perf_counter_ns() - start

def MySQL(database, **kwargs):
    def wrapper(cls):
        if not isinstance(cls.__base__(), Table):
            raise DatabaseException('Please inherit Table inside your class, for example:\n@MySQL(databaseName, **kwargs)\ndef YourClass(Table):\n\t# etc..')
        res = _Instance.addClassToConnection(database, cls.__name__)
        if res == -1:
            host = kwargs.get('host') or 'localhost'
            user = kwargs.get('user') or 'root'
            password = kwargs.get('password') or ''
            charset = kwargs.get('charset') or 'utf8mb4'
            _Instance.connect(database, host=host, user=user, password=password, charset=charset)
            res = _Instance.addClassToConnection(database, cls.__name__)
            if not res or res == -1:
                raise DatabaseException('Unable to create database. unknown error.')
        
        dropColumn = kwargs.get('dropColumn') or False
        addColumn = kwargs.get('addColumn') or False
        lamb = {k: v for k, v in cls.__dict__.items() if isinstance(v, Field)}
        if not lamb:
            raise FieldExecption('You should added field to your class, and one of field should be intField(auto=True)')
        _Commandes.createTableOrModify(cls.__name__, lamb, dropColumn, addColumn, kwargs)
        
        return cls
    return wrapper

class Table(Field):
    def __init__(self):
        self.__ignoreKeys = []
        self.tableName = self.__class__.__name__
        self.__database = _Instance.getDatabase(self.tableName)


    def __setattr__(self, name: str, value, fromlibrary=False) -> None:
        if name in self.__class__.__dict__:
            orgin = self.__class__.__dict__[name]
            if isinstance(orgin, Field):
                if orgin.isAuto() and not fromlibrary:
                    raise FieldExecption(f'(column {name} is auto increment) you can\'t set the value.')
                elif not orgin.isNull() and value is None:
                    raise FieldExecption(f'(column {name} NOT NULL), you can\'t set the value to null or None')
                elif orgin.get_type() != type(value):
                    raise FieldExecption(f'(column {name} is type of {orgin.get_type().__name__}) you can\'t set value to type of {type(value).__name__}')
                else:
                    self.__dict__[name] = value
            else:
                self.__dict__[name] = value
                if name not in self.__ignoreKeys:
                    self.__ignoreKeys.append(name)
        else:
            self.__dict__[name] = value
            if name not in self.__ignoreKeys:
                self.__ignoreKeys.append(name)

    def where(self, variable) -> _Where:
        return _Where(self, _Instance.getDatabase(self.__class__.__name__), variable)
    
    def execute(self, command: str, args: dict = None, db = None) -> Union[_Execute, None]:
        if not command:
            return None
        if db:
            return _Execute(self, db, command, args)
        return _Execute(self, self.__database, command, args)
    
    def _to_python(self, row):
        out = {}
        for variable in row:
            if variable in self.__class__.__dict__:
                field = self.__class__.__dict__[variable]
                value = row[variable]
                if field.get_type() is int:
                    if value:
                        if type(value) is int:
                            out[variable] = value
                        else:
                            if value.isdigit():
                                out[variable] = int(value)
                            else:
                                if field.isNull():
                                    out[variable] = None
                                else:
                                    out[variable] = 0 # change it to int anyway
                    elif field.isNull():
                        out[variable] = None
                    else:
                        out[variable] = 0 # change it to int anyway
                elif field.get_type() is str:
                    if value:
                        if type(value) is str:
                            out[variable] = value
                        else:
                            out[variable] = str(value)
                    else:
                        if field.isNull():
                            out[variable] = None
                        else:
                            out[variable] = '' # change it to str anyway
                elif field.get_type() is list:
                    if value:
                        try:
                            # maybe there dict inside list so we need it as smart dict.
                            value = []
                            parent = eval(value)
                            for item in parent:
                                if isinstance(item, dict):
                                    value.append(SmartDict(item))
                                else:
                                    value.append(item)
                                    
                            out[variable] = value
                        except:
                            out[variable] = [] # change it to list anyway
                    else:
                        out[variable] = [] # change it to list anyway
                elif field.get_type() is dict:
                    if value:
                        try:
                            out[variable] = SmartDict(eval(value))
                        except:
                            out[variable] = {} # change it to dict anyway
                    else:
                        out[variable] = {} # change it to dict anyway
                
                elif field.get_type() is bool:
                    if value:
                        try:
                            out[variable] = eval(value) # if we use bool(str) it will always true, so we use eval for (1, true) or (0, false)
                        except:
                            out[variable] = False # false anyway. value was not allowed to cover it to boolean. is string with characters?
                    else:
                        out[variable] = False # false anyway. value was None or empty.
        return out
    
    def _to_sql(self, value):
        if type(value).__name__ in ['dict', 'list']:
            return str(value)
        return value

    def __insert(self, changed):
        variables = list(changed.keys())
        values = list(changed.values())
        values = [self._to_sql(x) for x in values]
        if len(variables) > 1:
            command = f'INSERT INTO {self.__class__.__name__}{tuple(variables)} VALUES {tuple(["%s" for x in changed])}'
            command = command.replace("'", "")
        else:
            command = f'INSERT INTO {self.__class__.__name__}({variables[0]}) VALUES (%s)'
        if len(values) > 1:
            return self.execute(command, values, db=_Instance.getDatabase(self.__class__.__name__)).run()
        else:
            return self.execute(command, values[0], db=_Instance.getDatabase(self.__class__.__name__)).run()

    def __update(self, changed, auto, value):
        db = _Instance.getDatabase(self.__class__.__name__)
        find = f'SELECT * FROM {self.__class__.__name__} where {auto}=:{auto}' # check if auto increment row value exists on database?
        result = self.execute(find, args={auto: value}, db = db).first(asDict=True)
        if result:
            values = []
            command = f'UPDATE {self.__class__.__name__} set '
            for key in changed:
                command += f'{key}=%s, '
                values.append(self._to_sql(changed[key]))
            command = command[:-2]
            command += f' WHERE {auto} = %s;'
            values.append(value)
            return self.execute(command, values, db = db).run()
        else:
            _id = self.__insert(changed)
            this.__setattr__(auto, _id, True)
            return _id

    def save(self) -> Union[int, None]:
        auto = self._get_auto_field()
        changed = self.__dict__
        for ignor in self.__ignoreKeys:
            if ignor in changed:
                del changed[ignor]
        if not changed:
            return None
        if auto in changed:
            return self.__update(changed, auto, self._get_auto_field_value())
        else:

            _id = self.__insert(changed)
            this.__setattr__(auto, _id, True)
            return _id

    def delete(self):
        auto = self._get_auto_field()
        value = self._get_auto_field_value()
        if value:
            self.execute(f'delete from {self.__class__.__name__} where {auto}=:auto', args={'auto': value}).run()
            return value
        else:
            raise RuntimeError('Don\'t call delete if the result not from where or execute.')

    def _get_auto_field(self):
        for colum in self.__class__.__dict__:
            orgin = self.__class__.__dict__[colum]
            if isinstance(orgin, Field):
                if orgin.isAuto():
                    return colum
        return False
    
    def _get_auto_field_value(self):
        find = self._get_auto_field()
        if find:
            if find in self.__dict__:
                return self.__dict__[find]
        return None
        


