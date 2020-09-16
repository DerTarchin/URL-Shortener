import sys, requests, string, os, shutil, pexpect, re, random
from bs4 import BeautifulSoup

SITE_DIR = "/Users/Hizal/dev/sites/hiz.al/"
PORTFOLIO_SITE_DIR = "/Users/Hizal/dev/sites/hizalcelik.com/"
PORTFOLIO_SITE_URL = "http://hizalcelik.com/"

TEMPLATE = """
<html>
<head>
<meta http-equiv="refresh" content="0;URL='{{LONG_URL}}'" />
<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=UA-70907063-2"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'UA-70907063-2');</script>
<title{{CUSTOM}}>{{TITLE}}</title>
<meta property="og:title" content="{{TITLE}}">
<meta name="description" content="{{DESCRIPTION}}">
<meta property="og:description" content="{{DESCRIPTION}}">
<meta property="og:image" content="{{IMAGE}}">
<meta property="og:url" content="{{SHORT_URL}}">
</head></html>
"""

args = sys.argv #[1] = current working directory
params = {
  'batch': False, # create from a file
  'remove': False, # remove given shorturl
  'title': False, # custom title
  'reindex': False, # recreate every shorturl with updated code
  'list': False, # list all current shorturls,
  'sync': False, # sync with all pages on hizalcelik.com
}

def gitCommitAndPush(shorturl):
  print "Updating server..."
  child = pexpect.spawn("bash")
  child.sendline("cd /Users/Hizal/dev/sites/hiz.al/")
  child.sendline('git add .; git commit -m "/' + shorturl + '..."; git push origin master; git commit -m "/' + shorturl + '" --allow-empty; git push origin master');
  child.readline()
  child.sendline("exit")
  child.read()
  print "Done."

def set_params():
  global args, params, supported
  if len(args) > 1:
    if "-h" in args or "-help" in args:
      print "-l/list >> list all existing URLs"
      print "-b/batch >> convert from file (.txt file, each line as {shorturl [space] url})"
      print "-r/remove >> remove shorturl"
      print "-t/title >> custom page title (defualts to shorturl)"
      print "-reindex >> recreate existing shorturls"
      print "-h/help >> help"
      print "-sync >> Sync all pages on hizalcelik.com"
      print "\nFormat: shorturl [short url] [original url] >> becomes hiz.al/shorturlval"
      sys.exit()
    if "-b" in args or "-batch" in args: 
      argIndex = args.index("-f") if "-f" in args else args.index("-batch")
      params["batch"] = args.pop(argIndex + 1)
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
    if "-sync" in args:
      argIndex = args.index("-sync")
      params["sync"] = True
    if "-l" in args or "-list" in args:
      argIndex = args.index("-l") if "-l" in args else args.index("-list")
      params["list"] = True

def get_existing():
  urls = []
  for shorturl in next(os.walk(SITE_DIR[:-1]))[1]:
      if shorturl[0] == '.': continue
      with open(SITE_DIR + shorturl + '/index.html', "r") as f:
        result = re.search('URL=\'(.*)" />', f.read())
        longurl = result.group(1)[:-1] if result.group(1)[-1] == "'" else result.group(1)
        urls.append([shorturl, longurl])
  return urls

def process():
  global args, params
  if len(args) == 1 and not params["batch"] and not params["remove"]:
    print "ERROR: not enough arguments."
    print "Format: shorturl [opt:<shorturlVal>] <www.longurl.com> [opt:-t/title <titleStr>]"
    print "Format: shorturl -b/batch <list.txt>"
    print "Format: shorturl -r/remove <shorturlVal>"
    sys.exit()
  urls = []

  if params["list"]:
    for u in get_existing():
      print '{0:20}  {1}'.format(u[0], u[1])
    return

  if params["remove"]:
    shorturl = params["remove"]
    print "Removing /" + shorturl
    try:
      shutil.rmtree(SITE_DIR + shorturl)
    except:
      print "Error occured while removing"
      return
    return gitCommitAndPush(shorturl)

  if params["batch"]:
    with open(params["batch"], "r") as f:
      for line in f.readlines():
        urls.append(line.replace("\n","").split(" "))
        if "http://" not in urls[-1][1] and "https://" not in urls[-1][1]:
          urls[-1][1] = "http://" + urls[-1][1]

  elif params["sync"]:
    existing = get_existing()
    # iter through portfolio site directory
    for d in next(os.walk(PORTFOLIO_SITE_DIR[:-1]))[1]:
      # check if it's a page
      if os.path.exists(PORTFOLIO_SITE_DIR + d + '/index.html'):
        # check if there's a shorturl for it already, with updated URL
        hasUrl = False
        for e in existing:
          if e[0] == d and e[1] == PORTFOLIO_SITE_URL + d:
            hasUrl = True
        if not hasUrl:
          urls.append([d, PORTFOLIO_SITE_URL + d])
    if not len(urls):
      print "Nothing to sync"
      return

  elif params["reindex"]:
    urls = get_existing()

  else:
    if len(args) == 2:
      generated = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(5))
      urls = [[generated, args[1]]]
    else:
      urls = [[args[1],args[2]]]
    if "http://" not in urls[-1][1] and "https://" not in urls[-1][1]:
          urls[-1][1] = "http://" + urls[-1][1]

  for pair in urls:
    shorturl = pair[0]
    longurl = pair[1]
    custom_title = None
    
    if params["reindex"]:
      print "Recreating", shorturl, "(" + longurl + ")"
      # get custom title from previous shorturl
      with open(SITE_DIR + shorturl + "/index.html", "r") as f:
        contents = f.read()
        if "data-custom" in contents:
          result = re.search('property="og:title" content="(.*)">', contents)
          custom_title = result.group(1)[:-1] if result.group(1)[-1] == '"' else result.group(1)

    # create index
    if not os.path.exists(SITE_DIR + shorturl):
      os.makedirs(SITE_DIR + shorturl)
    else:
      if not params["reindex"] and not params["sync"]:
        print shorturl, "already exists! Do you want to replace it?"
        cont = raw_input("Y/N: ")
      if params["reindex"] or params["sync"] or cont.lower() == "y":
        try:
          os.remove(SITE_DIR + shorturl + "/index.html")
        except:
          print "Error occured while removing ", shorturl
        if not params["reindex"] and not params["sync"]:
          print "Removing ", shorturl
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
    page_title = custom_title
    if not page_title:
      if len(titleTags): page_title = titleTags[0].text.strip()
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
      if params["title"] or custom_title:
        html = html.replace("{{CUSTOM}}", " data-custom")
      else:
        html = html.replace("{{CUSTOM}}", "")
      html = html.encode('utf-8')
      f.write(html)
      f.close()

  if params["batch"]:
    print "Shortening all urls in", params["batch"]
  else:
    print "Shortening", urls[0][1], "\n...\n", "http://hiz.al/" + urls[0][0]

  gitCommitAndPush(shorturl)

set_params()
process()
