---
description: Produit le reporting hebdomadaire et le message Slack, sans le publier
---
1. Lance `PYTHONPATH=src python -m automatisations.reporting`.
2. Vérifie la cohérence des chiffres entre `sorties/reporting_hebdo.md` et `sorties/rapport_qualite.md`.
3. Montre-moi le message `sorties/slack_message.json` mis en forme. Ne le publie pas : j'enverrai moi-même.
