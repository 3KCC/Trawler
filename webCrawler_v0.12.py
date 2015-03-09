import cookielib
import urllib
import urllib2
import re
import MySQLdb
import time
import datetime
from time import strftime

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver

import ast

import collections

#constant
num_finding_cols = 6
order_col = 13
postData_col = 14
date_pos = 4
recursive_col = 15
main_end_col = 17
inverse_col = 18
method_col = 19
dynamic_col = 20
dynamicData_col = 28
exception_col = 29
checkCcyAvai_col = 30

#junk words
listOfJunk = ['min', 'minFee']


def getListOfUrl(source, start, end):
	#crawl plain text webpage
	aResp = urllib2.urlopen(source)
	web_pg = aResp.read()

	#only keep the portion that has the necessary info
	web_pg = web_pg[web_pg.find(start):web_pg.find(end)]
	web_pg = re.sub(r"\s+", " ", web_pg)
	listOfUrls = []

	pointer = 0
	#do until cannot find any href(s) in the web text
	while pointer != -1:
		url,pointer = getContent(web_pg, "href=\"", "\"", pointer)
		if url != -1:
			listOfUrls.append(url)

	return listOfUrls

def getDynamicList(source, method, patterns, postData='', dynamicData=''):
	#crawl plain text webpage
	#only keep the portion that has the necessary info
	#patterns = [baseMainStart, baseStart, baseMainEnd, CountermainStart, counterStart, counterEnd, counterMainEnd]
	base_main_start = patterns[0]
	base_main_end = patterns[3]
	counter_main_start = patterns[4]
	counter_main_end = patterns[7]

	if base_main_end != '' or counter_main_end != '':
		web_pg, ccyPairs = crawlWeb(source, method, postData, dynamicData)

		ccyList = []
		i = 0
		while i < 5:
			listOfResults = []
			pointer = 0
			start = patterns[i + 1]
			end = patterns[i + 2]
			if end != '':
				begin = web_pg.find(patterns[i]) + len(patterns[i])
				final = web_pg.find(patterns[i+3])
				content = web_pg[begin:final]
				content = re.sub(r"\s+", " ", content)
				
				#do until the end of the web text
				while pointer != -1:
					result, pointer = getContent(content, start, end, pointer)
					if result != -1 and len(result) == 3:
						listOfResults.append(result)
			else:
				if len(start) > 3:
					listOfResults = start.split(',')
			i += 4
			ccyList.append(listOfResults)
	else:
		if len(base_main_start) > 3:
			base_main_start = base_main_start.split(',')
		if len(counter_main_start) > 3:
			counter_main_start = counter_main_start.split(',')

		ccyList = [base_main_start, counter_main_start]

	return ccyList[0], ccyList[1]

def crawlWeb(url, method, postData='', dynamicData='', patterns='', endPattern=''):

	if method == 1:
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
	else:
		if not dynamicData:
			wd = webdriver.PhantomJS()
			wd.get(url)
			web_pg = wd.page_source
		else:
			wd = webdriver.PhantomJS()
			wd.get(url)

			listOfWebs = []
			ccyPairs = []

			if len(dynamicData) == 3:
				baseList = dynamicData[0]
				counterList = dynamicData[1]
				nameList = dynamicData[2]

				#1st loop for each baseCCY in baseList to all counterCCY in counterList
				for entry in baseList:
					for e in counterList:
						'''
						#choose baseCCY
						wd.find_element_by_name(nameList[0]).send_keys(entry)
						#choose counterCCY
						wd.find_element_by_name(nameList[1]).send_keys(e)
						#click
						wd.find_element_by_name(nameList[2]).click()
						'''
						handleRequests(wd, nameList, [entry, e])
						'''
						time.sleep(1)
						web_pg = getContent(wd.page_source, patterns[0], endPattern, 0)
						listOfWebs.append(web_pg)
						'''
						addWebpage(wd, listOfWebs, patterns[0], endPattern, 0, url, [entry, e])
						ccyPairs.append([entry, e])
				#2nd loop for baseCCY in baseList together
				#var i to prevent duplicates
				i = 1
				for entry in baseList:
					if i <= len(baseList):
						for e in baseList[i:]:
							'''
							#choose baseCCY
							wd.find_element_by_name(nameList[0]).send_keys(entry)
							#choose counterCCY
							wd.find_element_by_name(nameList[1]).send_keys(e)
							#click
							wd.find_element_by_name(nameList[2]).click()
							'''
							handleRequests(wd, nameList, [entry, e])
							'''
							time.sleep(1)
							web_pg = getContent(wd.page_source, patterns[0], endPattern, 0)
							listOfWebs.append(web_pg)
							'''
							addWebpage(wd, listOfWebs, patterns[0], endPattern, 0, url, [entry, e])
							ccyPairs.append([entry, e])

					i += 1
			else:
				baseList = dynamicData[0]
				nameList = dynamicData[1]
				for entry in baseList:
					handleRequests(wd, nameList, [entry])

					addWebpage(wd, listOfWebs, patterns[0], endPattern, 0, url, [entry])

			return listOfWebs, ccyPairs

	#testing only
	#textfile = file('cache.txt','wt')
	#textfile.write(web_pg.encode('utf8'))
	#textfile.close()

	return web_pg, []

