import requests
from lxml import html
import sys
import re

def run():
    industry = sys.argv[1]
    response = requests.get("http://www.investorguide.com/industry/"+industry)
    html_body = html.fromstring(response.text)
    links =  html_body.xpath('//div[@class="column one-half"]//a/@href')
    #print links
    for link in links:
        if "ticker" in link:
            x= re.search('=.*', link).group(0)[1:]
            print x
run()