import urllib
import urllib2
from selenium import webdriver
import time



baseurl = 'http://www.mustafa.com.sg/frmForexNew.aspx'

fox = webdriver.Firefox()
fox.get(baseurl)

el = fox.find_element_by_id('ctl00_MainContent_idForex_dbtCountryName')
for option in el.find_elements_by_tag_name('option'):
    if option.text == 'Malaysian Ringgit':
        option.click() # select() in earlier versions of webdriver
        break
#click the button
fox.find_element_by_id('ctl00_MainContent_idForex_ImageButton1').click()

def Connect2Web():
	aResp = urllib2.urlopen(baseurl)
	web_pg = aResp.read()

	return web_pg

textfile = file('cache.txt','wt')
time.sleep(10)
textfile.write(Connect2Web())
textfile.close()