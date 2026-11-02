"""Reporting hebdomadaire : synthèse Markdown + message Slack (format Block Kit) prêt à poster.

Usage : python -m automatisations.reporting
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from .qualite_crm import score_qualite


def construire(contacts: list[dict], relances: list[dict], n_doublons: int) -> tuple[str, dict]:
    clients = [c for c in contacts if c["lifecyclestage"] == "customer"]
    encours = sum(int(c["encours_eur"]) for c in clients)
    etapes = Counter(c["lifecyclestage"] for c in contacts)
    anomalies = {c["hs_object_id"]: [a for a in c["anomalies"].split("; ") if a] for c in contacts}
    par_conseiller = Counter(r["conseiller"] for r in relances)
    md = ["# Reporting hebdomadaire du cabinet", "",
          "| Indicateur | Valeur |", "|---|---|",
          f"| Contacts dans le CRM | {len(contacts)} |",
          f"| Clients | {etapes['customer']} |",
          f"| Opportunités / leads | {etapes['opportunity']} / {etapes['lead']} |",
          f"| Encours suivi (clients) | {encours:,} € |".replace(",", " "),
          f"| Fiches complètes et conformes | {score_qualite(anomalies):.0%} |",
          f"| Doublons à fusionner | {n_doublons} |",
          f"| Relances préparées | {len(relances)} |", "",
          "## Relances par conseiller", ""]
    md += [f"- {k} : {v}" for k, v in par_conseiller.most_common()]
    slack = {"blocks": [
        {"type": "header", "text": {"type": "plain_text", "text": "📊 Reporting hebdo du cabinet"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*Clients*\n{etapes['customer']}"},
            {"type": "mrkdwn", "text": f"*Encours suivi*\n{encours:,} €".replace(",", " ")},
            {"type": "mrkdwn", "text": f"*Qualité CRM*\n{score_qualite(anomalies):.0%} de fiches conformes"},
            {"type": "mrkdwn", "text": f"*Relances prêtes*\n{len(relances)} brouillons à relire"}]},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": "Généré automatiquement · détails dans le rapport qualité"}]},
    ]}
    return "\n".join(md) + "\n", slack


if __name__ == "__main__":
    from .qualite_crm import executer
    from .relances import preparer
    sorties = Path("sorties")
    res = executer(Path("data/export_hubspot_contacts.csv"), sorties)
    with open(sorties / "contacts_nettoyes.csv", encoding="utf-8") as f:
        contacts = list(csv.DictReader(f))
    relances = preparer(contacts, sorties)
    md, slack = construire(contacts, relances, len(res.doublons))
    (sorties / "reporting_hebdo.md").write_text(md, encoding="utf-8")
    (sorties / "slack_message.json").write_text(json.dumps(slack, ensure_ascii=False, indent=2), encoding="utf-8")
    print(md)
