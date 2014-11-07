import cookielib
import urllib
import urllib2


# Store the cookies and create an opener that will hold them
cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

# Add our headers
opener.addheaders = [('User-agent', 'RedditTesting')]

# Install our opener (note that this changes the global opener to the one
# we just made, but you can also just call opener.open() if you want)
urllib2.install_opener(opener)

# The action/ target from the form
authentication_url = 'http://ezfx.maventree.com/Account/Login.aspx?ReturnUrl=%2fAdmin%2fBankOrders.aspx'

# Input parameters we are going to send
payload = {
	'__VIEWSTATE': '/wEPDwUKLTc1MzkwOTY1NmQYAQUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFgIFF0xvZ2luQ29udHJvbCRSZW1lbWJlck1lBR1Mb2dpbkNvbnRyb2wkTG9naW5JbWFnZUJ1dHRvblRwNdm7t2he5isZi0sgU79dIUdeb3vgnSRTfA0UaFtz',
	'__EVENTVALIDATION': '/wEWBQLQ46iPCwKmg7i8CAKW58jlCgL+ho2mCwKki8v2DHQnNfAgvBg8Iapoon0ivrjG/KVrWNi+mfPsslUFwcv3',
	'LoginControl$UserName': 'trader2',
	'LoginControl$Password': 'password1!',
	'LoginControl$LoginButton': 'LOG IN'
}

# Use urllib to encode the payload
data = urllib.urlencode(payload)

# Build our Request object (supplying 'data' makes it a POST)
req = urllib2.Request(authentication_url, data)

# Make the request and read the response
resp = urllib2.urlopen(req)
contents = resp.read()
print contents