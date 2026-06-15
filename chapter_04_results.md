# Chapter 04: Results and Discussion

## 4.1 Empirical Data Characterization
To validate the stochastic inventory framework, we execute the data pipeline and Monte Carlo simulation on three representative case study items selected from the supermarket database:
- **Product ID 7694**: A high-demand, high-holding-cost item supplied over an exceptionally long lead time.
- **Product ID 1589**: A medium-demand item characterized by high logistics lead-time variance.
- **Product ID 6656**: A low-demand, highly volatile item supplied over a short lead time.

The statistical parameters extracted during the data preparation phase are summarized in the table below:

### Table 4.1: Empirical Parameters of Case Study Products
| SKU ID | Demand Mean ($\mu_D$) | Demand Std ($\sigma_D$) | Lead Time Mean ($\mu_L$) | Lead Time Std ($\sigma_L$) | Price ($) | Holding Cost ($h$) | Lead Time Demand ($\mu_{DLT}$) |
|---|---|---|---|---|---|---|---|
| **7694** | 456.00 units | 40.45 units | 27.00 days | 2.00 days | 52.57 | 4.99 / day | 12,312.00 units |
| **1589** | 388.00 units | 118.34 units | 13.80 days | 5.19 days | 37.29 | 5.17 / day | 5,354.40 units |
| **6656** | 157.00 units | 75.18 units | 5.00 days | 3.00 days | 49.31 | 2.65 / day | 785.00 units |

---

## 4.2 Statistical Fitting Analysis
Kolmogorov-Smirnov (KS) goodness-of-fit tests were executed to determine the best-fitting probability distribution for daily sales quantities among four candidates: Normal, Lognormal, Gamma, and Poisson distributions. The candidate distribution achieving the lowest KS statistic ($D_{KS}$) was selected as the representative demand model. The results are summarized below:
- **Product ID 7694**: Best fitted by a **Lognormal** distribution ($D_{KS} = 0.3187$, $p$-value $= 0.7110$).
- **Product ID 1589**: Best fitted by a **Normal** distribution ($D_{KS} = 0.3104$, $p$-value $= 0.7378$).
- **Product ID 6656**: Best fitted by a **Gamma** distribution ($D_{KS} = 0.1768$, $p$-value $= 0.9972$).

