#this is master
import pickle
import plotly
import plotly.plotly as py
from pylab import *
from plotly.graph_objs import *
import sys
from plotly.graph_objs import Figure,Data,Scatter
import numpy as np
import webscrapper
import xlsxwriter
import string
import ystockquote
import requests
from lxml import html
import sys
import re

#To Run: Call program python in_depth.py SPREADSHEET_NAME INDUSTRY
def get_industry_symbols():
    industry = sys.argv[2]
    response = requests.get("http://www.investorguide.com/industry/"+industry)
    html_body = html.fromstring(response.text)
    links =  html_body.xpath('//div[@class="column one-half"]//a/@href')
    tickers = []
    for link in links:
        if "ticker" in link:
            ticker= re.search('=.*', link).group(0)[1:]
            tickers.append(ticker)
    return tickers

def print_multi_year(row, row_to_analyze, worksheet, cell_format):
    r = str(row_to_analyze)
    worksheet.write_formula('B'+str(row),'{=IF(AND(B'+r+'>0,H'+r+'>0),(H'+r+'/B'+r+')^(1/7)-1,0)}',cell_format)
    worksheet.write_formula('C'+str(row),'{=IF(AND(C'+r+'>0,I'+r+'>0),(I'+r+'/C'+r+')^(1/7)-1,0)}',cell_format)
    worksheet.write_formula('D'+str(row),'{=IF(AND(D'+r+'>0,J'+r+'>0),(J'+r+'/D'+r+')^(1/7)-1,0)}',cell_format)
    worksheet.write_formula('E'+str(row),'{=IF(AND(E'+r+'>0,K'+r+'>0),(K'+r+'/E'+r+')^(1/7)-1,0)}',cell_format)
    worksheet.write_formula('F'+str(row),'{=IF(AND(B'+r+'>0,F'+r+'>0),(F'+r+'/B'+r+')^(1/5)-1,0)}',cell_format)
    worksheet.write_formula('G'+str(row),'{=IF(AND(C'+r+'>0,G'+r+'>0),(G'+r+'/C'+r+')^(1/5)-1,0)}',cell_format)
    worksheet.write_formula('H'+str(row),'{=IF(AND(D'+r+'>0,H'+r+'>0),(H'+r+'/D'+r+')^(1/5)-1,0)}',cell_format)
    worksheet.write_formula('I'+str(row),'{=IF(AND(E'+r+'>0,I'+r+'>0),(I'+r+'/E'+r+')^(1/5)-1,0)}',cell_format)
    worksheet.write_formula('J'+str(row),'{=IF(AND(F'+r+'>0,J'+r+'>0),(J'+r+'/F'+r+')^(1/5)-1,0)}',cell_format)
    worksheet.write_formula('K'+str(row),'{=IF(AND(G'+r+'>0,K'+r+'>0),(K'+r+'/G'+r+')^(1/5)-1,0)}',cell_format)

