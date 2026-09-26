import pathlib
p = pathlib.Path(r"D:\mysong\music\urls.py")
t = p.read_text(encoding="utf-8")

old = """    path("dashboard/", views_auth.dashboard_view, name="dashboard"),"""

new = """    path("dashboard/", views_auth.dashboard_view, name="dashboard"),
    path("api/dashboard/stats/", views_auth.dashboard_stats_api, name="dashboard_stats_api"),"""

assert t.count(old) == 1, "count=%d" % t.count(old)
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("URL route added")
