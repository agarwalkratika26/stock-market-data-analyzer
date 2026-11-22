# 05 - Models, Algorithms, and Learning

## 1. Technical Indicator Mathematics

### 1.1 Simple Moving Average (SMA)
For a window of length $k$:
$$\text{SMA}_k(t) = \frac{1}{k} \sum_{i=0}^{k-1} C_{t-i}$$
Implemented via Pandas: `close.rolling(k).mean()`.

### 1.2 Exponential Moving Average (EMA)
Weights recent prices with an exponential decay factor $\alpha = \frac{2}{\text{span} + 1}$:
$$\text{EMA}_t = \alpha C_t + (1 - \alpha) \text{EMA}_{t-1}$$
Implemented via Pandas: `close.ewm(span=span, adjust=False).mean()`.
- Fast Span: 12 bars
- Slow Span: 26 bars

### 1.3 Moving Average Convergence Divergence (MACD)
$$\text{MACD}_t = \text{EMA}_{12}(t) - \text{EMA}_{26}(t)$$
$$\text{Signal}_t = \text{EMA}_9(\text{MACD}_t)$$
$$\text{Histogram}_t = \text{MACD}_t - \text{Signal}_t$$

### 1.4 Relative Strength Index (RSI - Wilder's Formulation)
Given price changes $\Delta C_t = C_t - C_{t-1}$:
- $\text{Gain}_t = \max(\Delta C_t, 0)$
- $\text{Loss}_t = \max(-\Delta C_t, 0)$

Smoothed average gains and losses using $\alpha = \frac{1}{14}$:
$$\text{AvgGain}_t = \text{EWM}(\text{Gain}, \alpha=1/14)$$
$$\text{AvgLoss}_t = \text{EWM}(\text{Loss}, \alpha=1/14)$$
$$\text{RS}_t = \frac{\text{AvgGain}_t}{\text{AvgLoss}_t}$$
$$\text{RSI}_t = 100 - \frac{100}{1 + \text{RS}_t}$$

### 1.5 Bollinger Bands
$$\text{Middle Band}_t = \text{SMA}_{20}(t)$$
$$\sigma_t = \text{RollingStd}_{20}(t)$$
$$\text{Upper Band}_t = \text{Middle Band}_t + 2\sigma_t$$
$$\text{Lower Band}_t = \text{Middle Band}_t - 2\sigma_t$$

---

## 2. Trading Simulation & Backtest Engine

### 2.1 Signal Generation & Lookahead Prevention
The strategy compares a fast moving average against a slow moving average:
$$\text{Signal}_t = \begin{cases} 1 & \text{if } \text{FastSMA}_t > \text{SlowSMA}_t \\ 0 & \text{otherwise} \end{cases}$$

> [!IMPORTANT]
> **Lookahead Bias Correction**: To prevent impossible execution at the current bar's close price, positions are shifted forward by one bar:
> $$\text{Position}_t = \text{Signal}_{t-1}$$

### 2.2 Return Calculation & Friction Drag
- Market daily return: $R_{m, t} = \frac{C_t - C_{t-1}}{C_{t-1}}$
- Turnover (position change): $\tau_t = |\text{Position}_t - \text{Position}_{t-1}|$
- Transaction cost deduction: $\text{Cost}_t = \tau_t \times \frac{\text{Cost}_{\text{bps}}}{10,000}$
- Strategy net return:
  $$R_{s, t} = \text{Position}_t \cdot R_{m, t} - \text{Cost}_t$$
- Compounded equity curve:
  $$E_t = E_0 \prod_{i=1}^t (1 + R_{s, i})$$

### 2.3 Performance Analytics
- **Compound Annual Growth Rate (CAGR)**:
  $$\text{CAGR} = \left(\frac{E_T}{E_0}\right)^{\frac{1}{\text{Years}}} - 1, \quad \text{where } \text{Years} = \frac{T}{252}$$
- **Maximum Drawdown**:
  $$\text{Peak}_t = \max_{0 \le i \le t} E_i$$
  $$\text{MDD} = \min_t \left( \frac{E_t}{\text{Peak}_t} - 1 \right)$$
- **Sharpe Ratio (Zero Risk-Free Rate Assumption)**:
  $$\text{Sharpe} = \frac{\bar{R}_s \times 252}{\sigma_{R_s} \times \sqrt{252}}$$

---

## 3. Future Machine Learning / AI Model Roadmap

When machine learning forecasting models (e.g., Random Forest Classifier, LSTM, or XGBoost Direction Predictors) are added to this project, they will be structured under this exact lifecycle:

```mermaid
flowchart TD
    A[Historical OHLCV Bars] --> B[Feature Engineering: Lags, Returns, RSI, MACD, Volume Delta]
    B --> C[Target Formulation: Binary Direction y_t = Close_{t+1} > Close_t]
    C --> D[Walk-Forward Time-Series Split: No Shuffle Train/Val/Test]
    D --> E[Model Training: Objective Loss Minimization]
    E --> F[Probability Calibration & Thresholding]
    F --> G[Next-Bar Execution Simulation with Transaction Friction]
    G --> H[Model Validation Metrics: Accuracy, Precision, F1, Sharpe, Sortino]
```

1. **Features**:
   - Normalized returns: 1-day, 5-day, 20-day returns.
   - Indicator features: RSI-14, MACD histogram, Bollinger Band width $(BB_{upper} - BB_{lower}) / BB_{mid}$, Volume moving average ratio.
2. **Target Formulation**:
   - Classification: $y_t = \mathbb{I}(C_{t+1} > C_t)$ (binary direction).
   - Regression: $y_t = \ln(C_{t+1} / C_t)$ (next-day log return).
3. **Walk-Forward Validation**:
   - Standard k-fold cross-validation is strictly forbidden due to data leakage.
   - Expanding or rolling walk-forward windows must be used to validate model generalization across real market regimes.
