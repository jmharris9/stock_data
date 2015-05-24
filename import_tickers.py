import pickle
import csv

exchange_list = ['AMEX.txt', 'NASDAQ.txt', 'NYSE.txt']
ticker_dict = {}
for exchange in exchange_list:
    ticker_dict[exchange[:-4]]=[]
    with open(exchange, 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            x = row[0].split('\t')[0]
            if not x == 'Symbol':
                ticker_dict[exchange[:-4]].append(x)
    f.close()
with open("ticker_list_dict.pkl", "wb") as f:
    pickle.dump(ticker_dict,f)
f.close()
with open("ticker_list_dict.pkl") as f:
    test_dict=pickle.load(f)
    print test_dict["AMEX"]
