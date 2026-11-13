"""Versioned reviewed check inventories; ordinary engine outcomes stay unchanged."""

from typing import Any


def treasury_pack_manifest() -> dict[str, Any]:
    """Return the version-1 cash/funding pack's applicability and required checks.

    The returned document is detached on every call. Consumers decide completeness
    using required checks and their own severity threshold; this adds no run status
    and does not infer business limits, scope, currency conversion or legal terms.
    """
    return {
        "schema_version": 1,
        "pack_id": "treasury.cash-funding",
        "version": 1,
        "policy_schema_version": 1,
        "datasets": {
            "cash": {
                "template": "treasury-cash-forecast",
                "required_rules": [
                    "data.required_fields",
                    "data.no_duplicates",
                    "arithmetic.non_negative",
                    "treasury.forecast_coverage",
                    "accounting.cash_reconciles",
                    "treasury.cash_continuity",
                    "treasury.minimum_cash_buffer",
                ],
            },
            "facility": {
                "template": "treasury-facility-schedule",
                "required_rules": [
                    "data.required_fields",
                    "data.no_duplicates",
                    "treasury.forecast_coverage",
                    "treasury.facility_capacity",
                ],
            },
        },
        "optional_rules": [],
        "assumptions": [
            "Weekly calendar periods; explicit independently supplied scope, vintage and currency.",
            (
                "Amounts in currency major units; positive payment/repayment "
                "magnitudes; no FX or netting."
            ),
            (
                "Closing cash includes restricted funds; minimum and effective "
                "commitment are caller-owned."
            ),
            (
                "Prepare total_inflows = receipts + financing_inflows and "
                "total_outflows = payments + financing_outflows explicitly."
            ),
            (
                "Required checks must be present and evaluated; skipped/error/absent "
                "checks mean incomplete coverage."
            ),
        ],
        "limitations": [
            (
                "No forecast generation, legal eligibility, borrowing-base or "
                "intraperiod capacity claim."
            ),
            (
                "Cross-file draw/repayment linkage and first-opening actual tie-out "
                "are consumer mapping responsibilities."
            ),
            (
                "Starter expected scope and dates are synthetic examples and must be "
                "replaced before use."
            ),
        ],
    }


def policy_packs() -> tuple[dict[str, Any], ...]:
    """Return detached, versioned built-in pack manifests in stable order."""
    return (treasury_pack_manifest(),)
