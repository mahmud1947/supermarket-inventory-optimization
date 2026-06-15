import os
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

def fit_best_distribution(data):
    """
    Fits Normal, Lognormal, Gamma, and Poisson distributions to the data.
    Uses the Kolmogorov-Smirnov test to evaluate goodness-of-fit.
    Returns the best-fitting distribution's name, parameters, and a summary dict of all fits.
    """
    results = {}
    
    # 1. Normal Distribution
    try:
        loc, scale = stats.norm.fit(data)
        stat, p_val = stats.kstest(data, 'norm', args=(loc, scale))
        results['normal'] = {'stat': stat, 'p_value': p_val, 'params': (loc, scale)}
    except Exception as e:
        print(f"Normal fit error: {e}")

    # 2. Lognormal Distribution
    try:
        # floc=0 forces the lower bound to 0, which is suitable for demands >= 0
        shape, loc, scale = stats.lognorm.fit(data, floc=0)
        stat, p_val = stats.kstest(data, 'lognorm', args=(shape, loc, scale))
        results['lognorm'] = {'stat': stat, 'p_value': p_val, 'params': (shape, loc, scale)}
    except Exception as e:
        print(f"Lognormal fit error: {e}")

    # 3. Gamma Distribution
    try:
        a, loc, scale = stats.gamma.fit(data, floc=0)
        stat, p_val = stats.kstest(data, 'gamma', args=(a, loc, scale))
        results['gamma'] = {'stat': stat, 'p_value': p_val, 'params': (a, loc, scale)}
    except Exception as e:
        print(f"Gamma fit error: {e}")

    # 4. Poisson Distribution (discrete)
    try:
        mu = np.mean(data)
        # Poisson is discrete, so we compare empirical CDF with theoretical Poisson CDF
        stat, p_val = stats.kstest(data, lambda x: stats.poisson.cdf(x, mu))
        results['poisson'] = {'stat': stat, 'p_value': p_val, 'params': (mu,)}
    except Exception as e:
        print(f"Poisson fit error: {e}")

    # Select the distribution with the lowest KS statistic (best fit)
    best_name = 'normal'  # Default fallback
    best_stat = float('inf')
    best_params = (np.mean(data), np.std(data))
    
    for name, res in results.items():
        if res['stat'] < best_stat:
            best_stat = res['stat']
            best_name = name
            best_params = res['params']
            
    return best_name, best_params, results


# Create visualizations folder
os.makedirs("visualizations", exist_ok=True)

# Load datasets
print("Loading supermarket datasets...")
df_demand = pd.read_csv("demand_forecasting.csv")
df_inv = pd.read_csv("inventory_monitoring.csv")
df_price = pd.read_csv("pricing_optimization.csv")

# Identify products with >= 4 demand records and matching inventory/pricing
demand_counts = df_demand['Product ID'].value_counts()
products_with_min_demand = demand_counts[demand_counts >= 4].index.tolist()
common_products = set(products_with_min_demand).intersection(set(df_inv['Product ID'].unique())).intersection(set(df_price['Product ID'].unique()))
common_products = sorted(list(common_products))
print(f"Total matching products for analysis: {len(common_products)}")

# Select three representative products for deep analysis
selected_pids = [7694, 1589, 6656]
print(f"Selected products for case studies: {selected_pids}")

results_summary = []

