# Chapter 01: Introduction

## 1.1 Context and Background
In modern industrial engineering and operations management, inventory management stands as a foundational pillar determining the operational efficiency, capital structure, and service level of a supply chain network. The primary objective of inventory control is to balance two diametrically opposed financial forces: the cost of carrying inventory (holding cost) and the cost of inventory unavailability (shortage or stockout cost). Within a multi-item environment—typical of retail, automotive, and mechatronic assembly lines—this balancing act becomes significantly more complex. Items share warehouse space, logistics channels, and working capital budgets. Consequently, inventory decisions for a single SKU (Stock Keeping Unit) cannot be made in isolation.

Classical inventory control systems traditionally rely on deterministic assumptions where customer demand and supplier replenishment lead times are assumed to be static, constant, and predictable. The most notable example of such a deterministic approach is Harris's Economic Order Quantity (EOQ) model and its derivatives. While these models provide mathematically convenient closed-form solutions and offer valuable conceptual insights, they are built on assumptions that are frequently violated in real-world supply chain systems. In actual industrial settings, demand is subject to stochastic fluctuations driven by customer behavior, promotions, seasonality, and market trends. Concurrently, supplier lead times are influenced by logistics bottlenecks, manufacturing delays, customs clearances, and weather anomalies. Neglecting these variabilities leads to a system-wide misalignment: either an excess of holding stock that binds capital and decreases warehouse efficiency, or frequent stockouts that degrade customer service levels, lose sales, and erode brand equity.

To mitigate the risks associated with uncertainty, supply chain practitioners introduce "Safety Stock" (SS) as a buffer. The safety stock acts as an insurance policy against lead-time demand variability. The Reorder Point (ROP) is the threshold level of on-hand inventory that triggers a replenishment order of a fixed quantity ($Q$). Determining the optimal configuration of safety stock and reorder points is critical to maintaining high service levels while minimizing carrying costs.

---

## 1.2 Limitations of Deterministic Inventory Models
Deterministic inventory models fail to capture the dynamic and probabilistic nature of real-world supply chains. The primary limitations of deterministic approaches include:
1. **Underestimation of Safety Stock Requirements**: Deterministic models assume that lead-time demand is constant, thereby setting safety stock to zero. Under stochastic conditions, this guarantee of stock availability collapses, leading to immediate stockouts whenever actual demand exceeds the mean value.
2. **Static Reorder Point Misalignment**: When lead time $L$ or demand $D$ varies, the reorder point $ROP = D \times L$ fails to prevent stockouts. A delay of even a single day in supplier delivery can deplete the entire inventory.
3. **Ignore Multi-Item Interactions**: Traditional models analyze SKUs independently. In practice, a shared warehouse capacity or ordering budget couples the inventory policies of all items. Deterministic approaches do not have the mathematical flexibility to model these joint constraints under uncertainty.
4. **Lack of Risk Integration**: Deterministic models cannot express the relationship between inventory levels and service level probabilities. Industrial managers need to select safety stock based on risk thresholds (e.g., ensuring a 95% or 99% probability of not stocking out during a replenishment cycle), which requires stochastic, probability-based modeling.

---

## 1.3 Motivation of the Study
The motivation for this research stems from the critical need to bridge the gap between academic stochastic models and practical industrial applications. While advanced mathematical formulations for stochastic inventory control exist, they are often mathematically intractable when applied to large-scale, multi-item retail databases with non-standard probability distributions. 

Furthermore, mechatronics and industrial engineering systems are increasingly relying on automated, data-driven decision support tools. Developing an optimization framework that takes raw transactional sales data, supplier logistics logs, and pricing cost structures, processes them through distribution-fitting algorithms, and runs Monte Carlo simulations to find cost-optimized policies represents a major step forward. 

By utilizing real-world multi-item supermarket datasets, this study shows how simulation-based optimization can practically resolve inventory bottlenecks. Traditional stochastic models assume that demand fits a normal distribution. However, empirical demand patterns are often highly skewed, seasonal, or intermittent. Monte Carlo Simulation (MCS) offers the unique advantage of bypassing strict analytical distribution assumptions by simulating thousands of randomized supply chain scenarios, evaluating actual service levels, and identifying policies that minimize total inventory cost ($TC$) under arbitrary demand and lead-time distributions.

---

## 1.4 Research Objectives
The primary objectives of this thesis are:
1. **To develop a comprehensive stochastic modeling framework** for a multi-item supply chain that treats both customer demand and supplier lead times as independent random variables.
2. **To implement a data preprocessing and statistical fitting pipeline** that characterizes empirical demand and lead-time distributions using goodness-of-fit indicators (e.g., Kolmogorov-Smirnov and Chi-Square tests).
3. **To design and execute a robust Monte Carlo Simulation engine** simulating 10,000+ operational cycles per product category to compute actual service levels, holding costs, and stockout penalties.
4. **To optimize safety stock ($SS$) and reorder point ($ROP$) configurations** through grid search algorithms under target service level constraints.
5. **To evaluate the financial and operational improvements** of the optimized stochastic policies compared to baseline deterministic supermarket policies.

---

## 1.5 Significance and Scope of the Study
This research contributes directly to the fields of Industrial Engineering, Operations Research, and Systems Engineering by providing an empirical, data-driven framework for inventory control. The significance of this study includes:
- **Financial Optimization**: Demonstrating how stochastic modeling can reduce total carrying costs by over 70% while improving service level metrics.
- **Risk Mitigation**: Providing managers with a quantitative tool to trade off carrying costs against the risk of customer stockouts.
- **Operational Scalability**: The developed Python simulation engine is generalizable and can be scaled to multi-item chains in various industries (manufacturing, mechatronics assembly, and e-commerce).

The scope of this thesis is bounded by the following parameters:
- **System Boundaries**: Single-echelon, multi-item continuous review $(Q, R)$ inventory system.
- **Data Context**: Empirical sales, inventory, and pricing datasets containing 10,000 records across multiple retail stores.
- **Model Constraints**: Replenishment orders are placed under variable supplier lead times, and unfulfilled demand is modeled using the retail standard **lost sales** assumption rather than backordering.

---

## 1.6 Thesis Organization
This thesis is structured into five chapters:
- **Chapter 1: Introduction** defines the research background, limitations of deterministic models, motivation, objectives, and scope.
- **Chapter 2: Literature Review** examines the theoretical foundations of inventory control, stochastic models, Monte Carlo simulations, and details the research gaps this study addresses.
- **Chapter 3: Methodology** outlines the empirical dataset characterization, statistical distribution fitting, mathematical derivations for stochastic safety stocks, and the architecture of the Monte Carlo simulation engine.
- **Chapter 4: Results and Discussion** presents the empirical results of the statistical fitting, simulation runs, cost surface contours, and sensitivity analyses.
- **Chapter 5: Conclusion and Recommendations** summarizes key findings, limitations, mechatronic/industrial system contributions, and outlines directions for future research.
