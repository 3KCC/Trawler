import urllib
import urllib2
import re

patterns ={'http://www.travelex.com.my/MY/For-Individuals/Foreign-Exchange-Rates/Today-s-Online-Rates/': '(var rates=.*)'}

def Connect2Web():
	url = 'http://www.travelex.com.my/MY/For-Individuals/Foreign-Exchange-Rates/Today-s-Online-Rates/'
	aResp = urllib2.urlopen(url)
	web_pg = aResp.read()
	rates = re.search(patterns[url], web_pg).group(1)
	rates = findRates(rates)
	
	
	return str(rates)

#input: string of html text contains rates
#output: dictionary in form of {'Currency Code': rates}
def findRates(webtext):

	result = {}
	i = 0
	while i != -1:
		#find the currency code
		CcyCode, i = getContent(webtext, 'CurrencyCode":"', i)
		ExRate, i = getContent(webtext, 'ExchangeRate":', i)
		if i == -1 :
			break
		result[CcyCode] = ExRate
	
	return result

#input: string to search, index of string to begin search, the patterns
#output: desired text in the content and the index at the end of content
def getContent(webtext, patterns, start):
	start = webtext.find(patterns, start)
	content = -1
	end = -1

	if start != -1:
		start += len(patterns)
		end = webtext.find('"',start)
		content = webtext[start:end]

	#return -1 if not found
	return content, end

textfile = file('cache.txt','wt')
textfile.write(Connect2Web())
textfile.close()