import urllib
import urllib2
import re

patterns ={'http://www.travelex.com.my/MY/For-Individuals/Foreign-Exchange-Rates/Today-s-Online-Rates/': '(var rates=.*)'}

def Connect2Web():
	url = 'http://www.travelex.com.my/MY/For-Individuals/Foreign-Exchange-Rates/Today-s-Online-Rates/'
	aResp = urllib2.urlopen(url)
	web_pg = aResp.read()
	rates = re.search(patterns[url], web_pg).group(1)
	start = rates.find('"USD","ExchangeRate":')
	start += len('"USD","ExchangeRate":')
	end = rates.find(',',start)
	USD = rates[start:end]
	print USD
Connect2Web()
#textfile = file('cache.txt','wt')
#textfile.write(Connect2Web())
#textfile.close()