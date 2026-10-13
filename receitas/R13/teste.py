import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R13"); ex = p.ex
p.rect(0, 0, 1440, 810, K)
rows = [("Inter", "Regular"), ("Inter", "Medium"), ("Inter", "SemiBold"), ("Inter", "Bold"), ("Inter", "ExtraBold"),
        ("Source Sans 3", "Regular"), ("Source Sans 3", "Semibold"), ("Source Sans 3", "Bold"),
        ("Helvetica Neue", "Light"), ("Helvetica Neue", "Medium"), ("Helvetica Neue", "Bold")]
y = 90
for i, (f, s) in enumerate(rows):
    col = 70 if i < 6 else 760
    yy = 90 + (i % 6) * 110
    try:
        p.text(col, yy, "Corra mais 42K", f, s, 54, "#FFFFFF")
    except Exception as e:
        print("ERR", f, s, str(e)[:150])
    p.text(col, yy + 28, f"{f} / {s}", "Helvetica Neue", "Bold", 12, GOLD, tracking=150)
for x in ex("text.fonts", {}):
    print(x["family"], x["style"], x["status"], x["resolved"])
p.export()
