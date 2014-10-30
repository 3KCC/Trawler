import urllib
import urllib2
import re
import MySQLdb
import time
from time import strftime

def Connect2Web(url, patterns):
	aResp = urllib2.urlopen(url)
	web_pg = aResp.read()

	mainPattern = patterns[0]
	rates = re.search(mainPattern, web_pg).group(1)
	rates = finding(rates, patterns)
	return rates

#input: string of html text contains rates, start patern, end pattern
#output: dictionary in form of [CurrencyCode, unit, bid, offer, date]
def finding(webtext,patterns):
	result = []
	i = 0 #starting position
	while i != -1:
		output = []
		for j in range(1,7):
			#find the buyCCY, sellCCY, bid, offer, date and unit (6)
			SP = patterns[j]
			EP = patterns[j+6]
			content = ""
			#if it does not have end pattern, the website does not provide such the information
			if EP != "":
				content, i = getContent(webtext, SP, EP, i)
			#determine the value by setting default value in start pattern
			elif SP != "":
				content = SP
			if content == -1:
				break
			output.append(content)
		if output:
			result.append(output)
	
	return result

#input: string to search, start patern, end pattern, starting index
#output: desired text in the content and the index at the end of content
def getContent(webtext, SP, EP, start):
	start = webtext.find(SP, start)
	content = -1
	end = -1

	if start != -1:
		start += len(SP)
		end = webtext.find(EP,start)
		content = webtext[start:end]

	#return -1, -1 if not found
	return content, end

#textfile = file('cache.txt','wt')
#textfile.write(Connect2Web())
#textfile.close()

#generate unique ID for each rate - FORMAT: DDMMYY-url-FCYLCY
def generateID(day, urlCode, FCY, LCY):
	return day+'-'+urlCode+'-'+FCY+LCY

#input: website name
#outout: [ID, url], [main_pattern, code_pattern, bid_pattern, offer_pattern, date_pattern, unit_pattern, 
#								code_endPattern, bid_endPattern, offer_endPattern, date_endPattern, unit_endPattern]
def getDetails(name):
	db = MySQLdb.connect("localhost","root","ezfx0109","crawlerdb")
	cursor = db.cursor()
	# Prepare SQL query to INSERT a record into the database.
	sql = "SELECT * FROM url \
	       WHERE name = '%s'" % (name)
	try:
		cursor.execute(sql)
		results = cursor.fetchone()
		return results[1:3],results[4:]
	except:
	   print "Error: unable to fecth data"
	db.close()

def insert(urlCode_url, patterns):
	db = MySQLdb.connect("localhost","root","ezfx0109","crawlerdb")
	cursor = db.cursor()
	
	urlCode = urlCode_url[0]
	url = urlCode_url[1]
	data = Connect2Web(url, patterns) # [buyCCY, sellCCY, bid, offer, date, unit]

	vals = []
	for e in data:
		#[buyCCY, sellCCY, bid, offer, date, unit]
		date = time.strptime(e[4],'%A, %d %b %Y %H:%M:%S')
		date = strftime('%d%m%y', date)
		buyCCY = e[0]
		sellCCY = e[1]
		ID = generateID(date, urlCode, buyCCY, sellCCY)
		row = [ID, urlCode]
		for entry in e:
			row.append(entry)
		vals.append(tuple(row))
		
	#Prepare SQL query to INSERT a record into the database.
	sql = """INSERT INTO RATES (ID, URL, BUYCCY, SELLCCY, BID, OFFER, DATE, UNIT)\
			VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
	try:
		# Execute the SQL command
		cursor.executemany(sql,tuple(vals))
		# Commit your changes in the database
		db.commit()
	except:
		# Rollback in case there is any error
		db.rollback()

	db.close()

def main():
	target = raw_input('Enter the name of target website: ')
	urlCode_url, patterns = getDetails(target)
	insert(urlCode_url, patterns)

main()