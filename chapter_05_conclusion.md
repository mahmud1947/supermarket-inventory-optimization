# Chapter 05: Conclusion and Recommendations

## 5.1 Summary of Findings
This thesis has successfully developed, implemented, and validated a data-driven, simulation-based optimization framework for multi-item continuous review $(Q, R)$ inventory systems under joint demand and supplier lead-time uncertainty. Using empirical transactional supermarket datasets, the study demonstrated the severe operational and financial risks of using deterministic inventory parameters in volatile real-world supply chains.

The key quantitative findings from this research include:
1. **Severe Baseline Inefficiencies**: The baseline supermarket inventory policies, which set reorder points far below the lead-time demand, resulted in catastrophic stockouts (with service levels as low as 5.8%) and massive shortage costs, dominated by lost sales penalties.
2. **Impact of Safety Stock**: Shifting to a stochastic analytical safety stock policy significantly stabilized the replenishment cycles, raising service levels to over 93% for all tested SKU categories and reducing total costs by up to 64%.
3. **Optimality of Joint Parameters via Simulation**: Using Monte Carlo Simulation coupled with a Grid Search algorithm resolved the limitations of analytical normal approximations. The optimal $(Q^*, R^*)$ configurations achieved the target 95% service level while minimizing carrying costs.
4. **Significant Carrying Cost Reductions**: The grid search optimal policies achieved cost savings of **75.91%** for Product 6656, **68.40%** for Product 1589, and **77.85%** for Product 7694 compared to their respective baseline carrying costs, proving the substantial financial benefits of the proposed optimization framework.

---

## 5.2 Contributions to Mechatronics and Industrial Engineering
From an industrial engineering and systems mechatronics perspective, this research makes several distinct contributions:
- **Data-Driven Systems Integration**: The research provides a modular python-based decision support system that connects transactional point-of-sale databases directly with simulation and optimization algorithms. This represents a key component of Industry 4.0 automated warehouse control systems.
- **Handling of Complex Logistics Distributions**: The simulation engine bypasses rigid analytical assumptions, allowing industrial engineers to model supplier lead times and daily sales quantities under arbitrary probability distributions.
- **Robust Decision Support Tool**: The resulting cost contour surfaces (contour maps) serve as a visual tool for supply chain managers to understand the financial trade-offs between safety stocks and order sizes, allowing them to balance inventory holding capital against customer service levels.

---

## 5.3 Limitations of the Study
While the proposed framework demonstrates high performance, the following limitations should be noted:
1. **Single-Echelon System Boundaries**: The simulation models a single-echelon system (one store supplied by one warehouse). In practice, retail chains operate multi-echelon networks with transshipments between stores, which adds inventory positioning complexity.
2. **Constant Holding and Ordering Costs**: The model assumes holding costs ($h$) and ordering costs ($k$) are constant over the planning horizon. In reality, warehousing costs exhibit step-functions as capacity boundaries are crossed, and ordering costs vary based on fuel prices and freight consolidations.
3. **Demand Distribution Independence**: The model assumes demand is independent across SKUs. In large supermarkets, demands for different products are often correlated (e.g. promotional cross-selling or substitution effects), which shifts safety stock levels.

---

## 5.4 Future Research Directions
To extend the scope and capabilities of this inventory optimization framework, the following areas are recommended for future research:
1. **Multi-Echelon Network Expansion**: Expanding the simulation model to multi-echelon environments (such as warehouse-to-retailer networks) to evaluate centralized vs. decentralized safety stock positioning.
2. **Dynamic Holding Cost Functions**: Integrating non-linear carrying costs and capacity-constrained step-costs to reflect physical warehouse boundaries.
3. **Multi-Item Constraint Integration**: Adding joint constraints, such as ordering budget ceilings, warehouse capacity limits, and shipping vehicle weight limits, to represent resource-constrained industrial supply chains.
4. **Integration of Machine Learning Forecasting**: Connecting machine learning forecasting models (e.g., LSTMs or XGBoost) to predict future demand distributions, and passing those predicted parameters into the Monte Carlo simulation to dynamically adjust safety stocks.
5. **Heuristic Optimization Algorithms**: Implementing advanced heuristic algorithms (e.g., Genetic Algorithms, Particle Swarm Optimization) to replace grid search, enabling faster optimization of thousands of SKUs simultaneously.
