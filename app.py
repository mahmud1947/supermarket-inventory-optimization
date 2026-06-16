import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats
import plotly.graph_objects as go
import plotly.express as px
import os

# Set page configuration
st.set_page_config(
    page_title="Stochastic Inventory Optimization Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling matching the academic CUET Theme
st.markdown("""
    <style>
        .main-title {
            font-size: 2.2rem;
            color: #1E3A8A;
            font-weight: bold;
            text-align: center;
            margin-bottom: 0.2rem;
        }
        .subtitle {
            font-size: 1.1rem;
            color: #4B5563;
            text-align: center;
            margin-bottom: 2rem;
        }
        .section-header {
            font-size: 1.5rem;
            color: #1E3A8A;
            border-bottom: 2px solid #3B82F6;
            padding-bottom: 0.3rem;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }
        .metric-card {
            background-color: #F3F4F6;
            border-left: 5px solid #3B82F6;
            padding: 1rem;
            border-radius: 0.375rem;
            margin-bottom: 1rem;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: bold;
            color: #111827;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #6B7280;
        }
        .saving-highlight {
            color: #10B981;
            font-weight: bold;
            font-size: 1.1rem;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📦 Stochastic (Q, R) Inventory Optimization Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Chittagong University of Engineering and Technology (CUET)<br/>Department of Mechatronics & Industrial Engineering</div>', unsafe_allow_html=True)

# Add Author and Advisor Credits
st.markdown("""
    <div style="text-align: center; margin-top: -1.5rem; margin-bottom: 2rem; font-size: 1rem; color: #374151;">
        <strong>Prepared By:</strong> Md Mahmudur Rahman (ID: 2009007) &nbsp;&nbsp;|&nbsp;&nbsp;
        <strong>Supervised By:</strong> Nusrat Sultana
    </div>
""", unsafe_allow_html=True)

# Helper function to fit best distribution
def fit_best_distribution(data):
    results = {}
    
    # 1. Normal Distribution
    try:
        loc, scale = stats.norm.fit(data)
        stat, p_val = stats.kstest(data, 'norm', args=(loc, scale))
        results['normal'] = {'stat': stat, 'p_value': p_val, 'params': (loc, scale)}
    except Exception:
        pass

    # 2. Lognormal Distribution
    try:
        shape, loc, scale = stats.lognorm.fit(data, floc=0)
        stat, p_val = stats.kstest(data, 'lognorm', args=(shape, loc, scale))
        results['lognorm'] = {'stat': stat, 'p_value': p_val, 'params': (shape, loc, scale)}
    except Exception:
        pass

    # 3. Gamma Distribution
    try:
        a, loc, scale = stats.gamma.fit(data, floc=0)
        stat, p_val = stats.kstest(data, 'gamma', args=(a, loc, scale))
        results['gamma'] = {'stat': stat, 'p_value': p_val, 'params': (a, loc, scale)}
    except Exception:
        pass

    # 4. Poisson Distribution (discrete)
    try:
        mu = np.mean(data)
        stat, p_val = stats.kstest(data, lambda x: stats.poisson.cdf(x, mu))
        results['poisson'] = {'stat': stat, 'p_value': p_val, 'params': (mu,)}
    except Exception:
        pass

    best_name = 'normal'
    best_stat = float('inf')
    best_params = (np.mean(data), np.std(data))
    
    for name, res in results.items():
        if res['stat'] < best_stat:
            best_stat = res['stat']
            best_name = name
            best_params = res['params']
            
    return best_name, best_params, results

# Sidebar configuration
st.sidebar.header("📁 Data Sources & Configurations")

# Custom file uploaders
uploaded_demand = st.sidebar.file_uploader("Upload Demand Forecasting CSV", type="csv")
uploaded_inv = st.sidebar.file_uploader("Upload Inventory Monitoring CSV", type="csv")
uploaded_price = st.sidebar.file_uploader("Upload Pricing Optimization CSV", type="csv")

# Load Datasets (uses uploaded files or defaults to existing local files)
@st.cache_data
def load_datasets(demand_file, inv_file, price_file):
    try:
        df_demand = pd.read_csv(demand_file)
        df_inv = pd.read_csv(inv_file)
        df_price = pd.read_csv(price_file)
        
        # Identify matching products
        demand_counts = df_demand['Product ID'].value_counts()
        products_with_min_demand = demand_counts[demand_counts >= 4].index.tolist()
        common_products = set(products_with_min_demand).intersection(set(df_inv['Product ID'].unique())).intersection(set(df_price['Product ID'].unique()))
        common_products = sorted(list(common_products))
        
        return df_demand, df_inv, df_price, common_products, None
    except Exception as e:
        return None, None, None, [], str(e)

# Determine file paths/buffers
demand_source = uploaded_demand if uploaded_demand is not None else "demand_forecasting.csv"
inv_source = uploaded_inv if uploaded_inv is not None else "inventory_monitoring.csv"
price_source = uploaded_price if uploaded_price is not None else "pricing_optimization.csv"

df_demand, df_inv, df_price, common_products, load_error = load_datasets(demand_source, inv_source, price_source)

if load_error:
    st.error(f"Failed to load datasets: {load_error}. Please ensure the baseline CSV files are in the directory or upload custom files.")
    st.stop()

# Dropdown for Product ID selection
st.sidebar.markdown("---")
st.sidebar.header("🔎 Product Configuration")
selected_pid = st.sidebar.selectbox("Select Product ID for Deep Analysis", common_products, index=common_products.index(7694) if 7694 in common_products else 0)

# Target Service Level slider
target_SL = st.sidebar.slider("Target Service Level (SL)", min_value=0.80, max_value=0.99, value=0.95, step=0.01)

# Simulation duration slider
sim_days = st.sidebar.slider("Simulation Duration (Days)", min_value=365, max_value=10000, value=10000, step=100)

# Perform local calculations for the selected product ID
p_demand = df_demand[df_demand['Product ID'] == selected_pid]
p_inv = df_inv[df_inv['Product ID'] == selected_pid]
p_price = df_price[df_price['Product ID'] == selected_pid]

if len(p_demand) == 0 or len(p_inv) == 0 or len(p_price) == 0:
    st.warning("Insufficient data across databases for the selected Product ID.")
    st.stop()

# Calculate parameters
demand_values = p_demand['Sales Quantity'].values
mu_D = np.mean(demand_values)
sigma_D = np.std(demand_values) if len(demand_values) > 1 else 50.0
if sigma_D == 0:
    sigma_D = 10.0

lt_values = p_inv['Supplier Lead Time (days)'].values
mu_L = np.mean(lt_values)
sigma_L = np.std(lt_values) if len(lt_values) > 1 else 2.0
if sigma_L == 0:
    sigma_L = 1.0

price = np.mean(p_price['Price'].values)
h = np.mean(p_price['Storage Cost'].values)
k_order = 100.0
c_short = 1.5 * price
Z = stats.norm.ppf(target_SL)

# Baseline parameters
baseline_rop = np.mean(p_inv['Reorder Point'].values)
eoq = np.sqrt(2 * mu_D * k_order / h)
baseline_q = np.mean(p_inv['Warehouse Capacity'].values) / 5.0
if np.isnan(baseline_q) or baseline_q == 0:
    baseline_q = eoq

# Analytical stochastic calculations
mu_DLT = mu_L * mu_D
sigma_DLT = np.sqrt(mu_L * (sigma_D**2) + (mu_D**2) * (sigma_L**2))
ss_analytical = Z * sigma_DLT
rop_analytical = mu_DLT + ss_analytical
analytical_q = max(eoq, baseline_q)

# Fit best distribution
best_dist_name, best_dist_params, fit_results = fit_best_distribution(demand_values)

# Setup tabs
tab_fitting, tab_sim, tab_opt = st.tabs(["📊 Demand Fitting & Analysis", "🔁 Monte Carlo Simulation", "🎯 Policy Optimization"])

# =========================================================================
# TAB 1: DEMAND FITTING & ANALYSIS
# =========================================================================
with tab_fitting:
    st.markdown('<div class="section-header">📊 Statistical Demand Fitting Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        product_names = {
            7694: "Premium High-Demand Category (e.g. Fresh Dairy / Eggs)",
            1589: "Regular Stable-Demand Category (e.g. Packaged Snacks / Beverages)",
            6656: "Slow-Moving Volatile Category (e.g. Specialty Spices / Condiments)"
        }
        st.markdown("### Estimated Empirical Parameters")
        st.markdown(fr"""
        - **Product Description:** {product_names.get(selected_pid, f'Supermarket Item {selected_pid}')}
        - **Mean Daily Demand ($\mu_D$):** {mu_D:.2f} units
        - **Demand Std Dev ($\sigma_D$):** {sigma_D:.2f} units
        - **Mean Supplier Lead Time ($\mu_L$):** {mu_L:.2f} days
        - **Lead Time Std Dev ($\sigma_L$):** {sigma_L:.2f} days
        - **Unit Price:** ${price:.2f}
        - **Daily Storage (Holding) Cost ($h$):** ${h:.2f} / unit / day
        - **Stockout Shortage Penalty ($C_s$):** ${c_short:.2f} / unit
        """)
        
        st.markdown("### Kolmogorov-Smirnov Test Statistics")
        ks_df = pd.DataFrame([
            {"Distribution": name.capitalize(), "KS Statistic": res['stat'], "p-value": res['p_value']}
            for name, res in fit_results.items()
        ])
        # Highlight the minimum KS Statistic in light green and format values
        styled_df = ks_df.style.highlight_min(subset=['KS Statistic'], color='#D1FAE5').format({
            'KS Statistic': '{:.4f}',
            'p-value': '{:.4f}'
        })
        st.dataframe(styled_df, hide_index=True, use_container_width=True)
        
        st.info(f"**Best Fit Selection:** The distribution with the lowest KS statistic is **{best_dist_name.upper()}**.")

    with col2:
        st.markdown("### Demand Distribution & Goodness-of-Fit")
        
        # Plotly Histogram & PDF Overlays
        fig = go.Figure()
        
        # 1. Histogram
        fig.add_trace(go.Histogram(
            x=demand_values,
            histnorm='probability density',
            name='Empirical Sales Quantity',
            opacity=0.6,
            marker_color='skyblue',
            nbinsx=8
        ))
        
        # 2. Fitted distribution curve
        xmin, xmax = min(demand_values) * 0.8, max(demand_values) * 1.2
        x = np.linspace(xmin, xmax, 200)
        
        if best_dist_name == 'normal':
            y = stats.norm.pdf(x, *best_dist_params)
            fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name=f'Fitted Normal', line=dict(color='red', width=3)))
        elif best_dist_name == 'lognorm':
            y = stats.lognorm.pdf(x, *best_dist_params)
            fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name=f'Fitted Lognormal', line=dict(color='red', width=3)))
        elif best_dist_name == 'gamma':
            y = stats.gamma.pdf(x, *best_dist_params)
            fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name=f'Fitted Gamma', line=dict(color='red', width=3)))
        elif best_dist_name == 'poisson':
            x_int = np.arange(max(0, int(xmin)), int(xmax) + 1)
            y = stats.poisson.pmf(x_int, *best_dist_params)
            fig.add_trace(go.Scatter(x=x_int, y=y, mode='markers', name=f'Fitted Poisson', marker=dict(color='red', size=8)))
            
        fig.update_layout(
            xaxis_title="Daily Sales Quantity",
            yaxis_title="Density",
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

# =========================================================================
# TAB 2: MONTE CARLO SIMULATION
# =========================================================================
# Run simulation function
def run_simulation(rop_val, q_val, num_days=10000):
    np.random.seed(42)
    
    on_hand = q_val
    orders_in_transit = []
    
    total_holding_cost = 0
    total_ordering_cost = 0
    total_shortage_cost = 0
    
    demands_met = 0
    total_demand = 0
    
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
        
        inventory_history.append(on_hand)
        total_holding_cost += on_hand * h
        
        # 4. Check inventory position and place orders
        on_order_qty = sum([q for _, q in orders_in_transit])
        inv_position = on_hand + on_order_qty
        
        if inv_position <= rop_val:
            lead_time = max(1, np.random.normal(mu_L, sigma_L))
            lead_time = int(round(lead_time))
            arrival_day = day + lead_time
            orders_in_transit.append((arrival_day, q_val))
            total_ordering_cost += k_order
            
    service_level = demands_met / total_demand if total_demand > 0 else 1.0
    total_cost = total_holding_cost + total_ordering_cost + total_shortage_cost
    annualized_cost = total_cost * (365.0 / num_days)
    
    return service_level, annualized_cost, inventory_history

with tab_sim:
    st.markdown('<div class="section-header">🔁 Monte Carlo Simulation Comparison</div>', unsafe_allow_html=True)
    
    with st.spinner("Running Monte Carlo Simulation on the background..."):
        # Run baseline simulation
        sl_base, tc_base, hist_base = run_simulation(baseline_rop, baseline_q, sim_days)
        
        # Run analytical stochastic simulation
        sl_opt, tc_opt, hist_opt = run_simulation(rop_analytical, analytical_q, sim_days)

    st.markdown("### Performance Overview")
    
    # Grid of Metric Cards
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #EF4444;">
            <div class="metric-label">BASELINE POLICY</div>
            <div class="metric-value">${tc_base:,.2f} / yr</div>
            <div class="metric-label">ROP: {int(baseline_rop)} | Q: {int(baseline_q)}</div>
            <div class="metric-label" style="color: #EF4444; font-weight: bold;">Service Level: {sl_base:.2%}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_b:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #3B82F6;">
            <div class="metric-label">ANALYTICAL STOCHASTIC POLICY</div>
            <div class="metric-value">${tc_opt:,.2f} / yr</div>
            <div class="metric-label">ROP: {int(rop_analytical)} | Q: {int(analytical_q)}</div>
            <div class="metric-label" style="color: #3B82F6; font-weight: bold;">Service Level: {sl_opt:.2%}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_c:
        savings = (tc_base - tc_opt) / tc_base * 100
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #10B981;">
            <div class="metric-label">STOCHASTIC SAVINGS SUMMARY</div>
            <div class="metric-value" style="color: #10B981;">{savings:.1f}% Savings</div>
            <div class="metric-label">Safety Stock Added: +{ss_analytical:.1f} units</div>
            <div class="metric-label" style="color: #10B981; font-weight: bold;">Meets Target SL ({target_SL:.0%})</div>
        </div>
        """, unsafe_allow_html=True)

    # Inventory trajectory plot
    st.markdown("### 180-Day On-Hand Inventory Trajectory")
    fig2 = go.Figure()
    
    fig2.add_trace(go.Scatter(
        y=hist_base[:180],
        mode='lines',
        name=f'Baseline Policy (Service Level={sl_base:.1%})',
        line=dict(color='red', dash='dash')
    ))
    
    fig2.add_trace(go.Scatter(
        y=hist_opt[:180],
        mode='lines',
        name=f'Optimized Stochastic Policy (Service Level={sl_opt:.1%})',
        line=dict(color='blue')
    ))
    
    fig2.update_layout(
        xaxis_title="Simulated Day",
        yaxis_title="On-Hand Inventory Level (Units)",
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        height=400
    )
    st.plotly_chart(fig2, use_container_width=True)

# =========================================================================
# TAB 3: POLICY OPTIMIZATION
# =========================================================================
with tab_opt:
    st.markdown('<div class="section-header">🎯 Multi-Variable Policy Grid Search Optimization</div>', unsafe_allow_html=True)
    
    st.markdown("This tab searches for the absolute lowest cost policy $(Q^*, R^*)$ that guarantees meeting the customer service level limit.")
    
    run_opt = st.button("🚀 Run Grid Search Optimization")
    
    if run_opt:
        with st.spinner("Running Grid Search over 400 parameter configurations..."):
            # Setup search grid
            rop_range = np.linspace(mu_DLT - 1 * sigma_DLT, mu_DLT + 3 * sigma_DLT, 20)
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
                    # We run a slightly faster simulation (e.g. 2000 days) for search, to keep UX fast
                    sl, tc, _ = run_simulation(rop_val, q_val, num_days=2000)
                    cost_matrix[i, j] = tc
                    if sl >= target_SL and tc < best_tc:
                        best_tc = tc
                        best_rop = rop_val
                        best_q = q_val
                        best_sl = sl
            
            # Fallback if no policy met the limit
            if best_tc == float('inf'):
                best_tc = float('inf')
                for i, rop_val in enumerate(rop_range):
                    for j, q_val in enumerate(q_range):
                        sl, tc, _ = run_simulation(rop_val, q_val, num_days=2000)
                        if tc < best_tc:
                            best_tc = tc
                            best_rop = rop_val
                            best_q = q_val
                            best_sl = sl

        col_opt1, col_opt2 = st.columns([1, 2])
        
        with col_opt1:
            st.markdown("### Optimal Policy Results")
            st.success(f"""
            **Optimal Reorder Point (ROP*):** {int(best_rop)} units  
            **Optimal Order Quantity (Q*):** {int(best_q)} units  
            **Minimum Annual Operational Cost:** ${best_tc:,.2f}  
            **Expected Service Level:** {best_sl:.2%}
            """)
            
            grid_savings = (tc_base - best_tc) / tc_base * 100
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: #10B981; background-color: #ECFDF5;">
                <div class="metric-label" style="color: #065F46;">OPTIMAL SAVINGS</div>
                <div class="metric-value" style="color: #10B981;">{grid_savings:.1f}% Savings</div>
                <div class="metric-label" style="color: #065F46;">Compared to baseline annual cost of ${tc_base:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_opt2:
            st.markdown("### Cost Surface & Policy Space Contour Map")
            
            # Plotly Contour Chart
            fig3 = go.Figure(data=go.Contour(
                z=cost_matrix,
                x=q_range,
                y=rop_range,
                colorscale='Viridis',
                reversescale=True,
                colorbar=dict(title='Total Cost ($)')
            ))
            
            # Mark the optimal point
            fig3.add_trace(go.Scatter(
                x=[best_q],
                y=[best_rop],
                mode='markers',
                marker=dict(color='red', size=15, symbol='star'),
                name='Optimal Policy'
            ))
            
            fig3.update_layout(
                xaxis_title="Order Quantity (Q)",
                yaxis_title="Reorder Point (ROP)",
                margin=dict(l=20, r=20, t=20, b=20),
                height=400
            )
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Click the 'Run Grid Search Optimization' button to compute and visualize the optimal policy space.")