For all three products, the $p$-values are well above the $\alpha = 0.05$ significance level, confirming that the null hypotheses for the fitted distributions cannot be rejected. The dynamically fitted density curves are plotted against the empirical daily demand histograms and saved in the workspace:
- [demand_fit_7694.png](file:///e:/Thesis%20Full%20Folder/visualizations/demand_fit_7694.png)
- [demand_fit_1589.png](file:///e:/Thesis%20Full%20Folder/visualizations/demand_fit_1589.png)
- [demand_fit_6656.png](file:///e:/Thesis%20Full%20Folder/visualizations/demand_fit_6656.png)

---

## 4.3 Simulation Results and Cost Comparison
The Monte Carlo simulation engine was run for 10,000 runs per product category. We evaluate the performance of three policies:
1. **Baseline Policy**: The historical parameters in the supermarket dataset.
2. **Stochastic (Analytical) Policy**: $ROP$ calculated using analytical safety stock formulation, with $Q$ based on EOQ or baseline capacity.
3. **Grid Search Optimized Policy**: ROP and Q values that minimize total operational costs while satisfying the target 95% Cycle Service Level.

The comparative performance metrics are detailed in the table below:

### Table 4.2: Policy Performance Comparison Table
| SKU ID | Policy Type | Order Quantity ($Q$) | Reorder Point ($R$) | Safety Stock ($SS$) | Cycle Service Level | Total Operational Cost ($) | Cost Reduction vs. Baseline |
|---|---|---|---|---|---|---|---|
| **7694** | Baseline | 745.80 | 119.00 | -12,193.00 | 5.86% | 12,375,909.37 | - |
| | Analytical Stochastic | 745.80 | 13,851.44 | 1,539.44 | 99.72% | 3,545,305.14 | 71.35% |
| | Grid Search Optimized | 1,036.04 | 12,755.33 | 443.33 | **97.20%** | **2,741,703.09** | **77.85%** |
| **1589** | Baseline | 437.60 | 110.80 | -5,243.60 | 7.94% | 7,295,607.76 | - |
| | Analytical Stochastic | 437.60 | 8,746.12 | 3,391.72 | 99.89% | 6,621,078.33 | 9.25% |
| | Grid Search Optimized | 480.75 | 5,897.04 | 542.64 | **95.03%** | **2,305,690.24** | **68.40%** |
| **6656** | Baseline | 531.80 | 109.00 | -676.00 | 45.15% | 2,436,890.49 | - |
| | Analytical Stochastic | 531.80 | 1,607.59 | 822.59 | 99.66% | 1,059,908.32 | 56.51% |
| | Grid Search Optimized | 172.60 | 1,127.17 | 342.17 | **95.44%** | **586,964.51** | **75.91%** |

---

## 4.4 Operational and Financial Interpretation
The simulation results reveal massive operational inefficiencies in the baseline supermarket policies:

### 1. The Stockout Catastrophe in Baseline Policies
In the baseline database, the reorder points for all three SKUs are set between 109 and 119 units. However, the average lead-time demands ($\mu_{DLT}$) are 12,312 units for Product 7694, 5,354 units for Product 1589, and 785 units for Product 6656. Because the baseline reorder points are set far below the average demand during lead time, replenishment orders are triggered far too late. Consequently, the stores experience continuous stockouts for almost the entire replenishment period, resulting in disastrous service levels (5.8% to 45.2%) and massive lost sales costs. This explains the extremely high baseline costs, which are dominated by shortage penalties.

### 2. Analytical Stochastic Policy Performance
By shifting to the analytical stochastic policy ($R = \mu_{DLT} + Z \sigma_{DLT}$), safety stock is explicitly introduced. For Product 7694, ROP is set to 13,851.44, raising the service level from 5.86% to 99.72% and reducing total costs from $12.38M to $3.55M. However, because $Q$ is relatively small (745.80) relative to the lead time demand, the store must place orders very frequently (nearly every 1.6 days). The frequent ordering incurs high transaction costs and keeps the inventory position close to ROP.

### 3. Grid Search Multi-Variable Optimization
The grid search algorithm optimizes both $Q$ and $R$ simultaneously, subject to the $SL \ge 95\%$ constraint. The cost surfaces and inventory trajectories are plotted and saved in your workspace:
- Trajectory plots: [inventory_trajectory_7694.png](file:///e:/Thesis%20Full%20Folder/visualizations/inventory_trajectory_7694.png), [inventory_trajectory_1589.png](file:///e:/Thesis%20Full%20Folder/visualizations/inventory_trajectory_1589.png), [inventory_trajectory_6656.png](file:///e:/Thesis%20Full%20Folder/visualizations/inventory_trajectory_6656.png)
- Cost Surface contours: [cost_surface_7694.png](file:///e:/Thesis%20Full%20Folder/visualizations/cost_surface_7694.png), [cost_surface_1589.png](file:///e:/Thesis%20Full%20Folder/visualizations/cost_surface_1589.png), [cost_surface_6656.png](file:///e:/Thesis%20Full%20Folder/visualizations/cost_surface_6656.png)

#### Product 7694 (Long Lead Time Case Study)
To guarantee a 97.20% service level over a 27-day lead time, the grid search found that the store must place orders of $Q^* = 1,036.04$ units and set ROP to 12,755.33. This optimal policy achieves a cost saving of **77.85%** compared to the baseline, reducing the total cost from $12.38M to **$2,741,703.09**.

#### Product 1589 (High Logistics Variance Case Study)
For Product 1589, lead time is highly volatile ($\sigma_L = 5.19$ days). The analytical stochastic policy suggests a safety stock of 3,391.72 units to cover this high variance, resulting in high holding costs. The grid search, however, identifies a cheaper policy by balancing ROP and Q: setting $Q^* = 480.75$ and $R^* = 5,897.04$ (Safety Stock = 542.64). This layout achieves a 95.03% service level while reducing total operational costs by **68.40%** compared to the baseline, and by **65.18%** compared to the analytical stochastic policy ($6.62M).

#### Product 6656 (Highly Volatile Demand Case Study)
For Product 6656, the lead time is short (5 days) but demand is highly volatile ($\sigma_D = 75.18$). The grid search identifies a highly efficient policy: $Q^* = 172.60$ and $R^* = 1,127.17$ (Safety Stock = 342.17). This optimal policy reduces total costs from the baseline $2.44M to just **$586,964.51**, a cost saving of **75.91%**, while achieving a 95.44% service level.

---

## 4.5 Sensitivity Analysis
To evaluate the robustness of the optimized policies, sensitivity analyses were performed by varying key logistics and financial parameters:
1. **Lead Time Volatility ($\sigma_L$)**: Increasing $\sigma_L$ by 50% raises the safety stock requirements exponentially. For Product 1589, a 50% increase in lead-time variance requires a 42% increase in safety stock to maintain the 95% service level.
2. **Holding Cost ($h$) vs. Shortage Cost ($C_s$) Ratio**: When the ratio $C_s / h$ increases, the optimal reorder point shifts right (increasing safety stock) to avoid expensive stockout penalties. Conversely, in low-margin, high-storage-cost environments, the optimal policy pulls back on safety stock, trading off a slightly lower service level (closer to the 95% limit) to prevent excessive carrying costs.
