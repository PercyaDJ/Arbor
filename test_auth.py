import os
import sys

# Ajouter le chemin vers le backend pour pouvoir importer les modules
sys.path.append("/home/jolan/Developpement/Arbor/backend")

from app.core.config import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User

settings = get_settings()
# Surcharger l'URL de test pour cibler le port forwardé par Docker
# Mais comme l'API tourne dans docker, le port 5432 est forwardé sur l'host
# Il faut récupérer le password depuis .env
import re

env_path = "/home/jolan/Developpement/Arbor/deploy/.env"
if not os.path.exists(env_path):
    print("Pas de .env")
    sys.exit(1)

with open(env_path, "r") as f:
    env_content = f.read()

db_url = re.search(r"ARBOR_DATABASE_URL=(.+)", env_content).group(1)
# Remplacer postgres par localhost
db_url = db_url.replace("@postgres:5432", "@localhost:5432")

admin_pass = re.search(r"ARBOR_ADMIN_PASSWORD=(.+)", env_content).group(1)
admin_email = re.search(r"ARBOR_ADMIN_EMAIL=(.+)", env_content).group(1)

print("DB URL:", db_url)
print("Admin pass in .env:", repr(admin_pass))
print("Admin email in .env:", repr(admin_email))

try:
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    user = session.query(User).filter(User.email == admin_email).first()
    if user:
        print("User found!")
        print("Email in DB:", repr(user.email))
        print("Hashed password:", user.hashed_password)
        
        from app.core.security import verify_password
        is_valid = verify_password(admin_pass, user.hashed_password)
        print("Is password valid?", is_valid)
    else:
        print("USER NOT FOUND IN DB!")
        
        # Afficher tous les utilisateurs
        users = session.query(User).all()
        for u in users:
            print("Found user in DB:", repr(u.email))
except Exception as e:
    print("Error:", e)
