---
description: Fiabilise un export de contacts HubSpot et résume les actions à mener
argument-hint: [chemin de l'export CSV]
---
1. Lance `PYTHONPATH=src python -m automatisations.qualite_crm $ARGUMENTS` (par défaut `data/export_hubspot_contacts.csv`).
2. Lis `sorties/rapport_qualite.md`.
3. Résume en 5 lignes maximum : score avant/après, nombre de corrections, doublons proposés, les 3 anomalies les plus fréquentes.
4. Propose, sans les exécuter, les actions à confier aux conseillers. Ne fusionne aucun doublon.
