import pytest

from finassert.adapters import ColumnMapping, GroupKey


def test_column_mapping_resolves_semantics_and_preserves_group_order() -> None:
    source = {"opening_cash": "cash_open", "closing_cash": "cash_close"}
    mapping = ColumnMapping(
        source,
        group_keys=(
            GroupKey("portfolio", "portfolio_id"),
            GroupKey("currency", "currency_code"),
        ),
        row_key="record_id",
    )
    source["opening_cash"] = "mutated_after_construction"

    assert mapping.resolve("opening_cash") == "cash_open"
    assert mapping.required_columns("closing_cash", "opening_cash") == (
        "cash_close",
        "cash_open",
    )
    assert mapping.grouping_columns == ("portfolio_id", "currency_code")
    assert mapping.row_key == "record_id"


def test_column_mapping_is_immutable() -> None:
    mapping = ColumnMapping({"value": "market_value"})

    with pytest.raises(TypeError):
        mapping.columns["value"] = "replacement"  # type: ignore[index]


@pytest.mark.parametrize(
    ("mapping", "message"),
    [
        ({}, "at least one"),
        ({"": "value"}, "semantic"),
        ({"value": ""}, "physical"),
    ],
)
def test_column_mapping_rejects_invalid_columns(mapping: dict[str, str], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        ColumnMapping(mapping)


def test_column_mapping_rejects_duplicate_group_semantics() -> None:
    with pytest.raises(ValueError, match="names must be unique"):
        ColumnMapping(
            {"value": "value"},
            group_keys=(GroupKey("portfolio", "book"), GroupKey("portfolio", "account")),
        )


def test_missing_semantic_has_configuration_context() -> None:
    mapping = ColumnMapping({"value": "market_value"})

    with pytest.raises(KeyError, match="opening_cash"):
        mapping.resolve("opening_cash")
