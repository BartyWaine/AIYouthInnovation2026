"""Setup script to load 55 real teams into the database."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.database import SessionLocal
from app.models import (
    User, UserRole, Team, TeamMember, Competition, Deliverable,
    Judge, JudgeAssignment, Submission, Evaluation, EvaluationScore,
    EvaluationCriteria, AuditLog, SubmissionFile,
)
from app.security import get_password_hash
from app.models import DeliverableCategory
from collections import Counter

db = SessionLocal()

# === 0. Ensure submitted_at column exists ===
from sqlalchemy import inspect, text
insp = inspect(db.bind)
cols = [c['name'] for c in insp.get_columns('submission_files')]
if 'submitted_at' not in cols:
    db.execute(text("ALTER TABLE submission_files ADD COLUMN submitted_at DATETIME"))
    db.commit()
    print("Added submitted_at column")

# === 1. Clean up ALL data ===
print("=== Cleaning up ===")
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

admin_judge = db.query(Judge).filter(Judge.user_id == 1).first()
if admin_judge:
    db.delete(admin_judge)
    db.commit()
print("Cleanup complete")

# === 2. Verify existing data ===
competitions = db.query(Competition).all()
print(f"Competitions: {[(c.id, c.name, c.category) for c in competitions]}")

judges = db.query(Judge).all()
print(f"Judges: {[(j.id, j.user_id) for j in judges]}")

# Ensure standard deliverables
for comp in competitions:
    existing_cats = {d.category for d in db.query(Deliverable).filter(Deliverable.competition_id == comp.id).all() if d.category is not None}
    for cat in DeliverableCategory:
        if cat.value not in existing_cats:
            db.add(Deliverable(competition_id=comp.id, name=cat.value, category=cat))
    db.commit()
    delivs = db.query(Deliverable).filter(Deliverable.competition_id == comp.id).all()
    print(f"  Comp {comp.id} ({comp.name}): {len(delivs)} deliverables")

# === 3. Team data (55 teams) ===
TEAM_DATA = [
    ("Technologia Ventures", "ConceptX International School", "AI Entrepreneurship", "Htet Shwe Sin"),
    ("BlueNode", "Yangon Education Creation Corner (YECC)", "AI for Social Innovation", "Zay Thuya Oo, Chan Myae Thaw, Zwe Khant Oo"),
    ("BrainGrowth", "The Lumbini Mandalay", "AI for Social Innovation", "Aye Chan Zay, Yaung Ni Lin, La Yaung Naing"),
    ("Viva La Vida", "Majestic Academy", "AI Technology & Engineering", "Aunt Phyoe Maung, Wai Yan Min Khant, Wai Yan Lin"),
    ("Euphoria", "Majestic Private School", "AI for Social Innovation", "Nant Hay Mhan No No(Judith), Hlaing Min Khant(Riki), Zay Ye Myat(Ardan)"),
    ("Emolink", "STI School (Mandalay)", "AI for Social Innovation", "Phyo Thiri Kyaw, Su Pyae Tun, Chaw Thet Hmue Khin"),
    ("Beyond X", "STI School", "AI Entrepreneurship", "Eaint Hsu Mon Myint, Eaint Myat Noe San, Bhone Nyan Paing"),
    ("Trustlink Innovators", "STI School (Mandalay)", "AI for Social Innovation", "Aung Pyae Phyo San, Aung Oakga, Khin Meme Ko"),
    ("Jimmy/Htut Khaung", "STI School (Mandalay)", "AI Technology & Engineering", "Htut Khaung Hmue Win Soe, Oakkar Kyaw"),
    ("CodeTrio", "STI School", "AI Technology & Engineering", "Min Hein Ko, Swamsa, Zwe Htut Naing"),
    ("Team Magnet", "HMI", "AI Technology & Engineering", "Swam Bhone Lhyun, John Phyo, Shin Thadar Nyi"),
    ("RKD", "HMI", "AI Technology & Engineering", "Aye Myint Myat Paing, Pyae Phyo Maung, Waddy Thaw Tar"),
    ("Code Titans", "HMI", "AI for Social Innovation", "Arkar Kaung Thant, Kyal Sin Thant"),
    ("O-me Medix", "HMI", "AI for Social Innovation", "Hein Htet Soe, Kaung Khant Win Zaw"),
    ("Luminary(Lumi)", "STIMU", "AI Technology & Engineering", "Kyal Sin Shunn Lae"),
    ("AI Don't Understand Us", "STI School", "AI for Social Innovation", "Khant Zaw Hein, Pyae Wunn Thaw"),
    ("Sabina", "Future Kidz International School", "AI for Social Innovation", "Soe Pyae Yati"),
    ("Nwayly.", "GIC", "AI Entrepreneurship", "Nwayly"),
    ("White Sheet", "SAMS", "AI Technology & Engineering", "Zau Htoi Awng"),
    ("Dennis", "B.E.H.S(3) Pyapon", "AI Technology & Engineering", "Dennis"),
    ("The newbie", "B.E.H.S(9) Mawlamyine", "AI Technology & Engineering", "Si Thu Khant, Lin Htet Zaw"),
    ("77", "IMC", "AI Technology & Engineering", "Aung Kaung Thu"),
    ("Blind Mice", "YDP International School", "AI for Social Innovation", "Lu Maw, Hein Zay Lyan, Khant Min Paing"),
    ("Xcripted 3", "EC Private High School", "AI Technology & Engineering", "Aung Khant Zaw, Htet Aung Shane, Min Htet Khant Kyaw"),
    ("Synapse", "IIP International School", "AI for Social Innovation", "Yoon Mo Mo Eaim @ Laura, Htet Kyaw Lwin @ Felix"),
    ("NeuraNova", "OiAC Private School", "AI for Social Innovation", "May Myat Thu, Yu Shwe Yi Hlaing"),
    ("Hsu-Data-Divas", "B.E.H.S(1) Letpadan", "AI for Social Innovation", "Hsu Luck Pyae, Hsu Pyae Sone"),
    ("အထက်ကက္ကြောင်း ပင်းတယ", "အ၊ထ၊က ၁ ပင်းတယ", "AI Technology & Engineering", "Lat Yar Bo, Mya Hnin Khaing, Kyal Sin Lin Let"),
    ("THINN", "B.E.H.S (2) Sittwe", "AI for Social Innovation", "Thinn Thinn Hlaing"),
    ("Team GBK", "B.E.H.S (Branch) Thabyubin", "AI Technology & Engineering", "Shine Htet Aung, Ayar Swam Htet Paing"),
    ("Chan Nyein Kyal Sin", "B.E.H.S 1 Dagon", "AI Entrepreneurship", "Chan Nyein Kyal Sin, Hsu Lei Phyu, Thuta Aung Myo Htun"),
    ("V", "B.E.H.S 1 Dagon", "AI Technology & Engineering", "Thant Thura, Ye Myat Aung, Lwin Min Hein"),
    ("Viva La Vida", "B.E.H.S 1 Dagon", "AI for Social Innovation", "Hsu Eaint Lwin, Zayar Lin, Eaindray Phyu Sin Myo"),
    ("Daydreamers", "ELC Private High School", "AI Technology & Engineering", "Ye Yint Zaw, Bhone Turain Htun, Shwe Sin Phyo"),
    ("Cozy Companion", "B.E.H.S 1 Dagon", "AI for Social Innovation", "La Won Yin Myo, Wun Pa Thawdar Ko Htay, Khin Linn Latt Aung"),
    ("Team Vivante", "B.E.H.S 1 Dagon", "AI for Social Innovation", "Wai Yan Lwin, Win Pearl Phyu, Yuya Thanlwin Htut"),
    ("Three musketeers", "B.E.H.S 1 Dagon", "AI for Social Innovation", "Thin Yati Nay Win, Myu Linn Hay Man Khin, Hein Phyo Kywe"),
    ("Thakhin", "B.E.H.S 1 Dagon", "AI Entrepreneurship", "Aung Myint Myat, Ye Yint Paing, Zwe Wai Yan Lin"),
    ("Eclipse", "B.E.H.S 1 Dagon", "AI for Social Innovation", "KayZin WinHan, Yoon Nay Yee Hlaing, Shumawa Aung Kyaw"),
    ("Aesthetic students", "B.E.H.S 1 Dagon", "AI Entrepreneurship", "Zwe Myo Thant, Wai Yan Soe, Zin Min Oo"),
    ("M.I.A", "B.E.H.S 1 Dagon", "AI for Social Innovation", "Lin Lat May Maung, Su Sandi Oakca, Eaint Thu Thu Khin"),
    ("Prism Logic", "B.E.H.S 1 Dagon", "AI for Social Innovation", "Sin Sin Lin, Su Myat Phyu Sin, Myat Min Soe"),
    ("Teen Innovations", "Dagon 1", "AI for Social Innovation", "Ei Po Po Aung, Myat Yadanar Hlaing"),
    ("Thein Naing Squad", "B.E.H.S 1 Dagon", "AI for Social Innovation", "Nay Htet Thein Naing, Phone Myat Thaw, Lin Thuta Kyaw"),
    ("Innovators of the Global Nexus", "B.E.H.S 1 Dagon", "AI Technology & Engineering", "Hnin Ei Shwe Yee, Si That Shwe Thwe, Thoon Haythi Thet"),
    ("May Myint Mo Kyi", "B.E.H.S 1 Dagon", "AI Entrepreneurship", "May Myint Mo Kyi"),
    ("Growth learners Thanlwin", "Thanlwin", "AI for Social Innovation", "Aung Hein Kyaw, May Thiri Myat"),
    ("ETS Innovators", "Basic Education High School, Minhla, Bago (West)", "AI Entrepreneurship", "Eaint Chan Myae, Thaw Tar Nyein Chan, Swan Yi Htet"),
    ("ROS AI", "B.E.H S(2) Lanmadaw", "AI for Social Innovation", "Kyaw Thu Ya Aung, Shine Wana, Ye Htet Kyaw"),
    ("Hsu Hsu Htet+Khin Eaidra Min", "B.E.H.S (Puangde)", "AI for Social Innovation", "Khin Eaindra Min, Hsu Hsu Htet"),
    ("Min Myanmar Team -1", "Min Myanmar Private High School", "AI for Social Innovation", "Thura San, Paing Khant Ko, Si Thu Ye Naing"),
    ("Min Myanmar Team -2", "Min Myanmar Private High School", "AI Technology & Engineering", "Saw Moo Keh Blute, Kaung Myat Min"),
    ("Frame Moggers", "Strategy first international college", "AI Entrepreneurship", "Htet Kyal Sin"),
    ("The Ones", "STI School", "AI Technology & Engineering", "Nang Phyu Sin Myint Myat @ Angel, So Pyay Tun"),
    ("The 0478 Innovators", "STI School", "AI for Social Innovation", "Nyein Moe Wai, Saw Doh Nay Htoo"),
]

CAT_TO_COMP = {
    "AI for Engineering and Technology": 1,
    "AI Technology & Engineering": 1,
    "AI for Social Innovation": 2,
    "AI Entrepreneurship": 3,
    "AI for Entrepreneurship": 3,
}

comp_deliverables = {}
for comp in competitions:
    comp_deliverables[comp.id] = db.query(Deliverable).filter(Deliverable.competition_id == comp.id).all()

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

print(f"Created {len(TEAM_DATA)} teams")

# === 4. Assign judges ===
print(f"\n=== Assigning judges ===")
judges = db.query(Judge).filter(Judge.user_id != 1).all()
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

# === 5. Summary ===
print("\n=== FINAL SUMMARY ===")
print(f"Users: {db.query(User).count()}")
print(f"  Admin: {db.query(User).filter(User.role == UserRole.ADMIN).count()}")
print(f"  Team accounts (1 per team): {db.query(User).filter(User.role == UserRole.TEAM_MEMBER).count()}")
print(f"  Judges: {db.query(User).filter(User.role == UserRole.JUDGE).count()}")
print(f"Teams: {db.query(Team).count()}")
print(f"Submissions: {db.query(Submission).count()}")
print(f"Judge assignments: {db.query(JudgeAssignment).count()}")

comp_counts = Counter(t.competition_id for t in db.query(Team).all())
for comp_id, count in sorted(comp_counts.items()):
    deliv_count = len(comp_deliverables[comp_id])
    print(f"  Competition {comp_id}: {count} teams, {deliv_count} deliverables, {count * deliv_count} submissions")

# Count by category
cat_counts = Counter()
for team_name, school, cat_str, _ in TEAM_DATA:
    cat_counts[cat_str] += 1
print("\nTeams by category:")
for cat, count in cat_counts.most_common():
    print(f"  {cat}: {count}")

print("\nAll 5 judges: judge1@sti.edu.mm through judge5@sti.edu.mm / judge123")
print("All 55 team accounts: team1@sti.edu.mm through team55@sti.edu.mm / team123")
print("Done!")

db.close()
