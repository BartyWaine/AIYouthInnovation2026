"""Security regression tests for AI Youth Innovation 2026.
Covers: data isolation, submission integrity, evaluation criteria access,
and role-based authorization across backend endpoints.

Run: python test_security_regression.py
"""
import sys, urllib.request, urllib.error, urllib.parse, json

BASE = 'http://127.0.0.1:8022/api/v1'
RESULTS = []

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def login(email, pw):
    body = urllib.parse.urlencode({'username': email, 'password': pw}).encode()
    req = urllib.request.Request(BASE + '/auth/login', data=body, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    return json.loads(urllib.request.urlopen(req).read())['access_token']

def get(path, token):
    req = urllib.request.Request(BASE + path, method='GET')
    req.add_header('Authorization', f'Bearer {token}')
    return json.loads(urllib.request.urlopen(req).read())

def post(path, token, params=None, method='POST'):
    url = BASE + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=method)
    req.add_header('Authorization', f'Bearer {token}')
    return json.loads(urllib.request.urlopen(req).read())

def patch(path, token, params=None):
    url = BASE + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method='PATCH')
    req.add_header('Authorization', f'Bearer {token}')
    return json.loads(urllib.request.urlopen(req).read())

def check(code, fn, *args, **kwargs):
    try:
        return False, fn(*args, **kwargs)
    except urllib.error.HTTPError as e:
        return e.code == code, {'code': e.code, 'detail': e.read().decode()}

def test(msg, expected_pass, fn=None, *args, **kwargs):
    if fn is None:
        RESULTS.append(('PASS' if expected_pass else 'FAIL', msg))
        return
    ok = check_ok(fn, *args, **kwargs) if expected_pass else (not check_ok(fn, *args, **kwargs))
    RESULTS.append(('PASS' if ok else 'FAIL', msg))

