import pathlib
p = pathlib.Path(r"D:\mysong\yum_jukebox\settings.py")
t = p.read_text(encoding="utf-8")

# Find the exact text around STATICFILES_STORAGE
idx = t.find("STATICFILES_STORAGE")
if idx >= 0:
    print(repr(t[idx:idx+200]))
else:
    print("Not found")
