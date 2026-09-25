import pathlib
p = pathlib.Path(r"D:\mysong\music\views_auth.py")
t = p.read_text(encoding="utf-8")

# Fix user_list_view to add pagination
old = """def user_list_view(request):
    \"\"\"List all users with pagination and search\"\"\"
    query = request.GET.get("q", "")
    role_filter = request.GET.get("role", "")
    status_filter = request.GET.get("status", "")

    users = User.objects.select_related("profile").all().order_by("-date_joined")

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    if role_filter:
        users = users.filter(profile__role=role_filter)
    if status_filter == "active":
        users = users.filter(is_active=True)
    elif status_filter == "inactive":
        users = users.filter(is_active=False)

    paginator = Paginator(users, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "admin/user_list.html", {
        "page_obj": page_obj,
        "query": query,
        "role_filter": role_filter,
        "status_filter": status_filter,
    })"""

new = """def user_list_view(request):
    \"\"\"List all users with pagination and search\"\"\"
    query = request.GET.get("q", "")
    role_filter = request.GET.get("role", "")
    status_filter = request.GET.get("status", "")

    users = User.objects.select_related("profile").all().order_by("-date_joined")

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    if role_filter:
        users = users.filter(profile__role=role_filter)
    if status_filter == "active":
        users = users.filter(is_active=True)
    elif status_filter == "inactive":
        users = users.filter(is_active=False)

    paginator = Paginator(users, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "admin/user_list.html", {
        "page_obj": page_obj,
        "query": query,
        "role_filter": role_filter,
        "status_filter": status_filter,
    })"""

# The function already has pagination! Let me check if it needs fixing
print("user_list_view already has pagination")
