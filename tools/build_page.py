# Assemble index.html from page/template.html and the filament path data. The render layers are separate files under
# assets/<body>/, which the page loads on demand. AGPL-3.0 (see LICENSE).
import json, os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") + "/"
data = json.load(open(ROOT + "build/path.json"))
body = open(ROOT + "page/template.html").read().replace("__DATA__", json.dumps(data, separators=(",", ":"))).replace("__BUILD__", __import__("time").strftime("%Y%m%d%H%M%S"))
left = re.findall(r"__[A-Z]+__", body); assert not left, left
head = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
s_end = body.index("</style>") + len("</style>")
html = head + body[:s_end] + "\n<style>html,body{margin:0}</style>\n</head>\n<body>\n" + body[s_end:] + "\n</body>\n</html>\n"
open(ROOT + "index.html", "w").write(html); print("index.html", len(html))
