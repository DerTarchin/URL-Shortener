import sys
import shutil
import os
import pexpect

SITE_DIR = "/Users/Hizal/dev/sites/hiz.al/"
REDIR_TEMPLATE_PRE = "<html><head><meta http-equiv=\"refresh\" content=\"0;URL='"
REDIR_TEMPLATE_POST = """" />
<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=UA-70907063-2"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'UA-70907063-2');
</script>
</head></html>
"""

args = sys.argv #[1] = current working directory
params = {
  'list': False, # replace original files
  'remove': False, # remove given shorturl
}

def gitCommitAndPush(shorturl):
  print "Updating server..."
  child = pexpect.spawn("bash")
  # child.logfile = sys.stdout
  child.sendline("cd /Users/Hizal/dev/sites/hiz.al/")
  child.sendline("git add .")
  child.sendline('git commit -m "/' + shorturl + '..."')
  child.sendline("git push origin master")
  child.sendline('git commit -m "/' + shorturl + '" --allow-empty') # empty push
  child.sendline("git push origin master")
  child.sendline("exit")
  print child.read()
  print "... done."

def setparams():
  global args, params, supported
  if len(args) > 1 and args[1].startswith("-"):
    if "h" in args[1] or "help" in args[1]:
      print "-l/list >> convert from list (.txt file)"
      print "-r/remove >> remove shorturl"
      print "-h/help >> help"
      print "\nFormat: shorturl shorturlval www.longurl.com (becomes hiz.al/shorturlval)"
      sys.exit()
    if "list" in args[1] or "l" in args[1]: params["list"] = True
    if "r" in args[1] or "remove" in args[1]: params["remove"] = True
    args.remove(args[1])

def process():
  global args, params
  if len(args) == 1:
    print "ERROR: not enough arguments."
    print "Format: shorturl <shorturlval> <www.longurl.com>"
    sys.exit()
  urls = []

  if params["remove"]:
    shorturl = args[1]
    print "Removing /" + shorturl
    shutil.rmtree(SITE_DIR + shorturl)
    gitCommitAndPush(shorturl)
    return

  if params["list"]:
    with open(args[1], "r") as f:
      for line in f.readlines():
        urls.append(line.replace("\n","").split(" "))
        if "http://" not in urls[-1][1] and "https://" not in urls[-1][1]:
          urls[-1][1] = "http://" + urls[-1][1]
  else:
    urls = [[args[1],args[2]]]
    if "http://" not in urls[-1][1] and "https://" not in urls[-1][1]:
          urls[-1][1] = "http://" + urls[-1][1]

  for pair in urls:
    shorturl = pair[0]
    longurl = pair[1]
    # create index
    if not os.path.exists(SITE_DIR + shorturl):
      os.makedirs(SITE_DIR + shorturl)
    else:
      print shorturl, "already exists! Do you want to replace it?"
      cont = raw_input("Y/N: ")
      if cont.lower() == "y":
        os.remove(SITE_DIR + shorturl + "/index.html")
        print "Removing"
      else: 
        print "Cancelling process..."
        sys.exit()

    # create file
    with open(SITE_DIR + shorturl + "/index.html", "w") as f:
      f.write(REDIR_TEMPLATE_PRE + longurl + REDIR_TEMPLATE_POST)
      f.close()

  if params["list"]:
    print "Shortening all urls in", args[1]
  else:
    print "Shortening", urls[0][1], "to", "hiz.al/" + urls[0][0]

  gitCommitAndPush(shorturl)

setparams()
process()
