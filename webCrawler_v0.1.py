import urllib
import urllib2
import re
import MySQLdb
import time
from time import strftime

def Connect2Web(url, patterns, order):
	aResp = urllib2.urlopen(url)
	web_pg = aResp.read()

	mainPattern = patterns[0]
	rates = web_pg[web_pg.find(mainPattern):]
	rates = re.sub(r"\s+", " ", rates)
	rates = finding(rates, patterns, order)

	return rates

#input: string of html text contains rates, start patern, end pattern
#output: dictionary in form of [CurrencyCode, unit, bid, offer, date]
def finding(webtext, patterns, order):
	result = []
	i = 0 #starting position
	while i != -1:
		output = []
		for j in range(0,6):
			#find the buyCCY, sellCCY, bid, offer, date and unit (6) according to order
			SP = patterns[order[j]+1]
			EP = patterns[order[j]+7]
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
			#re-order before adding to result
			output = reOrder(output, order)
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
		end += 1

	#return -1, -1 if not found, end + 1 to avoid capturing the wrong text when the sign to recognize is not unique
	return content, end

#reorganize the output to follow the standard order [buyCCY, sellCCY, bid, offer, date, unit]
#input: the list and the current order
#output: list follow the standard order [0,1,2,3,4,5]
def reOrder(lst, order):
	i = 0
	temp = [] + order #to avoid the order change after going through process
	while i < len(temp):
		if i != temp[i]:
			#find current position of the right item for position i
			pos = temp.index(i)
			#swap it with the item in the position i
			lst[i], lst[pos] = lst[pos], lst[i]
			#update the order
			temp[i], temp[pos] = temp[pos], temp[i]
		i += 1

	return lst

#textfile = file('cache.txt','wt')
#textfile.write(Connect2Web())
#textfile.close()

#generate unique ID for each rate - FORMAT: DDMMYY-url-FCYLCY
def generateID(day, urlCode, FCY, LCY):
	return day+'-'+urlCode+'-'+FCY+LCY

#input: website name
#outout: [ID, url], [main_pattern, buyCCY_pattern, sellCCY_pattern, bid_pattern, offer_pattern, date_pattern, unit_pattern, 
#								buyCCY_endPattern, selCCY_pattern, bid_endPattern, offer_endPattern, date_endPattern, unit_endPattern,
#					order]
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
	# standard order [0,1,2,3,4,5] = [buyCCY, sellCCY, bid, offer, date, unit]
	order = convertToList(patterns[13])
	data = Connect2Web(url, patterns, order)

	vals = []
	
	for e in data:
		#[buyCCY, sellCCY, bid, offer, date, unit]
		date = e[4]
		while True:
			try:
				date = time.strptime(date,'%A, %d %b %Y %H:%M:%S')
				break
			except ValueError:
				try:
					date = time.strptime(date, '%m/%d/%Y at %H:%M %p')
					break
				except ValueError:
					print "Date Time format does not matched our stored format. Please review and update!"
					break
		date = strftime('%d%m%y', date)

		buyCCY = e[0]
		sellCCY = e[1]
		ID = generateID(date, urlCode, sellCCY, buyCCY)
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

#find the order of the website data, put it into list for taking out correctly in insert()
#input: a text '0,1,2,3,4,5'
#output: a list [0,1,2,3,4,5] - mapping for turn string into integer for the whole list
def convertToList(txt):
	return map(int, txt.split(','))

def main():
	target = raw_input('Enter the name of target website: ')
	urlCode_url, patterns = getDetails(target)
	insert(urlCode_url, patterns)

main()