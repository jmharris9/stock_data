import requests
from lxml import html
from locale import *
import numpy as np
import sys
import plotly
import plotly.plotly as py
from plotly.graph_objs import Figure,Data,Scatter
import urlparse
import pickle
import gdata.spreadsheet.service
import gspread
import glob


stock_symbols= sys.argv[1:]
alternating_row_xpaths = ['//tr[@bgcolor="#f0f0E7"]', '//tr[@bgcolor="#e5e5f3"]']
exchange_list = ['AMEX', 'NASDAQ', 'NYSE']
data_dict={}
ticker_dict_name = "ticker_list_dict.pkl"

#######      HELPERS     ##########

def load_data_from_pickle(symb):
	with open(symb+"_dict.pkl", "r") as f:
		return pickle.load(f)

def is_number(s):
        if s is None:
            return False
        try:
            atof(s)
            return True
        except ValueError:
            return False
        except AttributeError:
            return False

def lookup_exchange(symb):
    with open(ticker_dict_name) as f:
        ticker_dict = pickle.load(f)
	for exchange in exchange_list:
		if symb in ticker_dict[exchange]:
			return exchange
	return ""


def pickle_no_data():
    with open("no_data"+"_dict.pkl", "wb") as f:
		pickle.dump(no_data_dict,f)
    f.close()

######    DATA ACQUISITION    #########
def parse_html(html_body, years_to_add, data_dict):
	for path in alternating_row_xpaths:
                row = html_body.xpath(path)
                for x in row:
                    	key = x[0].text
                    	if not(key in data_dict):
                        	data_dict[key]=[]
                    	y=1
                    	while y<years_to_add+1:
                        	if is_number(x[y].text):
                           		data_point = atof(x[y].text)
                        	else:
                           		data_point = x[y].text
                        	data_dict[key].append(data_point)
                        	y=y+1
	return data_dict

def download_html(symb, year):
	exchange = lookup_exchange(symb) 	#####lookup your exchange
	if not(exchange == ""):			#####make sure stock is in an exchange
            	response = requests.get('http://www.advfn.com/exchanges/'+exchange+'/'+symb+'/financials?btn=start_date&start_date='+year+'&mode=annual_reports')
		print 'http://www.advfn.com/exchanges/'+exchange+'/'+symb+'/financials?btn=start_date&start_date='+year+'&mode=annual_reports'
		html_body = html.fromstring(response.text)
	        return html_body
	else:
		print symb, "exchange not found"


def years_of_data(html_body):
	years = html_body.xpath('//option')
	total_years = 0
	for i in years:
		if is_number(i.get('value')):
			total_years = total_years+1
	if total_years==0:
		total_years = 1
	return total_years