def graham_analysis():
    stock_symbols =get_industry_symbols()#sys.argv[2:]# Change between sector vs individual modes
    title = sys.argv[1]
    #stock_symbols = #["VVTV", "SPF", "TAIT", "CRV", "BZH", "MSN", "TUES", "HDNG"]
      #"GM", "USG", "MCO", "DVA", "DTV", "XOM", "PG", "WMT", "IBM", "KO"]#"CNTF", "GRVY", "XIN"]#"GILD","MRK","ABBV","VRTX","GSK","BMY","PFE","NVS"]
    graham_dict = {}

    workbook = xlsxwriter.Workbook(title+'.xlsx')
    worksheet = workbook.add_worksheet()

    ### SET CELL FORMATS
    bold = workbook.add_format({'bold': True})
    num_format = workbook.add_format({'num_format': "0.00"})
    percent_format = workbook.add_format({'num_format': 0x09})
    bad = workbook.add_format({'bg_color': '#FFC7CE','font_color': '#9C0006', 'num_format': "0.00"})
    good = workbook.add_format({'bg_color': '#C6EFCE','font_color': '#006100', 'num_format': "0.00"})
    warning = workbook.add_format({'bg_color': '#ffff00','font_color': '#006100', 'num_format': "0.00"})

    col = list(string.ascii_uppercase)
    number_of_tickers = len(stock_symbols)
    j=0
    while len(col)<number_of_tickers:
        i=0
        while i<26:
            col.append(list(string.ascii_uppercase)[j]+list(string.ascii_uppercase)[i])
            i=i+1
        j=j+1

    ### SET WORKSHEET FORMATS
    worksheet.set_column(0, 0, 50)
    worksheet.conditional_format('B19:'+col[-1]+'23', {'type': 'cell', 'criteria':'<','value':0,'format':warning})
    worksheet.conditional_format('B23:'+col[-1]+'23', {'type': 'cell', 'criteria':'<','value':0,'format':bad})
    worksheet.conditional_format('B24:'+col[-1]+'24', {'type': 'cell', 'criteria':'<','value':0,'format':bad})
    worksheet.conditional_format('B24:'+col[-1]+'24', {'type': 'cell', 'criteria':'>=','value':15,'format':good})
    worksheet.conditional_format('B25:'+col[-1]+'25', {'type': 'cell', 'criteria':'<','value':0,'format':bad})
    worksheet.conditional_format('B25:'+col[-1]+'25', {'type': 'cell', 'criteria':'>=','value':10,'format':good})
    worksheet.conditional_format('B30:'+col[-1]+'30', {'type': 'cell', 'criteria':'<','value':0,'format':bad})
    worksheet.conditional_format('B31:'+col[-1]+'31', {'type': 'cell', 'criteria':'>=','value':10,'format':good})
    worksheet.conditional_format('B38:'+col[-1]+'38', {'type': 'cell', 'criteria':'>=','value':3,'format':good})

    worksheet.write('A3', "CAPITALIZATION", bold)
    worksheet.write("A4", "Bonds at par")
    worksheet.write("A5", "Preferred shares")
    worksheet.write("A6", "Price of preferred shares")
    worksheet.write("A7", "Common shares outstanding")
    worksheet.write("A8", "Price of common")
    worksheet.write("A9", "Preferred stock at market value")
    worksheet.write("A10", "Common stock at market value")
    worksheet.write("A11", "Total capitalization")
    worksheet.write("A12", "Ratio of bonds to total cap")
    worksheet.write("A13", "Ratio of market value of preferred to total cap")
    worksheet.write("A14", "Ratio of market value of common to market cap")

    worksheet.write("A16", "INCOME ACCOUNT", bold)
    worksheet.write("A17", "Gross sales")
    worksheet.write("A18", "EBITDA")
    worksheet.write("A19", "Depreciation*")
    worksheet.write("A20", "Net available for bond interest (EBIT)")
    worksheet.write("A21", "Bond interest")
    worksheet.write("A22", "Preferred dividend requirement")
    worksheet.write("A23", "Balance for common")
    worksheet.write("A24", "Margin of profit %")
    worksheet.write("A25", "% earned on total capitalization")

    worksheet.write("A27", "CALCULATIONS", bold)
    worksheet.write("A28", "Number of times interest charges earned")
    worksheet.write("A29", "I.P. Number of times interest charges + preferred dividends earned")
    worksheet.write("A30", "Earned on common per share")
    worksheet.write("A31", "Earned on common % of market price (e/p)")
    worksheet.write("A32", "S.P. Earned on common per share")
    worksheet.write("A33", "S.P. Earned on common % of market price")
    worksheet.write("A34", "Ratio of gross to aggregate market value of common")
    worksheet.write("A35", "Ratio of gross to aggregate market value of preferred")

    worksheet.write("A37", "HISTORICAL AVERAGES (See Below)", bold)
    worksheet.write("A38", "Number of times interest charges earned")
    worksheet.write("A39", "Earned on common stock per share")
    worksheet.write("A40", "Earned on common stock, % of current market price (e/p)")

    worksheet.write("A42", "DIVIDENDS", bold)#Graph?
    worksheet.write("A43", "Dividend rate on common")
    worksheet.write("A44", "Dividend yield on common %")

    worksheet.write("A46", "BALANCE SHEET", bold)
    worksheet.write("A47", "Cash assets")
    worksheet.write("A48", "Receivables (less reserves)*")
    worksheet.write("A49", "Inventories (less proper reserves)")
    worksheet.write("A50", "Total current assets")
    worksheet.write("A51", "Total current liabilities")
    worksheet.write("A52", "Total net current assets")
    worksheet.write("A53", "Ratio of current assets to current liabilities")
    worksheet.write("A54", "Total liabilities")
    worksheet.write("A55", "Net tangible assets available for total capitalization")
    worksheet.write("A56", "Cash-asset value of common per share (deducting all prior obligations)")
    worksheet.write("A57", "Net current asset value of common per share (deducting all prior obligations)")
    worksheet.write("A58", "Net tangible asset value of common per share (deducting all prior obligations)")

    worksheet.write("A60", "SUPPLEMENTAL DATA*", bold)
    worksheet.write("A61", "Discount", bold)

    worksheet.write("A68", "AVERAGE GROWTH", bold)
    worksheet.write("A69", "Earned per share of common stock growth")
    worksheet.write("A70", "Owners earnings per share growth")
    worksheet.write("A71", "CROIC")


    i=1
    start = 74
    for stock in stock_symbols:

        worksheet.write(col[i]+'1', stock, bold)
        try:
            data_dict = webscrapper.load_data_from_pickle(stock)
        except IOError:
            print stock +" Ticker not found"
            continue
        graham_dict[stock]={}
        webscrapper.calculate_owners_earnings(data_dict)
        ##### CAPITALIZATION ######
        worksheet.write(col[i]+'4', data_dict["long-term debt"][-1])
        worksheet.write(col[i]+'5', data_dict["preferred shares"][-1])
        worksheet.write(col[i]+'7', data_dict["total common shares out"][-1])
        #gd_client, gc= webscrapper.gdocs_login()
        try:
            price = float(ystockquote.get_price(stock))
        except ValueError:
            price = 0
        worksheet.write(col[i]+'8', price, num_format)
        worksheet.write_formula(col[i]+'9', '{=('+col[i]+'5*'+col[i]+'6)}', num_format)
        worksheet.write_formula(col[i]+'10', '{=('+col[i]+'7*'+col[i]+'8)}', num_format)
        worksheet.write_formula(col[i]+'11', '{='+col[i]+'4+'+col[i]+'9+'+col[i]+'10}', num_format)
        worksheet.write_formula(col[i]+'12', '{='+col[i]+'4/'+col[i]+'11}', num_format)
        worksheet.write_formula(col[i]+'13', '{='+col[i]+'9/'+col[i]+'11}', num_format)
        worksheet.write_formula(col[i]+'14', '{='+col[i]+'10/'+col[i]+'11}', num_format)
        #graham_dict[stock]["total capitalization"]=graham_dict[stock]["bonds at par"]+ graham_dict[stock]["preferred stock equity"]+ graham_dict[stock]["common stock equity"]
        #if not(graham_dict[stock]["total capitalization"]==data_dict["total capitalization"][-1]):
        #    print "capitizaltion is fishy"
        num_years = len(data_dict["operating revenue"])
        #####  INCOME ACCOUNT #####
        last_annual = -1
        worksheet.write(col[i]+'17', data_dict["operating revenue"][last_annual])
        worksheet.write(col[i]+'18', data_dict["EBITDA"][last_annual])
        worksheet.write(col[i]+'19', -data_dict["depreciation (unrecognized)"][last_annual])
        worksheet.write_formula(col[i]+'20', '{='+col[i]+'18-'+col[i]+'19}', num_format)
        worksheet.write(col[i]+'21', data_dict["interest expense"][last_annual])
        worksheet.write(col[i]+'22', data_dict["preferred dividends"][last_annual])
        worksheet.write_formula(col[i]+'23', '{='+col[i]+'20-'+col[i]+'21-'+col[i]+'22}', num_format)
        worksheet.write_formula(col[i]+'24', '{='+col[i]+'20*100/'+col[i]+'17}', num_format)
        worksheet.write_formula(col[i]+'25', '{='+col[i]+'20*100/'+col[i]+'11}', num_format)

        #####  CALCULATIONS   #####
        worksheet.write_formula(col[i]+'28', '{='+col[i]+'20/'+col[i]+'21}', num_format)
        worksheet.write_formula(col[i]+'29', '{='+col[i]+'20/'+col[i]+'22}', num_format)
        worksheet.write_formula(col[i]+'30', '{='+col[i]+'23/'+col[i]+'7}', num_format)
        worksheet.write_formula(col[i]+'31', '{=100*'+col[i]+'30/'+col[i]+'8}', num_format)
        worksheet.write_formula(col[i]+'32', '{='+col[i]+'22/'+col[i]+'5}', num_format)
        worksheet.write_formula(col[i]+'33', '{='+col[i]+'32/'+col[i]+'6}', num_format)
        worksheet.write_formula(col[i]+'34', '{='+col[i]+'17/'+col[i]+'10}', num_format)
        worksheet.write_formula(col[i]+'35', '{='+col[i]+'17/'+col[i]+'9}', num_format)

        #####  HISTORICAL AVERAGE #####

        worksheet.write_formula(col[i]+'38', '{=AVERAGE('+col[1]+str(start+3)+':'+col[num_years]+str(start+3)+')/'+col[i]+'21}', num_format)
        worksheet.write_formula(col[i]+'39', '{=AVERAGE('+col[1]+str(start+3)+':'+col[num_years]+str(start+3)+')/'+col[i]+'7'+'}', num_format)
        worksheet.write_formula(col[i]+'40', '{=100*'+col[i]+'39/'+col[i]+'8}', num_format)



        #####  DIVIDENDS     #####
        worksheet.write(col[i]+'43', data_dict["Dividends Paid Per Share (DPS)"][last_annual])
        worksheet.write_formula(col[i]+'44', '{=100*'+col[i]+'43/'+col[i]+'8}', num_format)

        #####  BALANCE SHEET #####
        worksheet.write(col[i]+'47', data_dict["cash & equivalents"][-1]+data_dict["restricted cash"][-1]+data_dict["marketable securities"][-1])
        worksheet.write(col[i]+'48', data_dict["receivables"][-1])
        worksheet.write(col[i]+'49', data_dict["inventories"][-1])
        worksheet.write_formula(col[i]+'50', '{='+col[i]+'47+'+col[i]+'48+'+col[i]+'49}', num_format)
        worksheet.write(col[i]+'51', data_dict["total current liabilities"][-1])
        worksheet.write_formula(col[i]+'52', '{='+col[i]+'50-'+col[i]+'51}', num_format)
        worksheet.write_formula(col[i]+'53', '{='+col[i]+'50/'+col[i]+'51}', num_format)
        worksheet.write(col[i]+'54', data_dict["total liabilities"][-1])
        worksheet.write(col[i]+'55', data_dict["total current assets"][-1]+data_dict["total fixed assets"][-1]-data_dict["total liabilities"][-1])
        worksheet.write_formula(col[i]+'56', '{=('+col[i]+'47-'+col[i]+'54)/'+col[i]+'7}', num_format)
        worksheet.write_formula(col[i]+'57', '{=('+col[i]+'50-'+col[i]+'54)/'+col[i]+'7}', num_format)
        worksheet.write_formula(col[i]+'58', '{=('+col[i]+'55-'+col[i]+'54)/'+col[i]+'7}', num_format)

        #####  SUPPLEMENTAL DATA #####
        worksheet.write_formula(col[i]+'61', '{=1-(1/'+col[i]+'31)/AVERAGE('+col[i]+'69:'+col[i]+'71)}', percent_format)

        #####  TREND FIGURE  #####
        worksheet.write("A"+str(start), "HISTORICAL DATA FOR " + stock, bold)
        worksheet.write("A"+str(start+1), "EBITDA")
        worksheet.write("A"+str(start+2), "Depreciation*")
        worksheet.write("A"+str(start+3), "Net available for bond interest (EBIT)")
        worksheet.write("A"+str(start+4), "Common shares outstanding")
        worksheet.write("A"+str(start+5), "Earned per share of common stock")
        worksheet.write("A"+str(start+6), "Owners Earnings per share")
        worksheet.write("A"+str(start+7), "Earned per share of common stock growth")
        worksheet.write("A"+str(start+8), "Owners Earnings per share growth")
        worksheet.write("A"+str(start+9), "Croic")
        k=0
        print num_years
        while k<num_years:
            worksheet.write(col[k+1]+str(start+1), data_dict["EBITDA"][k], num_format)
            worksheet.write(col[k+1]+str(start+2), data_dict["EBITDA"][k]-data_dict["operating profit after depreciation"][k], num_format)
            worksheet.write_formula(col[k+1]+str(start+3), '{='+col[k+1]+str(start+1)+'-'+col[k+1]+str(start+2)+'}', num_format)
            worksheet.write(col[k+1]+str(start+4), data_dict["total common shares out"][k], num_format)
            worksheet.write_formula(col[k+1]+str(start+5), '{='+col[k+1]+str(start+3)+'/'+col[k+1]+str(start+4)+'}', num_format)
            worksheet.write_formula(col[k+1]+str(start+6), '{='+str(data_dict["owners earnings"][k])+'/'+str(col[k+1])+str(start+4)+'}', num_format)
            worksheet.write(col[k+1]+str(start+9), data_dict["croic"][k]/100, percent_format)
            k=k+1
        print_multi_year(start+7,start+5,worksheet, percent_format)
        print_multi_year(start+8,start+6,worksheet, percent_format)
        worksheet.write_formula(col[k+1]+str(start+7), '{=MEDIAN(B'+str(start+7)+':'+col[k]+str(start+7)+')}', percent_format)
        worksheet.write_formula(col[k+1]+str(start+8), '{=MEDIAN(B'+str(start+8)+':'+col[k]+str(start+8)+')}', percent_format)
        worksheet.write_formula(col[k+1]+str(start+9), '{=MEDIAN(B'+str(start+9)+':'+col[k]+str(start+9)+')}', percent_format)
        worksheet.write(col[num_years]+str(start+2), -data_dict["depreciation (unrecognized)"][num_years-1])

        #########NEED TO FIGURE OUT WHAT TO DO WITH LESS THAN 10 yrs of data when computing growth rates

        ##### Growth ####
        worksheet.write_formula(col[i]+'69', '{=MEDIAN(B'+str(start+7)+':K'+str(start+7)+')}', percent_format)
        worksheet.write_formula(col[i]+'70', '{=MEDIAN(B'+str(start+8)+':K'+str(start+8)+')}', percent_format)
        worksheet.write_formula(col[i]+'71', '{=MEDIAN(B'+str(start+9)+':K'+str(start+9)+')}', percent_format)
        i=i+1
        start = start+11
    workbook.close()

