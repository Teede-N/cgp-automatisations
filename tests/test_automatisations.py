import json
import sys
from datetime import date
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from automatisations.qualite_crm import fiabiliser, normaliser_nom, normaliser_telephone, score_qualite  # noqa: E402
from automatisations.relances import a_relancer, preparer  # noqa: E402
from automatisations.reporting import construire  # noqa: E402

AUJ = date(2026, 11, 2)


def contact(**kw):
    base = {"hs_object_id": "1", "firstname": "Claire", "lastname": "Martin", "email": "claire.martin@exemple.fr",
            "phone": "+33 6 12 34 56 78", "lifecyclestage": "customer", "date_dernier_contact": "2026-10-20",
            "date_kyc": "2026-06-01", "conseiller": "Nadia B.", "encours_eur": "80000"}
    return {**base, **kw}


@pytest.mark.parametrize("brut,attendu", [
    ("0612345678", "+33 6 12 34 56 78"), ("+33612345678", "+33 6 12 34 56 78"),
    ("06.12.34.56.78", "+33 6 12 34 56 78"), ("06 12", ""),
])
def test_normalisation_telephone(brut, attendu):
    assert normaliser_telephone(brut) == attendu


def test_normalisation_noms_composes():
    assert normaliser_nom("  jean-PIERRE ") == "Jean-Pierre"


def test_fiabilisation_corrige_et_trace():
    r = fiabiliser([contact(email=" CLAIRE.MARTIN@EXEMPLE.FR ", firstname="CLAIRE")], AUJ)
    assert r.contacts[0]["email"] == "claire.martin@exemple.fr"
    assert {m["champ"] for m in r.modifications} == {"email", "firstname"}
    assert r.anomalies["1"] == []


def test_anomalies_et_kyc_expire():
    r = fiabiliser([contact(email="", date_kyc="2025-01-10")], AUJ)
    assert set(r.anomalies["1"]) == {"e-mail manquant", "KYC expiré"}
    assert score_qualite(r.anomalies) == 0


def test_doublon_detecte_mais_pas_fusionne():
    r = fiabiliser([contact(), contact(hs_object_id="2", firstname="CLAIRE", email="")], AUJ)
    assert r.doublons == [("1", "2", 1.0, "même téléphone")]
    assert len(r.contacts) == 2


def test_regles_de_relance():
    assert a_relancer(contact(date_kyc="2025-11-20"), AUJ) == "kyc"          # expire dans < 30 j
    assert a_relancer(contact(date_dernier_contact="2026-05-01"), AUJ) == "point_annuel"
    assert a_relancer(contact(), AUJ) is None
    assert a_relancer(contact(lifecyclestage="lead", date_kyc="2024-01-01"), AUJ) is None


def test_brouillons_personnalises(tmp_path):
    faits = preparer([contact(date_kyc="2025-06-03")], tmp_path, AUJ)
    texte = (tmp_path / "brouillons" / "1_kyc.md").read_text(encoding="utf-8")
    assert faits[0]["motif"] == "kyc"
    assert "Bonjour Claire" in texte and "3 juin 2025" in texte and "Nadia B." in texte


def test_reporting_et_message_slack():
    md, slack = construire([{**contact(), "anomalies": ""}], [{"conseiller": "Nadia B."}], 0)
    assert "| Clients | 1 |" in md
    assert slack["blocks"][0]["type"] == "header"


@pytest.mark.parametrize("fichier", sorted((RACINE / "n8n").glob("*.json")), ids=lambda p: p.stem)
def test_workflows_n8n_valides(fichier):
    wf = json.loads(fichier.read_text(encoding="utf-8"))
    noms = {n["name"] for n in wf["nodes"]}
    assert wf["active"] is False                       # importés désactivés : activation manuelle
    for source, sorties in wf["connections"].items():  # chaque connexion relie des nœuds existants
        assert source in noms
        assert all(c["node"] in noms for groupe in sorties["main"] for c in groupe)
    relies = set(wf["connections"]) | {c["node"] for s in wf["connections"].values() for g in s["main"] for c in g}
    assert relies == noms                              # aucun nœud orphelin
    assert all(n["type"].startswith("n8n-nodes-base.") for n in wf["nodes"])
    assert "REMPLACER" in fichier.read_text() and "sk-" not in fichier.read_text()  # pas de secret commité
