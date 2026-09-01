"""Export team info as CSV with email, school, participants.
Uses TEAM_DATA indexed by team_id (1-based) to back-fill school/participants.
"""
import csv
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.database import SessionLocal
from app.models import User, Team, TeamMember, Competition

db = SessionLocal()

# Index 0 = team_id 1, etc. (team IDs are 1-based)
TEAM_DATA = [
    None,  # placeholder for 0-index convenience
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
    ("\u101e\u1004\u103b\u1038\u1040\u1030\u1014\u103e\u1005\u101b\u1038 \u1015\u103c\u102f\u101b\u1031\u102c\u103a", "\u101e\u101c\u1001\u102c\u1000 ၁ \u1015\u103c\u102f\u101b\u1031\u102c\u103a", "AI Technology & Engineering", "Lat Yar Bo, Mya Hnin Khaing, Kyal Sin Lin Let"),
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

comps = {c.id: c.name for c in db.query(Competition).all()}

rows = (
    db.query(Team, User)
    .join(TeamMember, TeamMember.team_id == Team.id)
    .join(User, User.id == TeamMember.user_id)
    .filter(User.role == 'TEAM_MEMBER')
    .order_by(Team.id)
    .all()
)

writer = csv.writer(sys.stdout)
writer.writerow(["team_id", "team_name", "school", "competition", "participants", "email", "password"])
for team, user in rows:
    info = TEAM_DATA[team.id] if team.id < len(TEAM_DATA) else None
    if info:
        school, participants = info[1], info[3]
    else:
        school, participants = "", ""
    comp_name = comps.get(team.competition_id, "")
    writer.writerow([
        team.id,
        team.name,
        school,
        comp_name,
        participants,
        user.email,
        "team123",
    ])

db.close()