def load_data(symb, data_dict):
	setlocale(LC_NUMERIC, '')
	html_body1 = download_html(symb, "")
	#print html_body1.text
	#print html_body1.xpath('//option[@selected]')
	try:
		html_body1.xpath('//option[@selected]')[0].get('value')
	except IndexError:
		return data_dict, "other"
	if html_body1.xpath('//option[@selected]')[0].get('value')==None:
		selected_year = 0
	else:
		selected_year = atof(html_body1.xpath('//option[@selected]')[1].get('value'))
	total_years = years_of_data(html_body1)
	length=0
	if total_years<6:
		length = total_years
	elif total_years<10:
		new_selected_year = 0
		data_dict={}
		html_body2 = download_html(symb, str(new_selected_year))
		data_dict=parse_html(html_body2, total_years-5-new_selected_year, data_dict)
		try:
			data=data_dict["loans"]
			return data_dict, "bank"
		except KeyError:
			for i in range(total_years-5-new_selected_year):
				if data_dict['operating revenue'][i] > 0:
					new_selected_year = i
					break
		if new_selected_year>0:
			data_dict={}
			html_body2 = download_html(symb, str(new_selected_year))
			data_dict=parse_html(html_body2, total_years-5-new_selected_year, data_dict)


		length=5
	else:
		new_selected_year = total_years-10
		data_dict={}
		html_body2 = download_html(symb, str(new_selected_year))
		data_dict = parse_html(html_body2, 5+total_years-10-new_selected_year, data_dict)
		try:
			data=data_dict["loans"]
			return data_dict, "bank"
		except KeyError:
			for i in range(5):
				if data_dict['operating revenue'][i] > 0:
					new_selected_year = i
					break
		if new_selected_year>total_years-10:
			data_dict={}
			html_body2 = download_html(symb, str(new_selected_year))
			data_dict=parse_html(html_body2, total_years-5-new_selected_year, data_dict)
		length=5
	data_dict = parse_html(html_body1, length, data_dict)
	try:
		data = data_dict["operating revenue"]
		print symb
		iter=0
		num_years = len(data_dict["operating revenue"])
		while iter<num_years-1:
			cur_year = data_dict['year end date'][iter].split('/')[0]
			next_year = data_dict['year end date'][iter+1].split('/')[0]
			revenue = data_dict['operating revenue'][iter]
			if not(atof(cur_year) +1 == atof(next_year)):
				return data_dict, "missing years"
			if revenue == 0:
				return data_dict, "missing years"
			iter = iter+1
		return data_dict, "real"

	except KeyError:
		return data_dict, "other"

###### ANALYSIS #########

def calculate_croic(data_dict):
	num_years = len(data_dict["interest expense"])
	data_dict["croic"]=[]
	for i in range(num_years):
		data_dict["croic"].append(0)
	for i in range(num_years):
		if data_dict["total current liabilities"][i]>data_dict["total current assets"][i]:
			excess_cash = data_dict["total current liabilities"][i]-data_dict["total current assets"][i]
		else:
			excess_cash = 0.0
		data_dict["croic"][i]=0
		if not(data_dict["total equity"][i]+data_dict["total liabilities"][i]==data_dict["total current liabilities"][i]+data_dict["cash & equivalents"][i]+excess_cash) and data_dict["total equity"][i]>0:
			if (data_dict["total equity"][i]+data_dict["total liabilities"][i]-data_dict["total current liabilities"][i]-(data_dict["cash & equivalents"][i]-excess_cash))<0:
			##### what do you do if the denominator is negative?
				#if data_dict["operating income"][i]-data_dict["income taxes"][i]>0:
				#else:
				x=1
			else:
				data_dict["croic"][i]= (data_dict["operating income"][i]-data_dict["income taxes"][i])*100.0/(data_dict["total equity"][i]+data_dict["total liabilities"][i]-data_dict["total current liabilities"][i]-(data_dict["cash & equivalents"][i]-excess_cash))
		else:
			data_dict["croic"][i]=0.0
	#print "Mean CROIC = ",np.mean(data_dict["croic"])
	return data_dict

def calculate_multiyear(key, data_dict):
	median_key = "multiyear "+key
	num_years = len(data_dict["interest expense"])
	data_dict[median_key] = []
	for i in range(num_years):
		data_dict[median_key].append(0)
	if num_years<10:
		for i in range(num_years):
			data_dict[median_key][i]=np.median(data_dict[key][0:num_years-1])
	else:
		for i in range(4):
			data_dict[median_key][i]=np.median(data_dict[key][i:num_years-4+i])
		for i in range(6):
			data_dict[median_key][i+4]=np.median(data_dict[key][i:num_years-6+i])
	return data_dict

