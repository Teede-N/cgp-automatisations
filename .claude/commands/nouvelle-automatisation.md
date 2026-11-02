---
description: Cadre puis implémente une nouvelle automatisation métier
argument-hint: [besoin exprimé par l'équipe]
---
Besoin : $ARGUMENTS

1. Reformule le besoin et pose au plus 3 questions si une règle métier est ambiguë.
2. Rédige d'abord la fiche process dans `docs/process/` (déclencheur, règles, sorties, validation humaine).
3. Implémente dans `src/automatisations/` avec des tests dans `tests/`, puis lance `pytest -q`.
4. Si l'automatisation doit tourner seule, propose le workflow n8n correspondant dans `n8n/`.
