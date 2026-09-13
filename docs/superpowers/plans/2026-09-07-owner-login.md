# Owner Login/Signup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Owner สมัคร/ล็อคอินด้วย username/password แบบ public auto-staff, บังคับล็อคอินหน้า player ส่วน request เปิด public (Q117=B, Q118=A, Q119=A, Q120=A, Q121=A)

**Estimated tasks:** 4 | **Estimated time:** ~45 min | **Touches:** Auth / Views / Templates / Tests

## Current Problem / Current Solution

- ไม่มีหน้า login/signup, `_is_owner` เช็ค `X-Player-Token` หรือ `is_staff` แต่ไม่มีทางให้ staff ล็อคอิน, `player_view` เปิด public ใครก็เข้าคุมได้ถ้ารู้ URL
- ต้องการ: owner สมัครแล้วเป็น staff ทันที, player ต้องล็อคอิน, request ไม่ต้อง

## Proposed Approach

- ใช้ Django `contrib.auth` มาตรฐาน: `UserCreationForm` + custom `SignupView` ที่ `user.is_staff=True` หลัง save, `LoginView/LogoutView` จาก auth, `LOGIN_URL=/accounts/login/`, `LOGIN_REDIRECT_URL=/`
- `player_view` ใส่ `@login_required` (คง `_is_owner` สำหรับ API ไว้ fallback token), `request_view` ไม่ล็อค
- Templates: `registration/login.html`, `registration/signup.html` ใช้ Tailwind เดียวกับ player/request, header player โชว์ user + logout
- ไม่ทำ email verify / custom user model / social (เกิน scope)

## Side by Side

| Scenario | Before | After |
| -------- | ------ | ----- |
| เปิด / | เห็น player ทันที | redirect /accounts/login/?next=/ ถ้าไม่ล็อคอิน |
| สมัคร /accounts/signup/ | 404 | สร้าง user + is_staff + auto login + redirect / |
| request | public | ยัง public เหมือนเดิม |

## Assumptions & Risks

- **Assumed:** `django.contrib.auth` พร้อมใช้, ไม่ต้อง migrate เพิ่ม (default User)
- **Assumed:** public auto-staff ยอมรับความเสี่ยงใครก็คุมได้ (ตาม Q121=A)
- **Risk:** `@login_required` จะ redirect ไป login แม้มี `X-Player-Token` → คงไว้แต่ player page ต้อง session, API ยังใช้ token ได้
- **Risk:** ไม่มี rate limit บน signup/login → อาจโดน spam (รับได้ MVP)

## Impact

- แตะ `music/views.py` (signup view), `music/urls.py` (accounts/), `templates/registration/*.html` (2 ไฟล์), `yum_jukebox/settings.py` (LOGIN_*), `player.html` header

---

## Task Overview

> **For implementation tasks:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development before editing production code. Each task is a RED -> GREEN -> REFACTOR slice.
> **Parallel-first:** Spawn separate sub-agents for independent lanes. Do not parallelize tasks that can race on the same files, migrations, generated artifacts, or shared state.

1. **[Signup auto-staff]** - Lane A | Can run together: none | Must wait for: none | TDD slice: POST /accounts/signup/ creates staff -> add view/form -> `manage.py test`
2. **[Login/Logout wiring]** - Lane A | Can run together: none | Must wait for: Task 1 | TDD slice: GET /accounts/login/ renders -> add urls/templates -> `manage.py test`
3. **[Protect player + header UI]** - Lane B | Can run together: Task 1 | Must wait for: none | TDD slice: GET / redirects when anon -> add login_required + header -> `manage.py test`
4. **[Auth regression tests]** - Sequential | Can run together: none | Must wait for: Task 1,2,3 | TDD slice: staff can access player, anon cannot, request always 200 -> update tests -> `manage.py test`

---

### Task 1: Signup auto-staff

**Files:**

