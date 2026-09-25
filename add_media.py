import pathlib
p = pathlib.Path(r"D:\mysong\yum_jukebox\settings.py")
t = p.read_text(encoding="utf-8")

old = "STATICFILES_STORAGE = \'whitenoise.storage.CompressedManifestStaticFilesStorage\'\n\nCACHES = {"
new = """STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (User uploads)
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

CACHES = {"""
assert t.count(old) == 1, "count=%d" % t.count(old)
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("OK: MEDIA settings added")
