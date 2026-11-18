# Run the page's own heat model headless and sweep retract_length per material.
# Uses node if it is on PATH, otherwise macOS JavaScript for Automation (osascript). AGPL-3.0 (see LICENSE).
import os, shutil, subprocess, tempfile
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(H, "..", "..")
js = open(os.path.join(ROOT, "index.html")).read().split("<script>")[1].split("</script>")[0].replace("const TP = 265, TG = 100", "var TP = 265, TG = 100")
src = open(os.path.join(H, "stubs.js")).read() + js + open(os.path.join(H, "sweep_post.js")).read()
f = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False); f.write(src); f.close()
if shutil.which("node"): subprocess.run(["node", f.name], check=True)
else:
    expr = 'ObjC.import("Foundation"); eval($.NSString.stringWithContentsOfFileEncodingError("%s", 4, null).js)' % f.name
    print(subprocess.run(["osascript", "-l", "JavaScript", "-e", expr], capture_output=True, text=True).stdout)