def sendRequest(web, name, key):
	try:
		web.find_element_by_name(name).send_keys(key)
	except:
		element = web.find_element_by_id(name)
		for option in element.find_elements_by_tag_name('option'):
		    if option.text == key:
		        option.click() # select() in earlier versions of webdriver
		        break

def clickElement(web, name):
	web.find_element_by_name(name).click()

def handleRequests(web, nameList, keyList):
	for i in range(0, len(nameList)):
		if i < 2:
			#only send request for base or counter CCY
			sendRequest(web, nameList[i], keyList[i])
		else:
			clickElement(web, nameList[i])

def addWebpage(web, listOfWebs, SP, EP, start, url, request):
	#time.sleep(1)
	try:
		WebDriverWait(web, 20).until(ajax_complete,  "Timeout waiting for page to load")
		web_pg, end = getContent(web.page_source, SP, EP, start)
	except:
		print url + ' didn\'t response with the following request '+ str(request) +' .We have skipped it.'
		web_pg = ''
	
	listOfWebs.append(web_pg)

def ajax_complete(driver):
    try:
        return 0 == driver.execute_script("return jQuery.active")
    except WebDriverException:
        pass

def parseText(web_pg, patterns, order, endPattern, filtered):

	if not filtered:
		mainPattern = patterns[0]
		if not endPattern:
			rates = web_pg[web_pg.find(mainPattern):]
		else:
			rates = web_pg[web_pg.find(mainPattern) : web_pg.find(endPattern)]
	else:
		rates = web_pg
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
				if isinstance(SP, basestring):
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
		if content in listOfJunk:
			content, end = getContent(webtext, SP, EP, end)

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
	#db = MySQLdb.connect("localhost","root","ezfx0109","testdb")
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

#search for ccy Code with given country name
def getCode(country):
	code = country

	#check if it is a junk word. Unecessary because in getContent function. It is checked
	#if code in listOfJunk:
		#return False

	#case1: 3 chars given -> check if it is a valid code in ID column
	if len(code) == 3:
		#check valid code
		if checkCode(code):
			return checkCode(code)

	#Case2: it is not a 3 chars string.
	#Case2a: it is a 6 chars string.
	elif len(code) == 6:
		#Case2a (1): it is a pair of CCY
		part1 = code[:3]
		part2 = code[3:]
		if checkCode(part1) and checkCode(part2):
			return code
	
	#Case3: its len is not 3. It might cointain 6chars but it is not a pair of chars. 
	#if it is a valid country namem it will return code by checkCode(). Otherwise, it is returned False by checkCode()

	return checkCode(code)

def checkCode(s):
	#db = MySQLdb.connect("localhost","root","ezfx0109","testdb")
	db = MySQLdb.connect("localhost","root","ezfx0109","crawlerdb")
	cursor = db.cursor()

	if len(s) == 3:
		sql = "SELECT * FROM ccy_list \
				WHERE ID = '%s'" % (s)
		try:
			#it is a valid code
			if cursor.execute(sql):
				return s
			else:
				#check if it is a valid country code
				sql = "SELECT * FROM ccy_list \
						WHERE CountryCode = '%s'" % (s)
				try:
					#it is a valid country code
					if cursor.execute(sql):
						s = cursor.fetchone()[1]
						return s
					else:
						print s + " is not a valid CCY code or Country Code in database. Please Update!"
				except:
					print "Error: unable to fecth data in finding CountryCode"
		except:
			print "Error: unable to fecth data"
	else:
		sql = "SELECT * FROM ccy_list \
				WHERE Country = '%s'" % (s)
		try:
			#it is a valid code
			if cursor.execute(sql):
				s = cursor.fetchone()[1]
				return s
			else:
				print s + " is not a valid country in database. Please Update!"
		except:
			print "Error: unable to fecth data in checkCode"

	db.close()
	return False