- Modify: `music/views.py` (add `SignupView`), `music/urls.py`
- Create: `music/templates/registration/signup.html`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 3`
- Must wait for: `none`
- Race risk: `music/urls.py` shared with Task 2 — Task 2 must wait

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

```python
def test_signup_creates_staff(self):
    self.client.post('/accounts/signup/', {'username':'owner1','password1':'pass12345','password2':'pass12345'})
    self.assertTrue(User.objects.get(username='owner1').is_staff)
```

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: FAIL (404/no staff).

- [ ] **Step 3: Implement the minimal code**

`music/views.py`: `class SignupView(CreateView): form_class=UserCreationForm; template_name='registration/signup.html'; success_url='/'; def form_valid(form): user=form.save(commit=False); user.is_staff=True; user.save(); login(self.request,user); return redirect('/')`

`music/urls.py`: `path('accounts/signup/', views.SignupView.as_view(), name='signup')`

`registration/signup.html`: extend minimal Tailwind form (username/password1/password2 + submit + link to login)

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2`. Expected: PASS

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 2: Login/Logout wiring

**Files:**

- Modify: `music/urls.py`, `yum_jukebox/settings.py` (LOGIN_URL, LOGIN_REDIRECT_URL, LOGOUT_REDIRECT_URL)
- Create: `music/templates/registration/login.html`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1` (urls.py)
- Race risk: `music/urls.py` shared

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`GET /accounts/login/ == 200` and contains `username`

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test`. Expected: FAIL 404.

- [ ] **Step 3: Implement the minimal code**

`urls.py`: `path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login')`, `path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/accounts/login/'), name='logout')` (POST via form)

`settings.py`: `LOGIN_URL='/accounts/login/'`, `LOGIN_REDIRECT_URL='/'`, `LOGOUT_REDIRECT_URL='/accounts/login/'`

`login.html`: Tailwind form (username/password + submit + link to signup + next hidden)

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test`. Expected: PASS

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 3: Protect player + header UI

**Files:**

- Modify: `music/views.py` (add `@login_required` to `player_view`), `music/templates/music/player.html` (header show user/logout)
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `Task 1`
- Must wait for: `none`
- Race risk: `music/views.py` shared with Task 1 — coordinate (Task 1 adds SignupView at bottom, Task 3 adds decorator + import)

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

`GET / anon -> 302 to /accounts/login/?next=/` ; `GET / as staff -> 200`

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test`. Expected: FAIL (200 anon)

- [ ] **Step 3: Implement the minimal code**

`views.py`: `from django.contrib.auth.decorators import login_required; @login_required def player_view...`

`player.html` header: `{% if user.is_authenticated %} <span>{{ user.username }}</span> <form method="post" action="{% url 'logout' %}">{% csrf_token %}<button>ออก</button></form> {% else %} <a href="{% url 'login' %}">เข้า</a> {% endif %}` (style minimal, reuse existing header flex)

Keep `request_view` without decorator

- [ ] **Step 4: Run the test and confirm it passes**

Run `manage.py test`. Expected: PASS

- [ ] **Step 5: Refactor only after green**

Rerun. No commit/push.

---

### Task 4: Auth regression tests

**Files:**

- Modify: `music/tests.py`
- Test: `music/tests.py`

**Parallelization:**

- Can run with: `none`
- Must wait for: `Task 1,2,3`
- Race risk: `music/tests.py` shared — must run last

- [ ] **Step 0: Load the TDD discipline**

Use `superpowers:test-driven-development`.

- [ ] **Step 1: Write the failing test**

Full matrix: anon player 302, staff player 200, request 200 anon, signup->staff, login success

- [ ] **Step 2: Run the test and confirm it fails for the expected reason**

Run `manage.py test`. Expected: FAIL until all wired

- [ ] **Step 3: Implement the minimal code**

Only `music/tests.py`: add `AuthRegressionTests` class covering matrix, ensure `_is_owner` still works via token fallback

- [ ] **Step 4: Run the test and confirm it passes**

Run `venv\Scripts\python.exe manage.py test music.tests -v2` — all 82+ new tests PASS, plus `manage.py check` PASS.

- [ ] **Step 5: Refactor only after green**

Clean helpers, rerun. No commit/push.