def calculate_multiyear_percent(key, data_dict):
	median_key = "multiyear "+key
	num_years = len(data_dict["interest expense"])
	data_dict[median_key] = []
	for i in range(num_years):
		data_dict[median_key].append(0)
	if num_years<10:
		for i in range(num_years-1):
			if data_dict[key][i]>0 and data_dict[key][i+1]>0:
				data_dict[median_key][i]=  ((data_dict[key][i+1]/data_dict[key][i])-1)*100
			else:
				data_dict[median_key][i]= 0
		data_dict[median_key][num_years-1]=np.median(data_dict[median_key])
	else:
		for i in range(4):
			if data_dict[key][i]>0 and data_dict[key][i+6]>0:
				data_dict[median_key][i] = ((data_dict[key][i+6]/data_dict[key][i])**(1/7.0) -1)*100
			else:
				data_dict[median_key][i] = 0
		for i in range(6):
			if data_dict[key][i]>0 and data_dict[key][i+4]>0:
				data_dict[median_key][i+4] = ((data_dict[key][i+4]/data_dict[key][i])**(1/5.0) -1)*100
			else:
				data_dict[median_key][i+4] = 0
	return data_dict

def calculate_dcf(data_dict, gr_array):
	growth_rate = np.amin(gr_array)
	#print gr_array
	discount_rate = 15
	terminal_growth_rate = 5
	rate = (1+growth_rate/100)/(1+discount_rate/100)
	terminal_rate = (1+terminal_growth_rate/100)/(1+discount_rate/100)
	last_key = len(data_dict["owners earnings"])-1
	#print last_key
	owners_earnings = data_dict["owners earnings"][last_key]
	data_dict["projected 10 year owners earnings"]=[]
	data_dict["projected 20 year owners earnings"]=[]
	for i in range(10):
		data_dict["projected 10 year owners earnings"].append(0)
		data_dict["projected 20 year owners earnings"].append(0)
	for i in range(10):
		data_dict["projected 10 year owners earnings"][i]= owners_earnings*rate
		owners_earnings = owners_earnings*rate
	for i in range(10):
		data_dict["projected 20 year owners earnings"][i]= owners_earnings*terminal_rate
        owners_earnings = owners_earnings*terminal_rate
	total_future_cash = (np.sum(data_dict["projected 10 year owners earnings"]) + np.sum(data_dict["projected 20 year owners earnings"]))/data_dict["total common shares out"][last_key]
	#print "total future cash per share =",total_future_cash
	return total_future_cash

def calculate_owners_earnings(data_dict):
	num_years = len(data_dict["interest expense"])
	data_dict["owners earnings"]=[]
	for i in range(num_years):
		data_dict["owners earnings"].append(0)
	if num_years>5:
		start = num_years-5
	else:
		start = 1
	mean_ppe = np.mean(data_dict["purchase of property, plant & equipment"][start:num_years])
	for i in range(num_years):
		data_dict["owners earnings"][i] = data_dict["net cash from continuing operations"][i]-data_dict["deferred income taxes"][i]-data_dict["operating gains"][i]-data_dict["extraordinary gains"][i]-mean_ppe
	return data_dict

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

######## RECORD RESULTS ###########
def plot_data(key_list, data_dict):
	my_creds = plotly.tools.get_credentials_file()
	plotly.plotly.sign_in(my_creds['username'], my_creds['api_key'])
	i=0
	trace_list = []
	for key in key_list:
		trace = Scatter(x=data_dict["year end date"],y=data_dict[key], name=key)
		trace_list.append(trace)
	my_data = Data(trace_list)
	my_fig = Figure(data=my_data)
	py.plot(my_fig)

def write_to_gdocs(ticker, value, data_dict):
	last_key = len(data_dict['croic'])-1
	spreadsheet_key = '1A9uLVV21BEZBhuSBhDMUUnoP_ICAzz2YAkVKCGWZHQs'
	worksheet_key = 'od6'
	gd_client = gdata.spreadsheet.service.SpreadsheetsService(spreadsheet_key, worksheet_key)
	gd_client.email = 'jmharris9@gmail.com'
	gd_client.password = "alkezuowfwtexxer"
	gd_client.ProgrammaticLogin()

	dict = {'symbol':ticker, 'croic':str(np.median(data_dict["multiyear croic"])), 'value': value}
	gd_client.InsertRow(dict, spreadsheet_key, worksheet_key)
	list_feed = gd_client.GetListFeed(spreadsheet_key, worksheet_key)
	#for entry in list_feed.entry:
	#	print "%s: %s\n" % (entry.title.text, entry.content.text)

