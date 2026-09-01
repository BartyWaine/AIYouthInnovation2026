"""Setup script to load 46 real teams into the database.
SAFE FOR DEVELOPMENT ONLY — requires SEED_DEV=1 environment variable.
Never run this against a production database.
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

if os.getenv("SEED_DEV") != "1":
    print("ERROR: This script is for development only.")
    print("Set SEED_DEV=1 to run. Aborting.")
    sys.exit(1)

from app.database import SessionLocal
from app.models import (
    User, UserRole, Team, TeamMember, Competition, Deliverable,
    Judge, JudgeAssignment, Submission, Evaluation, EvaluationScore,
    EvaluationCriteria, AuditLog, SubmissionFile,
)
from app.security import get_password_hash
from app.models import DeliverableCategory
from collections import Counter
from sqlalchemy import inspect as _sqlainspect, text as _text

db = SessionLocal()

# === 0. Create admin and judge users (idempotent) ===
pw_hash = get_password_hash("admin123")
admin = db.query(User).filter(User.email == "admin@sti.edu.mm").first()
if not admin:
    admin = User(email="admin@sti.edu.mm", password_hash=pw_hash, role=UserRole.ADMIN)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    print(f"Created admin: admin@sti.edu.mm")
else:
    print(f"Admin exists: admin@sti.edu.mm (id={admin.id})")

for i in range(1, 6):
    email = f"judge{i}@sti.edu.mm"
    role = UserRole.HEAD_JUDGE if i == 1 else UserRole.JUDGE
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, password_hash=get_password_hash("judge123"), role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created {email} -> {role.value} (id={user.id})")
    else:
        if user.role != role:
            user.role = role
            db.add(user)
            db.commit()
        print(f"Updated {email} -> {role.value}")
    judge_row = db.query(Judge).filter(Judge.user_id == user.id).first()
    if not judge_row:
        judge_row = Judge(user_id=user.id)
        db.add(judge_row)
        db.commit()
        db.refresh(judge_row)
        print(f"  Created Judge row: id={judge_row.id}")

# === 1. Ensure submitted_at column exists (for existing DBs) ===
cols = [c['name'] for c in _sqlainspect(db.bind).get_columns('submission_files')]
if 'submitted_at' not in cols:
    db.execute(_text("ALTER TABLE submission_files ADD COLUMN submitted_at DATETIME"))
    db.commit()
    print("Added submitted_at column")

# === 2. Ensure 3 competitions exist ===
comp1 = db.query(Competition).filter(Competition.name == "AI Youth 2026").first()
if not comp1:
    comp1 = Competition(name="AI Youth 2026", category="AI for Engineering and Technology")
    db.add(comp1)

comp2 = db.query(Competition).filter(Competition.name == "AI Youth 2026_Social").first()
if not comp2:
    comp2 = Competition(name="AI Youth 2026_Social", category="AI for Social Innovation")
    db.add(comp2)

comp3 = db.query(Competition).filter(Competition.name == "AI Youth 2026_Entrepreneur").first()
if not comp3:
    comp3 = Competition(name="AI Youth 2026_Entrepreneur", category="AI for Entrepreneurship")
    db.add(comp3)

db.commit()
competitions = [comp1, comp2, comp3]
print(f"Competitions: {[(c.id, c.name, c.category) for c in competitions]}")

# === 3. Ensure deliverables for each competition ===
for comp in competitions:
    existing_cats = {d.category for d in db.query(Deliverable).filter(Deliverable.competition_id == comp.id).all() if d.category is not None}
    for cat in DeliverableCategory:
        if cat.value not in existing_cats:
            db.add(Deliverable(competition_id=comp.id, name=cat.value, category=cat))
    db.commit()

comp_deliverables = {c.id: db.query(Deliverable).filter(Deliverable.competition_id == c.id).all() for c in competitions}

# === 4. Clean up ALL team data (preserve judge/admin users) ===
print("\n=== Cleaning up ===")
for model in [EvaluationScore, Evaluation, SubmissionFile, Submission,
              JudgeAssignment, TeamMember, AuditLog]:
    for row in db.query(model).all():
        db.delete(row)
    db.commit()

for t in db.query(Team).all():
    db.delete(t)
db.commit()

for u in db.query(User).filter(User.role == UserRole.TEAM_MEMBER).all():
    db.delete(u)
db.commit()

print("Cleanup complete")

# === 5. Create 46 teams ===
# AI Entrepreneurship (comp_id=3), AI for Social Innovation (comp_id=2), AI Technology & Engineering (comp_id=1)
TEAM_DATA = [
    # AI Entrepreneurship
    ("Technologia Ventures", "ConceptX International School", "AI for Entrepreneurship", "Htet Shwe Sin"),
    ("Beyond X", "STI School", "AI for Entrepreneurship", "Eaint Hsu Mon Myint, Eaint Myat Noe San, Bhone Nyan Paing"),
    ("Secret Weapon", "B.E.H.S 1 Dagon", "AI for Entrepreneurship", "Chan Nyein Kyal Sin, Hsu Lei Phyu, Thuta Aung Myo Htun"),
    ("Thakhin", "B.E.H.S 1 Dagon", "AI for Entrepreneurship", "Aung Myint Myat, Ye Yint Paing, Zwe Wai Yan Lin"),
    ("Aesthetic students", "B.E.H.S 1 Dagon", "AI for Entrepreneurship", "Zwe Myo Thant, Wai Yan Soe, Zin Min Oo"),
    ("May Myint Mo Kyi", "B.E.H.S 1 Dagon", "AI for Entrepreneurship", "May Myint Mo Kyi"),
    ("ETS Innovators", "Basic Education High School, Minhla, Bago (West)", "AI for Entrepreneurship", "Eaint Chan Myae, Thaw Tar Nyein Chan, Swan Yi Htet"),
    ("Frame Moggers", "Strategy first international college", "AI for Entrepreneurship", "Htet Kyal Sin, Min Khant Wai Yan Kyaw"),
    # AI for Social Innovation
    ("BlueNode", "Yangon Education Creation Corner (YECC)", "AI for Social Innovation", "Zay Thuya Oo, Chan Myae Thaw, Zwe Khant Oo"),
    ("BrainGrowth", "The Lumbini Mandalay", "AI for Social Innovation", "Aye Chan Zay, Yaung Ni Lin, La Yaung Naing"),
    ("Euphoria", "Majestic Private School", "AI for Social Innovation", "Nant Hay Mhan No No(Judith), Hlaing Min Khant(Riki), Zay Ye Myat(Ardan)"),
    ("Emolink", "STI School (Mandalay)", "AI for Social Innovation", "Phyo Thiri Kyaw, Su Pyae Tun, Chaw Thet Hmue Khin"),
    ("Trustlink Innovators", "STI School (Mandalay)", "AI for Social Innovation", "Aung Pyae Phyo San, Aung Oakga, Khin Meme Ko"),
    ("Code Titans", "HMI", "AI for Social Innovation", "Arkar Kaung Thant, Kyal Sin Thant, Hein Htet Soe"),
    ("O-me Medix", "HMI", "AI for Social Innovation", "Kaung Khant Win Zaw"),
    ("AI Don't Understand Us", "STI School", "AI for Social Innovation", "Khant Zaw Hein, Pyae Wunn Thaw, Aunt Bhone Aung"),
    ("Sabina", "Future Kidz International School", "AI for Social Innovation", "Soe Pyae Yati"),
    ("Blind Mice", "YDP International School", "AI for Social Innovation", "Lu Maw, Hein Zay Lyan, Khant Min Paing"),
    ("Synapse", "IIP International School", "AI for Social Innovation", "Yoon Mo Mo Eaim @ Laura, Htet Kyaw Lwin @ Felix"),
    ("NeuraNova", "OiAC Private School", "AI for Social Innovation", "May Myat Thu, Yu Shwe Yi Hlaing"),
    ("Hsu-Data-Divas", "B.E.H.S(1) Letpadan", "AI for Social Innovation", "Hsu Luck Pyae, Hsu Pyae Sone"),
    ("Viva La Vida", "B.E.H.S 1 Dagon", "AI for Social Innovation", "Hsu Eaint Lwin, Zayar Lin, Eaindray Phyu Sin Myo"),
    ("Cozy Companion", "B.E.H.S 1 Dagon", "AI for Social Innovation", "La Won Yin Myo, Wun Pa Thawdar Ko Htay, Khin Linn Latt Aung"),
    ("Team Vivante", "B.E.H.S 1 Dagon", "AI for Social Innovation", "Wai Yan Lwin, Win Pearl Phyu, Yuya Thanlwin Htut"),
    ("Three Musketeers", "B.E.H.S 1 Dagon", "AI for Social Innovation", "Thin Yati Nay Win, Myu Linn Hay Man Khin, Hein Phyo Kywe"),
    ("Eclipse", "B.E.H.S 1 Dagon", "AI for Social Innovation", "KayZin WinHan, Yoon Nay Yee Hlaing, Shumawa Aung Kyaw"),
    ("M.I.A", "B.E.H.S 1 Dagon", "AI for Social Innovation", "Lin Lat May Maung, Su Sandi Oakca, Eaint Thu Thu Khin"),
    ("Prism Logic", "B.E.H.S 1 Dagon", "AI for Social Innovation", "Sin Sin Lin, Su Myat Phyu Sin, Myat Min Soe"),
    ("Teen Innovations", "Dagon 1", "AI for Social Innovation", "Ei Po Po Aung, Myat Yadanar Hlaing"),
    ("Thein Naing Squad", "B.E.H.S 1 Dagon", "AI for Social Innovation", "Nay Htet Thein Naing, Phone Myat Thaw, Lin Thuta Kyaw"),
    ("Growth learners Thanlwin", "Thanlwin", "AI for Social Innovation", "Aung Hein Kyaw, May Thiri Myat"),
    ("Core 2 AI", "B.E.H.S (Puangde)", "AI for Social Innovation", "Khin Eaindra Min, Hsu Hsu Htet"),
    ("Min Myanmar Team -1", "Min Myanmar Private High School", "AI for Social Innovation", "Thura San, Paing Khant Ko, Si Thu Ye Naing"),
    # AI Technology & Engineering
    ("Viva La Vida", "Majestic Academy", "AI for Engineering and Technology", "Aunt Phyoe Maung, Wai Yan Min Khant, Wai Yan Lin"),
    ("Jimmy/Htut Khaung", "STI School (Mandalay)", "AI for Engineering and Technology", "Htut Khaung Hmue Win Soe, Oakkar Kyaw"),
    ("CodeTrio", "STI School", "AI for Engineering and Technology", "Min Hein Ko, Swamsa, Zwe Htut Naing"),
    ("Team Magnet", "HMI", "AI for Engineering and Technology", "Swam Bhone Lhyun, John Phyo, Shin Thadar Nyi"),
    ("RKD", "HMI", "AI for Engineering and Technology", "Aye Myint Myat Paing, Pyae Phyo Maung, Waddy Thaw Tar"),
    ("Luminary(Lumi)", "STIMU", "AI for Engineering and Technology", "Kyal Sin Shunn Lae"),
    ("The newbie", "B.E.H.S(9) Mawlamyine", "AI for Engineering and Technology", "Si Thu Khant, Lin Htet Zaw"),
    ("77", "IMC", "AI for Engineering and Technology", "Aung Kaung Thu"),
    ("Xcripted 3", "EC Private High School", "AI for Engineering and Technology", "Aung Khant Zaw, Htet Aung Shane, Min Htet Khant Kyaw"),
    ("Team GBK", "B.E.H.S (Branch) Thabyubin", "AI for Engineering and Technology", "Shine Htet Aung, Ayar Swam Htet Paing"),
    ("V", "B.E.H.S 1 Dagon", "AI for Engineering and Technology", "Thant Thura, Ye Myat Aung, Lwin Min Hein"),
    ("Innovators of the Global Nexus", "B.E.H.S 1 Dagon", "AI for Engineering and Technology", "Hnin Ei Shwe Yee, Si That Shwe Thwe, Thoon Haythi Thet"),
]

CAT_TO_COMP = {
    "AI for Engineering and Technology": 1,
    "AI for Social Innovation": 2,
    "AI for Entrepreneurship": 3,
}

print(f"\n=== Creating {len(TEAM_DATA)} teams ===")
for i, (team_name, school, cat_str, participants) in enumerate(TEAM_DATA):
    comp_id = CAT_TO_COMP.get(cat_str, 1)
    team = Team(name=team_name, competition_id=comp_id)
    db.add(team)
    db.commit()
    db.refresh(team)

    pw_hash = get_password_hash("team123")
    user = User(email=f"team{team.id}@sti.edu.mm", password_hash=pw_hash, role=UserRole.TEAM_MEMBER)
    db.add(user)
    db.commit()
    db.refresh(user)
    tm = TeamMember(user_id=user.id, team_id=team.id, is_leader=True)
    db.add(tm)

    for d in comp_deliverables[comp_id]:
        sub = Submission(deliverable_id=d.id, team_id=team.id, version=1)
        db.add(sub)

    db.commit()
    print(f"  [{i+1}] {team_name} (id={team.id}, comp_id={comp_id})")

print(f"Created {len(TEAM_DATA)} teams")

# === 6. Assign all judges to all teams ===
print(f"\n=== Assigning judges ===")
judges = db.query(Judge).all()
all_teams = db.query(Team).all()
print(f"Judges: {len(judges)}, Teams: {len(all_teams)}")

for judge in judges:
    for team in all_teams:
        existing = db.query(JudgeAssignment).filter(
            JudgeAssignment.judge_id == judge.id,
            JudgeAssignment.team_id == team.id,
            JudgeAssignment.competition_id == team.competition_id,
        ).first()
        if not existing:
            assignment = JudgeAssignment(
                judge_id=judge.id,
                team_id=team.id,
                competition_id=team.competition_id,
            )
            db.add(assignment)
    db.commit()

total_assign = db.query(JudgeAssignment).count()
print(f"Total judge assignments: {total_assign}")

# === 7. Summary ===
print("\n=== FINAL SUMMARY ===")
print(f"Users: {db.query(User).count()}")
print(f"  Admin: {db.query(User).filter(User.role == UserRole.ADMIN).count()}")
print(f"  Head Judge: {db.query(User).filter(User.role == UserRole.HEAD_JUDGE).count()}")
print(f"  Judges: {db.query(User).filter(User.role == UserRole.JUDGE).count()}")
print(f"  Team accounts (1 per team): {db.query(User).filter(User.role == UserRole.TEAM_MEMBER).count()}")
print(f"Teams: {db.query(Team).count()}")
print(f"Submissions: {db.query(Submission).count()}")
print(f"Judge assignments: {db.query(JudgeAssignment).count()}")

comp_counts = Counter(t.competition_id for t in db.query(Team).all())
for comp_id, count in sorted(comp_counts.items()):
    comp = db.get(Competition, comp_id)
    deliv_count = len(comp_deliverables[comp_id])
    print(f"  Competition {comp_id} ({comp.name if comp else '?'}): {count} teams, {deliv_count} deliverables, {count * deliv_count} submissions")

cat_counts = Counter()
for team_name, school, cat_str, _ in TEAM_DATA:
    cat_counts[cat_str] += 1
print("\nTeams by category:")
for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")

print("\nJudge accounts:")
print("  Judge1 (HEAD_JUDGE): judge1@sti.edu.mm / judge123")
print("  Judges 2-5 (JUDGE):  judge2@sti.edu.mm through judge5@sti.edu.mm / judge123")
print("All team accounts: team{id}@sti.edu.mm / team123")
print("Done!")

db.close()
