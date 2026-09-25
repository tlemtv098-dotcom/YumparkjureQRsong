import pathlib
p = pathlib.Path(r'D:\mysong\music\views.py')
t = p.read_text(encoding='utf-8')
idx = t.find('thumbnail = str(data.get')
if idx >= 0:
    print(repr(t[idx:idx+300]))
