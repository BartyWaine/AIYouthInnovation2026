"""Test submission submit-final and lock behavior."""
import sys, json, uuid
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
import urllib.request, urllib.error, urllib.parse

BASE = 'http://127.0.0.1:8022/api/v1'

def login(email, password):
    body = urllib.parse.urlencode({'username': email, 'password': password}).encode('utf-8')
    req = urllib.request.Request(BASE + '/auth/login', data=body, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())['access_token']

def api_get(path, token):
    req = urllib.request.Request(BASE + path, method='GET')
    req.add_header('Authorization', f'Bearer {token}')
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

def api_post(path, token, params=None):
    url = BASE + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method='POST')
    req.add_header('Authorization', f'Bearer {token}')
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

def api_delete(path, token):
    req = urllib.request.Request(BASE + path, method='DELETE')
    req.add_header('Authorization', f'Bearer {token}')
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

def check(code, fn, *args, **kwargs):
    try:
        return False, fn(*args, **kwargs)
    except urllib.error.HTTPError as e:
        return e.code == code, {'code': e.code, 'detail': e.read().decode()}

# Login as team1
token = login('team1@sti.edu.mm', 'team123')
print('Team1 login: OK')

# Get team info
team_info = api_get('/teams/mine', token)
comp_id = team_info.get('competition_id')

# Get or create a submission
subs = api_get(f'/teams/mine/submissions?competition_id={comp_id}', token)
print(f'Submissions: {len(subs)}')

# Find a submission that is not already submitted
sub_id = None
for s in subs:
    if s.get('status') not in ('SUBMITTED', 'LOCKED'):
        sub_id = s['id']
        break

if not sub_id and subs:
    # All submissions are locked, we can't test
    print('All submissions are already submitted/locked, skipping test')
    sys.exit(0)

if not sub_id:
    print('No submissions found, skipping test')
    sys.exit(0)

print(f'Using submission {sub_id} with status: {next(s.get("status") for s in subs if s["id"] == sub_id)}')

# Upload a file first
boundary = uuid.uuid4().hex
body = (
    b'--' + boundary.encode() + b'\r\n'
    b'Content-Disposition: form-data; name="version"\r\n\r\n1\r\n'
    b'--' + boundary.encode() + b'\r\n'
    b'Content-Disposition: form-data; name="file"; filename="test_submit.pdf"\r\n'
    b'Content-Type: application/pdf\r\n\r\n'
    + b'%PDF-1.4 test submit file content' + b'\r\n'
    b'--' + boundary.encode() + b'--\r\n'
)
req = urllib.request.Request(BASE + f'/deliverables/submissions/{sub_id}/files', data=body, method='POST')
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
req.add_header('Authorization', f'Bearer {token}')
try:
    resp = urllib.request.urlopen(req)
    upload = json.loads(resp.read())
    print(f'Upload: file={upload.get("original_filename")}, v={upload.get("version")}')
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'Upload failed: {e.code} - {body[:200]}')
    sys.exit(1)

# Submit final
print(f'\nSubmitting submission {sub_id}...')
result = api_post(f'/deliverables/submissions/{sub_id}/submit', token)
print(f'Submit result: status={result.get("status")}')

# Verify status is SUBMITTED
subs_after = api_get(f'/teams/mine/submissions?competition_id={comp_id}', token)
sub = next((s for s in subs_after if s['id'] == sub_id), None)
if sub:
    print(f'Submission status after submit: {sub.get("status")}')
    assert sub.get('status') == 'SUBMITTED', f'Expected SUBMITTED, got {sub.get("status")}'
    print('PASS: Submission status is SUBMITTED')
else:
    print('FAIL: Submission not found after submit')
    sys.exit(1)

# Try to upload another file - should fail
boundary2 = uuid.uuid4().hex
body2 = (
    b'--' + boundary2.encode() + b'\r\n'
    b'Content-Disposition: form-data; name="version"\r\n\r\n1\r\n'
    b'--' + boundary2.encode() + b'\r\n'
    b'Content-Disposition: form-data; name="file"; filename="test_replace.pdf"\r\n'
    b'Content-Type: application/pdf\r\n\r\n'
    + b'%PDF-1.4 test replace file content' + b'\r\n'
    b'--' + boundary2.encode() + b'--\r\n'
)
req2 = urllib.request.Request(BASE + f'/deliverables/submissions/{sub_id}/files', data=body2, method='POST')
req2.add_header('Content-Type', f'multipart/form-data; boundary={boundary2}')
req2.add_header('Authorization', f'Bearer {token}')
try:
    urllib.request.urlopen(req2)
    print('FAIL: Upload after submit should have been rejected')
    sys.exit(1)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'Upload after submit response: {e.code} - {body[:200]}')
    if e.code == 403:
        print('PASS: Upload after submit rejected with 403')
    else:
        print(f'FAIL: Expected 403, got {e.code}')
        sys.exit(1)

# Try to delete file - should fail
ok, resp = check(403, api_delete, f'/deliverables/submissions/{sub_id}/files/{upload.get("id")}', token)
if ok:
    print('PASS: Delete after submit rejected with 403')
else:
    print(f'FAIL: Expected 403, got {resp.get("code")}')
    sys.exit(1)

# Download should still work
files = api_get(f'/deliverables/submissions/{sub_id}/files', token)
if files:
    fid = files[0]['id']
    req = urllib.request.Request(BASE + f'/deliverables/submissions/{sub_id}/files/{fid}/download')
    req.add_header('Authorization', f'Bearer {token}')
    resp = urllib.request.urlopen(req)
    content = resp.read()
    print(f'Download after submit: {resp.status}, size={len(content)} bytes')
    print('PASS: Download still works after submit')
else:
    print('FAIL: No files found for download test')
    sys.exit(1)

print('\nAll submission lock tests passed!')
