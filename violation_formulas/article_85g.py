"""Article 8.5.G violation detection and remedy calculations.

This module handles violations that occur when OTDL carriers are not maximized
while non-OTDL carriers are working overtime.
"""

import pandas as pd

from utils import set_display


def detect_85g_violations(data, date_maximized_status=None):
    """Detect Article 8.5.G violations for OTDL carriers not maximized.

    Args:
        data (pd.DataFrame): Carrier work hour data containing:
            - carrier_name: Name of the carrier
            - list_status: WAL/NL/OTDL status
            - total_hours: Total hours worked
            - code: Route assignment code
            - date: Date of potential violation
        date_maximized_status (dict, optional): Date-keyed dict of OTDL maximization status

    Returns:
        pd.DataFrame: Detected violations with calculated remedies. Contains ALL carriers,
            with non-OTDL carriers marked as "No Violation (Non OTDL)"

    Note:
        Violation occurs when:
        - OTDL carrier is not maximized to their hour limit
        - Non-OTDL carrier worked overtime that day
        - Not auto-excused (sick, NS protect, holiday, guaranteed, annual)
        - Not manually excused in maximization status
        - Not a Sunday
    """

    # First prepare the basic data
    result_df = data.copy()
    result_df["list_status"] = result_df["list_status"].str.strip().str.lower()

    # Convert numeric columns for all carriers
    result_df["total_hours"] = pd.to_numeric(
        result_df["total"], errors="coerce"
    ).fillna(0)
    result_df["hour_limit"] = pd.to_numeric(
        result_df["hour_limit"], errors="coerce"
    ).fillna(12.00)

    # Add display indicators for excusal checking
    result_df["display_indicator"] = result_df.apply(set_display, axis=1)

    # Convert dates to datetime for vectorized operations
    result_df["date_dt"] = pd.to_datetime(result_df["rings_date"])
    result_df["day_of_week"] = result_df["date_dt"].dt.strftime("%A")

    # Vectorized checks for auto-excusal indicators
    auto_excusal_indicators = [
        "(sick)",
        "(NS protect)",
        "(holiday)",
        "(guaranteed)",
        "(annual)",
    ]
    result_df["is_auto_excused"] = result_df["display_indicator"].apply(
        lambda x: any(indicator in str(x) for indicator in auto_excusal_indicators)
    )
    result_df["is_sunday"] = result_df["day_of_week"].astype(str) == "Sunday"

    # Create maximized status DataFrame for vectorized lookup
    max_status_df = pd.DataFrame()
    if date_maximized_status:
        max_status_records = []
        for date_str, status in date_maximized_status.items():
            if isinstance(status, dict):
                is_maximized = status.get("is_maximized", False)
                excused_carriers = {
                    str(c).strip().lower() for c in status.get("excused_carriers", [])
                }
                carrier_excusals = {
                    str(k).strip().lower(): v
                    for k, v in status.items()
                    if k not in ["is_maximized", "excused_carriers"]
                }
                max_status_records.append(
                    {
                        "date": pd.to_datetime(date_str),
                        "is_maximized": is_maximized,
                        "excused_carriers": excused_carriers,
                        "carrier_excusals": carrier_excusals,
                    }
                )
            else:
                max_status_records.append(
                    {
                        "date": pd.to_datetime(date_str),
                        "is_maximized": bool(status),
                        "excused_carriers": set(),
                        "carrier_excusals": {},
                    }
                )
        max_status_df = pd.DataFrame(max_status_records)

    # Merge maximized status with result_df
    if not max_status_df.empty:
        result_df = pd.merge(
            result_df, max_status_df, left_on="date_dt", right_on="date", how="left"
        )
    else:
        result_df["is_maximized"] = False
        result_df["excused_carriers"] = None
        result_df["carrier_excusals"] = None

    # Vectorized check for manually excused carriers
    def check_manual_excusal(row):
        if pd.isna(row["excused_carriers"]) and pd.isna(row["carrier_excusals"]):
            return False
        carrier_str = str(row["carrier_name"]).strip().lower()
        excused_carriers = (
            row["excused_carriers"]
            if isinstance(row["excused_carriers"], set)
            else set()
        )
        carrier_excusals = (
            row["carrier_excusals"] if isinstance(row["carrier_excusals"], dict) else {}
        )

        return carrier_str in excused_carriers or carrier_excusals.get(
            carrier_str, False
        )

    result_df["is_manually_excused"] = result_df.apply(check_manual_excusal, axis=1)

    # Process each date group separately to match original implementation
    final_results = []
    for date, day_data in result_df.groupby("date_dt"):
        date_str = date.strftime("%Y-%m-%d")
        is_maximized = day_data["is_maximized"].iloc[0]

        if is_maximized:
            # Handle maximized case
            for _, carrier_data in day_data.iterrows():
                violation_type = (
                    "No Violation (Auto Excused)"
                    if carrier_data["is_auto_excused"] or carrier_data["is_sunday"]
                    else "No Violation (Manually Excused)"
                    if carrier_data["is_manually_excused"]
                    else "No Violation (Maximized)"
                    if carrier_data["total_hours"] >= carrier_data["hour_limit"]
                    else "No Violation"
                )

                final_results.append(
                    {
                        "carrier_name": carrier_data["carrier_name"],
                        "date": date_str,
                        "violation_type": violation_type,
                        "remedy_total": 0.0,
                        "total_hours": carrier_data["total_hours"],
                        "hour_limit": carrier_data["hour_limit"],
                        "list_status": carrier_data["list_status"],
                        "trigger_carrier": "",
                        "trigger_hours": 0,
                        "off_route_hours": 0,
                        "display_indicator": carrier_data["display_indicator"],
                    }
                )
            continue

        # Find WAL/NL carriers working overtime
        wal_nl_overtime = day_data[
            (day_data["list_status"].isin(["wal", "nl"]))
            & (day_data["total_hours"] > 8)
        ]

        if not wal_nl_overtime.empty:
            # Get trigger carrier info
            trigger_carrier = wal_nl_overtime.loc[
                wal_nl_overtime["total_hours"].idxmax()
            ]

            # Process OTDL carriers
            otdl_carriers = day_data[day_data["list_status"] == "otdl"]
            for _, otdl in otdl_carriers.iterrows():
                # Get display indicator
                display_indicators = str(otdl["display_indicator"]).strip()

                # Check for automatic excusal conditions
                is_auto_excused = any(
                    indicator in display_indicators
                    for indicator in auto_excusal_indicators
                )

                violation_type = (
                    "No Violation (Auto Excused)"
                    if is_auto_excused or otdl["is_sunday"]
                    else "No Violation (Manually Excused)"
                    if otdl["is_manually_excused"]
                    else "No Violation (Maximized)"
                    if otdl["total_hours"] >= otdl["hour_limit"]
                    else "8.5.G OTDL Not Maximized"
                )

                remedy_total = (
                    max(0, round(otdl["hour_limit"] - otdl["total_hours"], 2))
                    if violation_type == "8.5.G OTDL Not Maximized"
                    else 0.0
                )

                final_results.append(
                    {
                        "carrier_name": otdl["carrier_name"],
                        "date": date_str,
                        "violation_type": violation_type,
                        "remedy_total": remedy_total,
                        "total_hours": otdl["total_hours"],
                        "hour_limit": otdl["hour_limit"],
                        "list_status": "otdl",
                        "trigger_carrier": str(trigger_carrier["carrier_name"]),
                        "trigger_hours": float(trigger_carrier["total_hours"]),
                        "off_route_hours": float(
                            trigger_carrier.get("off_route_hours", 0)
                        ),
                        "display_indicator": otdl["display_indicator"],
                    }
                )

        # Add remaining carriers
        processed_carriers = {
            r["carrier_name"] for r in final_results if r["date"] == date_str
        }
        remaining_carriers = day_data[
            ~day_data["carrier_name"].isin(processed_carriers)
        ]

        for _, carrier_data in remaining_carriers.iterrows():
            # For non-OTDL carriers, always use "No Violation (Non OTDL)"
            violation_type = (
                "No Violation (Non OTDL)"
                if carrier_data["list_status"] != "otdl"
                else "No Violation (Auto Excused)"
                if carrier_data["is_auto_excused"] or carrier_data["is_sunday"]
                else "No Violation (Manually Excused)"
                if carrier_data["is_manually_excused"]
                else "No Violation (Maximized)"
                if carrier_data["total_hours"] >= carrier_data["hour_limit"]
                else "No Violation"
            )

            final_results.append(
                {
                    "carrier_name": carrier_data["carrier_name"],
                    "date": date_str,
                    "violation_type": violation_type,
                    "remedy_total": 0.0,
                    "total_hours": carrier_data["total_hours"],
                    "hour_limit": carrier_data["hour_limit"],
                    "list_status": carrier_data["list_status"],
                    "trigger_carrier": "",
                    "trigger_hours": 0,
                    "off_route_hours": 0,
                    "display_indicator": carrier_data["display_indicator"],
                }
            )

    return (
        pd.DataFrame(final_results)
        .sort_values("carrier_name", ascending=True)
        .reset_index(drop=True)
    )
