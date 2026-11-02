# CLAUDE.md – consignes pour Claude Code sur ce dépôt

## Contexte
Automatisations d'un cabinet de conseil en gestion de patrimoine (données FICTIVES) :
fiabilisation du CRM HubSpot, relances clients, reporting, workflows n8n.

## Règles non négociables
- **Aucun envoi automatique** au client : les relances sont des *brouillons* relus par un conseiller.
- **Aucune fusion automatique** de doublons : on les propose, un humain valide.
- Ne jamais committer de données réelles ni de secrets (`.env`, jetons HubSpot, clés API).
- Toute nouvelle règle métier est documentée dans `docs/process/` **et** testée dans `tests/`.

## Commandes utiles
- `PYTHONPATH=src python -m automatisations.reporting` : chaîne complète (qualité → relances → reporting)
- `pytest -q` : tests (obligatoires avant tout commit)

## Conventions
- Python 3.11, bibliothèque standard uniquement (pas de dépendance sans raison).
- Fonctions pures et testables ; les entrées/sorties de fichiers restent dans `executer()` / `__main__`.
- Messages, rapports et brouillons en français, vouvoiement, ton sobre.
