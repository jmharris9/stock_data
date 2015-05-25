import requests
from lxml import html
from locale import *
import numpy as np
import sys
import urlparse
import sqlite3 as lite
from bs4 import BeautifulSoup

statements = ['bs', 'is', 'cf']
###need to figure out currency conversion.
def sanatize_key(key):
    key=key.replace(" ","_")
    key=key.replace(",","")
    key=key.replace(")","")
    key=key.replace("(","")
    key=key.replace("(","")
    key=key.replace("-","_")
    key=key.replace("'","")
    key=key.replace("&","and")
    key=key.replace("/","_over_")
    key = key.lower()
    key = key.strip()
    return key

def get_data(symbol, key, year, cur):
    cur.execute('SELECT Id FROM Stocks WHERE symbol="'+symbol+'"')
    index = cur.fetchall()[0][0]
    cur.execute('SELECT '+year+' FROM '+key+' WHERE Id='+str(index))
    if year == "*":
        return cur.fetchall()[0][1:]
    else:
        return cur.fetchall()[0][0]

def insert_data(symbol, key, data, cur):
    cur.execute('SELECT Id FROM Stocks WHERE symbol="'+symbol+'"')
    index = cur.fetchall()[0][0]
    sql_string = 'INSERT OR REPLACE INTO '+key+' VALUES ('+str(index)
    i=0
    while i<len(data):
        sql_string = sql_string+', '+str(data[i])
        i=i+1
    sql_string = sql_string+')'
    cur.execute(sql_string)

def download_html(ticker, statement):
    response = requests.get("http://financials.morningstar.com/ajax/ReportProcess4HtmlAjax.html?t=XNAS:"+ticker+"&region=usa&culture=en-US&productcode=MLE&cur=&reportType="+statement+"&period=12&dataType=A&order=asc&columnYear=10&curYearPart=1st5year&rounding=3&view=raw")
    x = response.text
    y=x.split('","')
    htmlx = y[22][9:].replace('\\', '')
    html_body = html.fromstring(htmlx)
    keys = []
    nodes = html_body.xpath("//*[contains(@class, 'lbl')]")
    con = None
    try:
        con = lite.connect('stock_data.db')
        cur = con.cursor()
        cur.execute('SELECT count(*) FROM sqlite_master WHERE tbl_name = "Stocks" AND type = "table"')
        if cur.fetchall()[0][0]==0:
            cur.execute('CREATE TABLE Stocks (Id INT PRIMARY KEY, Symbol TEXT, Exchange TEXT)')
        index = 2
        cur.execute('SELECT count(*) FROM Stocks WHERE Id='+str(index))
        if cur.fetchall()[0][0]==0:
            insert_string = 'INSERT INTO Stocks (Id, Symbol, Exchange) VALUES ('+str(index)+', "'+ticker+'", "nasdaq")'
            cur.execute(insert_string)
        con.commit()
        eps = 0
        diluted = 0
        for t in nodes:
            if len(t.xpath("../@id"))>0:
                if t.xpath("../@id")[0][6]=='i' or t.xpath("../@id")[0][6]=='t':
                    if t.xpath("@title"):
                        key=t.xpath("@title")[0]
                    else:
                        key=t.text
                    key = sanatize_key(key)
                    if key:
                        key = key+'_'+statement
                        if key == 'basic_is':
                            if eps == 0:
                                key = 'eps_basic_is'
                                eps = 1
                            else:
                                key = 'weighted_average_shares_outstanding_basic_is'
                        if key == 'diluted_is':
                            if diluted == 0:
                                key = 'eps_diulted_is'
                                diluted = 1
                            else:
                                key = 'weighted_average_shares_outstanding_diluted_is'
                        cur.execute('SELECT count(*) FROM sqlite_master WHERE tbl_name = "'+key+'" AND type = "table"')
                        if cur.fetchall()[0][0]==0:
                            sql_type = 'FLOAT'
                            cur.execute('CREATE TABLE "'+key+'" (Id INT PRIMARY KEY, "0" '+sql_type+', "1" '+sql_type+', "2" '+sql_type+', "3" '+sql_type+', "4" '+sql_type+', "5" '+sql_type+', "6" '+sql_type+', "7" '+sql_type+', "8" '+sql_type+', "9" '+sql_type+', "10" '+sql_type+')')
                    key_code = t.xpath("../@id")[0][6:]
                    tester= html_body.xpath('//*[@id="data_'+key_code+'"]/*')
                    sql_string = 'INSERT OR REPLACE INTO '+key+' VALUES ('+str(index)
                    for z in tester:
                        if len(z.xpath('@rawvalue'))>0:
                            if z.xpath('@rawvalue')[0]==u'\u2014':
                                sql_string = sql_string + ', 0'
                            else:
                                last= z.xpath('@rawvalue')[0]
                                sql_string = sql_string +', '+last
                    if len(tester)<11:
                        sql_string = sql_string + ', 0'
                    sql_string = sql_string +')'
                    if key:
                        #cur.execute('SELECT count(*) FROM '+key+' WHERE Id = '+str(index))
                        cur.execute(sql_string)
        con.commit()
    except lite.Error, e:
        print 'Error %s:' %e.args[0]
        sys.exit(1)
    finally:
        if con:
            con.close()

