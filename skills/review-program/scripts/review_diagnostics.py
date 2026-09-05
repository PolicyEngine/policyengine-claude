"""Batch model-review diagnostics with explicit periods and named in-memory controls.

Import from a diagnostic script under RUN_ROOT using the available model interpreter.
This helper records calculations, not policy assertions or confirmed findings.
"""

from __future__ import annotations

import copy
import json
import re
import time
import traceback
from pathlib import Path


def normalize_inputs(values, variable, default_period: str) -> dict:
    """Require explicit intent for annual inputs to monthly variables; never guess units."""
    unit = str(variable.definition_period).lower()
    if not isinstance(values, dict):
        values = {"ETERNITY" if unit == "eternity" else default_period: values}
    result = {}
    for period, value in values.items():
        period = str(period)
        period_unit = (
            "eternity"
            if period.upper() == "ETERNITY"
            else "year"
            if re.fullmatch(r"\d{4}", period)
            else "month"
            if re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", period)
            else None
        )
        if period_unit is None:
            raise ValueError(
                f"Unsupported input period {period!r}; use YYYY, YYYY-MM or ETERNITY"
            )
        expanded = {}
        if unit == period_unit:
            if isinstance(value, dict):
                raise ValueError(
                    "Expansion operators apply only to a year of monthly inputs"
                )
            expanded["ETERNITY" if unit == "eternity" else period] = value
        elif unit == "month" and period_unit == "year":
            if not isinstance(value, dict) or len(value) != 1:
                raise ValueError(
                    "Monthly variable needs explicit months, annual_total, or monthly_value"
                )
            if "annual_total" in value:
                amount = value["annual_total"]
                if variable.value_type is not float or type(amount) not in (int, float):
                    raise ValueError(
                        "annual_total requires a float variable and numeric total"
                    )
                monthly = amount / 12
            elif "monthly_value" in value:
                monthly = value["monthly_value"]
            else:
                raise ValueError("Use annual_total or monthly_value")
            expanded = {f"{period}-{month:02}": monthly for month in range(1, 13)}
        else:
            raise ValueError(f"Input period {period} does not match {unit} variable")
        if result.keys() & expanded.keys():
            raise ValueError(
                "Overlapping input periods; supply one explicit monthly schedule"
            )
        result.update(expanded)
    return result


def normalize_situation(situation: dict, system, period: str) -> dict:
    normalized = copy.deepcopy(situation)
    entities = {entity.plural: entity for entity in system.entities}
    for plural, members in normalized.items():
        if plural not in entities:
            raise ValueError(f"Unknown entity group: {plural}")
        entity = entities[plural]
        role_names = {
            name
            for role in (getattr(entity, "roles", None) or [])
            for name in (role.key, role.plural)
            if name
        }
        for member in members.values():
            for name, values in member.items():
                if name in role_names:
                    continue
                if name not in system.variables:
                    raise ValueError(f"Unknown variable: {name}")
                variable = system.variables[name]
                if variable.entity.plural != plural:
                    raise ValueError(
                        f"{name} belongs to {variable.entity.plural}, not {plural}"
                    )
                try:
                    member[name] = normalize_inputs(values, variable, str(period))
                except ValueError as error:
                    raise ValueError(f"{name}: {error}") from error
    return normalized


def run_cases(
    model,
    cases: list[dict],
    *,
    snapshot: Path,
    output: Path,
    controls: dict | None = None,
) -> dict:
    """Use one imported model for a batch; controls map descriptive names to Reforms.

    Caller owns PYTHONPATH, bytecode/cache placement, and source-backed expectations.
    Inspect case statuses: a completed calculation is not a passing assertion.
    """
    started = time.time()
    imported = Path(model.__file__).resolve()
    if not imported.is_relative_to(snapshot.resolve()):
        raise ValueError(f"Model imported outside snapshot: {imported}")
    if output.resolve().is_relative_to(snapshot.resolve()):
        raise ValueError(
            "Write diagnostic artifacts under RUN_ROOT, outside the snapshot"
        )
    controls = controls or {}
    if "current" in controls:
        raise ValueError("'current' is reserved for the unchanged captured model")
    names = [case["name"] for case in cases]
    if len(names) != len(set(names)):
        raise ValueError("Diagnostic names must be unique")
    system = model.Simulation.default_tax_benefit_system_instance
    if system is None:
        system = model.CountryTaxBenefitSystem()
    result = {"import_path": str(imported), "started_epoch": started, "cases": []}
    for case in cases:
        begin = time.time()
        control = case.get("control", "current")
        record = {
            "name": case["name"],
            "control": control,
            "conditions": case.get("conditions", []),
            "raw_inputs": case["situation"],
            "outputs": {},
        }
        try:
            if control != "current" and control not in controls:
                raise ValueError(f"Unknown control: {control}")
            normalized = normalize_situation(
                case["situation"], system, str(case["period"])
            )
            record["normalized_inputs"] = normalized
            kwargs = {} if control == "current" else {"reform": controls[control]}
            simulation = model.Simulation(situation=normalized, **kwargs)
            for variable, period in case["outputs"].items():
                value = simulation.calculate(variable, str(period))
                if hasattr(value, "decode_to_str"):
                    value = value.decode_to_str()
                record["outputs"][variable] = {
                    "period": str(period),
                    "value": value.tolist(),
                }
            record["status"] = "CALCULATED"
        except Exception:
            record["status"] = "ERROR"
            record["error"] = traceback.format_exc()
        record["elapsed_seconds"] = time.time() - begin
        result["cases"].append(record)
    result.update(finished_epoch=time.time(), elapsed_seconds=time.time() - started)
    result["errors"] = sum(case["status"] == "ERROR" for case in result["cases"])
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result
