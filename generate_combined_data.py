import pandas as pd
import numpy as np
import os

def main():
    print("Loading original datasets...")
    # Paths to files
    demand_path = "demand_forecasting.csv"
    inventory_path = "inventory_monitoring.csv"
    pricing_path = "pricing_optimization.csv"
    
    if not (os.path.exists(demand_path) and os.path.exists(inventory_path) and os.path.exists(pricing_path)):
        print("Error: One or more source CSV files are missing in the directory.")
        return
        
    df_demand = pd.read_csv(demand_path)
    df_inv = pd.read_csv(inventory_path)
    df_price = pd.read_csv(pricing_path)
    
    # -------------------------------------------------------------
    # 1. Create Combined Transactional Dataset (Merged on Product ID)
    # -------------------------------------------------------------
    print("Merging datasets on Product ID...")
    # Merge demand and inventory
    merged_df = pd.merge(df_demand, df_inv, on="Product ID", suffixes=("_demand", "_inventory"))
    # Merge with pricing
    merged_df = pd.merge(merged_df, df_price, on="Product ID")
    
    # Clean up column names for readability
    rename_dict = {
        "Store ID_demand": "Demand Store ID",
        "Store ID_inventory": "Inventory Store ID",
        "Store ID": "Pricing Store ID",
        "Price_x": "Demand Price",
        "Price_y": "Pricing Price",
    }
    merged_df = merged_df.rename(columns=rename_dict)
    
    # Save the combined transactional dataset
    combined_transactional_path = "combined_transactional_dataset.csv"
    merged_df.to_csv(combined_transactional_path, index=False)
    print(f"Combined Transactional Dataset created: {combined_transactional_path} ({merged_df.shape[0]} rows, {merged_df.shape[1]} columns)")
    
    # -------------------------------------------------------------
    # 2. Create Product-Level Master Dataset (Summarized Statistics)
    # -------------------------------------------------------------
    print("Creating Product-Level Master Dataset...")
    
    # Group by Product ID and calculate aggregates
    # Demand stats
    demand_stats = df_demand.groupby("Product ID").agg(
        Mean_Daily_Demand=("Sales Quantity", "mean"),
        Demand_Std_Dev=("Sales Quantity", lambda x: np.std(x) if len(x) > 1 else 10.0),
        Total_Sales_Records=("Sales Quantity", "count")
    ).reset_index()
    
    # Fill standard deviation if it's 0 or NaN
    demand_stats["Demand_Std_Dev"] = demand_stats["Demand_Std_Dev"].replace(0, 10.0).fillna(10.0)
    
    # Inventory stats
    inv_stats = df_inv.groupby("Product ID").agg(
        Mean_Supplier_Lead_Time=("Supplier Lead Time (days)", "mean"),
        Lead_Time_Std_Dev=("Supplier Lead Time (days)", lambda x: np.std(x) if len(x) > 1 else 1.5),
        Current_Reorder_Point=("Reorder Point", "mean"),
        Current_Stock_Levels=("Stock Levels", "mean"),
        Warehouse_Capacity=("Warehouse Capacity", "mean")
    ).reset_index()
    
    inv_stats["Lead_Time_Std_Dev"] = inv_stats["Lead_Time_Std_Dev"].replace(0, 1.5).fillna(1.5)
    
    # Pricing stats
    price_stats = df_price.groupby("Product ID").agg(
        Mean_Price=("Price", "mean"),
        Mean_Storage_Cost=("Storage Cost", "mean"),
        Elasticity_Index=("Elasticity Index", "mean")
    ).reset_index()
    
    # Merge summaries
    summary_df = pd.merge(demand_stats, inv_stats, on="Product ID", how="inner")
    summary_df = pd.merge(summary_df, price_stats, on="Product ID", how="inner")
    
    # Add calculated columns for Stochastic Optimization
    summary_df["Shortage_Penalty"] = summary_df["Mean_Price"] * 1.5
    
    # Round float values for presentation
    float_cols = [
        "Mean_Daily_Demand", "Demand_Std_Dev", 
        "Mean_Supplier_Lead_Time", "Lead_Time_Std_Dev", 
        "Current_Reorder_Point", "Current_Stock_Levels", 
        "Warehouse_Capacity", "Mean_Price", 
        "Mean_Storage_Cost", "Elasticity_Index", "Shortage_Penalty"
    ]
    summary_df[float_cols] = summary_df[float_cols].round(2)
    
    # Save the product summary dataset
    product_summary_path = "product_summary_dataset.csv"
    summary_df.to_csv(product_summary_path, index=False)
    print(f"Product-Level Master Dataset created: {product_summary_path} ({summary_df.shape[0]} rows, {summary_df.shape[1]} columns)")

if __name__ == "__main__":
    main()