def download_price(symbol):
    response = requests.get('http://quotes.morningstar.com/stock/c-header?&t=XNAS'+symbol)
    x = response.text
    html_body = html.fromstring(x)
    keys = []
    nodes = html_body.xpath("//*[contains(@id, 'last-price-value')]")
    price = nodes[0].text.strip()
    return price

def calculate_croic(symbol, cur):
    cur.execute('SELECT count(*) FROM sqlite_master WHERE tbl_name = "croic" AND type = "table"')
    if cur.fetchall()[0][0]==0:
        sql_type = 'FLOAT'
        cur.execute('CREATE TABLE "croic" (Id INT PRIMARY KEY, "0" '+sql_type+', "1" '+sql_type+', "2" '+sql_type+', "3" '+sql_type+', "4" '+sql_type+', "5" '+sql_type+', "6" '+sql_type+', "7" '+sql_type+', "8" '+sql_type+', "9" '+sql_type+', "10" '+sql_type+')')
    total_curr_liabs = get_data(symbol, "total_current_liabilities_bs", "*", cur)
    total_curr_assets = get_data(symbol, "total_current_assets_bs", "*", cur)
    total_equity = get_data(symbol, "total_assets_bs", "*", cur)
    total_liabs = get_data(symbol, "total_liabilities_bs", "*", cur)
    income = get_data(symbol, "revenue_is", "*", cur)
    income_tax = get_data(symbol, "provision_for_income_taxes_is", "*", cur)
    cash = get_data(symbol, "total_cash_bs", "*", cur)
    croic =[]
    i = 0
    while i<len(total_curr_liabs):
        if income[i]>0:
            excess_cash = total_curr_liabs[i]-total_curr_assets[i]
            if total_equity[i] + total_liabs[i]-total_curr_liabs[i]-cash[i]-excess_cash<=0:
                croic.append(0)
            else:
                croic.append((income[i]-income_tax[i])*100/(total_equity[i] +total_liabs[i] - total_curr_liabs[i] - cash[i] -excess_cash))
        i=i+1
    insert_data(symbol, "croic", croic, cur)


def calculate_owners_earnings(symbol, cur):
  cur.execute('SELECT count(*) FROM sqlite_master WHERE tbl_name = "oe" AND type = "table"')
  if cur.fetchall()[0][0]==0:
      sql_type = 'FLOAT'
      cur.execute('CREATE TABLE "oe" (Id INT PRIMARY KEY, "0" '+sql_type+', "1" '+sql_type+', "2" '+sql_type+', "3" '+sql_type+', "4" '+sql_type+', "5" '+sql_type+', "6" '+sql_type+', "7" '+sql_type+', "8" '+sql_type+', "9" '+sql_type+', "10" '+sql_type+')')
  purchase_of_ppe = get_data(symbol, "investments_in_property_plant_and_equipment_cf", "*", cur)
  continuing_ops = get_data(symbol, "net_cash_provided_by_operating_activities_cf", "*", cur)
  mean_ppe = np.mean(purchase_of_ppe)
  oe = []
  i=0
  while i<len(continuing_ops):
      if continuing_ops[i]!=0:
          oe.append(continuing_ops[i]+mean_ppe)
      else:
          oe.append(0)
      i=i+1
  insert_data(symbol, "oe", oe, cur)

