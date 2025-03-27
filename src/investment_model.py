import json
import pandas as pd

class InvestmentModel:
    def __init__(self, risk_profile="balanced"):
        """Initialize the investment agent with a risk profile."""
        self.risk_profile = risk_profile.lower()
        self.allocation = self.get_allocation()

    def get_allocation(self):
        """Defines the percentage allocation for each risk category based on the chosen risk profile."""
        risk_allocations = {
            "risk averse": {"high": 0.0, "medium": 0.3, "low": 0.7},
            "balanced": {"high": 0.1, "medium": 0.4, "low": 0.5},
            "aggressive": {"high": 0.3, "medium": 0.4, "low": 0.3},
        }
        return risk_allocations.get(self.risk_profile, risk_allocations["balanced"])

    def prioritize_assets(self, df):
        """Sorts assets by risk level and highest APY within each level."""
        risk_priority = {"low": 0, "medium": 1, "high": 2}
        df["risk_priority"] = df["risk_rating"].map(risk_priority)
        return df.sort_values(by=["risk_priority", "net_apy"], ascending=[True, False])

    def allocate_assets(self, data, user_assets):
        """
        Allocates 100% of each asset according to the risk profile, ensuring:
        1. All funds go to the highest APY pool in the allowed risk category.
        2. Medium-risk pools are skipped if a better low-risk pool exists.
        3. High-risk pools are skipped if a better medium-risk pool exists.
        4. Duplicates are merged into a single entry per pool.
        """
        df = pd.DataFrame(data)
        df = self.prioritize_assets(df)

        investment_plan = {}
        risk_groups = df.groupby("risk_rating")

        for asset, balance in user_assets.items():
            asset_allocations = {}  # Dictionary to store unique allocations per pool

            # Get the best pool for each risk category
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

            for risk, percentage in self.allocation.items():
                if percentage > 0 and risk in risk_groups.groups:
                    risk_assets = risk_groups.get_group(risk)
                    
                    # Find the best pool (highest APY) for this asset in the risk category
                    best_pool = risk_assets[risk_assets["asset"] == asset].nlargest(1, "net_apy")

                    if not best_pool.empty:
                        best_pool = best_pool.iloc[0]

                        # **Step 1: Check if a medium-risk pool has lower APY than a low-risk pool**
                        if (
                            risk == "medium"
                            and best_low_risk_pool is not None
                            and best_pool["net_apy"] < best_low_risk_pool["net_apy"]
                        ):
                            print(
                                f"Skipping {best_pool['pool_name']} (Medium Risk, {best_pool['net_apy']}%) "
                                f"in favor of {best_low_risk_pool['pool_name']} (Low Risk, {best_low_risk_pool['net_apy']}%)"
                            )
                            best_pool = best_low_risk_pool  # Replace with better low-risk option

                        # **Step 2: Check if a high-risk pool has lower APY than a medium-risk pool**
                        if (
                            risk == "high"
                            and best_medium_risk_pool is not None
                            and best_pool["net_apy"] < best_medium_risk_pool["net_apy"]
                        ):
                            print(
                                f"Skipping {best_pool['pool_name']} (High Risk, {best_pool['net_apy']}%) "
                                f"in favor of {best_medium_risk_pool['pool_name']} (Medium Risk, {best_medium_risk_pool['net_apy']}%)"
                            )
                            best_pool = best_medium_risk_pool  # Replace with better medium-risk option

                            # **Step 3: After replacing high-risk with medium-risk, check again if this new medium-risk pool is better than the low-risk pool**
                            if (
                                best_low_risk_pool is not None
                                and best_pool["net_apy"] > best_low_risk_pool["net_apy"]
                            ):
                                print(
                                    f"Choosing {best_pool['pool_name']} (Medium Risk, {best_pool['net_apy']}%) "
                                    f"over {best_low_risk_pool['pool_name']} (Low Risk, {best_low_risk_pool['net_apy']}%)"
                                )
                                # Keep best_pool as it now provides a better return despite higher risk

                        allocated_amount = percentage * balance
                        allocated_percentage = percentage * 100

                        # **Merge duplicate pools**
                        if best_pool["pool_name"] in asset_allocations:
                            asset_allocations[best_pool["pool_name"]]["allocated_amount"] += allocated_amount
                            asset_allocations[best_pool["pool_name"]]["% allocation"] += allocated_percentage
                        else:
                            asset_allocations[best_pool["pool_name"]] = {
                                "pool": best_pool["pool_name"],
                                "allocated_amount": allocated_amount,
                                "% allocation": allocated_percentage,
                                "net_apy": best_pool["net_apy"],
                                "risk": best_pool["risk_rating"]
                            }

            if asset_allocations:
                investment_plan[asset] = list(asset_allocations.values())  # Convert dict to list

        return investment_plan

# Load investment options from a JSON file
def load_investment_options(file_path):
    """Loads investment options from a JSON file."""
    with open(file_path, "r") as file:
        return json.load(file)

# Example user assets
user_assets = {
    "USDC": 1000,
    "ETH": 10,
    "STRK": 10000
}

# Load data and allocate assets
investment_data = load_investment_options("src/data/investment_options.json")  # Load JSON file

modeli = InvestmentModel(risk_profile="risk averse")  # Example: Balanced Strategy
investment_plan = modeli.allocate_assets(investment_data, user_assets)  # Allocate funds

# Print the structured investment plan
print(json.dumps(investment_plan, indent=4))
