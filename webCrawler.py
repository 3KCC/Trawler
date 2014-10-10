import urllib
import urllib2

def Connect2Web():
  aResp = urllib2.urlopen("file:///C:/Users/MinhTrang-EZFX/Desktop/portfolio/framework_v0.1/test.html")
  web_pg = aResp.read()
  return web_pg

textfile = file('cache.txt','wt')
textfile.write(Connect2Web())
textfile.close()