for pid in selected_pids:
    print(f"\n=================== Deep Analysis for Product ID: {pid} ===================")
    
    # 1. Extract local data
    p_demand = df_demand[df_demand['Product ID'] == pid]
    p_inv = df_inv[df_inv['Product ID'] == pid]
    p_price = df_price[df_price['Product ID'] == pid]
    
    # Calculate demand characteristics
    demand_values = p_demand['Sales Quantity'].values
    mu_D = np.mean(demand_values)
    sigma_D = np.std(demand_values) if len(demand_values) > 1 else 50.0
    if sigma_D == 0:
        sigma_D = 10.0
        
    # Fit the best distribution to demand values
    best_dist_name, best_dist_params, fit_results = fit_best_distribution(demand_values)
    print(f"KS Goodness-of-Fit Results:")
    for dist_name, res in fit_results.items():
        print(f"  - {dist_name.capitalize()}: KS Stat = {res['stat']:.4f}, p-value = {res['p_value']:.4f}")
    print(f"Best Fitting Demand Distribution: {best_dist_name.upper()}")

    # Lead time characteristics
    lt_values = p_inv['Supplier Lead Time (days)'].values
    mu_L = np.mean(lt_values)
    sigma_L = np.std(lt_values) if len(lt_values) > 1 else 2.0
    if sigma_L == 0:
        sigma_L = 1.0
        
    # Price and holding cost
    price = np.mean(p_price['Price'].values)
    h = np.mean(p_price['Storage Cost'].values) # daily holding cost per unit
    k_order = 100.0  # Ordering cost per order ($)
    c_short = 1.5 * price  # Shortage cost per unit ($) - lost sale penalty
    target_SL = 0.95
    Z = stats.norm.ppf(target_SL)
    
    # Baseline parameters from dataset
    baseline_rop = np.mean(p_inv['Reorder Point'].values)
    eoq = np.sqrt(2 * mu_D * k_order / h)
    baseline_q = np.mean(p_inv['Warehouse Capacity'].values) / 5.0
    if np.isnan(baseline_q) or baseline_q == 0:
        baseline_q = eoq
        
    print(f"Demand parameters: Mean={mu_D:.2f}, Std={sigma_D:.2f}")
    print(f"Lead time parameters: Mean={mu_L:.2f}, Std={sigma_L:.2f}")
    print(f"Price={price:.2f}, Daily Holding Cost={h:.2f}, Order Cost={k_order:.2f}, Shortage Penalty={c_short:.2f}")
    print(f"EOQ calculated: {eoq:.2f}, Baseline Q used: {baseline_q:.2f}, Baseline ROP: {baseline_rop:.2f}")

    # Analytical Calculations (stochastic DLT)
    mu_DLT = mu_L * mu_D
    sigma_DLT = np.sqrt(mu_L * (sigma_D**2) + (mu_D**2) * (sigma_L**2))
    ss_analytical = Z * sigma_DLT
    rop_analytical = mu_DLT + ss_analytical
    
    print(f"Analytical Safety Stock (SS): {ss_analytical:.2f}")
    print(f"Analytical Reorder Point (ROP): {rop_analytical:.2f}")

    # 3. Distribution Fitting Visualizations
    plt.figure(figsize=(8, 5))
    plt.hist(demand_values, bins=5, density=True, alpha=0.6, color='skyblue', label='Empirical Sales Quantity')
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    
    # Dynamic curve plotting
    if best_dist_name == 'normal':
        p = stats.norm.pdf(x, *best_dist_params)
        label_str = f'Fitted Normal ($N({best_dist_params[0]:.1f}, {best_dist_params[1]:.1f}^2)$)'
        plt.plot(x, p, 'r-', linewidth=2, label=label_str)
    elif best_dist_name == 'lognorm':
        p = stats.lognorm.pdf(x, *best_dist_params)
        label_str = f'Fitted Lognormal ($LN(s={best_dist_params[0]:.2f}, scale={best_dist_params[2]:.1f})$)'
        plt.plot(x, p, 'r-', linewidth=2, label=label_str)
    elif best_dist_name == 'gamma':
        p = stats.gamma.pdf(x, *best_dist_params)
        label_str = fr'Fitted Gamma ($\Gamma(a={best_dist_params[0]:.1f}, scale={best_dist_params[2]:.1f})$)'
        plt.plot(x, p, 'r-', linewidth=2, label=label_str)
    elif best_dist_name == 'poisson':
        x_int = np.arange(max(0, int(xmin)), int(xmax) + 1)
        p = stats.poisson.pmf(x_int, *best_dist_params)
        plt.stem(x_int, p, linefmt='r-', markerfmt='ro', basefmt=' ', label=fr'Fitted Poisson ($\lambda={best_dist_params[0]:.1f}$)')
        
    plt.title(f'Product {pid}: Historical Demand Distribution Fitting ({best_dist_name.capitalize()})')
    plt.xlabel('Daily Sales Quantity')
    plt.ylabel('Density')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(f'visualizations/demand_fit_{pid}.png')
    plt.close()

    # 4. Standard (Q, R) Monte Carlo Simulation Engine with Pipeline Inventory
    def run_simulation(rop_val, q_val, num_days=10000):
        np.random.seed(42)  # For reproducibility
        
        on_hand = q_val  # Start with on-hand inventory equal to Q
        orders_in_transit = []  # List of tuples: (arrival_day, quantity)
        
        total_holding_cost = 0
        total_ordering_cost = 0
        total_shortage_cost = 0
        
        demands_met = 0
        total_demand = 0
        days_stocked_out = 0
        
        inventory_history = []
        
        for day in range(num_days):
            # 1. Process arrivals
            arrivals = [q for arr_day, q in orders_in_transit if arr_day == day]
            on_hand += sum(arrivals)
            orders_in_transit = [(d, q) for d, q in orders_in_transit if d != day]
            
            # 2. Daily demand
            if best_dist_name == 'normal':
                daily_demand = stats.norm.rvs(*best_dist_params)
            elif best_dist_name == 'lognorm':
                daily_demand = stats.lognorm.rvs(*best_dist_params)
            elif best_dist_name == 'gamma':
                daily_demand = stats.gamma.rvs(*best_dist_params)
            elif best_dist_name == 'poisson':
                daily_demand = stats.poisson.rvs(*best_dist_params)
            else:
                daily_demand = np.random.normal(mu_D, sigma_D)
                
            daily_demand = max(0, int(round(daily_demand)))
            total_demand += daily_demand

            
            # 3. Fulfill demand (lost sales model)
            if on_hand >= daily_demand:
                on_hand -= daily_demand
                demands_met += daily_demand
            else:
                demands_met += on_hand
                shortage = daily_demand - on_hand
                total_shortage_cost += shortage * c_short
                on_hand = 0
                days_stocked_out += 1
            
            inventory_history.append(on_hand)
            total_holding_cost += on_hand * h
            
            # 4. Check inventory position and place orders
            on_order_qty = sum([q for _, q in orders_in_transit])
            inv_position = on_hand + on_order_qty
            
            if inv_position <= rop_val:
                # Place order
                lead_time = max(1, np.random.normal(mu_L, sigma_L))
                lead_time = int(round(lead_time))
                arrival_day = day + lead_time
                orders_in_transit.append((arrival_day, q_val))
                total_ordering_cost += k_order
        
        service_level = demands_met / total_demand if total_demand > 0 else 1.0
        total_cost = total_holding_cost + total_ordering_cost + total_shortage_cost
        
        # Annualize the total cost to remain consistent with a 365-day planning horizon
        annualized_cost = total_cost * (365.0 / num_days)
        
        return service_level, annualized_cost, inventory_history

    # Run baseline simulation
    sl_base, tc_base, hist_base = run_simulation(baseline_rop, baseline_q)
    print(f"Baseline Simulation: Service Level = {sl_base:.2%}, Total Cost = ${tc_base:,.2f}")

    # Run analytical simulation
    # We use baseline_q as analytical Q (or EOQ if baseline is not available)
    analytical_q = max(eoq, baseline_q)
    sl_opt, tc_opt, hist_opt = run_simulation(rop_analytical, analytical_q)
    print(f"Optimized Simulation: Service Level = {sl_opt:.2%}, Total Cost = ${tc_opt:,.2f}")

    # 5. Save Inventory Trajectory Visualizations
    plt.figure(figsize=(12, 5))
    plt.plot(hist_base[:180], 'r--', alpha=0.7, label=f'Baseline Policy (Service Level={sl_base:.1%})')
    plt.plot(hist_opt[:180], 'b-', label=f'Optimized Stochastic Policy (Service Level={sl_opt:.1%})')
    plt.axhline(y=baseline_rop, color='r', linestyle=':', label=f'Baseline ROP ({int(baseline_rop)})')
    plt.axhline(y=rop_analytical, color='b', linestyle=':', label=f'Optimized ROP ({int(rop_analytical)})')
    plt.title(f'Product {pid}: 180-Day On-Hand Inventory Trajectory Comparison')
    plt.xlabel('Simulated Day')
    plt.ylabel('On-Hand Inventory Level (Units)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(f'visualizations/inventory_trajectory_{pid}.png')
    plt.close()

    # 6. Grid Search Optimization with wider search space for Q
    print("Running grid search optimization for ROP and Q...")
    # ROP should search around the lead time demand
    rop_range = np.linspace(mu_DLT - 1 * sigma_DLT, mu_DLT + 3 * sigma_DLT, 20)
    # Q should search from a small quantity up to twice the baseline or lead time demand
    q_min = min(eoq, baseline_q) * 0.5
    q_max = max(eoq, baseline_q, mu_DLT) * 1.5
    q_range = np.linspace(q_min, q_max, 20)
    
    best_tc = float('inf')
    best_rop = 0
    best_q = 0
    best_sl = 0
    
    cost_matrix = np.zeros((len(rop_range), len(q_range)))
    
    for i, rop_val in enumerate(rop_range):
        for j, q_val in enumerate(q_range):
            sl, tc, _ = run_simulation(rop_val, q_val)
            cost_matrix[i, j] = tc
            if sl >= 0.95 and tc < best_tc:
                best_tc = tc
                best_rop = rop_val
                best_q = q_val
                best_sl = sl
                
    # If no configuration meets 95%, find the one with the lowest cost
    if best_tc == float('inf'):
        print("Warning: No policy met 95% service level in grid search. Finding best cost policy instead.")
        best_tc = float('inf')
        for i, rop_val in enumerate(rop_range):
            for j, q_val in enumerate(q_range):
                sl, tc, _ = run_simulation(rop_val, q_val)
                if tc < best_tc:
                    best_tc = tc
                    best_rop = rop_val
                    best_q = q_val
                    best_sl = sl

    print(f"Grid Search Optimal: ROP={best_rop:.2f}, Q={best_q:.2f}, Service Level={best_sl:.2%}, Min Cost=${best_tc:,.2f}")

    # 7. Plot Cost Surface (Contour plot)
    plt.figure(figsize=(8, 6))
    X, Y = np.meshgrid(q_range, rop_range)
    cp = plt.contourf(X, Y, cost_matrix, cmap='viridis_r', levels=20)
    plt.colorbar(cp, label='Total Operational Cost ($)')
    plt.scatter([best_q], [best_rop], color='red', marker='*', s=200, label=f'Optimal Policy (ROP={int(best_rop)}, Q={int(best_q)})')
    plt.title(f'Product {pid}: Total Cost Surface & Policy Optimality')
    plt.xlabel('Order Quantity (Q)')
    plt.ylabel('Reorder Point (ROP)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'visualizations/cost_surface_{pid}.png')
    plt.close()

    # Save summary results
    results_summary.append({
        'Product ID': pid,
        'Daily Demand Mean': mu_D,
        'Daily Demand Std': sigma_D,
        'Lead Time Mean': mu_L,
        'Lead Time Std': sigma_L,
        'Price': price,
        'Storage Cost (Holding)': h,
        'Baseline ROP': baseline_rop,
        'Baseline Cost': tc_base,
        'Baseline Service Level': sl_base,
        'Stochastic ROP': rop_analytical,
        'Stochastic Cost': tc_opt,
        'Stochastic Service Level': sl_opt,
        'Grid Search Optimal ROP': best_rop,
        'Grid Search Optimal Q': best_q,
        'Grid Search Cost': best_tc,
        'Grid Search Service Level': best_sl
    })

# Output summary table
df_summary = pd.DataFrame(results_summary)
df_summary.to_csv("simulation_results_summary.csv", index=False)
print("\nSimulation complete! Summary saved to simulation_results_summary.csv.")
print(df_summary[['Product ID', 'Baseline Cost', 'Baseline Service Level', 'Stochastic Cost', 'Stochastic Service Level', 'Grid Search Cost', 'Grid Search Service Level']])
