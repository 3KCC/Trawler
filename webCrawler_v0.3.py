import cookielib
import urllib
import urllib2
import re
import MySQLdb
import time
import datetime
from time import strftime

#constant
num_finding_cols = 6
order_col = 13
postData_col = 14
date_pos = 4

def Connect2Web(url, patterns, order, postData):

	if not postData:
		aResp = urllib2.urlopen(url)
		web_pg = aResp.read()
	else:
		# Store the cookies and create an opener that will hold them
		cj = cookielib.CookieJar()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
		# Install our opener (note that this changes the global opener to the one
		# we just made, but you can also just call opener.open() if you want)
		urllib2.install_opener(opener)
		# Build our Request object (supplying 'data' makes it a POST)
		req = urllib2.Request(url, postData)

		# Make the request and read the response
		try:
			resp = urllib2.urlopen(req)
			web_pg = resp.read()
		except urllib2.HTTPError, error:
			web_pg = error.read()

	#testing only
	#textfile = file('cache.txt','wt')
	#textfile.write(web_pg)
	#textfile.close()
	mainPattern = patterns[0]
	rates = web_pg[web_pg.find(mainPattern):]
	rates = re.sub(r"\s+", " ", rates)
	rates = finding(rates, patterns, order)

	return rates

#input: string of html text contains rates, start patern, end pattern and the order
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
			#if it does not have both start and end pattern, the website does not provide such the information
			if EP != "":
				content, i = getContent(webtext, SP, EP, i)
			#determine the value by setting default value in start pattern
			elif SP != "":
				content = SP
			if content == -1:
				break
			output.append(content)

		if len(output) == num_finding_cols:
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

	#convert patterns from tuple to list
	patterns = list(patterns)

	# standard order [0,1,2,3,4,5] = [buyCCY, sellCCY, bid, offer, date, unit]
	order = convertToList(patterns[order_col])
	postData = patterns[postData_col]
	patterns = patterns[:postData_col-1]

	data = Connect2Web(url, patterns, order, postData)
	vals = []

	for e in data:
		#[buyCCY, sellCCY, bid, offer, date, unit]
		full_date = e[date_pos].strip()
		if full_date and full_date != '-':
			try:
				full_date = time.strptime(full_date,'%A, %d %b %Y %H:%M:%S')
			except ValueError:
				try:
					full_date = time.strptime(full_date, '%m/%d/%Y at %H:%M %p')
				except ValueError:
					try:
						full_date = time.strptime(full_date, '%d/%m %H:%M:%S')
					except ValueError:
						print "Date Time format does not matched our stored format. Please review and update!"
						break
		else:
			#if it does not provide the time, take the current time
			full_date = datetime.datetime.now().timetuple()
		
		#deal with %m/%d - no year indicator, have to push the current year into time_struct/tuple format
		if full_date[0] == 1900: #year part
			full_date = time.struct_time(tuple([time.localtime()[0]]) + full_date[1:]) #tuple objects are immutable, need to construct a new obj

		date_p = strftime('%d-%m-%Y', full_date)
		short_date = strftime('%d%m%y', full_date)
		time_p = strftime('%H:%M:%S', full_date)
		#change date item to push it into a correct format
		e[4] = date_p
		#deal with CCYpair issue
		if len(e[0]) > 3:
			#the 2nd assignment for Insert to DB, 1st for generating ID
			sellCCY = e[0][:3]
			e[1] = sellCCY
			buyCCY = e[0][3:]
			e[0] = buyCCY
		else:
			buyCCY = e[0]
			sellCCY = e[1]

		#special case for EZFX
		if urlCode != 'EZFX':
			ID = generateID(short_date, urlCode, sellCCY, buyCCY)
		elif data.index(e) % 2 == 0:
			ID = generateID(short_date, 'MAY', sellCCY, buyCCY)
		else:
			#get buyCCY, sellCCY from Maybank rates. the 1st assignment for Insert to DB, 2nd for generating ID
			e[0] = data[data.index(e)-1][0]
			e[1] = data[data.index(e)-1][1]
			buyCCY = e[0]
			sellCCY = e[1]
			ID = generateID(short_date, 'CIT', sellCCY, buyCCY)

		row = [ID, urlCode]
		#push all into a tuple according pre-set format
		for entry in e:
			row.append(entry)
		row.insert(len(row)-1,time_p)
		vals.append(tuple(row))

	#determine which table to push data
	if urlCode == 'TRA' or urlCode == 'MMM':
		nameOfTb = 'RATES'
	else:
		nameOfTb = urlCode + 'rates'
	
	#Prepare SQL query to INSERT a record into the database.
	sql = "INSERT INTO " + nameOfTb + " (ID, URL, BUYCCY, SELLCCY, BID, OFFER, DATE_P, TIME_P, UNIT)\
			VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"

	try:
		# Execute the SQL command
		cursor.executemany(sql, tuple(vals))
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