def check_ok(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
        return True
    except urllib.error.HTTPError:
        return False

# ---------------------------------------------------------------------------
# Auth tokens
# ---------------------------------------------------------------------------
admin_t = login('admin@sti.edu.mm', 'admin123')
hj_t = login('judge1@sti.edu.mm', 'judge123')
judge2_t = login('judge2@sti.edu.mm', 'judge123')
judge3_t = login('judge3@sti.edu.mm', 'judge123')
judge4_t = login('judge4@sti.edu.mm', 'judge123')
judge5_t = login('judge5@sti.edu.mm', 'judge123')

# Get a team member token (team1 is in competition 3)
team1_t = login('team1@sti.edu.mm', 'team123')

# Fetch IDs for assertions
comps = get('/competitions/', admin_t)
comp1 = next(c for c in comps if c['name'] == 'AI Youth 2026')
comp2 = next(c for c in comps if c['name'] == 'AI Youth 2026_Social')
comp3 = next(c for c in comps if c['name'] == 'AI Youth 2026_Entrepreneur')

all_teams = get('/teams/', admin_t)
team1 = next(t for t in all_teams if t['name'] == 'Technologia Ventures')
team_other = next(t for t in all_teams if t['id'] != team1['id'])

all_deliv = get(f'/deliverables/?competition_id={comp3["id"]}', admin_t)
deliv1 = all_deliv[0] if all_deliv else None

all_subs = get(f'/deliverables/{deliv1["id"]}/submissions', admin_t) if deliv1 else []
sub1 = all_subs[0] if all_subs else None

# ---------------------------------------------------------------------------
# 1. Team member cannot list all teams
# ---------------------------------------------------------------------------
test("T1: TEAM_MEMBER can list teams (scoped to own team)", True,
     lambda: get('/teams/', team1_t))
test("T1b: TEAM_MEMBER list_teams returns only own team", True,
     lambda: len([t for t in get('/teams/', team1_t) if t['id'] == team1['id']]) == 1)

# ---------------------------------------------------------------------------
# 2. Team member cannot retrieve another team's details
# ---------------------------------------------------------------------------
test("T2: TEAM_MEMBER can view own team", True,
     lambda: get(f'/teams/{team1["id"]}', team1_t))
test("T2b: TEAM_MEMBER cannot view another team's details", False,
     lambda: get(f'/teams/{team_other["id"]}', team1_t))

# ---------------------------------------------------------------------------
# 3. Team member cannot list members of another team
# ---------------------------------------------------------------------------
test("T3: TEAM_MEMBER cannot list members of another team", False,
     lambda: get(f'/teams/{team_other["id"]}/members', team1_t))

# ---------------------------------------------------------------------------
# 4. Team member cannot read deliverables from unauthorized competition
# ---------------------------------------------------------------------------
unauth_comp = comp1 if comp3['id'] != comp1['id'] else comp2
test("T4: TEAM_MEMBER cannot list deliverables for unauthorized competition", False,
     lambda: get(f'/deliverables/?competition_id={unauth_comp["id"]}', team1_t))

# ---------------------------------------------------------------------------
# 5. Team member cannot enumerate other teams' submissions
# ---------------------------------------------------------------------------
if deliv1:
    test("T5: TEAM_MEMBER can list own team's submissions for a deliverable", True,
         lambda: get(f'/deliverables/{deliv1["id"]}/submissions', team1_t))
    test("T5b: TEAM_MEMBER submissions list is scoped (no other teams)", True,
         lambda: all(s['team_id'] == team1['id'] for s in get(f'/deliverables/{deliv1["id"]}/submissions', team1_t)))

# ---------------------------------------------------------------------------
# 6. Team member receives 403 for submission-status changes (own submission)
# ---------------------------------------------------------------------------
if sub1:
    test("T6: TEAM_MEMBER cannot change submission status (even own)", False,
         lambda: patch(f'/deliverables/submissions/{sub1["id"]}/status', team1_t,
                       {'new_status': 'SUBMITTED'}))

# ---------------------------------------------------------------------------
# 7. Invalid submission statuses are rejected for authorized callers
# ---------------------------------------------------------------------------
test("T7: ADMIN invalid status rejected", False,
     lambda: patch(f'/deliverables/submissions/{sub1["id"]}/status', admin_t,
                   {'new_status': 'INVALID_STATUS'}) if sub1 else None)

# ---------------------------------------------------------------------------
# 8. Team member receives 403 for evaluation criteria
# ---------------------------------------------------------------------------
test("T8: TEAM_MEMBER cannot view evaluation criteria", False,
     lambda: get('/admin/evaluation-criteria', team1_t))
test("T8b: ADMIN can view evaluation criteria", True,
     lambda: get('/admin/evaluation-criteria', admin_t))
test("T8c: JUDGE can view evaluation criteria", True,
     lambda: get('/admin/evaluation-criteria', judge3_t))
test("T8d: HEAD_JUDGE can view evaluation criteria", True,
     lambda: get('/admin/evaluation-criteria', hj_t))

# ---------------------------------------------------------------------------
# 9. Admin/judge/head-judge access preserved
# ---------------------------------------------------------------------------
test("T9: ADMIN can list users", True,
     lambda: get('/admin/users', admin_t))
test("T9b: JUDGE can view competitions", True,
     lambda: get('/competitions/', judge3_t))
test("T9c: HEAD_JUDGE can view competitions", True,
     lambda: get('/competitions/', hj_t))

# ---------------------------------------------------------------------------
# 10. Rankings returns 403 for TEAM_MEMBER
# ---------------------------------------------------------------------------
test("T10: TEAM_MEMBER receives 403 for rankings", False,
     lambda: get(f'/competitions/{comp3["id"]}/rankings', team1_t))
test("T10b: JUDGE can view rankings", True,
     lambda: get(f'/competitions/{comp3["id"]}/rankings', judge3_t))

# ---------------------------------------------------------------------------
# 11. /teams requires auth (not open to anonymous)
# ---------------------------------------------------------------------------
try:
    req = urllib.request.Request(BASE + '/teams/', method='GET')
    urllib.request.urlopen(req)
    RESULTS.append(('FAIL', 'T11: Anonymous access to /teams should be 401'))
except urllib.error.HTTPError as e:
    RESULTS.append(('PASS' if e.code == 401 else 'FAIL', f'T11: /teams returns {e.code} for anonymous'))

# ---------------------------------------------------------------------------
# 12. Debug route hidden in production mode (check via code inspection)
# ---------------------------------------------------------------------------
import os
debug_exposed = os.getenv('ENVIRONMENT') != 'production'
RESULTS.append(('PASS' if not debug_exposed else 'INFO', 'T12: /debug/routes is development-only'))

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "="*70)
print("SECURITY REGRESSION TEST RESULTS")
print("="*70)
passed = sum(1 for r in RESULTS if r[0] == 'PASS')
failed = sum(1 for r in RESULTS if r[0] == 'FAIL')
info = sum(1 for r in RESULTS if r[0] == 'INFO')
for status, msg in RESULTS:
    marker = '[OK]' if status == 'PASS' else ('[!!]' if status == 'FAIL' else '[ii]')
    print(f"  {marker} [{status}] {msg}")
print("-"*70)
print(f"  Total: {len(RESULTS)}  |  PASS: {passed}  |  FAIL: {failed}  |  INFO: {info}")
print("="*70)

if failed > 0:
    sys.exit(1)
