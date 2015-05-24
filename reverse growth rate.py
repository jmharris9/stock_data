from __future__ import division
import pickle
import plotly
import plotly.plotly as py
import glob
import sys
from plotly.graph_objs import Figure,Data,Scatter
import numpy as np
import webscrapper
from sympy import *

stock_symbol= sys.argv[1]


def run():
	r = symbols('r')
	gd_client, gc = webscrapper.gdocs_login()
    	data_dict = webscrapper.load_data_from_pickle(stock_symbol)
    	num_years = len(data_dict["interest expense"])
	stock_price = float(webscrapper.get_price(stock_symbol, gd_client, gc))
	total_cost = stock_price*data_dict["total common shares out"][num_years-1]
	oe=data_dict["owners earnings"][num_years-1]
	terminal_rate = 1.05/1.15
	roots = real_roots(r**10-((total_cost-(oe*r**10)*terminal_rate)/oe)*r+((total_cost-(oe*r**10)*terminal_rate)/oe)-1)
	print roots
	for root in roots:
		if not(root==1):
			assumed_value = ((float(root)*1.15)-1)*100
			#if assumed_value>0:
	 		print assumed_value,"%"

if __name__ == "__main__":
	run()

