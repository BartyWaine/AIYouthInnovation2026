import sys, json, uuid
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
import urllib.request, urllib.error, urllib.parse

BASE = 'http://127.0.0.1:8023/api/v1'

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

# Upload as team1
token = login('team1@sti.edu.mm', 'team123')
print(f'Team1 login: OK')

team_info = api_get('/teams/mine', token)
comp_id = team_info.get('competition_id')
print(f'Team: {team_info.get("name")}, Comp: {comp_id}')

subs = api_get(f'/teams/mine/submissions?competition_id={comp_id}', token)
print(f'Submissions: {len(subs)}')

if subs:
    sub_id = subs[0]['id']
    boundary = uuid.uuid4().hex
    body = (
        b'--' + boundary.encode() + b'\r\n'
        b'Content-Disposition: form-data; name="version"\r\n\r\n1\r\n'
        b'--' + boundary.encode() + b'\r\n'
        b'Content-Disposition: form-data; name="file"; filename="team_upload.pdf"\r\n'
        b'Content-Type: application/pdf\r\n\r\n'
        + b'%PDF-1.4 team upload file content' + b'\r\n'
        b'--' + boundary.encode() + b'--\r\n'
    )
    req = urllib.request.Request(BASE + f'/deliverables/submissions/{sub_id}/files', data=body, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    req.add_header('Authorization', f'Bearer {token}')
    resp = urllib.request.urlopen(req)
    upload = json.loads(resp.read())
    print(f'Upload: file={upload.get("original_filename")}, v={upload.get("version")}')
    print(f'submitted_at={upload.get("submitted_at")}')

# Judge downloads
jtoken = login('judge1@sti.edu.mm', 'judge123')
print(f'\nJudge1 login: OK')

comp_subs = api_get(f'/deliverables/competitions/{comp_id}/submissions', jtoken)
print(f'Judge sees {len(comp_subs)} submissions')

for s in comp_subs:
    if s.get('team_name') == team_info.get('name') and s.get('files'):
        fid = s['files'][0]['id']
        sid = s['submission_id']
        fname = s['files'][0]['original_filename']
        print(f'File: submission_id={sid}, file_id={fid}, name={fname}')
        req = urllib.request.Request(BASE + f'/deliverables/submissions/{sid}/files/{fid}/download')
        req.add_header('Authorization', f'Bearer {jtoken}')
        try:
            resp = urllib.request.urlopen(req)
            content = resp.read()
            print(f'Download: {resp.status}, size={len(content)} bytes')
            print(f'Content-Disposition: {resp.headers.get("Content-Disposition", "NOT SET")}')
            print(f'Content-Type: {resp.headers.get("Content-Type", "NOT SET")}')
            print(f'Content: {content[:40]}')
        except urllib.error.HTTPError as e:
            print(f'Download FAILED: {e.code}: {e.read().decode()[:200]}')
        break