def gdocs_login():
	spreadsheet_key = '1A9uLVV21BEZBhuSBhDMUUnoP_ICAzz2YAkVKCGWZHQs'
	worksheet_key = 'od6'
	gd_client = gdata.spreadsheet.service.SpreadsheetsService(spreadsheet_key, worksheet_key)
	gd_client.email = 'jmharris9@gmail.com'
	gd_client.password = "alkezuowfwtexxer"
	gd_client.ProgrammaticLogin()
	gc = gspread.login('jmharris9@gmail.com', "alkezuowfwtexxer")
	return gd_client, gc

def test_write_to_gdocs(ticker, value, data_dict, gd_client, gc):
	header_dict={}
	header_keys = ['croic', 'value']
	spreadsheet_key = '1A9uLVV21BEZBhuSBhDMUUnoP_ICAzz2YAkVKCGWZHQs'
	worksheet_key = 'od6'
	num_years = len(data_dict["interest expense"])
	if num_years>1:
		dict = {'symbol':ticker, 'croic':str(np.median(data_dict["multiyear croic"])), 'value': value}
	else:
		dict = {'symbol':ticker, 'croic':str(np.median(data_dict["croic"])), 'value': value}
	wks = gc.open("python_stock_data").sheet1
	for key in header_keys:
		header_dict[key]=wks.find(key).col
	try:
		row = int(wks.find(ticker).row)
		for key in header_dict:
			wks.update_cell(row, int(header_dict[key]), dict[key])
	except gspread.exceptions.CellNotFound:
		gd_client.InsertRow(dict, spreadsheet_key, worksheet_key)

#### Plots data
def test(data_dict):
	plot_these=["owners earnings", "free cash flow"]
	plot_data(plot_these, data_dict)
	plot_these=["croic", "Return on Assets (ROA)", "Return on Capital Invested (ROCI)", "Return on Stock Equity (ROE)"]
	plot_data(plot_these, data_dict)

def get_price(ticker, gd_client, gc):
	spreadsheet_key = '1A9uLVV21BEZBhuSBhDMUUnoP_ICAzz2YAkVKCGWZHQs'
	worksheet_key = 'od6'
	wks = gc.open("python_stock_data").sheet1
	column= int(wks.find('price').col)
	row = int(wks.find(ticker).row)
	price = wks.cell(row, column).value
	return price

def webscrape_indicies():
	stocks_that_didnt_work={}
	stocks_that_didnt_work["bank"]=[]
	stocks_that_didnt_work['other']=[]
	stocks_that_didnt_work['missing years']=[]
	with open(ticker_dict_name) as f:
           	ticker_dict = pickle.load(f)
	finished_stocks = glob.glob("*dict.pkl")
	gd_client, gc = gdocs_login()
	for exchange in exchange_list:
		for symb in ticker_dict[exchange]:
	#for symb in stock_symbols:
			#for char in symb:
			#		if char in ".":
			#			symb=symb.replace(char,'')
			if not (symb in no_data_dict['not_real_tickers'] or symb+"_dict.pkl" in finished_stocks or symb in no_data_dict['missing_years'] or symb in no_data_dict['banks']):
				print stocks_that_didnt_work
				data_dict={}
				data_dict, type = load_data(symb, data_dict)
				print type
				if type == "real":
					#data_dict = load_data_from_pickle(symb)
					data_dict = analyze_data(symb, data_dict, gd_client, gc)
					#test(data_dict)
					with open(symb+"_dict.pkl", "wb") as f:
						pickle.dump(data_dict,f)
					f.close()
				else:
					stocks_that_didnt_work[type].append(symb)
	print stocks_that_didnt_work

def run():
    webscrape_indicies()



if __name__ == "__main__":
	run()

