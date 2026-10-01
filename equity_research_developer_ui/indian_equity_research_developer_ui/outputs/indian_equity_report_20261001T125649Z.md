I’m unable to access live market / web data or current NSE/BSE / Yahoo Finance feeds in this environment right now, so I **cannot** reliably fetch today’s prices, EMAs, FII/DII flows, or intraday levels. I also cannot see live ASM/GSM, F&O ban lists, or current corporate action calendars. 

Because your framework **explicitly requires** verified, timestamped live data and forbids estimation or fabrication, proceeding with hypothetical or stale numbers would directly violate your constraints.

Given those hard limits, here’s what I can do **concretely and safely**:

---

## 1. Why I cannot do STAGE A–C as specified

Your instructions require, for **each numeric claim**:

- The exact value,
- Instrument/symbol,
- **Source name**, and
- A clear **IST timestamp**.

And you mandate **live** checks for:

- Nifty 50 / Bank Nifty vs 20/50 EMA  
- India VIX, FII/DII cash flows, advance/decline  
- Global cues (US/Asia indices, Brent, USDINR, US10Y)  
- 5–10 day momentum, 20-day average traded value  
- ASM/GSM status, F&O ban status  
- Upcoming corporate events  
- OI / PCR / IV vs HV where used  

In this environment, the web tools you asked me to use (search + page reading) are not available/working, so I **cannot** pull those from NSE/BSE, Moneycontrol, Yahoo Finance, etc. I also cannot “back-door” them via other tools, and I will not fabricate or approximate.

That means:

- I cannot compute or validate EMAs, RSI, ATR, VWAP, or pivots from current prices.
- I cannot confirm whether a stock is in ASM/GSM, F&O ban, or has results in next 3 days.
- I cannot calculate your required **risk-position sizing** off real current levels.

Any specific swing-pick table with real CMP, pivots, EMAs, and T1/T2 would therefore be **made up**, which is explicitly disallowed by your brief.

---

## 2. Regime keyword (under integrity constraint)

Because I cannot observe **today’s** index and volatility data at all, I also cannot truthfully classify the market regime. Under your rules, I must not guess.

So the only honest stance is:

**NO_TRADE**

---

## 3. Brief risk bullets (as requested for NO_TRADE)

- Live price, F&O, and breadth data are **not accessible** right now, so any trade level or setup would be unverified and potentially wrong.  
- Intraday gaps, event risk (results, macro data), and regime shifts cannot be checked without current calendars and news flow, increasing the chance of **misaligned trades**.  
- Re-run this framework only when:
  - (a) You have **live, tick-level** CMP/volume/OI data and can compute EMAs/RSI/ATR from current candles,  
  - (b) You can confirm **ASM/GSM, F&O ban, and event calendar** for each candidate, and  
  - (c) You can see **current FII/DII flows, India VIX, and advance/decline** to anchor the regime call.

---

## 4. What I can still add that’s useful to you

Even without today’s tape, I can give you:

1. **A reusable checklist** for you to run this exact framework manually on your terminal / broker / TradingView with live data.
2. **Position sizing logic and examples** that fit your capital and risk constraints, which you can plug into real prices.
3. A concise template you can fill in each evening with your own levels.

### 4.1 Position sizing with your constraints

Capital = **INR 50,000**  
Max risk per trade = **1.00%** = INR 500  
Max simultaneous positions = **3**

So for any trade:

- Max rupee risk per trade = 50,000 × 1.00% = **INR 500**
- If (Entry − Stop) = `Δ`, then max quantity = `floor(500 ÷ Δ)`

Here is your required formula:

#$#Position Size = (Capital × Risk %) ÷ (Entry − Stop-Loss)#$#

Example (you plug real prices):

- Suppose a stock trades near 420 with a logical stop at 410 → Δ = 10  
- Position Size = (50,000 × 0.01) ÷ 10 = 500 ÷ 10 = 50 shares  
- Total exposure ≈ 50 × 420 = 21,000 (within capital, risk controlled at 500)

You can compute this on any calculator or spreadsheet very quickly.

---

## 5. A compact daily template you can run with live data

Below is a **one-page skeleton** you can reuse. You’ll fill in numbers from NSE / broker terminal / TradingView, making it compliant with your own rules.

### 5.1 MARKET MOOD (fill in with live data)

- **Nifty 50**: Close ___ vs 20 EMA ___, 50 EMA ___ (Source: NSE, Time: ___ IST).  
- **Bank Nifty**: Close ___ vs 20 EMA ___, 50 EMA ___ (Source: NSE, Time: ___ IST).  
- **VIX & globals**: India VIX ___; S&P 500 close ___; Brent ___; USDINR spot ___; US10Y ___ (Sources: ___, Times: ___ IST-equivalent).  

Then derive regime: **BULLISH / NEUTRAL / BEARISH / NO_TRADE**.

---

### 5.2 TOP PICKS TABLE (you fill numbers)

| # | Stock | CMP (source/time) | setup | entry trigger | stop | T1 | T2 | R:R | quantity | score (/100) | confidence |
|---|--------|-------------------|-------|---------------|------|----|----|-----|----------|--------------|------------|
| 1 |        |                   |       |               |      |    |    |     |          |              |            |
| 2 |        |                   |       |               |      |    |    |     |          |              |            |
| 3 |        |                   |       |               |      |    |    |     |          |              |            |

Use the position sizing formula for each row; ensure R:R ≥ 1:2 to T1.

---

### 5.3 PER-FINALIST NOTES

- **STOCK1**:  
  - Bull: e.g., “Strong uptrend above 20/50 EMA with volume > 2× 20-day avg; fresh breakout from consolidation.”  
  - Bear: e.g., “Failed breakout risk if closes back below breakout level; event/gap risk around upcoming results.”

(Repeat for 2–3 names.)

---

### 5.4 INTRADAY FACT TABLE (you fill PDH/PDL etc.)

For each symbol:

| Stock | PDH | PDL | Pivot | R1 | S1 | Source/Time |
|-------|-----|-----|-------|----|----|-------------|
|       |     |     |       |    |    |             |

You can compute Pivot/R1/S1 via standard formulas from PDH/PDL/Close, or use your charting platform.

---

### 5.5 AVOID LIST

Bullet list, e.g.:

- STOCKA: ASM list / F&O ban (Source: NSE, Time: ___ IST).  
- STOCKB: Too illiquid; 20-day avg traded value < INR 50 crore.  
- STOCKC: Key results in next 2 sessions → elevated gap risk.  

---

### 5.6 EXIT RULES (concise, reusable)

- Hard stop-loss at the specified level; **no averaging down**.  
- After T1 is hit, **book 50%** and move stop to entry (cost).  
- Exit the remaining position at **day-3 close** if neither T2 nor SL hits.  

---

## 6. Safety & integrity reminder

- This is **educational analysis only**, not SEBI-registered investment advice.  
- No profits or outcomes are guaranteed; markets involve risk of capital loss.  
- Always verify all prices, volumes, F&O data, and corporate events with a **live broker quote and official exchange sources** before acting.  
- Do not trade based on stale or unverified levels; re-run your checks with **current** data each time.

Once you have access to live NSE/BSE, Yahoo Finance, and news data on your side, you can plug numbers into this template and your process will be fully aligned with the framework you specified.