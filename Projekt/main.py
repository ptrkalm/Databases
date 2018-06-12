import psycopg2
import sys
import json
import ast

def openDatabase(login, password, database):
    conn = None
    try:
        conn = psycopg2.connect(host='localhost', dbname=database, user=login, password=password)
        print("SUCCES: openDatabase")
        return conn
    except:
        print('openDatabase error')

def buildDatabase(conn):
    commands = (
    """
    CREATE TABLE employee (
        emp         int PRIMARY KEY,
        data        text,
        password    text,
        ancestors   integer[]
    )
    """,
    """
    CREATE USER app PASSWORD 'qwerty'
    """,
    """
    ALTER USER app SUPERUSER
    """
    )
    #temporary solution

    cur = conn.cursor()

    for command in commands:
        cur.execute(command)

    cur.close()
    print("SUCCES: buildDatabase")

def buildRoot(conn, data, password, emp):
    command = """
    INSERT INTO employee (emp, data, password)
    VALUES (%s, %s, md5(%s));"""

    cur = conn.cursor()
    cur.execute(command, (emp, data, password))
    cur.close()
    print("SUCCES: buildRoot")

def authentication(conn, admin, passwd):
    command = """
        SELECT * FROM employee
        WHERE password = md5(%s) AND emp = (%s);"""

    cur = conn.cursor()
    cur.execute(command, (passwd, admin))
    admin = cur.fetchone()
    cur.close()
    if (admin is None):
        return 0
    return 1

def privilege(conn, emp, admin):
    command = """
        SELECT * FROM employee
        WHERE emp = %s;"""

    cur = conn.cursor()
    cur.execute(command, (emp,))
    ancestors = cur.fetchone()
    cur.close()
    if (ancestors is None):
        return 0

    ancestors = ancestors[3]
    if (ancestors is None):
        return -1

    ancestors = ast.literal_eval(str(ancestors))
    if (admin == emp or admin in ancestors):
        return len(ancestors)

    return 0

def calcDepth(conn, emp):
    depth = """
        SELECT * FROM employee
        WHERE emp = %s;"""

    cur = conn.cursor()
    cur.execute(depth, (emp,))
    depth = cur.fetchone()[3]
    depth = len(depth)
    return depth

def addEmployee(conn, admin, passwd, data, newpasswd, emp1, emp):
    insertEmployee = """
        INSERT INTO employee (emp, data, password)
        VALUES (%s, %s, md5(%s));"""

    inheritAncestors = """
        UPDATE employee SET ancestors =
            (SELECT ancestors FROM employee
             WHERE emp = %s)
        WHERE emp = %s"""

    addAncestor = """
        UPDATE employee SET ancestors[%s] = %s
        WHERE emp = %s;"""

    if(not authentication(conn, admin, passwd)):
        print("FAILURE: addEmploye - failed authentication")
        return

    hasPrivilege = privilege(conn, emp1, admin)
    cur = conn.cursor()
    if (hasPrivilege == -1):
        if (emp1 == 0):
            try:
                cur.execute(insertEmployee, (emp, data, newpasswd))
                cur.execute(addAncestor, (0, 0, emp))
            except:
                print("FAILURE: addEmploye - duplicated key")
                conn.rollback()
                cur.close()
                return
        else:
            print("FAILURE: addEmploye - admin without privelege")
            cur.close()
            return

    elif (hasPrivilege):
        depth = hasPrivilege
        try:
            cur.execute(insertEmployee, (emp, data, newpasswd))
            cur.execute(inheritAncestors, (emp1, emp))
            cur.execute(addAncestor, (depth, emp1, emp))
        except:
            print("FAILURE: addEmploye - duplicated key")
            conn.rollback()
            cur.close()
            return
    else:
        print("FAILURE: addEmploye - admin without privelege")
        cur.close()
        return

    cur.close()
    print("SUCCES: addEmployee")
    return

