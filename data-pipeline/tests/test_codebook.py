"""Tests that report/codebook.qmd documents SPF cleaned tables."""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

EXPECTED_TABLES = frozenset(
    {
        "forecast_individual",
        "forecaster_survey",
        "adjusted_cpi10",
        "inflation_news",
        "reputation_measure",
    }
)


def extract_tables_config():
    """Extract TABLES from the first ```{python} block in codebook.qmd."""
    codebook_path = Path(__file__).parent.parent / "report" / "codebook.qmd"
    if not codebook_path.exists():
        return None
    content = codebook_path.read_text(encoding="utf-8")
    python_blocks = re.findall(r"```\{python\}(.*?)```", content, re.DOTALL)
    if not python_blocks:
        return None
    code = python_blocks[0]
    code = re.sub(r"#\|.*\n", "", code)
    local_vars: dict = {}
    exec(
        code,
        {"pd": pd, "plt": plt, "Path": Path},
        local_vars,
    )
    return local_vars.get("TABLES")


def test_codebook_exists():
    """Codebook file should exist."""
    codebook_path = Path(__file__).parent.parent / "report" / "codebook.qmd"
    assert codebook_path.exists(), "Expected report/codebook.qmd"


def test_tables_config_exists():
    """TABLES configuration should be defined."""
    tables = extract_tables_config()
    assert tables is not None, "Could not load TABLES from codebook.qmd"


def test_expected_spf_tables_present():
    """All core SPF cleaned tables should appear in TABLES."""
    tables = extract_tables_config()
    assert tables is not None
    missing = EXPECTED_TABLES - frozenset(tables.keys())
    assert not missing, f"Missing TABLES entries: {sorted(missing)}"


def test_all_tables_have_descriptions():
    """Each table should have a non-TODO description."""
    tables = extract_tables_config()
    assert tables is not None
    for name, config in tables.items():
        desc = config.get("description", "")
        assert "TODO" not in desc, f"Table {name!r} description still has TODO"
        assert len(desc) > 10, f"Table {name!r} description too short: {desc!r}"


def test_all_tables_have_file_and_primary_key():
    """Each table should name an output file and a primary key."""
    tables = extract_tables_config()
    assert tables is not None
    for name, config in tables.items():
        file_val = config.get("file", "")
        assert file_val, f"Table {name!r} missing non-empty file"
        pk = config.get("primary_key", [])
        assert isinstance(pk, list) and len(pk) > 0, (
            f"Table {name!r} needs primary_key as non-empty list"
        )


def test_all_tables_have_variables():
    """Each table should document variables with type, unit, desc."""
    tables = extract_tables_config()
    assert tables is not None
    required_fields = ("type", "unit", "desc")
    for table_name, config in tables.items():
        variables = config.get("variables", {})
        assert variables, f"Table {table_name!r} has no variables"
        for var_name, var_config in variables.items():
            for field in required_fields:
                assert field in var_config, (
                    f"Table {table_name!r} variable {var_name!r} missing {field!r}"
                )
                value = var_config[field]
                assert value and "TODO" not in str(value), (
                    f"Table {table_name!r} variable {var_name!r} field {field!r} "
                    f"incomplete: {value!r}"
                )


def test_float_economic_columns_have_meaningful_units():
    """Float variables that are not dimensionless should not use '-' as unit."""
    tables = extract_tables_config()
    assert tables is not None
    checks = [
        ("adjusted_cpi10", "adjusted_cpi10"),
        ("inflation_news", "inflation_news"),
    ]
    for table_name, var_name in checks:
        var_config = tables[table_name]["variables"][var_name]
        unit = var_config.get("unit", "")
        assert unit and unit != "-", (
            f"{table_name}.{var_name} should document a concrete unit, got {unit!r}"
        )
