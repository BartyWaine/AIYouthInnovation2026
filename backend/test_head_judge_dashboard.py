"""Head Judge Dashboard functional test suite (20 scenarios)."""
import sys, urllib.request, urllib.error, urllib.parse, json

BASE = 'http://127.0.0.1:8022/api/v1'
RESULTS = []

# ─── helpers ────────────────────────────────────────────────────────────────

def login(email, pw):
    body = urllib.parse.urlencode({'username': email, 'password': pw}).encode()
    req = urllib.request.Request(BASE + '/auth/login', data=body, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    return json.loads(urllib.request.urlopen(req).read())['access_token']

def get(path, token):
    req = urllib.request.Request(BASE + path, method='GET')
    req.add_header('Authorization', f'Bearer {token}')
    return json.loads(urllib.request.urlopen(req).read())

def post(path, token, params=None):
    url = BASE + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method='POST')
    req.add_header('Authorization', f'Bearer {token}')
    return json.loads(urllib.request.urlopen(req).read())

def patch(path, token, params=None):
    url = BASE + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method='PATCH')
    req.add_header('Authorization', f'Bearer {token}')
    return json.loads(urllib.request.urlopen(req).read())

def expect_code(path, token, code, method='GET', params=None):
    """Return True if the endpoint returns the expected HTTP code."""
    url = BASE + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=method)
    req.add_header('Authorization', f'Bearer {token}')
    try:
        urllib.request.urlopen(req)
        return False  # expected an error but got 2xx
    except urllib.error.HTTPError as e:
        return e.code == code

def reset_eval(token, eval_id, status, reason=None):
    """Helper to transition evaluation to a known status."""
    p = {'new_status': status}
    if reason:
        p['reason'] = reason
    try:
        post(f'/judges/evaluations/{eval_id}/status', token, p)
    except Exception:
        pass

def result(msg, ok):
    RESULTS.append(('PASS' if ok else 'FAIL', msg))

# ─── login ────────────────────────────────────────────────────────────────────

hjt  = login('judge1@sti.edu.mm', 'judge123')
jt2  = login('judge2@sti.edu.mm', 'judge123')
jt3  = login('judge3@sti.edu.mm', 'judge123')
at   = login('admin@sti.edu.mm', 'admin123')
tm_t = login('team1@sti.edu.mm', 'team123')
print('Login OK')

# ─── Test fixtures ────────────────────────────────────────────────────────────
# Use eval_id=2 for sequential tests. Each test resets to a known state first.

# H1: HEAD_JUDGE can view all-scores for a competition
reset_eval(hjt, 2, 'OPEN', 'Test reset')
scores = get('/judges/all-scores?competition_id=3', hjt)
result(f"H1: HEAD_JUDGE view all-scores: {len(scores)} evals", len(scores) >= 0)

# H2: HEAD_JUDGE can view audit trail
reset_eval(hjt, 2, 'OPEN', 'Test reset')
audit = get('/judges/evaluations/2/audit', hjt)
result(f"H2: HEAD_JUDGE view audit trail: {len(audit)} entries", len(audit) >= 0)

# H3: JUDGE cannot view all-scores
ok = expect_code('/judges/all-scores?competition_id=3', jt2, 403)
result(f"H3: JUDGE blocked from all-scores: 403", ok)

# H4: TEAM_MEMBER cannot view all-scores
ok = expect_code('/judges/all-scores?competition_id=3', tm_t, 403)
result(f"H4: TEAM_MEMBER blocked from all-scores: 403", ok)

# H5: ADMIN can view all-scores
reset_eval(at, 2, 'OPEN', 'Test reset')
scores = get('/judges/all-scores?competition_id=3', at)
result(f"H5: ADMIN view all-scores: {len(scores)} evals", len(scores) >= 0)

# H6: HEAD_JUDGE can correct a score (requires OPEN status)
reset_eval(hjt, 2, 'OPEN', 'Test reset')
r = patch('/judges/evaluations/2/scores/correct', hjt, {'criterion_id': 1, 'score': 7, 'reason': 'Test correction'})
result(f"H6: HEAD_JUDGE correct score: old={r.get('old_value')}, new={r.get('new_value')}", r.get('new_value') == 7.0)

# H7: Correction without reason is rejected (requires OPEN status)
reset_eval(hjt, 2, 'OPEN', 'Test reset')
ok = expect_code('/judges/evaluations/2/scores/correct', hjt, 400, 'PATCH', {'criterion_id': 1, 'score': 6})
result(f"H7: Correction without reason rejected: 400", ok)

