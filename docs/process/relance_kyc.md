# Process – Relance de mise à jour KYC

| Élément | Règle |
|---|---|
| **Objectif** | Tenir à jour la connaissance client (obligation réglementaire) sans charge manuelle de suivi |
| **Déclencheur** | Chaque lundi à 8 h (workflow n8n `01_relance_kyc_hebdo`) |
| **Population** | Clients (`lifecyclestage = customer`) avec un e-mail valide |
| **Règle** | KYC de plus de 11 mois (expiré ou expirant dans les 30 jours) |
| **Sortie** | Un **brouillon** d'e-mail par client dans la boîte du conseiller + un récapitulatif Slack |
| **Validation humaine** | Le conseiller relit, personnalise si besoin et envoie lui-même |
| **Indicateur suivi** | Nombre de KYC expirés (reporting hebdomadaire) |
| **Propriétaire** | Responsable conformité du cabinet |
