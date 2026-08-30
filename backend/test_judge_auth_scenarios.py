"""18-scenario HEAD_JUDGE and judge authorization test suite."""
import sys, urllib.request, urllib.error, urllib.parse, json

BASE = 'http://127.0.0.1:8022/api/v1'
RESULTS = []

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

def check(code, fn, *args, **kwargs):
    try:
        return False, fn(*args, **kwargs)
    except urllib.error.HTTPError as e:
        return e.code == code, {'code': e.code, 'detail': e.read().decode()}

def check_ok(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
        return True
    except urllib.error.HTTPError:
        return False

def test(msg, expected_pass, fn=None, *args, **kwargs):
    if fn is None:
        RESULTS.append(('PASS' if expected_pass else 'FAIL', msg))
        return
    ok = check_ok(fn, *args, **kwargs) if expected_pass else (not check_ok(fn, *args, **kwargs))
    RESULTS.append(('PASS' if ok else 'FAIL', msg))

hjt = login('judge1@sti.edu.mm', 'judge123')
jt2 = login('judge2@sti.edu.mm', 'judge123')
at  = login('admin@sti.edu.mm', 'admin123')
print('Login OK')

try:
    post('/judges/evaluations/2/status', hjt, {'new_status': 'OPEN', 'reason': 'Test reset'})
except:
    pass

# S1: HEAD_JUDGE create evaluation
ok, r = check(200, post, '/judges/evaluations/mine', hjt, {'team_id': 7, 'competition_id': 3})
RESULTS.append(('PASS' if not ok else 'FAIL', f"S1: HEAD_JUDGE create eval: {r if ok else 'OK'}"))

# S2: HEAD_JUDGE add score
ok, r = check(200, post, '/judges/evaluations/2/scores', hjt, {'criterion_id': 1, 'score': 8})
RESULTS.append(('PASS' if not ok else 'FAIL', f"S2: HEAD_JUDGE add score: {r if ok else 'OK'}"))

# S3: HEAD_JUDGE view all scores
ok, r = check(200, get, '/judges/all-scores?competition_id=3', hjt)
RESULTS.append(('PASS' if not ok else 'FAIL', f"S3: HEAD_JUDGE view all-scores ({len(r) if ok else 0} entries): {r if not ok else 'OK'}"))

# S4: Score >10 rejected
ok, r = check(400, post, '/judges/evaluations/2/scores', hjt, {'criterion_id': 2, 'score': 11})
RESULTS.append(('PASS' if ok else 'FAIL', f"S4: Score>10 rejected: {r if not ok else 'OK'}"))

# S5: Score <1 rejected
ok, r = check(400, post, '/judges/evaluations/2/scores', hjt, {'criterion_id': 2, 'score': 0})
RESULTS.append(('PASS' if ok else 'FAIL', f"S5: Score<1 rejected: {r if not ok else 'OK'}"))

# S6: HEAD_JUDGE lock evaluation
ok, r = check(200, post, '/judges/evaluations/2/status', hjt, {'new_status': 'LOCKED'})
RESULTS.append(('PASS' if not ok else 'FAIL', f"S6: HEAD_JUDGE lock: {r if ok else 'OK'}"))

# S7: JUDGE cannot add score to LOCKED evaluation
ok, r = check(403, post, '/judges/evaluations/2/scores', jt2, {'criterion_id': 1, 'score': 9})
RESULTS.append(('PASS' if ok else 'FAIL', f"S7: JUDGE blocked from locked eval: {r if not ok else 'OK'}"))

# S8: HEAD_JUDGE correct score with reason
ok, r = check(200,
    lambda: post('/judges/evaluations/2/scores/correct', hjt, {'criterion_id': 1, 'score': 7, 'reason': 'Typo'}, method='PATCH')
)
RESULTS.append(('PASS' if not ok else 'FAIL', f"S8: HEAD_JUDGE correct with reason: {r if ok else 'OK'}"))

# S9: Correction without reason rejected
ok, r = check(400,
    lambda: post('/judges/evaluations/2/scores/correct', hjt, {'criterion_id': 1, 'score': 6}, method='PATCH')
)
RESULTS.append(('PASS' if ok else 'FAIL', f"S9: Correction without reason rejected: {r if not ok else 'OK'}"))

# S10: HEAD_JUDGE finalize
ok, r = check(200, post, '/judges/evaluations/2/status', hjt, {'new_status': 'FINALIZED'})
RESULTS.append(('PASS' if not ok else 'FAIL', f"S10: HEAD_JUDGE finalize: {r if ok else 'OK'}"))

# S11: Reopen finalized with reason
ok, r = check(200, post, '/judges/evaluations/2/status', hjt, {'new_status': 'OPEN', 'reason': 'Admin review'})
RESULTS.append(('PASS' if not ok else 'FAIL', f"S11: Reopen finalized with reason: {r if ok else 'OK'}"))

# S12: Reopen without reason rejected
post('/judges/evaluations/2/status', hjt, {'new_status': 'LOCKED'})
post('/judges/evaluations/2/status', hjt, {'new_status': 'FINALIZED'})
ok, r = check(400, post, '/judges/evaluations/2/status', hjt, {'new_status': 'OPEN'})
RESULTS.append(('PASS' if ok else 'FAIL', f"S12: Reopen without reason rejected: {r if not ok else 'OK'}"))

# S13: JUDGE cannot view all-scores
ok, r = check(403, get, '/judges/all-scores?competition_id=3', jt2)
RESULTS.append(('PASS' if ok else 'FAIL', f"S13: JUDGE blocked from all-scores: {r if not ok else 'OK'}"))

# S14: JUDGE can view own evaluations
ok, r = check(200, get, '/judges/evaluations', jt2)
RESULTS.append(('PASS' if not ok else 'FAIL', f"S14: JUDGE can view own evaluations: {r if ok else 'OK'}"))

# S15: Invalid transition OPEN->FINALIZED rejected
post('/judges/evaluations/2/status', hjt, {'new_status': 'OPEN', 'reason': 'reset'})
ok, r = check(400, post, '/judges/evaluations/2/status', hjt, {'new_status': 'FINALIZED'})
RESULTS.append(('PASS' if ok else 'FAIL', f"S15: Invalid OPEN->FINALIZED rejected: {r if not ok else 'OK'}"))

# S16: Duplicate evaluation (same judge/team/comp) returns existing
ok, r = check(200, post, '/judges/evaluations/mine', jt2, {'team_id': 7, 'competition_id': 3})
RESULTS.append(('PASS' if not ok else 'FAIL', f"S16: Duplicate eval returns existing: {r if ok else 'OK'}"))

# S17: ADMIN can view all-scores
ok, r = check(200, get, '/judges/all-scores?competition_id=3', at)
RESULTS.append(('PASS' if not ok else 'FAIL', f"S17: ADMIN can view all-scores: {r if ok else 'OK'}"))

# S18: ADMIN can lock/finalize/reopen
ok, r = check(200, post, '/judges/evaluations/2/status', at, {'new_status': 'LOCKED'})
RESULTS.append(('PASS' if not ok else 'FAIL', f"S18a: ADMIN lock: {r if ok else 'OK'}"))
ok, r = check(200, post, '/judges/evaluations/2/status', at, {'new_status': 'FINALIZED'})
RESULTS.append(('PASS' if not ok else 'FAIL', f"S18b: ADMIN finalize: {r if ok else 'OK'}"))
ok, r = check(200, post, '/judges/evaluations/2/status', at, {'new_status': 'OPEN', 'reason': 'Admin reset'})
RESULTS.append(('PASS' if not ok else 'FAIL', f"S18c: ADMIN reopen: {r if ok else 'OK'}"))

passed = sum(1 for p, _ in RESULTS if p == 'PASS')
failed = [m for p, m in RESULTS if p == 'FAIL']
print(f"\nResults: {passed}/{len(RESULTS)} passed")
for p, m in RESULTS:
    print(f"  [{p}] {m}")
if failed:
    print("\nFAILED:")
    for m in failed:
        print(f"  {m}")
    sys.exit(1)
else:
    print("\nAll 18 scenarios passed!")
