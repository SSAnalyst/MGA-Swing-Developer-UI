I’m not able to access live NSE/BSE, Yahoo Finance, or news data from this environment right now, so I cannot safely verify any current prices, indicators, volumes, or events as of today. That makes it impossible to meet your core constraints:

- Every numeric point must have a verifiable source + IST timestamp.
- Hot universe, F&O ban list, ASM/GSM status, pledges, events, and intraday pivots all need current data.
- Regime classification (BULLISH / NEUTRAL / BEARISH / NO_TRADE) must be based on fresh index levels, VIX, flows, and global cues.

Providing a swing report without those checks would force me either to fabricate or to reuse stale historical levels, which violates your “no guessing / no fabrication” rule.

Given that, the only fully honest regime output I can give is:

**NO_TRADE**

**Why (brief):**
- Live index levels (NIFTY50, BANKNIFTY), India VIX, and flows cannot be confirmed now with a timestamped source.
- I cannot verify F&O ban list, ASM/GSM status, or event calendars for the next three sessions, so any candidate list would be structurally unsafe.
- Intraday PDH/PDL/pivots, ATR14, EMA alignment, and derivatives stats all require up-to-date OHLC data, which I cannot fetch.

**Key risk factors (structural, not market-specific):**
- Acting on an analysis that lacks verified live levels (index, stock CMP, ATR, pivots) can lead to wrong position sizing and invalid R:R.
- Missing F&O ban / ASM / GSM / results calendar checks substantially increases gap risk and liquidity risk.
- Without current OI and IV/HV, any derivatives-based edge (or risk) is opaque.

**Conditions to re-run and potentially allow trades:**
- You (or a separate data tool) can provide a fresh end-of-day snapshot (csv / screenshots / table) with:  
  - NIFTY50, BANKNIFTY, India VIX, FII/DII cash flows, and key global cues (US indices, Brent, USDINR, US10Y).  
  - A list of 15–30 liquid names you care about (with CMP, 20-day avg value, market cap, sector).
- Access to any one live, queryable data source (NSE/BSE, Yahoo Finance, broker API, or a local file you upload) so I can compute:  
  EMAs, RSI, ATR, volume vs average, PDH/PDL, pivots, and basic valuation ratios.
- A short confirmation that you will do the final live-price sanity check with your broker before acting.

**What I can still do usefully, if you wish:**
- Draft a reusable *template* of the exact report structure you want (including tables, position sizing math, and scoring framework) so you can plug in live data yourself each day.
- Provide a generic, data-agnostic rule-set for your Stage A/B/C process, including:  
  - How to gate trades by regime and VIX.  
  - How to filter a hot universe using simple screeners (CMP, value, liquidity, pledges, events).  
  - How to compute and use the scoring grid and position sizing formula:

#$#Position Size = (Capital × Risk %) ÷ (Entry − Stop-Loss)#$#

- Help you design a small spreadsheet / pseudo-code that you (or your desk) can connect to live feeds to auto-generate this report daily.

All levels, pivots, and stock-specific setups must be cross-checked with **live broker quotes** and official NSE/BSE data before any order is considered. This is educational process design only, not SEBI-registered investment advice.