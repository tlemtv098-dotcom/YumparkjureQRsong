import pathlib
p = pathlib.Path(r"D:\mysong\music\models.py")
t = p.read_text(encoding="utf-8")

# Fix the SongQueue reference to use string
old = """    song = models.ForeignKey(SongQueue, on_delete=models.CASCADE, related_name="playlist_entries")"""
new = """    song = models.ForeignKey("SongQueue", on_delete=models.CASCADE, related_name="playlist_entries")"""
assert t.count(old) == 1, "count=%d" % t.count(old)
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("Fixed SongQueue reference")