def removeEmployee(conn, admin, passwd, emp):
    command = """
        DELETE FROM employee WHERE emp = %s OR ancestors[%s] = %s"""

    if(not authentication(conn, admin, passwd)):
        print("FAILURE: addEmploye - failed authentication")
        return

    hasPrivilege = privilege(conn, emp, admin)
    cur = conn.cursor()
    if (hasPrivilege == -1):
        if (admin == 0):
            cur.execute(command, (0, 0))
        else:
            print("FAILURE: removeEmploye - admin without privelege")
            cur.close()
            return

    elif (hasPrivilege):
        depth = hasPrivilege
        cur.execute(command, (emp, depth, emp))
    else:
        print("FAILURE: removeEmploye - admin without privelege")
        cur.close()
        return

    cur.close()
    print("SUCCES: removeEmployee")
    return

def childEmployee(conn, admin, passwd, emp):
    command = """
        SELECT emp FROM employee
        WHERE ancestors[%s] = %s AND array_length(ancestors, 1) = %s"""

    if(not authentication(conn, admin, passwd)):
        print("FAILURE: childEmployee - failed authentication")
        return

    depth = calcDepth(conn, emp)

    cur = conn.cursor()
    if (emp == 0):
        cur.execute(command, (0, 0, 1))
    else:
        cur.execute(command, (depth, emp, depth+1))

    child = cur.fetchall()
    print child;

    cur.close()
    print("SUCCES: childEmployee")
    return

def parentEmployee(conn, admin, passwd, emp):
    command = """
        SELECT emp FROM employee
        WHERE emp = (
            SELECT ancestors[%s] FROM employee
            WHERE emp = %s
        )"""

    if(not authentication(conn, admin, passwd)):
        print("FAILURE: parentEmployee - failed authentication")
        return

    depth = calcDepth(conn, emp)

    cur = conn.cursor()
    parent = None

    if (emp != 0):
        cur.execute(command, (depth-1, emp))

    parent = cur.fetchone()
    print(parent)

    cur.close()
    print("SUCCES: parentEmployee")
    return

def ancestorsEmployee(conn, admin, passwd, emp):
    command = """
        SELECT ancestors FROM employee
        WHERE emp = %s;"""

    if(not authentication(conn, admin, passwd)):
        print("FAILURE: ancestorsEmployee - failed authentication")
        return

    cur = conn.cursor()
    cur.execute(command, (emp,))
    ancestors = cur.fetchone()
    print ancestors
    cur.close()
    print("SUCCES: ancestorsEmployee")
    return

def descendantsEmployee(conn, admin, passwd, emp):
    command = """
        SELECT emp FROM employee
        WHERE ancestors[%s] = %s"""

    if(not authentication(conn, admin, passwd)):
        print("FAILURE: descendantsEmployee - failed authentication")
        return

    depth = calcDepth(conn, emp)
    cur = conn.cursor()
    if(emp == 0):
        cur.execute(command, (0, 0))
    else:
        cur.execute(command, (depth, emp))

    descendants = cur.fetchall()
    print descendants
    cur.close()
    print("SUCCES: descendantsEmployee")
    return

def ancestorEmployee(conn, admin, passwd, emp1, emp2):
    command = """
        SELECT %s = ANY(
            (SELECT ancestors FROM employee
            WHERE emp = %s)::integer[]
            );"""

    if(not authentication(conn, admin, passwd)):
        print("FAILURE: ancestorEmployee - failed authentication")
        return

    cur = conn.cursor()
    cur.execute(command, (emp2, emp1))
    ancestor = cur.fetchone()
    print(ancestor)
    cur.close()
    print("SUCCES: ancestorEmployee")
    return

