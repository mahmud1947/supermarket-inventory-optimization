# Chapter 02: Literature Review

## 2.1 Safety Stock Determination Under Uncertainty
The calculation of safety stock ($SS$) serves as a protective inventory cushion to absorb variability in both market demand and supplier lead times during the replenishment cycle. Early research in inventory management, beginning with Harris (1913) and expanded by Clark and Scarf (1960), focused primarily on deterministic environments. However, the introduction of uncertainty by Arrow, Harris, and Marschak (1951) highlighted the necessity of treating demand as a stochastic process.

Under uncertainty, safety stock is directly linked to the concept of **Cycle Service Level** ($CSL$, denoted as $P_k$), which is defined as the probability of not experiencing a stockout during a replenishment lead-time cycle. Alternatively, the **Product Fill Rate** ($\beta$) measures the proportion of customer demand that is met directly from on-hand inventory. Historically, safety stock is calculated as:
$$SS = Z \cdot \sigma_{DLT}$$
Where:
- $Z$: The service factor (standard normal coordinate) corresponding to the target service level.
- $\sigma_{DLT}$: The standard deviation of demand during lead time ($DLT$).

Traditionally, researchers assume that supplier lead time $L$ is constant and only demand $D$ varies. In this case, $\sigma_{DLT} = \sigma_D \sqrt{L}$. When both demand and lead time are variable, the analytical complexity increases. Key researchers like Silver, Pyke, and Peterson (1998) derived standard mathematical approximations, yet these rely on the critical assumption that demand and lead time follow independent normal distributions. In real-world retail and industrial settings, demand distributions are highly skewed (lognormal, gamma) or discrete (Poisson), violating the assumptions of standard normal approximations.

---

## 2.2 Stochastic Inventory Models
Stochastic inventory control policies generally fall into two categories: continuous review systems and periodic review systems.

### 2.2.1 Continuous Review $(Q, R)$ Policy
In a continuous review system, the inventory level is monitored continuously. When the inventory position ($IP$), defined as:
$$IP = \text{On-Hand Inventory} + \text{On-Order Inventory} - \text{Backorders}$$
falls to or below a specified Reorder Point ($ROP$), a replenishment order for a fixed quantity $Q$ is placed. The continuous review system is widely applied in industries where automated barcode scanners, RFID systems, and ERP integrations allow real-time inventory tracking (Simchi-Levi et al., 2008). 

The optimal configuration of the $(Q, R)$ policy requires the simultaneous determination of $Q$ and $R$. The economic order quantity ($Q^*$) is derived from the classical trade-off between holding cost and ordering cost, while the optimal reorder point ($R^*$) balances carrying cost and stockout penalties. Under stochastic conditions, these parameters are interdependent, requiring iterative numerical solution methods.

### 2.2.2 Periodic Review $(s, S)$ and $(R, s, S)$ Policies
In contrast, periodic review systems monitor inventory levels at fixed time intervals (e.g., weekly or monthly). Under an $(s, S)$ policy, if the inventory level is found to be at or below the reorder level $s$ at the review epoch, an order is placed to bring the inventory position up to the target level $S$. Periodic review is suitable for environments with high coordination costs or joint replenishment channels (Hadley & Whitin, 1963). However, periodic review models introduce an additional "risk period" (the review interval plus the lead time), necessitating higher safety stock levels compared to continuous review systems.

---

## 2.3 Monte Carlo Simulation in Inventory Optimization
When probability distributions of demand and lead time are non-normal, or when the system constraints (such as storage capacity limits, joint ordering budgets, and lost sales) are complex, analytical mathematical solutions become intractable. In these cases, simulation-based optimization emerges as the dominant research methodology.

Monte Carlo Simulation (MCS), pioneered by von Neumann and Ulam in the 1940s, utilizes repeated random sampling from fitted probability distributions to simulate the behavior of complex systems. In supply chain research, MCS is used to model the inventory trajectory over a specified planning horizon. 

Numerous studies demonstrate the flexibility of MCS in evaluating inventory policies:
- **Non-Standard Distributions**: Simulation allows the modeling of demand using Gamma, Weibull, or empirical distributions without requiring closed-form analytical integrations (Law & Kelton, 2000).
- **Lead Time Uncertainty**: MCS can model complex supplier lead-time distributions, including multi-modal or highly variable logistics patterns.
- **Service Level Evaluation**: By simulating thousands of runs, MCS provides highly accurate empirical estimations of the product fill rate ($\beta$) and cycle service level ($CSL$) under varying safety stock configurations.

---

## 2.4 Multi-Item Inventory Optimization
In a multi-item supply chain, inventory management is constrained by shared resources. The classical approach of optimizing SKUs independently ignores these system-level constraints, leading to sub-optimal configurations.

Key constraints in multi-item optimization include:
1. **Warehouse Capacity Constraints**: The total storage space occupied by all items cannot exceed the physical warehouse limit ($W$):
   $$\sum_{i=1}^N v_i \cdot I_{it} \le W$$
   Where $v_i$ is the storage volume per unit of item $i$, and $I_{it}$ is the inventory level on day $t$.
2. **Working Capital Budget Constraints**: The total capital tied up in inventory cannot exceed a specified budget ($B$):
   $$\sum_{i=1}^N c_i \cdot I_{it} \le B$$
   Where $c_i$ is the unit cost of item $i$.
3. **Correlated Demands**: Demands for different items may exhibit positive correlation (substitutable products) or negative correlation (complementary products), which significantly shifts safety stock requirements.

Heuristic search methods, such as Genetic Algorithms (GA), Simulated Annealing (SA), and Grid Search Optimization, are frequently coupled with Monte Carlo simulations to solve constrained multi-item models (Glover & Kochenberger, 2003).

---

## 2.5 Literature Gaps
Despite the extensive literature on stochastic inventory control, two major research gaps persist:
1. **Simultaneous Stochastic Variability in Demand and Lead Time**: A significant portion of literature assumes either deterministic lead times or constant demand. Studies that treat both as variable often assume Normal distributions. Few researchers have evaluated the joint impact of discrete, skewed distributions (like Poisson and Gamma) under continuous review lost-sales models.
2. **Lack of Empirical Retail Dataset Integration**: Many stochastic models are tested on purely theoretical, synthetic parameters. There is a lack of frameworks that take messy, multi-store supermarket transactional datasets, extract lead times and storage costs, fit statistical distributions, and optimize safety stocks directly.

This thesis bridges these gaps by implementing a complete data-to-optimization pipeline. Using empirical supermarkets data, we characterize demand and lead-time distributions, run a robust continuous review $(Q, R)$ simulation, and optimize safety stock configurations to minimize operational costs under joint target service constraints.
