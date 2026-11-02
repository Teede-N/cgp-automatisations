"""Génère un export CRM FICTIF au format HubSpot (contacts), volontairement « sale ».

Défauts introduits : doublons (même personne saisie deux fois), casse et espaces
incohérents, téléphones dans tous les formats, e-mails invalides, champs manquants.

Usage : python data/generer_export.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(5)
AUJ = date(2026, 11, 2)
PRENOMS = ["claire", "Thomas", "SOPHIE", "Nicolas", "julie", "Antoine", "Camille", "Hugo", "Léa", "Marc",
           "Inès", "Paul", "Sarah", "Louis", "Emma", "Karim", "Chloé", "Yanis", "Anne", "Victor"]
NOMS = ["martin", "BERNARD", "Dubois", "Lefèvre", "Moreau", "laurent", "Simon", "Michel", "Garcia", "Roux",
        "Fournier", "Girard", "Bonnet", "Mercier", "Blanc", "Faure", "Chevalier", "Robin", "Masson", "Henry"]
CONSEILLERS = ["Alexandre P.", "Nadia B."]


def tel(r):
    n = f"6{r.randint(10000000, 99999999)}"
    return r.choice([f"0{n}", f"+33{n}", f"0{n[0]} {n[1:3]} {n[3:5]} {n[5:7]} {n[7:]}", f"0{n[0]}.{n[1:3]}.{n[3:5]}.{n[5:7]}.{n[7:]}", ""])


lignes = []
identites = random.sample([(p, n) for p in PRENOMS for n in NOMS], 60)  # 60 personnes distinctes
for i, (p, n) in enumerate(identites, 1):
    email = f"{p}.{n}@exemple.fr".lower()
    email = random.choices([email, f" {email.upper()} ", email.replace("@", ""), ""], weights=[70, 12, 6, 12])[0]
    lignes.append({
        "hs_object_id": 1000 + i, "firstname": f" {p}" if random.random() < 0.2 else p, "lastname": n,
        "email": email, "phone": tel(random),
        "lifecyclestage": random.choice(["lead", "opportunity", "customer", "customer"]),
        "date_dernier_contact": (AUJ - timedelta(days=random.randint(3, 260))).isoformat(),
        "date_kyc": (AUJ - timedelta(days=random.randint(20, 520))).isoformat() if random.random() < 0.9 else "",
        "conseiller": random.choice(CONSEILLERS),
        "encours_eur": random.choice([0, 25000, 80000, 150000, 320000, 600000]),
    })
# Doublons : 4 personnes ressaisies avec un autre format (casse, téléphone, e-mail vide)
for src in random.sample(lignes, 4):
    d = dict(src)
    d.update(hs_object_id=2000 + src["hs_object_id"], firstname=src["firstname"].strip().upper(),
             email="", date_dernier_contact=(AUJ - timedelta(days=400)).isoformat())
    lignes.append(d)

with open(Path(__file__).with_name("export_hubspot_contacts.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=lignes[0].keys())
    w.writeheader()
    w.writerows(lignes)
print(f"{len(lignes)} contacts exportés")