def readEmployee(conn, admin, passwd, emp):
    command = """
        SELECT data FROM employee
        WHERE emp = %s"""

    if(not authentication(conn, admin, passwd)):
        print("FAILURE: readEmployee - failed authentication")
        return

    hasPrivilege = privilege(conn, emp, admin)
    data = None
    cur = conn.cursor()
    if (hasPrivilege == -1):
        if (admin == 0):
            cur.execute(command, (0,))
        else:
            print("FAILURE: readEmploye - admin without privelege")
            cur.close()
            return

    elif (hasPrivilege):
        cur.execute(command, (emp,))
    else:
        print("FAILURE: readEmploye - admin without privelege")
        cur.close()
        return

    data = cur.fetchone()
    print data
    cur.close()
    print("SUCCES: readEmployee")
    return

def updateEmployee(conn, admin, passwd, emp, newdata):
    command = """
        UPDATE employee SET data = %s
        WHERE emp = %s;"""

    if(not authentication(conn, admin, passwd)):
        print("FAILURE: updateEmployee - failed authentication")
        return

    hasPrivilege = privilege(conn, emp, admin)

    cur = conn.cursor()
    if (hasPrivilege == -1 or hasPrivilege):
        cur.execute(command, (newdata, emp))
    else:
        print("FAILURE: updateEmploye - admin without privelege")
        cur.close()
        return

    cur.close()
    print("SUCCES: updateEmployee")
    return

def initDatabase():
    commands = open('init.in')
    openLine = json.loads(commands.readline())
    openLine = openLine['open']
    conn = openDatabase(openLine['login'], openLine['password'], openLine['database'])
    buildDatabase(conn)

    rootLine = json.loads(commands.readline())
    rootLine = rootLine['root']
    buildRoot(conn, rootLine['data'], rootLine['newpassword'], rootLine['emp'])

    for line in commands:
        newLine = json.loads(line)
        newLine = newLine['new']
        addEmployee(conn, newLine['admin'], newLine['passwd'], newLine['data'],
                    newLine['newpasswd'], newLine['emp1'], newLine['emp'])

    conn.commit()
    conn.close()
    print("SUCCES: initDatabase")

def accessDatabase(input):
    commands = open(input)
    openLine = json.loads(commands.readline())
    openLine = openLine['open']
    conn = openDatabase(openLine['login'], openLine['password'], openLine['database'])

    for line in commands:
        nextLine = json.loads(line)
        if ('new' in nextLine):
            newLine = nextLine['new']
            addEmployee(conn, newLine['admin'], newLine['passwd'], newLine['data'],
                        newLine['newpasswd'], newLine['emp1'], newLine['emp'])
        elif ('remove' in nextLine):
            remLine = nextLine['remove']
            removeEmployee(conn, remLine['admin'], remLine['passwd'], remLine['emp'])
        elif ('child' in nextLine):
            childLine = nextLine['child']
            childEmployee(conn, childLine['admin'], childLine['passwd'], childLine['emp'])
        elif ('parent' in nextLine):
            parLine = nextLine['parent']
            parentEmployee(conn, parLine['admin'], parLine['passwd'], parLine['emp'])
        elif ('ancestors' in nextLine):
            ancsLine = nextLine['ancestors']
            ancestorsEmployee(conn, ancsLine['admin'], ancsLine['passwd'], ancsLine['emp'])
        elif ('descendants' in nextLine):
            descsLine = nextLine['descendants']
            descendantsEmployee(conn, descsLine['admin'], descsLine['passwd'], descsLine['emp'])
        elif ('ancestor' in nextLine):
            ancLine = nextLine['ancestor']
            ancestorEmployee(conn, ancLine['admin'], ancLine['passwd'], ancLine['emp1'], ancLine['emp2'])
        elif ('read' in nextLine):
            readLine = nextLine['read']
            readEmployee(conn, readLine['admin'], readLine['passwd'], readLine['emp'])
        elif ('update' in nextLine):
            upLine = nextLine['update']
            updateEmployee(conn, upLine['admin'], upLine['passwd'], upLine['emp'], upLine['newdata'])
    conn.commit()
    conn.close()

if __name__ == "__main__":
    if (sys.argv[1] == '--init'):
        initDatabase()
    else:
        accessDatabase(sys.argv[1])
