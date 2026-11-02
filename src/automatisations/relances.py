"""Relances automatiques : prépare des brouillons d'e-mails personnalisés, jamais envoyés seuls.

Règles (documentées dans docs/process/relance_kyc.md) :
  - KYC expiré, ou qui expire dans les 30 jours  -> relance « mise à jour KYC »
  - client sans contact depuis plus de 90 jours  -> relance « point annuel »
Sortie : un fichier par brouillon dans sorties/brouillons/ + un récapitulatif par conseiller.

Usage : python -m automatisations.relances sorties/contacts_nettoyes.csv
"""
from __future__ import annotations

import csv
import sys
from datetime import date, timedelta
from pathlib import Path

MODELES = {
    "kyc": ("Mise à jour de votre dossier client",
            "Bonjour {prenom},\n\nLa réglementation nous demande de mettre à jour régulièrement votre dossier "
            "(situation, objectifs, profil de risque). Votre dernière mise à jour date du {date_kyc}.\n\n"
            "Pourriez-vous me proposer un créneau de 20 minutes dans les deux prochaines semaines ?\n\n"
            "Bien cordialement,\n{conseiller}"),
    "point_annuel": ("Faisons le point sur votre patrimoine",
                     "Bonjour {prenom},\n\nNous ne nous sommes pas parlé depuis le {dernier_contact}. "
                     "C'est le bon moment pour faire le point sur vos objectifs et l'allocation de votre patrimoine.\n\n"
                     "Seriez-vous disponible pour un rendez-vous de 30 minutes ?\n\nBien cordialement,\n{conseiller}"),
}


def date_fr(iso: str) -> str:
    d = date.fromisoformat(iso)
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre",
            "octobre", "novembre", "décembre"][d.month - 1]
    return f"{d.day} {mois} {d.year}"


def a_relancer(c: dict, aujourd_hui: date) -> str | None:
    if c["lifecyclestage"] != "customer" or not c["email"] or "e-mail invalide" in c.get("anomalies", ""):
        return None
    if c["date_kyc"] and date.fromisoformat(c["date_kyc"]) + timedelta(days=365 - 30) <= aujourd_hui:
        return "kyc"
    if (aujourd_hui - date.fromisoformat(c["date_dernier_contact"])).days > 90:
        return "point_annuel"
    return None


def preparer(contacts: list[dict], sorties: Path, aujourd_hui: date = date(2026, 11, 2)) -> list[dict]:
    dossier = sorties / "brouillons"
    dossier.mkdir(parents=True, exist_ok=True)
    faits = []
    for c in contacts:
        motif = a_relancer(c, aujourd_hui)
        if not motif:
            continue
        objet, corps = MODELES[motif]
        texte = corps.format(prenom=c["firstname"], conseiller=c["conseiller"],
                             date_kyc=date_fr(c["date_kyc"]) if c["date_kyc"] else "—",
                             dernier_contact=date_fr(c["date_dernier_contact"]))
        (dossier / f"{c['hs_object_id']}_{motif}.md").write_text(
            f"À : {c['email']}\nObjet : {objet}\n\n{texte}\n", encoding="utf-8")
        faits.append({"id": c["hs_object_id"], "client": f"{c['firstname']} {c['lastname']}",
                      "conseiller": c["conseiller"], "motif": motif})
    return faits


if __name__ == "__main__":
    with open(sys.argv[1] if len(sys.argv) > 1 else "sorties/contacts_nettoyes.csv", encoding="utf-8") as f:
        relances = preparer(list(csv.DictReader(f)), Path("sorties"))
    for r in relances:
        print(f"{r['conseiller']:14s} {r['motif']:13s} {r['client']}")
    print(f"\n{len(relances)} brouillons préparés dans sorties/brouillons/ (à relire avant envoi)")
