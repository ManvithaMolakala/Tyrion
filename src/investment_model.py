import json
import pandas as pd


def get_allocation(risk_profile):
    """Returns risk allocation percentages based on the chosen risk profile."""
    risk_allocations = {
        "risk averse": {"high": 0.0, "medium": 0.3, "low": 0.7},
        "balanced": {"high": 0.1, "medium": 0.4, "low": 0.5},
        "aggressive": {"high": 0.3, "medium": 0.4, "low": 0.3},
    }
    return risk_allocations.get(risk_profile.lower(), risk_allocations["balanced"])


def prioritize_assets(df):
    """Sorts assets by risk level and highest APY within each level."""
    risk_priority = {"low": 0, "medium": 1, "high": 2}
    df["risk_priority"] = df["risk_rating"].map(risk_priority)
    return df.sort_values(by=["risk_priority", "net_apy"], ascending=[True, False])


def adjust_allocation_percentages(asset_allocations, balance):
    """Ensures the total allocated percentage sums to 100% by adjusting the highest APY pool."""
    total_percentage = sum(pool["% allocation"] for pool in asset_allocations)

    if total_percentage != 100.0:
        difference = 100.0 - total_percentage
        best_pool = max(asset_allocations, key=lambda p: p["net_apy"])
        best_pool["% allocation"] += difference
        best_pool["allocated_amount"] += (difference / 100) * balance

    return asset_allocations


def allocate_assets(data, user_assets, risk_profile="balanced"):
    """
    Allocates 100% of each asset according to the risk profile, ensuring:
    ✅ Full allocation of all funds.
    ✅ Prioritization of highest-APY pools.
    ✅ Avoidance of redundant medium/high-risk pools if a better lower-risk option exists.
    ✅ Handling of rounding errors.
    """
    df = pd.DataFrame(data)
    df = prioritize_assets(df)
    allocation = get_allocation(risk_profile)
    investment_plan = {}
    risk_groups = df.groupby("risk_rating")

    for asset, balance in user_assets.items():
        asset_allocations = {}

        # Identify the best low & medium-risk pools for comparison
        best_low_risk_pool = None
        best_medium_risk_pool = None

        if "low" in risk_groups.groups:
            low_risk_assets = risk_groups.get_group("low")
            best_low_risk_pool = low_risk_assets[low_risk_assets["asset"] == asset].nlargest(1, "net_apy")

            if not best_low_risk_pool.empty:
                best_low_risk_pool = best_low_risk_pool.iloc[0]

        if "medium" in risk_groups.groups:
            medium_risk_assets = risk_groups.get_group("medium")
            best_medium_risk_pool = medium_risk_assets[medium_risk_assets["asset"] == asset].nlargest(1, "net_apy")

            if not best_medium_risk_pool.empty:
                best_medium_risk_pool = best_medium_risk_pool.iloc[0]

        total_allocated = 0  # Track total allocated amount for full distribution

        for risk, percentage in allocation.items():
            if percentage > 0 and risk in risk_groups.groups:
                risk_assets = risk_groups.get_group(risk)
                best_pool = risk_assets[risk_assets["asset"] == asset].nlargest(1, "net_apy")

                if not best_pool.empty:
                    best_pool = best_pool.iloc[0]

                    # **Skip medium risk if a better low-risk option exists**
                    if (
                        risk == "medium"
                        and best_low_risk_pool is not None
                        and not best_low_risk_pool.empty
                        and best_pool["net_apy"] < best_low_risk_pool["net_apy"]
                    ):
                        print(
                            f"Skipping {best_pool['pool_name']} (Medium Risk, {best_pool['net_apy']}%) "
                            f"in favor of {best_low_risk_pool['pool_name']} (Low Risk, {best_low_risk_pool['net_apy']}%)"
                        )
                        best_pool = best_low_risk_pool  # Replace with better low-risk option

                    # **Skip high risk if a better medium-risk option exists**
                    if (
                        risk == "high"
                        and best_medium_risk_pool is not None
                        and not best_medium_risk_pool.empty
                        and best_pool["net_apy"] < best_medium_risk_pool["net_apy"]
                    ):
                        print(
                            f"Skipping {best_pool['pool_name']} (High Risk, {best_pool['net_apy']}%) "
                            f"in favor of {best_medium_risk_pool['pool_name']} (Medium Risk, {best_medium_risk_pool['net_apy']}%)"
                        )
                        best_pool = best_medium_risk_pool  # Replace with better medium-risk option

                    allocated_amount = percentage * balance
                    total_allocated += allocated_amount  # Track total allocation

                    # **Merge duplicate pools**
                    if best_pool["pool_name"] in asset_allocations:
                        asset_allocations[best_pool["pool_name"]]["allocated_amount"] += allocated_amount
                        asset_allocations[best_pool["pool_name"]]["% allocation"] += percentage * 100
                    else:
                        asset_allocations[best_pool["pool_name"]] = {
                            "pool": best_pool["pool_name"],
                            "allocated_amount": allocated_amount,
                            "% allocation": percentage * 100,
                            "net_apy": best_pool["net_apy"],
                            "risk": best_pool["risk_rating"]
                        }

        # **Handle any unallocated funds due to rounding**
        rounding_error = balance - total_allocated
        if rounding_error > 0 and asset_allocations:
            best_pool = max(asset_allocations.values(), key=lambda p: p["net_apy"])
            best_pool["allocated_amount"] += rounding_error
            best_pool["% allocation"] += (rounding_error / balance) * 100

        if asset_allocations:
            investment_plan[asset] = adjust_allocation_percentages(list(asset_allocations.values()), balance)

    return investment_plan


# **Load investment options from a JSON file**
def load_investment_options(file_path):
    """Loads investment options from a JSON file."""
    with open(file_path, "r") as file:
        return json.load(file)


# # **Example User Assets**
# user_assets = {
#     "USDC": 1000,
#     "ETH": 10,
#     "STRK": 10000
# }

# # **Load Data and Allocate Assets**
# investment_data = load_investment_options("src/data/investment_options.json")  # Load JSON file

# investment_plan = allocate_assets(investment_data, user_assets, risk_profile="aggressive")  # Allocate funds

# # **Print Structured Investment Plan**
# print(json.dumps(investment_plan, indent=4))
