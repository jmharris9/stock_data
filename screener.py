import pickle
import glob
import webscrapper
import pylab as P
import numpy as np
import sqlite3 as lite
import urllib
import re
import ystockquote

def convert_key_to_SQL(key):
    key=key.replace(" ","_")
    key=key.replace("/","_over_")
    key=key.replace("%","percent")
    key=key.replace("__","_")
    key = ''.join(e for e in key if e.isalnum()or e=="_")
    key = key.lower()
    return key

def get_last(symbol, key, cur):
    key = convert_key_to_SQL(key)
    cur.execute('SELECT Id FROM Stocks WHERE symbol="'+symbol+'"')
    index = cur.fetchall()
    index = index[0][0]
    cur.execute('SELECT "9" FROM '+key+' WHERE Id='+str(index))
    return cur.fetchall()[0][0]

def get_single_year(symbol, key, year, cur):
    key = convert_key_to_SQL(key)
    cur.execute('SELECT Id FROM Stocks WHERE symbol="'+symbol+'"')
    index = cur.fetchall()
    index = index[0][0]
    cur.execute('SELECT "'+str(year)+'" FROM '+key+' WHERE Id='+str(index))
    return cur.fetchall()[0][0]

def get_data(symbol, key, cur):
    key = convert_key_to_SQL(key)
    cur.execute('SELECT Id FROM Stocks WHERE symbol="'+symbol+'"')
    index = cur.fetchall()
    index = index[0][0]
    cur.execute('SELECT * FROM '+key+' WHERE Id='+str(index))
    my_data = cur.fetchall()[0][1:]
    my_datas = [x if not webscrapper.is_number(x) else 0 for x in my_data]
    return my_datas

def calculate_ebit_ev(cur, ticker):

    ebit = float(get_last(ticker, "EBIT", cur))
    shares = float(get_last(ticker, "total common shares out", cur))
    bonds = float(get_last(ticker, "long-term debt", cur))
    #try:
    price = float(ystockquote.get_price(ticker))
    #except ValueError:
    #    return 0
    ev = price*shares+bonds
    if ev==0:
        return
    return ebit/ev

def run():
    con = lite.connect('stock.db')
    cur = con.cursor()
    my_stocks = glob.glob("*dict.pkl")
    ebit_ev = []
    for stock in my_stocks:
        ticker = stock[:-9]
        if ticker =="ticker_list" or ticker =="no_data":
            continue
        result = calculate_ebit_ev(cur, ticker)
        if result == 0:
            continue
        ebit_ev.append((ticker, result))
    with open("ebit_ev_screen.pkl", "wb") as f:
						pickle.dump(ebit_ev,f)
    P.hist(ebit_ev, bins=20)
    P.show


def run2():
    con = lite.connect('stock.db')
    cur = con.cursor()
    with open("ebit_ev_screen.pkl") as f:
        ebit_ev= pickle.load(f)
    ebit_ev = [x for x in ebit_ev if x[1] !=None]
    total_buffets = 0
    for y in ebit_ev:
        if y[1]>1:

            if float(get_single_year(y[0], "EBIT", "9", cur))>10*float(get_single_year(y[0], "EBIT", "8", cur)):
                continue
            else:
                print y[0]
                total_buffets=total_buffets+1
    print total_buffets
    #P.hist(gaussian_numbers)
def root(n, r):
    my_roots=np.roots([1]+[0]*(r-1)+[-n])
    for rs in my_roots:
        if rs.imag==0 and rs.real>0:
            return rs.real-1
        #else:
        #    return 0

def compute_multiyear_median(l):
    my_gr=[]
    i=0
    if not len(l)==10:
        return 0
    while i<4:
        if l[i]>0 and l[i+6]>0:
            gr = root(l[i+6]/l[i], 7)
            my_gr.append(gr)
        else:
            my_gr.append(0)
        i=i+1
    i=0
    while i<6:
        if l[i]>0 and l[i+4]>0:

            gr = root(l[i+4]/l[i], 5)
            my_gr.append(gr)
        else:
            my_gr.append(0)
        i=i+1

    median = np.median(my_gr)
    return median


def screen_for_stocks(symbol, cur):
    #Profit margin
    ebitda = get_last(symbol,"EBITDA",cur)
    depreciation = get_last(symbol,"depreciation (unrecognized)",cur)
    ebit = ebitda-depreciation
    sales = get_last(symbol,"operating revenue",cur)
    if sales<=0:
        profit_margin =0
    else:
        profit_margin =ebit/sales
    #% earned on total capitalization
    bonds = get_last(symbol,"long-term debt",cur)
    try:
        price= float(ystockquote.get_price(symbol))
    except ValueError:
        price = 0
    shares = get_last(symbol,"total common shares out",cur)
    total_cap = bonds + price*shares
    if total_cap <=0:
        percent_earned=0
    else:
        percent_earned = ebit/total_cap

    #interest charges earned
    interest = get_last(symbol,"interest expense",cur)
    if interest<=0:
        interest_earned = 10
    else:
        interest_earned = ebit/interest

    #historical interest earned
    hist_ebitda = get_data(symbol,"EBITDA",cur)
    hist_depreciation = get_data(symbol,"depreciation (unrecognized)",cur)
    hist_ebit = [a-b for a,b in zip(hist_ebitda, hist_depreciation)]
    if len(hist_ebit)>0:
        average_earnings = sum(hist_ebit)/float(len(hist_ebit))
    else:
        average_earnings = 0
    if interest<=0:
        hist_interest_earned=10
    else:
        hist_interest_earned = average_earnings/interest

    #discount
    common_balance = ebit-interest
    if shares<=0 or common_balance<=0:
        pe=0
    else:
        pe=price/(common_balance/shares)
    croic = get_data(symbol,"Croic",cur)
    av_croic = np.median(croic)
    hist_shares = get_data(symbol,"total common shares out",cur)
    hist_eps = [a/b if b>0 else 0 for a,b in zip(hist_ebit, hist_shares)]
    av_eps_gr = compute_multiyear_median(hist_eps)
    hist_oe = get_data(symbol,"owners earnings",cur)
    hist_oeps = [a/b if b>0 else 0 for a,b in zip(hist_oe,hist_shares)]
    av_oeps_gr = compute_multiyear_median(hist_oeps)
    if len(hist_shares)==10:
        gr=(av_croic+av_eps_gr*100+av_oeps_gr*100)/3
    else:
        gr = av_croic
    if not gr == 0:
        discount = 1-(pe/gr)
    else:
        discount = 0
    if profit_margin>0.15 and percent_earned>0.1 and interest_earned>3 and hist_interest_earned>3 and discount>0.5:
        return True
    else:
        return False

def stock_screener():
    con = lite.connect('stock.db')
    cur = con.cursor()
    my_stocks = glob.glob("*dict.pkl")
    f = open ("screen_results.txt", "w")
    good_stocks =[]

    for stock in my_stocks:
        ticker = stock[:-9]
        if ticker =="ticker_list" or ticker =="no_data":
            continue
        if screen_for_stocks(ticker,cur):
            good_stocks.append(ticker)
            print ticker
    with open("screen_results.txt","w") as f:
        for stock in good_stocks:
            f.write(stock+" ")

if __name__ == "__main__":
	  stock_screener()
