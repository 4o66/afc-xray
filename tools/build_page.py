# Assemble index.html from page/template.html and the build outputs (images embedded as data URIs). AGPL-3.0 (see LICENSE).
import base64, json, os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") + "/"; B = ROOT + "build/"
def uri(p, mime): return f"data:{mime};base64," + base64.b64encode(open(p, "rb").read()).decode()
data = json.load(open(B + "path.json")); data["sprites"] = json.load(open(B + "sprites.json"))
body = open(ROOT + "page/template.html").read()
body = body.replace("__DATA__", json.dumps(data, separators=(",", ":"))).replace('"__BASE__"', '"' + uri(B + "base.webp", "image/webp") + '"')
for k in ["arm", "slide", "guid", "dgear", "igear", "socc"]: body = body.replace(f'"__{k.upper()}__"', '"' + uri(B + f"sprite_{k}.png", "image/png") + '"')
body = body.replace('spring:"__SPRING__", ', "")
left = re.findall(r"__[A-Z]+__", body); assert not left, left
head = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
t = body.index("<style>"); s_end = body.index("</style>") + len("</style>")
html = head + body[:s_end] + "\n<style>html,body{margin:0}</style>\n</head>\n<body>\n" + body[s_end:] + "\n</body>\n</html>\n"
open(ROOT + "index.html", "w").write(html); print("index.html", len(html))
