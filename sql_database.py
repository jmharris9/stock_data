#database converter
#TICKER TABLE
# id | ticker | exchange
#TABLE FOR EACH LINE OF ADVFN
# id | ticker_id | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 0 |
#

import sqlite3 as lite
import sys
import webscrapper
import numpy
import glob

def convert_key_to_SQL(key):
    key=key.replace(" ","_")
    key=key.replace("/","_over_")
    key=key.replace("%","percent")
    key=key.replace("__","_")
    key = ''.join(e for e in key if e.isalnum()or e=="_")
    key = key.lower()
    return key

def make_table():
    con = None

    data_dict = webscrapper.load_data_from_pickle('GILD')
    keys = data_dict.keys()

    try:
        con = lite.connect('stock.db')
        cur = con.cursor()
        cur.execute('CREATE TABLE Stocks (Id INT, Symbol TEXT, Exchange TEXT)')
        for key in keys:
            my_type = type(data_dict[key][-1])
            if my_type == float or my_type == numpy.float64:
                sql_type = 'FLOAT'

            else:
                sql_type = 'TEXT'
            key=key.replace(" ","_")
            key=key.replace("/","_over_")
            key=key.replace("%","percent")
            key=key.replace("__","_")
            key = ''.join(e for e in key if e.isalnum()or e=="_")
            key = key.lower()
            #cur.execute('ALTER TABLE Stocks ADD COLUMN "'+key+'_id" INT')
            #print 'CREATE TABLE "'+key+'" (Id INT, "Symbol id" INT, "0" '+sql_type+', "1" '+sql_type+', "2" '+sql_type+', "3" '+sql_type+', "4" '+sql_type+', "5" '+sql_type+', "6" '+sql_type+', "7" '+sql_type+', "8" '+sql_type+', "9" '+sql_type+', "10" '+sql_type+')'

            cur.execute('CREATE TABLE "'+key+'" (Id INT, "0" '+sql_type+', "1" '+sql_type+', "2" '+sql_type+', "3" '+sql_type+', "4" '+sql_type+', "5" '+sql_type+', "6" '+sql_type+', "7" '+sql_type+', "8" '+sql_type+', "9" '+sql_type+')')

        cur.execute('SELECT * FROM Stocks')
        rows = cur.fetchall()
        for row in rows:
            print row
    except lite.Error, e:
        print 'Error %s:' %e.args[0]
        sys.exit(1)

    finally:
        if con:
            con.close()
def populate_table(ticker, con, index):
    data_dict = webscrapper.load_data_from_pickle(ticker)
    keys = data_dict.keys()
    try:
        con = lite.connect('stock.db')
        with con:
            cur = con.cursor()

            cur.execute('SELECT * FROM Stocks WHERE symbol="'+ticker+'"')
            x = cur.fetchall()
            #print len(x)
            if not (len(x)==0):
                return

            insert_string = 'INSERT INTO Stocks VALUES('+str(index)+', "'+ticker+'", "nasdaq")'
            cur.execute(insert_string)
            for key in keys:
                sql_key = convert_key_to_SQL(key)
                sql_string = 'INSERT INTO '+sql_key+' VALUES( '+str(index)
                num_years = len(data_dict["operating revenue"])
                j=0
                while j<10-num_years:
                    sql_string=sql_string+", 0"
                    j=j+1
                for i in range(1,num_years+1):
                    if data_dict[key][i-(num_years+1)]==None:
                        sql_string=sql_string+', 0'
                    else:
                        try:
                            sql_string=sql_string+', "'+str(data_dict[key][i-(num_years+1)])+'"'
                        except UnicodeEncodeError:
                            sql_string=sql_string+', "problem character encoding"'
                sql_string = sql_string+')'

                #print sql_string
                cur.execute(sql_string)
        con.commit()

    except lite.Error, e:
        print 'Error %s:' %e.args[0]
        sys.exit(1)

    finally:
        if con:
            con.close()
    return

def populate_all():
    con = None
    my_stocks = glob.glob("*dict.pkl")
    index = 2
    for stock in my_stocks:
        ticker = stock[:-9]
        if ticker =="ticker_list" or ticker =="no_data":
            continue
        populate_table(ticker, con, index)
        index = index+1

def output_run():
    con = lite.connect('stock.db')
    with con:
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        #print(cur.fetchall())
        cur.execute('SELECT Id FROM Stocks WHERE symbol="EME"')
        index = cur.fetchall()
        #index = index[0][0]
        print index
        slq_string = 'SELECT "9" FROM treasury_stock WHERE Id='+str(index)
        print slq_string
        cur.execute(slq_string)
        print cur.fetchall()

def run():
    #make_table()
    populate_all()
    #output_run()

if __name__ == "__main__":
	run()