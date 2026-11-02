"""Fiabilisation d'un export de contacts HubSpot.

Étapes : normalisation (casse, espaces, e-mails, téléphones) -> détection des doublons
-> contrôles de complétude et de conformité (KYC) -> 3 sorties :
  - sorties/contacts_nettoyes.csv      : la base propre (une ligne par contact)
  - sorties/import_hubspot.csv         : uniquement les champs modifiés, prêt à réimporter
  - sorties/rapport_qualite.md         : synthèse pour l'équipe (avant / après, doublons, actions)
Rien n'est fusionné automatiquement : les doublons sont PROPOSÉS, un humain valide la fusion.

Usage : python -m automatisations.qualite_crm data/export_hubspot_contacts.csv
"""
from __future__ import annotations

import csv
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

RE_EMAIL = re.compile(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$")
CHAMPS_OBLIGATOIRES = ["firstname", "lastname", "email", "phone", "date_kyc"]
LIBELLES = {"firstname": "prénom manquant", "lastname": "nom manquant", "email": "e-mail manquant",
            "phone": "téléphone manquant", "date_kyc": "date de KYC manquante"}
KYC_VALIDITE_JOURS = 365


def sans_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normaliser_nom(s: str) -> str:
    s = " ".join(s.split())
    return "-".join(p.capitalize() for p in s.split("-")) if s else ""


def normaliser_email(s: str) -> str:
    return s.strip().lower()


def normaliser_telephone(s: str) -> str:
    chiffres = re.sub(r"\D", "", s)
    if chiffres.startswith("33"):
        chiffres = "0" + chiffres[2:]
    if not re.fullmatch(r"0[1-9]\d{8}", chiffres):
        return ""
    n = chiffres[1:]
    return f"+33 {n[0]} {n[1:3]} {n[3:5]} {n[5:7]} {n[7:9]}"


@dataclass
class Resultat:
    contacts: list[dict]
    modifications: list[dict] = field(default_factory=list)       # (id, champ, avant, après)
    doublons: list[tuple[str, str, float, str]] = field(default_factory=list)
    anomalies: dict[str, list[str]] = field(default_factory=dict)


def fiabiliser(lignes: list[dict], aujourd_hui: date) -> Resultat:
    res = Resultat(contacts=[])
    for brut in lignes:
        c = dict(brut)
        propre = {
            "firstname": normaliser_nom(c["firstname"]),
            "lastname": normaliser_nom(c["lastname"]),
            "email": normaliser_email(c["email"]),
            "phone": normaliser_telephone(c["phone"]) if c["phone"].strip() else "",
        }
        for champ, valeur in propre.items():
            if valeur != c[champ]:
                res.modifications.append({"hs_object_id": c["hs_object_id"], "champ": champ,
                                          "avant": c[champ], "apres": valeur})
                c[champ] = valeur
        anomalies = [LIBELLES[ch] for ch in CHAMPS_OBLIGATOIRES if not c[ch]]
        if c["email"] and not RE_EMAIL.match(c["email"]):
            anomalies.append("e-mail invalide")
        if c["date_kyc"] and (aujourd_hui - date.fromisoformat(c["date_kyc"])).days > KYC_VALIDITE_JOURS:
            anomalies.append("KYC expiré")
        res.anomalies[c["hs_object_id"]] = anomalies
        res.contacts.append(c)

    # Doublons : même e-mail, même téléphone, ou nom complet très proche (accents/casse ignorés)
    cles = [(c["hs_object_id"], sans_accents(f"{c['firstname']} {c['lastname']}".lower()), c) for c in res.contacts]
    for i, (id_a, nom_a, a) in enumerate(cles):
        for id_b, nom_b, b in cles[i + 1:]:
            if a["email"] and a["email"] == b["email"]:
                res.doublons.append((id_a, id_b, 1.0, "même e-mail"))
            elif a["phone"] and a["phone"] == b["phone"]:
                res.doublons.append((id_a, id_b, 1.0, "même téléphone"))
            else:
                ratio = SequenceMatcher(None, nom_a, nom_b).ratio()
                if ratio >= 0.92 and a["conseiller"] == b["conseiller"]:
                    res.doublons.append((id_a, id_b, round(ratio, 2), "nom quasi identique, même conseiller"))
    return res


def score_qualite(anomalies: dict[str, list[str]]) -> float:
    return sum(1 for a in anomalies.values() if not a) / len(anomalies) if anomalies else 1.0


def rapport(avant: Resultat, apres: Resultat, n_modifs: int) -> str:
    compte: dict[str, int] = {}
    for a in apres.anomalies.values():
        for x in a:
            compte[x] = compte.get(x, 0) + 1
    l = ["# Rapport de fiabilisation du CRM", "",
         f"- **Contacts analysés :** {len(apres.contacts)}",
         f"- **Fiches complètes et conformes :** {score_qualite(avant.anomalies):.0%} avant → "
         f"**{score_qualite(apres.anomalies):.0%}** après normalisation",
         f"- **Corrections automatiques :** {n_modifs} (casse, espaces, e-mails, téléphones)",
         f"- **Doublons proposés à la fusion :** {len(apres.doublons)} (validation humaine requise)", "",
         "## Anomalies restantes (à traiter par les conseillers)", "", "| Anomalie | Contacts |", "|---|---|"]
    l += [f"| {k} | {v} |" for k, v in sorted(compte.items(), key=lambda x: -x[1])]
    l += ["", "## Doublons proposés", "", "| Contact A | Contact B | Similarité | Motif |", "|---|---|---|---|"]
    l += [f"| {a} | {b} | {s:.0%} | {m} |" for a, b, s, m in apres.doublons]
    return "\n".join(l) + "\n"


def executer(chemin: Path, sorties: Path, aujourd_hui: date = date(2026, 11, 2)) -> Resultat:
    with open(chemin, encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    # « avant » : contrôles appliqués aux données brutes, sans normalisation
    avant = Resultat(contacts=lignes, anomalies={
        l["hs_object_id"]: ([LIBELLES[ch] for ch in CHAMPS_OBLIGATOIRES if not l[ch].strip()]
                            + ([] if RE_EMAIL.match(l["email"]) or not l["email"] else ["e-mail invalide"])
                            + ([] if not l["phone"] or re.fullmatch(r"\+33 \d( \d{2}){4}", l["phone"]) else ["téléphone"])
                            + (["KYC expiré"] if l["date_kyc"] and (aujourd_hui - date.fromisoformat(l["date_kyc"])).days > KYC_VALIDITE_JOURS else []))
        for l in lignes})
    res = fiabiliser(lignes, aujourd_hui)
    sorties.mkdir(parents=True, exist_ok=True)
    with open(sorties / "contacts_nettoyes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(res.contacts[0]) + ["anomalies"])
        w.writeheader()
        w.writerows({**c, "anomalies": "; ".join(res.anomalies[c["hs_object_id"]])} for c in res.contacts)
    with open(sorties / "import_hubspot.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["hs_object_id", "champ", "avant", "apres"])
        w.writeheader()
        w.writerows(res.modifications)
    (sorties / "rapport_qualite.md").write_text(rapport(avant, res, len(res.modifications)), encoding="utf-8")
    return res


if __name__ == "__main__":
    entree = Path(sys.argv[1] if len(sys.argv) > 1 else "data/export_hubspot_contacts.csv")
    r = executer(entree, Path("sorties"))
    print(Path("sorties/rapport_qualite.md").read_text(encoding="utf-8"))
