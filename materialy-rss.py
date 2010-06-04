#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Wyświetla RSS dla materiałów umieszczonych na stronie wz.uni.lodz.pl.

BY d33tah, LICENSED UNDER WTFPL.

Wymaga RSS2Gen: http://www.dalkescientific.com/Python/PyRSS2Gen.html
"""

import urllib 

import time
import pysqlite2.dbapi2 as sqlite3

import PyRSS2Gen
from lxml import html

frequency = 30 #for caching purposes
db_file = "/home/deathplanter/www/wz/cache.sqlite"
xpath_contains = "contains(., 'semestr 2') and contains(., 'anie,')" + \
	    "and not(contains(., 'niestacjonarne'))"

def get_usage():
  return """
  Skrypt uruchamiamy podając mu ID profilu pracownika, np: <br />
  http://jakis-serwer/katalog/materialy.wsgi?123
	 """

def try_from_cache(url):
  
  now = int(time.time())
  conn = sqlite3.connect(db_file)
  c = conn.cursor()
  c.execute("CREATE TABLE IF NOT EXISTS cache " + \
	      "(url TEXT UNIQUE, value TEXT, lasttime TEXT)")
  entry = c.execute("SELECT * FROM cache WHERE url = ?", (url,) ).fetchone()
  if entry:
    if now - int(entry[2]) < frequency:
      ret = entry[1]
    else:
      ret = urllib.urlopen(url).read().decode('utf-8')
      c.execute("UPDATE cache SET lasttime = ?, value = ?" \
		+ "WHERE url = ?", (now,ret,url))
      conn.commit()
  else:
    ret = urllib.urlopen(url).read().decode('utf-8')
    c.execute("INSERT INTO cache VALUES (?,?,?)", (url,ret,now))
    conn.commit()
  return ret

def application(environ, start_response):
  
  try:
    lecturer_id = int(environ["QUERY_STRING"])
  except:
    start_response('200 OK', [('Content-type','text/html')])
    return get_usage()
    
  filelist_url = 
      "http://zarzadzanie.uni.lodz.pl/Stronag%C5%82%C3%B3wna/Wyszukiwanie" +\
      "Materia%C5%82%C3%B3w/tabid/167/ctl/results/mid/552/language/pl-PL/" +\
      "Default.aspx?uid="+str(lecturer_id)
      
  page = try_from_cache(filelist_url)
  
  materials_id = "dnn_ctr552_Results_TabContainer2_TabPanel4_grvWykladowca"
  xpath_str = "//table[@id='%s']//*[%s]//td" % (materials_id, xpath_contains)
  tree = html.fromstring(page)
  entries = tree.xpath(xpath_str)

  if len(entries)>0:
    rss_title = elements[0][1][0].text
  else:
    rss_title = "WZ UŁ - materiały"
  
  rss = PyRSS2Gen.RSS2(
    title = rss_title,
    link = "http://deetah.jogger.pl",
    description = "Kanał RSS zawiera najnowsze ogłoszenia od wybranych"
		  "wykładowców Wydziału Zarządzania Uniwersytetu Łódzkiego.",
  )
  
  for entry in reversed(entries):
  
    file_name = entry[4].text
    lecturer = entry[1][0].text
    file_title = entry[1][1].text or file_name
    #subject = entry[1][0].tail.split(', ')[1]
    
    rss_title = '[%s] %s' % (lecturer, file_title)
    rss_description = (u'<b>Nazwa pliku: </b>%s<br /><b>Wykładowca: </b>' + \
         '<a href="%s">%s</a><br />') % (file_name, profile_url, lecturer)
    
    rss.items.append(PyRSS2Gen.RSSItem(
	title = rss_title, link = url, description = rss_description,
	guid = PyRSS2Gen.Guid( title ),
    ))
    
  start_response('200 OK', [('Content-type','application/rss+xml')])
  return rss.to_xml(encoding='utf-8')
  
if __name__ == "__main__":
  print application({"QUERY_STRING":"137"},'')