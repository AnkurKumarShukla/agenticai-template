from mcp.server.fastmcp import FastMCP
import httpx
import os

# TAAPI_SECRET = os.getenv("TAAPI_SECRET")  # store securely in .env

from dotenv import load_dotenv , find_dotenv
load_dotenv(find_dotenv())
TAAPI_SECRET = os.getenv("TAAPI_KEY")
mcp = FastMCP("Financial MCP Server")

@mcp.tool()
async def pivotpoints(
    symbol: str = "BTC/USDT",
    interval: str = "1d",
    exchange: str = "binance",
    backtrack: int = 0,
    chart: str = "candles",
    addResultTimestamp: bool = False,
    fromTimestamp: str = None,
    toTimestamp: str = None,
    gaps: bool = True,
    results: str = "1"
) -> dict:
    """
    Calculate traditional pivot points (support and resistance levels) for a given token.
    
    Recommended intervals: 1d or 1w for useful daily/weekly levels.
    Matches the "Pivot Points Standard" on TradingView.

    API Parameters:
    ----------------
    secret: Required String
        Your TAAPI.IO API key (set in TAAPI_SECRET env variable).
    exchange: Required String
        The exchange to fetch data from (e.g., binance, binancefutures).
    symbol: Required String
        Token symbol in uppercase with market, e.g., BTC/USDT, LTC/BTC.
    interval: Required String
        Timeframe: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 12h, 1d, 1w.
    backtrack: Optional Integer
        Number of candles to look back. Default 0 (last closed candle).
    chart: Optional String
        Type of candle: "candles" (default) or "heikinashi".
    addResultTimestamp: Optional Boolean
        Include timestamp with results. Default False.
    fromTimestamp: Optional String
        Unix epoch start time to fetch historical values.
    toTimestamp: Optional String
        Unix epoch end time.
    gaps: Optional Boolean
        Fill missing candles with 0 volume and last close. Default True.
    results: Optional String
        Number of historical results to return. Default 1.

    Returns:
    ----------------
    dict containing pivot point levels:
        r3, r2, r1, p (pivot), s1, s2, s3
    """
      # store securely in .env
    BASE_URL = "https://api.taapi.io/pivotpoints"
    params = {
        "secret": TAAPI_SECRET,
        "exchange": exchange,
        "symbol": symbol,
        "interval": interval,
        "backtrack": backtrack,
        "chart": chart,
        "addResultTimestamp": addResultTimestamp,
        "gaps": gaps,
        "results": results
    }
    if fromTimestamp:
        params["fromTimestamp"] = fromTimestamp
    if toTimestamp:
        params["toTimestamp"] = toTimestamp

    async with httpx.AsyncClient() as client:
        r = await client.get(BASE_URL, params=params)
        r.raise_for_status()
        data = r.json()

    return {
        "symbol": symbol,
        "interval": interval,
        "pivot_points": data
    }

@mcp.tool()
async def engulfing(symbol: str = "BTC/USDT", interval: str = "1h", exchange: str = "binance") -> dict:
    """
    Detects the Engulfing candlestick pattern on a specified cryptocurrency pair.
    
    Engulfing patterns are reversal patterns that can be bullish or bearish.
    This tool queries the TAAPI.io endpoint for Engulfing pattern detection.

    API Parameters:
    ---------------
    secret : str
        Required. Your TAAPI.io API secret key.
    exchange : str
        Required. The exchange to calculate the indicator from. Supported: binance, binancefutures, etc.
    symbol : str
        Required. The trading pair symbol (uppercase, COIN/MARKET format), e.g., BTC/USDT.
    interval : str
        Required. The timeframe for candle data. Supported values: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 12h, 1d, 1w.

    Returns:
    --------
    dict : 
        {
            "symbol": str,
            "interval": str,
            "engulfing_value": int
        }

        - "engulfing_value": 
            100 -> bullish engulfing pattern found
            -100 -> bearish engulfing pattern found
            0 -> pattern not found
    """
    BASE_URL = "https://api.taapi.io/engulfing"
    params = {
        "secret": TAAPI_SECRET,
        "exchange": exchange,
        "symbol": symbol,
        "interval": interval
    }
    
    async with httpx.AsyncClient() as client:
        r = await client.get(BASE_URL, params=params)
        r.raise_for_status()
        data = r.json()
    pattrn_type = ""
    if data.get("value", 0) == 100:
        pattrn_type = "Bullish Engulfing"
    elif data.get("value", 0) == -100:
        pattrn_type = "Bearish Engulfing"
    else:
        pattrn_type = "No Engulfing Pattern detected"
    return {
        "symbol": symbol,
        "interval": interval,
        "pattern_type": pattrn_type,
    }


