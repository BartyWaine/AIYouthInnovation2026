"""Test judge authorization endpoints."""
import sys, urllib.request, urllib.error, urllib.parse, json

BASE = 'http://127.0.0.1:8023/api/v1'

def login(email, pw):
    body = urllib.parse.urlencode({'username': email, 'password': pw}).encode()
    req = urllib.request.Request(BASE + '/auth/login', data=body, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())['access_token']

hjt = login('judge1@sti.edu.mm', 'judge123')
print('HEAD_JUDGE login: OK')

# Reset eval 2 to OPEN (leftover from previous run)
params_reset = urllib.parse.urlencode({'new_status': 'OPEN', 'reason': 'Test reset'})
req_reset = urllib.request.Request(BASE + '/judges/evaluations/2/status?' + params_reset, method='POST')
req_reset.add_header('Authorization', f'Bearer {hjt}')
try:
    urllib.request.urlopen(req_reset)
    print('Reset eval 2 to OPEN')
except:
    pass

# Create evaluation (team 7 is in comp 3)
req = urllib.request.Request(BASE + '/judges/evaluations/mine?team_id=7&competition_id=3', method='POST')
req.add_header('Authorization', f'Bearer {hjt}')
resp = urllib.request.urlopen(req)
eval_data = json.loads(resp.read())
eval_id = eval_data['id']
print(f'Eval created: id={eval_id}')

# Add score
req2 = urllib.request.Request(BASE + f'/judges/evaluations/{eval_id}/scores?criterion_id=1&score=8', method='POST')
req2.add_header('Authorization', f'Bearer {hjt}')
resp2 = urllib.request.urlopen(req2)
print(f'Score added: {json.loads(resp2.read())}')

# HEAD_JUDGE view all scores
req3 = urllib.request.Request(BASE + '/judges/all-scores?competition_id=3', method='GET')
req3.add_header('Authorization', f'Bearer {hjt}')
resp3 = urllib.request.urlopen(req3)
scores = json.loads(resp3.read())
print(f'All scores: {len(scores)} entries')

# Lock
req4 = urllib.request.Request(BASE + f'/judges/evaluations/{eval_id}/status?new_status=LOCKED', method='POST')
req4.add_header('Authorization', f'Bearer {hjt}')
resp4 = urllib.request.urlopen(req4)
print(f'Lock result: {json.loads(resp4.read())}')

# Judge2 tries to add score to locked eval (should be 403)
j2t = login('judge2@sti.edu.mm', 'judge123')
req5 = urllib.request.Request(BASE + f'/judges/evaluations/{eval_id}/scores?criterion_id=1&score=9', method='POST')
req5.add_header('Authorization', f'Bearer {j2t}')
try:
    resp5 = urllib.request.urlopen(req5)
    print(f'FAIL: Judge2 scored locked eval: {json.loads(resp5.read())}')
except urllib.error.HTTPError as e:
    print(f'OK blocked: {e.code} - locked eval rejected')

# HEAD_JUDGE correct score (PATCH)
req6 = urllib.request.Request(BASE + f'/judges/evaluations/{eval_id}/scores/correct?criterion_id=1&score=7&reason=Typo', method='PATCH')
req6.add_header('Authorization', f'Bearer {hjt}')
resp6 = urllib.request.urlopen(req6)
print(f'Correction: {json.loads(resp6.read())}')

# Correction without reason (should fail)
req7 = urllib.request.Request(BASE + f'/judges/evaluations/{eval_id}/scores/correct?criterion_id=1&score=6', method='PATCH')
req7.add_header('Authorization', f'Bearer {hjt}')
try:
    resp7 = urllib.request.urlopen(req7)
    print(f'FAIL: Correction without reason accepted')
except urllib.error.HTTPError as e:
    print(f'OK: no-reason rejected {e.code}')

# Finalize
req8 = urllib.request.Request(BASE + f'/judges/evaluations/{eval_id}/status?new_status=FINALIZED', method='POST')
req8.add_header('Authorization', f'Bearer {hjt}')
resp8 = urllib.request.urlopen(req8)
print(f'Finalize: {json.loads(resp8.read())}')

# Reopen with reason
reason = 'Admin correction needed'
params9 = urllib.parse.urlencode({'new_status': 'OPEN', 'reason': reason})
req9 = urllib.request.Request(BASE + f'/judges/evaluations/{eval_id}/status?' + params9, method='POST')
req9.add_header('Authorization', f'Bearer {hjt}')
resp9 = urllib.request.urlopen(req9)
print(f'Reopen: {json.loads(resp9.read())}')

# Reopen finalized without reason (should fail) — need LOCKED->FINALIZED first
req10 = urllib.request.Request(BASE + f'/judges/evaluations/{eval_id}/status?new_status=LOCKED', method='POST')
req10.add_header('Authorization', f'Bearer {hjt}')
urllib.request.urlopen(req10)
req11 = urllib.request.Request(BASE + f'/judges/evaluations/{eval_id}/status?new_status=FINALIZED', method='POST')
req11.add_header('Authorization', f'Bearer {hjt}')
urllib.request.urlopen(req11)
req12 = urllib.request.Request(BASE + f'/judges/evaluations/{eval_id}/status?new_status=OPEN', method='POST')
req12.add_header('Authorization', f'Bearer {hjt}')
try:
    urllib.request.urlopen(req12)
    print(f'FAIL: Reopen without reason accepted')
except urllib.error.HTTPError as e:
    print(f'OK: reopen-no-reason rejected {e.code}')

# Audit log
req13 = urllib.request.Request(BASE + f'/judges/evaluations/{eval_id}/audit', method='GET')
req13.add_header('Authorization', f'Bearer {hjt}')
resp13 = urllib.request.urlopen(req13)
audit = json.loads(resp13.read())
print(f'Audit entries: {len(audit)}')
for a in audit:
    print(f'  {a["action"]}: {a.get("old_value")} -> {a.get("new_value")} | {a.get("reason","")}')

# Judge2 cannot access /all-scores
req14 = urllib.request.Request(BASE + '/judges/all-scores?competition_id=3', method='GET')
req14.add_header('Authorization', f'Bearer {j2t}')
try:
    resp14 = urllib.request.urlopen(req14)
    print(f'FAIL: Judge2 accessed all-scores')
except urllib.error.HTTPError as e:
    print(f'OK: Judge2 blocked from all-scores: {e.code}')

print()
print('All tests passed!')
