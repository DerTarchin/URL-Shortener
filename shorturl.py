import sys
import requests
from bs4 import BeautifulSoup
import shutil
import os
import pexpect
import re

SITE_DIR = "/Users/Hizal/dev/sites/hiz.al/"

TEMPLATE = """
<html>
<head>
<meta http-equiv="refresh" content="0;URL='{{LONG_URL}}'" />
<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=UA-70907063-2"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'UA-70907063-2');</script>
<title>{{TITLE}}</title>
<meta property="og:title" content="{{TITLE}}">
<meta name="description" content="{{DESCRIPTION}}">
<meta property="og:description" content="{{DESCRIPTION}}">
<meta property="og:image" content="{{IMAGE}}">
<meta property="og:url" content="{{SHORT_URL}}">
</head></html>
"""

args = sys.argv #[1] = current working directory
params = {
  'list': False, # replace original files
  'remove': False, # remove given shorturl
  'title': False, # custom title
  'reindex': False # recreate every shorturl with updated code
}

def gitCommitAndPush(shorturl):
  print "Updating server..."
  child = pexpect.spawn("bash")
  child.sendline("cd /Users/Hizal/dev/sites/hiz.al/")
  child.sendline('git add .; git commit -m "/' + shorturl + '..."; git push origin master; git commit -m "/' + shorturl + '" --allow-empty; git push origin master');
  child.readline()
  child.sendline("exit")
  child.read()
  print "... done."

def setparams():
  global args, params, supported
  if len(args) > 1:
    if "-h" in args or "-help" in args:
      print "-l/list >> convert from list (.txt file, each line as {shorturl [space] url})"
      print "-r/remove >> remove shorturl"
      print "-t/title >> custom page title (defualts to shorturl)"
      print "-reindex >> recreate existing shorturls"
      print "-h/help >> help"
      print "\nFormat: shorturl shorturlval www.longurl.com (becomes hiz.al/shorturlval)"
      sys.exit()
    if "-l" in args or "-list" in args: 
      argIndex = args.index("-l") if "-l" in args else args.index("-list")
      params["list"] = args.pop(argIndex + 1)
      del args[argIndex]
    if "-r" in args or "-remove" in args: 
      argIndex = args.index("-r") if "-r" in args else args.index("-remove")
      params["remove"] = args.pop(argIndex + 1)
      del args[argIndex]
    if "-t" in args or "-title" in args: 
      argIndex = args.index("-t") if "-t" in args else args.index("-title")
      params["title"] = args.pop(argIndex + 1)
      del args[argIndex]
    if "-reindex" in args:
      argIndex = args.index("-reindex")
      params["reindex"] = True

def process():
  global args, params
  if len(args) == 1 and not params["list"] and not params["remove"]:
    print "ERROR: not enough arguments."
    print "Format: shorturl <shorturlval> <www.longurl.com>"
    sys.exit()
  urls = []

  if params["remove"]:
    shorturl = params["remove"]
    print "Removing /" + shorturl
    try:
      shutil.rmtree(SITE_DIR + shorturl)
    except:
      print "Error occured while removing"
    gitCommitAndPush(shorturl)
    return

  if params["list"]:
    with open(params["list"], "r") as f:
      for line in f.readlines():
        urls.append(line.replace("\n","").split(" "))
        if "http://" not in urls[-1][1] and "https://" not in urls[-1][1]:
          urls[-1][1] = "http://" + urls[-1][1]
  elif params["reindex"]:
    for shorturl in next(os.walk(SITE_DIR[:-1]))[1]:
      if shorturl[0] == '.': continue
      with open(SITE_DIR + shorturl + '/index.html', "r") as f:
        result = re.search('URL=\'(.*)" />', f.read())
        longurl = result.group(1)[:-1] if result.group(1)[-1] == "'" else result.group(1)
        urls.append([shorturl, longurl])
  else:
    urls = [[args[1],args[2]]]
    if "http://" not in urls[-1][1] and "https://" not in urls[-1][1]:
          urls[-1][1] = "http://" + urls[-1][1]

  for pair in urls:
    shorturl = pair[0]
    longurl = pair[1]
    
    if params["reindex"]:
      print "Recreating", shorturl, "(" + longurl + ")"
    
    # create index
    if not os.path.exists(SITE_DIR + shorturl):
      os.makedirs(SITE_DIR + shorturl)
    else:
      if not params["reindex"]:
        print shorturl, "already exists! Do you want to replace it?"
        cont = raw_input("Y/N: ")
      if params["reindex"] or cont.lower() == "y":
        try:
          os.remove(SITE_DIR + shorturl + "/index.html")
        except:
          print "Error occured while removing ", shorturl
        if not params["reindex"]:
          print "Removing"
      else: 
        print "Cancelling process..."
        sys.exit()

    res = requests.get(longurl)
    parsed = BeautifulSoup(res.text, features="html5lib")
    metas = parsed.find_all('meta')
    titleTags = parsed.find_all('title')

    # description
    mainDesc = [ meta.attrs['content'] for meta in metas if 'name' in meta.attrs and meta.attrs['name'] == 'description' ]
    mainDesc = mainDesc[0] if len(mainDesc) else None
    ogDesc = [ meta.attrs['content'] for meta in metas if 'property' in meta.attrs and meta.attrs['property'] == 'og:description' ]
    ogDesc = ogDesc[0] if len(ogDesc) else None
    page_desc = None
    if mainDesc: page_desc = mainDesc.strip()
    if ogDesc: page_desc = ogDesc.strip()
    page_desc = page_desc if page_desc else "URL shortener by Hizal Celik"

    # title
    ogTitle = [ meta.attrs['content'] for meta in metas if 'property' in meta.attrs and meta.attrs['property'] == 'og:title' ]
    ogTitle = ogTitle[0] if len(ogTitle) else None
    if len(titleTags): page_title = titleTags[0].text.strip()
    page_title = None
    if ogTitle: page_title = ogTitle.strip()
    if params["title"]: page_title = params["title"]
    else: page_title = page_title if page_title else ("hiz.al/" + shorturl)

    # image card
    ogImage = [ meta.attrs['content'] for meta in metas if 'property' in meta.attrs and meta.attrs['property'] == 'og:image' ]
    page_image = ogImage[0] if len(ogImage) else "http://hiz.al/card-thumb.jpg"

    # create file
    with open(SITE_DIR + shorturl + "/index.html", "w") as f:
      html = TEMPLATE.replace("{{LONG_URL}}", longurl).replace("{{SHORT_URL}}","http://hiz.al/" + shorturl)
      html = html.replace("{{IMAGE}}", page_image)
      html = html.replace("{{TITLE}}", page_title)
      html = html.replace("{{DESCRIPTION}}", page_desc)
      html = html.encode('utf-8')
      f.write(html)
      f.close()

  if params["list"]:
    print "Shortening all urls in", params["list"]
  else:
    print "Shortening", urls[0][1], "\n...\n", "http://hiz.al/" + urls[0][0]

  gitCommitAndPush(shorturl)

setparams()
process()