def insert(urlCode_url, patterns):
	
	urlCode = urlCode_url[0]
	url = urlCode_url[1]

	#convert patterns from tuple to list
	patterns = list(patterns)

	# standard order [0,1,2,3,4,5] = [buyCCY, sellCCY, bid, offer, date, unit]
	order = convertToList(patterns[order_col])
	postData = patterns[postData_col]
	recursive_pt = patterns[recursive_col : recursive_col + 2]
	dynamic_pt = patterns[dynamic_col : dynamic_col + 8]
	endPattern = patterns[main_end_col]
	inverse = patterns[inverse_col]
	method = patterns[method_col]
	dynamicData = []
	exception = patterns[exception_col]
	checkCcyAvai = patterns[checkCcyAvai_col]
	if exception:
		exception = ast.literal_eval(exception)
	
	#check dynamic crawl
	if dynamic_pt[0] != '':
		baseList, counterList = getDynamicList(url, method, dynamic_pt)
		dynamicData = [baseList, counterList, patterns[dynamicData_col].split(',')]
		dynamicData = filter(None, dynamicData)

	#check recursive crawl
	if recursive_pt[0] != '':
		listOfUrls = getListOfUrl(url, recursive_pt[0], recursive_pt[1])
	else:
		listOfUrls = [url]

	#check ccyAvai
	if checkCcyAvai:
		checkCcyAvai = checkCcyAvai.split("/,/")
		#list of ccy got
		ccyGot = []
		ccyBaseToGot = []
		#baseList
		if dynamic_pt[0] != '':
			for e in baseList:
				ccyBaseToGot.append(getCode(e))

	#check multi-postData
	postData = postData.split('/,/')
	#check muil-patterns and inverse
	patterns= patterns[:postData_col-1]
	patterns = convertPattern(patterns)

	inverse = convertPattern(inverse)
	#print inverse
	EURMYR_bid = ''
	EURMYR_offer = ''
	#list CCY for Quantas
	quantas_ccy = []

	#listOfUrls = ['https://azimo.com/en/send-money-to-abkhazia.html','https://azimo.com/en/send-money-to-thailand.html','https://azimo.com/en/send-money-to-uzbekistan.html']
	#listOfUrls = ['https://azimo.com/en/send-money-to-abkhazia.html','https://azimo.com/en/send-money-to-armenia.html']
	for link in listOfUrls:
		#exception crawl
		if link in exception:
			#{'https://azimo.com/en/send-money-to-the-philippines.html':
			#[2, '', [['United Kingdom', 'Austria'],['calculator-sendingCountry']],
			#['id=\"calculator-sendingCurrency\"', 'val=\"', 'PHP', 'style=\"position:static;\">',
			#'','','1','\"','','<','','',''],[0,1,2,3,4,5],'<td><strong>*</strong>']}
			e_method = exception[link][0]
			e_pD = exception[link][1]
			e_dynamicData = exception[link][2]
			e_pt = exception[link][3]
			e_order = exception[link][4]
			e_endPattern = exception[link][5]
			webpage, ccyPairs = crawlWeb(link, e_method, e_pD, e_dynamicData, e_pt, endPattern)
			#print webpage
			if isinstance(webpage, basestring):
				data = parseText(webpage, e_pt, order, e_endPattern, False)
			else:
				while webpage:
					wp = webpage.pop()
					#baseCCY
					if ccyPairs:
						pair = ccyPairs.pop()
						patterns[pt_index][1] = pair[0]
						patterns[pt_index][2] = pair[1]
					data = parseText(wp, e_pt, e_order, e_endPattern, True)
			#print data
		else:
			dynamicData_modified = [] + dynamicData
			if dynamicData:
				dynamicData_modified[0] = [] + dynamicData[0]

			if checkCcyAvai:
				aResp = urllib2.urlopen(link)
				ccyWebpage = aResp.read()

				start = ccyWebpage.find(checkCcyAvai[0]) + len(checkCcyAvai[0])
				end = ccyWebpage.find(checkCcyAvai[1], start)
				countryName = ccyWebpage[start:end]

				start = ccyWebpage.find(checkCcyAvai[2]) + len(checkCcyAvai[2])
				end = ccyWebpage.find(checkCcyAvai[3], start)
				originalCcy = ccyWebpage[start:end]


				findStr = checkCcyAvai[4]+countryName+checkCcyAvai[5]
				start = ccyWebpage.find(findStr) + len(findStr)
				
				start = ccyWebpage.find(checkCcyAvai[6], start) + len(checkCcyAvai[6])

				end = ccyWebpage.find(checkCcyAvai[7], start)

				ccyNameList = [ccyWebpage[start:end]]

				stop = ccyWebpage.find(checkCcyAvai[10], start)
				ccyWebpage = ccyWebpage[start:stop]

				start = 0
				while True:
					start = ccyWebpage.find(checkCcyAvai[8], start)
					
					if start == -1 :
						break
					else:
						start += len(checkCcyAvai[8])
					end = ccyWebpage.find(checkCcyAvai[9], start)
					ccyName = ccyWebpage[start:end]

					ccyNameList.append(ccyName)
				
				#remove the last one that is not valid - Azimo special
				ccyNameList.pop()

				if ccyNameList:
					if originalCcy not in ccyNameList:
						removeList = []
						if ccyNameList[0] in ccyBaseToGot:
							removeList.append(ccyBaseToGot.index(ccyNameList[0]))

						
						for e in ccyBaseToGot:
							ccyPairToGot = e + ccyNameList[0]
							if ccyPairToGot in ccyGot:
								idx = ccyBaseToGot.index(e)
								if idx not in removeList:
									removeList.append(idx)

						for e in removeList:
							dynamicData_modified[0].pop(e)


						#all ccypair in this page has been crawled by previous pages - Azimo
						if not dynamicData_modified[0]:
							continue

			data = []
			pt_index = 0
			for pD in postData:
				webpage, ccyPairs = crawlWeb(link, method, pD, dynamicData_modified, patterns[pt_index], endPattern)

				if isinstance(webpage, basestring):
					dt = parseText(webpage, patterns[pt_index], order, endPattern, False)

					if inverse:
						for e in dt:
							e.append(inverse[pt_index][0])
					data = data + dt
				else:
					webpage = filter(None, webpage)
					while webpage:
						wp = webpage.pop()
						if ccyPairs:
							#baseCCY
							pair = ccyPairs.pop()
							patterns[pt_index][1] = pair[0]
							patterns[pt_index][2] = pair[1]
						dt = parseText(wp, patterns[pt_index], order, endPattern, True)
						if inverse:
							for e in dt:
								e.append(inverse[pt_index][0])
						data = data + dt

				pt_index += 1

		#end for loop for listOfUrls
		#print data
		#data: compressed all data
		#vals: clean data	
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
							try:
								full_date = time.strptime(full_date, '%Y-%m-%d %H:%M:%S')
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

			#deal with CCY issue
			for i in range(0,2):
				#special case for Austria
				if e[i] == 'Austria' or e[i] == " "  or e[i] == '' or ',' in e[i]:
					continue
				
				#if it is not a valid code/country/pair
				if not getCode(e[i]):
					e[i] = -1
					break
				else:
					code = getCode(e[i])
					#it is a pair
					if len(code) == 6:
						e[1] = code[3:]
						e[0] = code[:3]
						break
					#it is a country name or a valid code
					else:
						e[i] = code

			if e[0] == -1 or e[1] == -1:
				break
			elif e[0] == 'Austria' or e[1] == 'Austria' or e[0] == e[1]:
				continue
			else:
				#capitalize
				e[0] = e[0].upper()
				e[1] = e[1].upper()
				buyCCY = e[0]
				sellCCY = e[1]

			#special case for EZFX
			if urlCode != 'EZFX':
				#special case for QTA
				if urlCode == 'QTA':
					if not quantas_ccy:
						quantas_ccy = e[0].split(',')
					if data.index(e) % 9 == 0:
						e[0] = quantas_ccy.pop(0)
					else:
						e[0] = data[data.index(e) - 1][0]
					buyCCY = e[0]
				ID = generateID(short_date, urlCode, buyCCY, sellCCY)
			elif data.index(e) % 2 == 0:
				ID = generateID(short_date, 'MAY', buyCCY, sellCCY)
			else:
				#get buyCCY, sellCCY from Maybank rates. the 1st assignment for Insert to DB, 2nd for generating ID
				e[0] = data[data.index(e)-1][0]
				e[1] = data[data.index(e)-1][1]
				buyCCY = getCode(e[0])
				sellCCY = getCode(e[1])
				if not buyCCY or  not sellCCY or buyCCY == sellCCY:
					continue
				ID = generateID(short_date, 'CIT', buyCCY, sellCCY)

			#remove , in bid and offer values
			e[2] = e[2].replace(',','')
			e[3] = e[3].replace(',','')

			#do not add if it is all 0
			if e[2] != '' and e[3] != '':
				if round(float(e[2]),4) == 0.0000 and round(float(e[3]),4) == 0.0000:
					continue

			row = [ID, urlCode]
			#push all into a tuple according pre-set format
			for entry in e:
				row.append(entry)
			#[ID, URL, BUYCCY, SELLCCY, BID, OFFER, DATE_P, TIME_P, UNIT, INVERSE]
			row.insert(7,time_p)

			#special case for MUS-EURMYR
			if urlCode == 'MUS' and ID[-6:] == 'EURMYR':
				if e[2]: EURMYR_bid = round(1/float(e[2]),4)
				if e[3]: EURMYR_offer = e[3]
				if not EURMYR_bid or not EURMYR_offer:
					continue
				else:
					#bid, offer
					row[4] = EURMYR_bid
					row[5] = EURMYR_offer
					row[9] = 'Y'

			#checkCcyAvai - ccyGot
			if checkCcyAvai:
				ccyGot.append(row[0][-6:])

			vals.append(tuple(row))
		#print vals
		
		#determine which table to push data
		if urlCode == 'TRA' or urlCode == 'MMM' or urlCode == 'MUS':
			nameOfTb = 'RATES'
		else:
			nameOfTb = urlCode + 'rates'
		
		#db = MySQLdb.connect("localhost","root","ezfx0109","testdb")
		db = MySQLdb.connect("localhost","root","ezfx0109","crawlerdb")
		cursor = db.cursor()
		#Prepare SQL query to INSERT a record into the database.
		if not inverse:
			sql = "INSERT IGNORE INTO " + nameOfTb + " (ID, URL, BUYCCY, SELLCCY, BID, OFFER, DATE_P, TIME_P, UNIT)\
				VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
		else:
			sql = "INSERT IGNORE INTO " + nameOfTb + " (ID, URL, BUYCCY, SELLCCY, BID, OFFER, DATE_P, TIME_P, UNIT, INVERSE)\
				VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

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

#split into different list of patterns
#input: [pt1, 'pt2a, pt2b' , pt3]
#output: [[pt1, pt2a, pt3],[pt1, pt2b, pt3]]
compare = lambda x, y: collections.Counter(x) == collections.Counter(y)
def convertPattern(compressPattern):
	result = []
	if compressPattern:
		if not isinstance(compressPattern, list):
			compressPattern = [compressPattern]
		#split
		temp = []
		for e in compressPattern:
			if '/,/' in e:
				e = e.split('/,/')
			temp.append(e)

		compressPattern = temp

		boolean = True
		isNestedList = False
		while boolean:
			temp = []
			for e in compressPattern:
				if not isinstance(e, list):
					temp.append(e)

				else:
					isNestedList = True
					if not e:
						boolean = False
					else:
						temp.append(e.pop(0))
			if boolean:
				result.append(temp)
			#in case there is no nested list
			if not isNestedList:
				if compare(temp, compressPattern):
					boolean = False
	return result

#convertPattern(['1','a,b','2'])

def main():
	target = raw_input('Enter the name of target website: ')
	urlCode_url, patterns = getDetails(target)
	insert(urlCode_url, patterns)

start_time = time.time()
main()
print("--- %s seconds ---" % str(time.time() - start_time))