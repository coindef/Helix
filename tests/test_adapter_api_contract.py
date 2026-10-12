"""Do the optional-model adapters speak their upstream package's real API?

Each adapter is covered elsewhere by a fake module injected into ``sys.modules``. A fake
proves the output mapping, but it cannot catch an adapter that calls a signature the real
package does not have: the fake is written to match the adapter, so both can be wrong
together. These tests inject stubs shaped like the **documented upstream API** instead.

Sources for the shapes asserted here:
  inDelphi    github.com/maxwshen/inDelphi-model  — init_model(celltype=...),
              predict(seq, cutsite) -> (DataFrame, stats) with 'Frameshift frequency'
  BE-Hive     github.com/maxwshen/be_predict_efficiency — init_model(base_editor=,
              celltype=), predict(seq) -> (DataFrame, stats)
  PRIDICT     github.com/Schwank-lab/PRIDICT — a command-line script, no importable
              predict(spacer=, pbs=, rtt=)

``indelphi`` matches and works. ``behive`` and ``pridict`` do not: with their real
packages installed they raise mid-compile instead of predicting. The two xfail tests
below are the todo list — when an adapter is fixed, its test XPASSes and should be
converted into a positive assertion.
"""

import sys
import types

import pytest

pd = pytest.importorskip("pandas")


def _indelphi_stub():
    mod = types.ModuleType("inDelphi")
    mod.init_model = lambda celltype=None: None
    mod.predict = lambda seq, cutsite: (
        pd.DataFrame({"Category": ["del", "ins"], "Length": [3, 1],
                      "Predicted frequency": [40.0, 20.0]}),
        {"Frameshift frequency": 66.7},
    )
    return mod


def _behive_stub():
    """Real be_predict_efficiency: init_model(...) first, then predict(seq) -> tuple."""
    mod = types.ModuleType("be_predict_efficiency")
    mod.init_model = lambda base_editor=None, celltype=None: None
    mod.predict = lambda seq: (pd.DataFrame({"Predicted logit score": [0.3]}),
                               {"Predicted efficiency": 0.42})
    return mod


def test_indelphi_adapter_drives_the_real_api(monkeypatch):
    from helix.adapters.repair import InDelphiBackend

    monkeypatch.setitem(sys.modules, "inDelphi", _indelphi_stub())
    pred = InDelphiBackend(celltype="HEK293").predict("ACGT" * 20, 40)
    assert pred.frameshift_fraction == pytest.approx(0.667, abs=1e-3)
    assert [g.label for g in pred.genotypes] == ["3bp_deletion", "1bp_insertion"]


@pytest.mark.xfail(reason="BEHiveBackend calls predict(protospacer, editor)->dict; upstream "
                          "needs init_model(...) then predict(seq)->(df, stats). Selecting "
                          "'behive' with the real package installed raises mid-compile.",
                   strict=True)
def test_behive_adapter_drives_the_real_api(monkeypatch):
    from helix.adapters.base_edit_model import BEHiveBackend

    monkeypatch.setitem(sys.modules, "be_predict_efficiency", _behive_stub())
    pred = BEHiveBackend(celltype="mES").predict("ACGTACGTACGTACGTACGT", "CBE", [5, 6])
    assert 0.0 <= pred.efficiency <= 1.0


@pytest.mark.xfail(reason="PridictBackend calls predict(spacer=, pbs=, rtt=); upstream PRIDICT "
                          "ships a CLI script with no such import. Selecting 'pridict' with it "
                          "installed raises mid-compile.",
                   strict=True)
def test_pridict_adapter_drives_the_real_api(monkeypatch):
    from helix.adapters.prime_edit_model import PridictBackend

    monkeypatch.setitem(sys.modules, "pridict", types.ModuleType("pridict"))
    pred = PridictBackend().predict("ACGTACGTACGTACGTACGT", "GGCATC", "TTAGCA", "A>G @ 1")
    assert 0.0 <= pred.efficiency <= 1.0


def test_unavailable_models_still_fail_cleanly_when_absent(monkeypatch):
    """Whatever happens above, a *missing* package must give an actionable error and never
    a silent downgrade to a heuristic."""
    from helix.adapters.base_edit_model import BEHiveBackend, BEHiveNotConfigured
    from helix.adapters.prime_edit_model import PridictBackend, PridictNotConfigured
    from helix.adapters.repair import InDelphiBackend, InDelphiNotConfigured

    for name in ("inDelphi", "be_predict_efficiency", "pridict"):
        monkeypatch.setitem(sys.modules, name, None)  # force ImportError on import

    with pytest.raises(InDelphiNotConfigured):
        InDelphiBackend().predict("ACGT" * 20, 40)
    with pytest.raises(BEHiveNotConfigured):
        BEHiveBackend().predict("ACGT" * 5, "CBE", [5])
    with pytest.raises(PridictNotConfigured):
        PridictBackend().predict("ACGT", "pbs", "rtt", "A>G @ 1")
