import random
import string
import sys
import os

# Ensure the project root (backend) is in Python path so we can import the app package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.database import SessionLocal
from app import models
from app.security import get_password_hash

def random_email():
    return f"user_{''.join(random.choices(string.ascii_lowercase, k=6))}@example.com"

def create_competition(db):
    comp = models.Competition(name="AI Innovation Youth 2026")
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return comp

def create_deliverables(db, competition_id):
    names = [
        "Problem Statement & User Persona",
        "AI Driven Solution Concept",
        "Functional Prototype or Mockup",
        "Competition Pitch Deck",
        "Business Model Summary",
        "Impact & SDG Alignment Summary",
    ]
    for name in names:
        d = models.Deliverable(
            competition_id=competition_id,
            name=name,
            description=f"Deliverable for {name}",
            deadline=None,
            required_file_types=None,
            max_file_size=None,
        )
        db.add(d)
    db.commit()

def create_teams_and_members(db, competition_id, team_count=55, members_per_team=3):
    for i in range(1, team_count + 1):
        team = models.Team(name=f"Team_{i:03d}", competition_id=competition_id)
        db.add(team)
        db.commit()
        db.refresh(team)
        # create members
        for j in range(1, members_per_team + 1):
            email = random_email()
            password_hash = get_password_hash("password123")
            user = models.User(email=email, password_hash=password_hash, role=models.UserRole.TEAM_MEMBER)
            db.add(user)
            db.commit()
            db.refresh(user)
            is_leader = (j == 1)  # first member is leader
            member = models.TeamMember(team_id=team.id, user_id=user.id, is_leader=is_leader)
            db.add(member)
        db.commit()

def seed():
    db = SessionLocal()
    try:
        competition = create_competition(db)
        create_deliverables(db, competition.id)
        create_teams_and_members(db, competition.id)
        print(f"Seeded competition {competition.id} with 55 teams and deliverables.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
