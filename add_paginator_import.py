import pathlib
p = pathlib.Path(r"D:\mysong\music\views.py")
t = p.read_text(encoding="utf-8")

old = "from django.core.cache import cache"
new = "from django.core.cache import cache\nfrom django.core.paginator import Paginator"

assert t.count(old) == 1, "count=%d" % t.count(old)
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("Paginator import added")