@mcp.tool()
async def three_white_soldiers(
    symbol: str = "BTC/USDT",
    interval: str = "1h",
    exchange: str = "binance",
    backtrack: int = 0,
    chart: str = "candles",
    addResultTimestamp: bool = False,
    fromTimestamp: int | None = None,
    toTimestamp: int | None = None,
    gaps: bool = True,
    results: str | int = 1
) -> dict:
    """
    Detects the Three Advancing White Soldiers candlestick pattern on a specified cryptocurrency pair.

    This is a bullish reversal pattern consisting of three consecutive long-bodied candlesticks that 
    open within the real body of the previous candle and close above its high. Useful to anticipate 
    reversals in a downtrend.

    API Parameters:
    ---------------
    secret : str
        Required. Your TAAPI.io API secret key.
    exchange : str
        Required. Exchange to calculate the indicator from (e.g., binance, binancefutures).
    symbol : str
        Required. Trading pair symbol (uppercase, COIN/MARKET), e.g., BTC/USDT.
    interval : str
        Required. Timeframe for candle data (1m, 5m, 15m, 30m, 1h, 2h, 4h, 12h, 1d, 1w).
    backtrack : int, optional
        Fetch pattern value X candles back. Default is 0 (current candle).
    chart : str, optional
        "candles" (default) or "heikinashi" for Heikin Ashi candles (Pro/Expert plans only).
    addResultTimestamp : bool, optional
        Return timestamp with each result. Default False.
    fromTimestamp : int, optional
        Unix epoch time to start fetching historical values.
    toTimestamp : int, optional
        Unix epoch time to end fetching historical values.
    gaps : bool, optional
        Fill gaps in thin markets. Default True.
    results : int or str, optional
        Number of historical candle values to fetch. Use "max" for all available. Default 1.

    Returns:
    --------
    dict :
        {
            "symbol": str,
            "interval": str,
            "three_white_soldiers": int | list[int]
        }

        - Value meanings:
            100 -> bullish pattern found
            -100 -> bearish variation found (if applicable)
            0 -> pattern not found
            list -> multiple historical candle values if results > 1
    """
    BASE_URL = "https://api.taapi.io/threewhitesoldiers"
    params = {
        "secret": TAAPI_SECRET,
        "exchange": exchange,
        "symbol": symbol,
        "interval": interval,
        "backtrack": backtrack,
        "chart": chart,
        "addResultTimestamp": str(addResultTimestamp).lower(),
        "gaps": str(gaps).lower(),
        "results": results
    }

    if fromTimestamp:
        params["fromTimestamp"] = fromTimestamp
    if toTimestamp:
        params["toTimestamp"] = toTimestamp

    async with httpx.AsyncClient() as client:
        r = await client.get(BASE_URL, params=params)
        r.raise_for_status()
        data = r.json()
    pattern_type = ""
    if data.get("value", 0) == 100:
        pattern_type = "Three Advancing White Soldiers pattern found"
    elif data.get("value", 0) == -100:
        pattern_type = "Bearish variation of Three White Soldiers found"
    else:
        pattern_type = "No Three White Soldiers pattern detected"

    return {
        "symbol": symbol,
        "interval": interval,
        "pattern_type": pattern_type,
    }

@mcp.tool()
async def morningstar(
    symbol: str = "BTC/USDT",
    interval: str = "1h",
    exchange: str = "binance",
    backtrack: int = 0,
    chart: str = "candles",
    addResultTimestamp: bool = False,
    fromTimestamp: int | None = None,
    toTimestamp: int | None = None,
    gaps: bool = True,
    results: str | int = 10,
    optInPenetration: float = 0.3
) -> dict:
    """
    Detects the Morning Star candlestick pattern on a given symbol and timeframe.

    The Morning Star is a bullish reversal pattern formed by:
    - A long bearish candle
    - A small indecisive candle (doji or small body)
    - A strong bullish candle closing well into the body of the first bearish candle

    Useful to anticipate a potential trend reversal from bearish to bullish.

    API Parameters:
    ---------------
    secret : str
        Required. Your TAAPI.io API secret key.
    exchange : str
        Required. Exchange to calculate the indicator from (e.g., binance, binancefutures).
    symbol : str
        Required. Trading pair symbol (uppercase, COIN/MARKET), e.g., BTC/USDT.
    interval : str
        Required. Timeframe for candle data (1m, 5m, 15m, 30m, 1h, 2h, 4h, 12h, 1d, 1w).
    backtrack : int, optional
        Fetch pattern value X candles back. Default is 0 (current candle).
    chart : str, optional
        "candles" (default) or "heikinashi" for Heikin Ashi candles (Pro/Expert plans only).
    addResultTimestamp : bool, optional
        Return timestamp with each result. Default False.
    fromTimestamp : int, optional
        Unix epoch time to start fetching historical values.
    toTimestamp : int, optional
        Unix epoch time to end fetching historical values.
    gaps : bool, optional
        Fill gaps in thin markets. Default True.
    results : int or str, optional
        Number of historical candle values to fetch. Use "max" for all available. Default 1.
    optInPenetration : float, optional
        Default 0.3. Controls penetration factor used in pattern recognition.

    Returns:
    --------
    dict :
        {
            "symbol": str,
            "interval": str,
            "morningstar": int | list[int]
        }

        - Value meanings:
            100 -> bullish Morning Star pattern found
            -100 -> bearish variation found (if applicable)
            0 -> pattern not found
            list -> multiple historical candle values if results > 1
    """
    params = {
        "secret": TAAPI_SECRET,
        "exchange": exchange,
        "symbol": symbol,
        "interval": interval,
        "backtrack": backtrack,
        "chart": chart,
        "addResultTimestamp": str(addResultTimestamp).lower(),
        "gaps": str(gaps).lower(),
        "results": results,
        "optInPenetration": optInPenetration
    }
    BASE_URL = "https://api.taapi.io/morningstar"
    if fromTimestamp:
        params["fromTimestamp"] = fromTimestamp
    if toTimestamp:
        params["toTimestamp"] = toTimestamp

    async with httpx.AsyncClient() as client:
        r = await client.get(BASE_URL, params=params)
        r.raise_for_status()
        data = r.json()

    return {
        "symbol": symbol,
        "interval": interval,
        "morningstar": data
    }

if __name__ == "__main__":
    print("[SERVER] Starting Financial MCP...", flush=True)
    mcp.run()