def plot_breakdown_of_croic():
    my_creds = plotly.tools.get_credentials_file()
    plotly.plotly.sign_in(my_creds['username'], my_creds['api_key'])
    negative_income = 0
    stock_symbols = ["GILD", "EME"]
    for stock in stock_symbols:
        data_dict = webscrapper.load_data_from_pickle(stock)
        print data_dict["owners earnings"]
        plot_data_dict = {}
        num_years = len(data_dict["interest expense"])
        print data_dict["total common shares out"][num_years-1]
        i = 0
        plot_data_dict["numerator"]=[]
        plot_data_dict["denominator"]=[]
        plot_data_dict["year end date"]=[]
        plot_data_dict["owners earnings"]=[]
        total_capex = 0
        net_earnings = 0
        while i<num_years:
            plot_data_dict["numerator"].append(0)
            plot_data_dict["denominator"].append(0)
            plot_data_dict["owners earnings"].append(0)
            plot_data_dict["year end date"].append("")
            total_capex = total_capex- data_dict["purchase of property, plant & equipment"][i]
            net_earnings = net_earnings + data_dict["net income (continuing operations)"][i]
            i=i+1
        i=0
        while i<num_years:
            excess_cash = data_dict["total current liabilities"][i]-data_dict["total current assets"][i]
            if excess_cash <0:
                excess_cash = 0
                plot_data_dict["year end date"][i]=data_dict["year end date"][i]
                plot_data_dict["owners earnings"][i]=data_dict["owners earnings"][i]
                plot_data_dict["numerator"][i]=data_dict["operating income"][i]-data_dict["income taxes"][i]
            if plot_data_dict["numerator"][i]<0:
                negative_income=negative_income+1
                plot_data_dict["denominator"][i]=data_dict["total equity"][i]+data_dict["total liabilities"][i]-data_dict["total current liabilities"][i]-(data_dict["cash & equivalents"][i]-excess_cash)

			  #cash flow
            i=i+1
        if not(negative_income == num_years):
			  i=0
			  key_list = plot_data_dict.keys()
			  trace_list=[]
			  for key in key_list:
				    if not(key=="year end date"):
					  trace = Scatter(x=plot_data_dict["year end date"],y=plot_data_dict[key], name=key, xaxis ='x1', yaxis='y2')
					  trace_list.append(trace)
			  key = "croic"
			  trace = Scatter(x=data_dict["year end date"],y=data_dict[key], name=key, xaxis ='x1', yaxis='y1')
			  trace_list.append(trace)
			  my_data = Data(trace_list)
			  my_layout = Layout(yaxis=YAxis(domain=[0, 0.45]),yaxis2=YAxis(domain=[0.5,1]))
 			  my_fig = Figure(data=my_data, layout=my_layout)
			  py.plot(my_fig)

					#else:
			  #print "negative income"
        print "Cash Flow Statement"
        print "10yr capex/10 yr net earnings = "+str(total_capex*100/net_earnings)+"<50% is good and <25% signals a business with a moat"

def run():
  graham_analysis()

if __name__ == "__main__":
	run()
