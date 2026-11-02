# Process – Fiabilisation mensuelle du CRM

1. **Export** des contacts HubSpot (CSV) le premier lundi du mois.
2. **Normalisation automatique** : casse des noms, espaces, e-mails en minuscules, téléphones au format `+33 6 12 34 56 78`.
3. **Contrôles** : champs obligatoires (nom, prénom, e-mail, téléphone, date de KYC), e-mail valide, KYC à jour.
4. **Doublons** : même e-mail, même téléphone ou nom quasi identique avec le même conseiller → **proposés**, jamais fusionnés automatiquement.
5. **Réimport** dans HubSpot du fichier `import_hubspot.csv` (uniquement les champs modifiés, avec leur ancienne valeur pour audit).
6. **Suivi** du score « fiches complètes et conformes » dans le reporting hebdomadaire.