def calculate_multiyear(input_data):
  multiyear_data = []
  first_year =np.nonzero(input_data)[0][0]
  num_years = 10-first_year
  if num_years<10:
		for i in range(num_years):
			multiyear_data.append(np.median(input_data[0:num_years-1]))
  else:
		for i in range(4):
			multiyear_data.append(np.median(input_data[i:num_years-4+i]))
		for i in range(6):
			multiyear_data.append(np.median(input_data[i:num_years-6+i]))
  return multiyear_data

def calculate_multiyear_percent(input_data):
  multiyear_percent =[]
  first_year =np.nonzero(input_data)[0][0]
  num_years = 11-first_year
  if num_years<10:
		for i in range(first_year, num_years-1):
			if input_data[i]>0 and input_data[i+1]>0:
				multiyear_percent.append(((input_data[i+1]/input_data[i])-1)*100)
			else:
				multiyear_percent.append(0)
		multiyear_percent[num_years-1].append(np.median(multiyear_percent))
  else:
		for i in range(4):
			if input_data[i]>0 and input_data[i+6]>0:
				multiyear_percent.append(((input_data[i+6]/input_data[i])**(1/7.0) -1)*100)
			else:
				multiyear_percent.append(0)
		for i in range(6):
			if input_data[i]>0 and input_data[i+4]>0:
				multiyear_percent.append(((input_data[i+4]/input_data[i])**(1/5.0) -1)*100)
			else:
				multiyear_percent.append(0)
  return multiyear_percent

def calculate_dcf(symbol, gr_array, cur):
  growth_rate = np.amin(gr_array)
  discount_rate = 15.0
  terminal_growth_rate = 5.0
  rate = (1+growth_rate/100)/(1+discount_rate/100)
  terminal_rate = (1+terminal_growth_rate/100)/(1+discount_rate/100)
  owners_earnings = get_data(symbol, "oe", "*", cur)[9]
  shares_out = get_data(symbol, "weighted_average_shares_outstanding_basic_is", "*", cur)[10]
  projected_earnings =[]
  for i in range(10):
    projected_earnings.append(owners_earnings*rate)
    owners_earnings = owners_earnings*rate
  for i in range(10):
    projected_earnings.append(owners_earnings*terminal_rate)
    owners_earnings = owners_earnings*terminal_rate
  total_future_cash = (np.sum(projected_earnings))/shares_out
  return total_future_cash
  '''

def analyze_data(symb, data_dict, gd_client, gc):
	#for i in range(10):
	#	print data_dict["total equity"][i],data_dict["total liabilities"][i],data_dict["total current liabilities"][i],(data_dict["cash & equivalents"][i])
		#print x
	data_dict = calculate_croic(data_dict)
	data_dict = calculate_owners_earnings(data_dict)
	num_years = len(data_dict["interest expense"])
	if num_years>1:
		data_dict=calculate_multiyear("croic", data_dict)
		data_dict=calculate_multiyear_percent("free cash flow", data_dict)
		data_dict=calculate_multiyear_percent("owners earnings", data_dict)
		data_dict=calculate_multiyear_percent("total equity", data_dict)
		gr_array = [np.median(data_dict["multiyear croic"]), np.median(data_dict["multiyear free cash flow"]), np.median(data_dict["multiyear owners earnings"]), np.median(data_dict["multiyear total equity"])]
	else:
		gr_array = [np.median(data_dict["croic"])]
	dcf = calculate_dcf(data_dict, gr_array)
	test_write_to_gdocs(symb, str(dcf), data_dict, gd_client, gc)
	return data_dict
'''
def download_data(symbol):
    for statement in statements:
        download_html(symbol ,statement)
    con = lite.connect('stock_data.db')
    cur = con.cursor()
    calculate_owners_earnings(symbol, cur)
    calculate_croic(symbol, cur)
    croic = get_data(symbol, "croic", "*", cur)
    calculate_multiyear(croic)
    con.commit()
    gr_array = croic[:-1]
    calculate_dcf(symbol, gr_array, cur)
    download_price(symbol)

if __name__ == "__main__":
    run()