# H8: HEAD_JUDGE can lock an OPEN evaluation
reset_eval(hjt, 2, 'OPEN', 'Test reset')
r = post('/judges/evaluations/2/status', hjt, {'new_status': 'LOCKED'})
result(f"H8: HEAD_JUDGE lock eval: changed={r.get('changed')}", r.get('changed') == True)

# H9: HEAD_JUDGE can finalize a LOCKED evaluation
reset_eval(hjt, 2, 'LOCKED', None)
r = post('/judges/evaluations/2/status', hjt, {'new_status': 'FINALIZED'})
result(f"H9: HEAD_JUDGE finalize eval: changed={r.get('changed')}", r.get('changed') == True)

# H10: Reopen FINALIZED evaluation requires reason
reset_eval(hjt, 2, 'FINALIZED', None)
ok = expect_code('/judges/evaluations/2/status', hjt, 400, 'POST', {'new_status': 'OPEN'})
result(f"H10: Reopen without reason rejected: 400", ok)

# H11: Reopen FINALIZED evaluation with reason succeeds
reset_eval(hjt, 2, 'FINALIZED', None)
r = post('/judges/evaluations/2/status', hjt, {'new_status': 'OPEN', 'reason': 'Test reopen'})
result(f"H11: Reopen with reason: changed={r.get('changed')}", r.get('changed') == True)

# H12: Multiple judges' evaluations visible in all-scores
reset_eval(hjt, 2, 'OPEN', 'Test reset')
scores = get('/judges/all-scores?competition_id=3', hjt)
judge_ids = sorted(set(s['judge_id'] for s in scores if s.get('judge_id')))
result(f"H12: All-judge scores visible: {len(judge_ids)} judge(s) {judge_ids}", len(judge_ids) >= 1)

# H13: ADMIN can lock evaluation
reset_eval(at, 2, 'OPEN', 'Test reset')
r = post('/judges/evaluations/2/status', at, {'new_status': 'LOCKED'})
result(f"H13: ADMIN lock eval: changed={r.get('changed')}", r.get('changed') == True)

# H14: ADMIN can finalize evaluation
reset_eval(at, 2, 'LOCKED', None)
r = post('/judges/evaluations/2/status', at, {'new_status': 'FINALIZED'})
result(f"H14: ADMIN finalize eval: changed={r.get('changed')}", r.get('changed') == True)

# H15: ADMIN can reopen evaluation
reset_eval(at, 2, 'FINALIZED', None)
r = post('/judges/evaluations/2/status', at, {'new_status': 'OPEN', 'reason': 'Admin reset'})
result(f"H15: ADMIN reopen eval: changed={r.get('changed')}", r.get('changed') == True)

# H16: Rankings endpoint blocks TEAM_MEMBER
ok = expect_code('/competitions/3/rankings', tm_t, 403)
result(f"H16: TEAM_MEMBER blocked from /rankings: 403", ok)

# H17: Rankings endpoint accessible to HEAD_JUDGE
reset_eval(hjt, 2, 'OPEN', 'Test reset')
rankings = get('/competitions/3/rankings', hjt)
result(f"H17: HEAD_JUDGE /rankings accessible: {len(rankings)} entries", isinstance(rankings, list))

# H18: Leaderboard endpoint blocks TEAM_MEMBER
ok = expect_code('/competitions/3/leaderboard', tm_t, 403)
result(f"H18: TEAM_MEMBER blocked from /leaderboard: 403", ok)

# H19: HEAD_JUDGE cannot correct FINALIZED evaluation directly (must reopen first)
reset_eval(hjt, 2, 'LOCKED', None)
reset_eval(hjt, 2, 'FINALIZED', None)
ok = expect_code('/judges/evaluations/2/scores/correct', hjt, 403, 'PATCH', {'criterion_id': 1, 'score': 5, 'reason': 'Try'})
result(f"H19: Correct finalized eval blocked: 403", ok)

# H20: Judge creating evaluation for non-existent team is blocked
ok = expect_code('/judges/evaluations/mine', jt3, 403, 'POST', {'team_id': 99999, 'competition_id': 3})
result(f"H20: Judge create eval for fake team: 403", ok)

# ─── summary ─────────────────────────────────────────────────────────────────

passed = sum(1 for p, _ in RESULTS if p == 'PASS')
failed = [m for p, m in RESULTS if p == 'FAIL']
print(f"\nResults: {passed}/{len(RESULTS)} passed")
for p, m in RESULTS:
    print(f"  [{p}] {m}")
if failed:
    print(f"\n{len(failed)} test(s) FAILED:")
    for m in failed:
        print(f"  {m}")
    sys.exit(1)
else:
    print("\nAll Head Judge Dashboard tests passed!")
