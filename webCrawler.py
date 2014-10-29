import urllib
import urllib2
import re
import MySQLdb

patterns ={'http://www.travelex.com.my/MY/For-Individuals/Foreign-Exchange-Rates/Today-s-Online-Rates/': '(var rates=.*)'}

def Connect2Web(url, pattern):
	aResp = urllib2.urlopen(url)
	web_pg = aResp.read()
	rates = re.search(pattern, web_pg).group(1)
	rates = findRates(rates)
	return rates

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
		result[CcyCode] = ExRate[:-1]
	
	return result

#input: string to search, start patern, end pattern, starting index
#output: desired text in the content and the index at the end of content
def getContent(webtext, SP, EP, start):
	start = webtext.find(SP, start)
	content = -1
	end = -1

	if start != -1:
		start += len(patterns)
		end = webtext.find('"',start)
		content = webtext[start:end]

	#return -1 if not found
	return content, end

#textfile = file('cache.txt','wt')
#textfile.write(Connect2Web())
#textfile.close()

#generate unique ID for each rate - FORMAT: DDMMYY-url-FCYLCY
def generateID(day, url, LCY, FCY):
	return day+'-'+url+'-'+FCY+LCY

#input: website name
#outout: ID, url, patterns
def getDetails(name):
	db = MySQLdb.connect("localhost","root","ezfx0109","crawlerdb")
	cursor = db.cursor()
	# Prepare SQL query to INSERT a record into the database.
	sql = "SELECT * FROM url \
	       WHERE name = '%s'" % (name)
	try:
		cursor.execute(sql)
		results = cursor.fetchone()
		return results[1],results[2],results[4]
	except:
	   print "Error: unable to fecth data"
	db.close()

def insert(url, pattern):
	db = MySQLdb.connect("localhost","root","ezfx0109","crawlerdb")
	cursor = db.cursor()
	#Prepare SQL query to INSERT a record into the database.
	rates = Connect2Web(url, pattern)
	vals = []
	for e in rates:
		sellCCY = e
		offer = rates[e]
		vals.append((sellCCY,offer))

	sql = "INSERT INTO RATES (SELLCCY, OFFER)\
			VALUES (%s, %s)"
	try:
		# Execute the SQL command
		cursor.executemany(sql,vals)
		# Commit your changes in the database
		db.commit()
	except:
		# Rollback in case there is any error
		db.rollback()
	db.close()

def main():
	target = raw_input('Enter the name of target website: ')
	ID, url, pattern = getDetails(target)
	print pattern
	insert(url, pattern)

main()