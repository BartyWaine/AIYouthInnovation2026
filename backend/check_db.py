import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
from app.database import SessionLocal, engine
from sqlalchemy import inspect, text

db = SessionLocal()
insp = inspect(engine)
cols = [c['name'] for c in insp.get_columns('submission_files')]
print(f'SubmissionFile columns: {cols}')
print(f'submitted_at exists: {"submitted_at" in cols}')

# Check if any files exist
from app.models import SubmissionFile
count = db.query(SubmissionFile).count()
print(f'Total SubmissionFile records: {count}')
if count > 0:
    f = db.query(SubmissionFile).first()
    print(f'First file: id={f.id}, submission_id={f.submission_id}, has_submitted_at={hasattr(f, "submitted_at")}')
db.close()
