# File: backend_api.py

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Advanced Stock Market Analytics API",
    description="Backend API for stock market analysis with real database integration",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_supabase_client() -> Client:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured")
    
    return create_client(supabase_url, supabase_key)

# Pydantic models for API responses
class StockPrice(BaseModel):
    datetime: datetime
    ticker: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    timeframe: str # <--- DITAMBAHKAN KEMBALI

class CompanyInfo(BaseModel):
    ticker: str
    address1: Optional[str] = None
    sector: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    longname: Optional[str] = None
    longbusinesssummary: Optional[str] = None # <--- TYPO DIKOREKSI

class CompanyFinance(BaseModel):
    ticker: str
    marketcap: Optional[float] = None
    shareoutstanding: Optional[float] = None
    totalrevenue: Optional[float] = None
    netincometocommon: Optional[float] = None
    profitmargins: Optional[float] = None
    trailingeps: Optional[float] = None
    grossmargins: Optional[float] = None
    operatingmargins: Optional[float] = None
    operatingcashflow: Optional[float] = None
    freecashflow: Optional[float] = None

class CompanyValuation(BaseModel):
    ticker: str
    trailingpe: Optional[float] = None
    forwardpe: Optional[float] = None
    pricetobook: Optional[float] = None
    pricetosalestrailing12months: Optional[float] = None
    bookvalue: Optional[float] = None
    stockholders_equity: Optional[float] = None

class CompanyDividend(BaseModel):
    ticker: str
    dividendrate: Optional[float] = None
    dividendyield: Optional[float] = None
    exdividenddate: Optional[str] = None
    payoutratio: Optional[float] = None

class CompanyGrowth(BaseModel):
    ticker: str
    revenuegrowth: Optional[float] = None
    earningsgrowth: Optional[float] = None
    earningsquarterlygrowth: Optional[float] = None

class CompanyProfitabilities(BaseModel):
    ticker: str
    returnonequity: Optional[float] = None
    returnonassets: Optional[float] = None

class CompanyLiquidity(BaseModel):
    ticker: str
    totalcash: Optional[float] = None
    totaldebt: Optional[float] = None
    debttoequity: Optional[float] = None
    currentratio: Optional[float] = None

# API Endpoints

@app.get("/")
async def root():
    return {
        "message": "Stock Market Analytics API",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

# Stock Price endpoints
@app.get("/stock-prices/", response_model=List[StockPrice])
async def get_stock_prices(
    ticker: Optional[str] = None,
    timeframe: Optional[str] = Query("1d", description="Timeframe of the stock price data (e.g., '1d', '1wk', '1mo')"), # <--- DITAMBAHKAN KEMBALI
    limit: int = 100,
    offset: int = 0,
    supabase: Client = Depends(get_supabase_client)
):
    """Get stock prices with optional filtering"""
    query = supabase.table("stock_prices").select("*")
    
    if ticker:
        query = query.eq("ticker", ticker)
    if timeframe: # <--- FILTER DITAMBAHKAN
        query = query.eq("timeframe", timeframe)
    
    query = query.order("datetime", desc=True).limit(limit).offset(offset)
    
    response = query.execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    return response.data

@app.get("/stock-prices/{ticker}", response_model=List[StockPrice])
async def get_stock_price_by_ticker(
    ticker: str,
    timeframe: Optional[str] = Query("1d", description="Timeframe of the stock price data (e.g., '1d', '1wk', '1mo')"), # <--- DITAMBAHKAN KEMBALI
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    supabase: Client = Depends(get_supabase_client)
):
    """Get stock prices for a specific ticker"""
    query = supabase.table("stock_prices").select("*").eq("ticker", ticker)
    
    if timeframe: # <--- FILTER DITAMBAHKAN
        query = query.eq("timeframe", timeframe)
    
    if start_date:
        query = query.gte("datetime", start_date)
    
    if end_date:
        query = query.lte("datetime", end_date)
    
    query = query.order("datetime", desc=True).limit(limit)
    
    response = query.execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"No stock prices found for ticker {ticker}")
    
    return response.data

# --- Bagian lain dari API tetap sama ---
# Company Info endpoints
@app.get("/company-info/", response_model=List[CompanyInfo])
async def get_all_company_info(
    sector: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    supabase: Client = Depends(get_supabase_client)
):
    """Get all company information with optional sector filtering"""
    query = supabase.table("company_info").select("*")
    
    if sector:
        query = query.eq("sector", sector)
    
    query = query.limit(limit).offset(offset)
    
    response = query.execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    return response.data

@app.get("/company-info/{ticker}", response_model=CompanyInfo)
async def get_company_info_by_ticker(
    ticker: str,
    supabase: Client = Depends(get_supabase_client)
):
    """Get company information for a specific ticker"""
    response = supabase.table("company_info").select("*").eq("ticker", ticker).execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Company info not found for ticker {ticker}")
    
    return response.data[0]

# Company Finance endpoints
@app.get("/company-finance/{ticker}", response_model=CompanyFinance)
async def get_company_finance_by_ticker(
    ticker: str,
    supabase: Client = Depends(get_supabase_client)
):
    """Get company finance data for a specific ticker"""
    response = supabase.table("company_finance").select("*").eq("ticker", ticker).execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Company finance data not found for ticker {ticker}")
    
    return response.data[0]

# Company Valuation endpoints
@app.get("/company-valuation/{ticker}", response_model=CompanyValuation)
async def get_company_valuation_by_ticker(
    ticker: str,
    supabase: Client = Depends(get_supabase_client)
):
    """Get company valuation data for a specific ticker"""
    response = supabase.table("company_valuation").select("*").eq("ticker", ticker).execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Company valuation not found for ticker {ticker}")
    
    return response.data[0]

# Company Dividend endpoints
@app.get("/company-dividend/{ticker}", response_model=CompanyDividend)
async def get_company_dividend_by_ticker(
    ticker: str,
    supabase: Client = Depends(get_supabase_client)
):
    """Get company dividend data for a specific ticker"""
    response = supabase.table("company_dividend").select("*").eq("ticker", ticker).execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Company dividend not found for ticker {ticker}")
    
    return response.data[0]

# Company Growth endpoints
@app.get("/company-growth/{ticker}", response_model=CompanyGrowth)
async def get_company_growth_by_ticker(
    ticker: str,
    supabase: Client = Depends(get_supabase_client)
):
    """Get company growth data for a specific ticker"""
    response = supabase.table("company_growth").select("*").eq("ticker", ticker).execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Company growth data not found for ticker {ticker}")
    
    return response.data[0]

# Company Profitabilities endpoints
@app.get("/company-profitabilities/{ticker}", response_model=CompanyProfitabilities)
async def get_company_profitabilities_by_ticker(
    ticker: str,
    supabase: Client = Depends(get_supabase_client)
):
    """Get company profitabilities data for a specific ticker"""
    response = supabase.table("company_profitabilities").select("*").eq("ticker", ticker).execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Company profitabilities not found for ticker {ticker}")
    
    return response.data[0]

# Company Liquidity endpoints
@app.get("/company-liquidity/{ticker}", response_model=CompanyLiquidity)
async def get_company_liquidity_by_ticker(
    ticker: str,
    supabase: Client = Depends(get_supabase_client)
):
    """Get company liquidity data for a specific ticker"""
    response = supabase.table("company_liquidity").select("*").eq("ticker", ticker).execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Company liquidity not found for ticker {ticker}")
    
    return response.data[0]

# Comprehensive company data endpoint
@app.get("/company/{ticker}")
async def get_comprehensive_company_data(
    ticker: str,
    supabase: Client = Depends(get_supabase_client)
):
    """Get comprehensive company data from all tables"""
    # Get data from each table for the specified ticker
    info_response = supabase.table("company_info").select("*").eq("ticker", ticker).execute()
    finance_response = supabase.table("company_finance").select("*").eq("ticker", ticker).execute()
    valuation_response = supabase.table("company_valuation").select("*").eq("ticker", ticker).execute()
    dividend_response = supabase.table("company_dividend").select("*").eq("ticker", ticker).execute()
    growth_response = supabase.table("company_growth").select("*").eq("ticker", ticker).execute()
    profitabilities_response = supabase.table("company_profitabilities").select("*").eq("ticker", ticker).execute()
    liquidity_response = supabase.table("company_liquidity").select("*").eq("ticker", ticker).execute()
    
    # Check for errors in any response
    responses = [info_response, finance_response, valuation_response, 
                 dividend_response, growth_response, profitabilities_response, 
                 liquidity_response]
    
    for response in responses:
        if hasattr(response, "error") and response.error:
            raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    # Combine all data into a single response
    result = {
        "ticker": ticker,
        "info": info_response.data[0] if info_response.data else None,
        "finance": finance_response.data[0] if finance_response.data else None,
        "valuation": valuation_response.data[0] if valuation_response.data else None,
        "dividend": dividend_response.data[0] if dividend_response.data else None,
        "growth": growth_response.data[0] if growth_response.data else None,
        "profitabilities": profitabilities_response.data[0] if profitabilities_response.data else None,
        "liquidity": liquidity_response.data[0] if liquidity_response.data else None
    }
    
    return result

# Stock screener endpoint (tidak ada perubahan signifikan yang diminta di sini)
@app.get("/stock-screener", response_model=List[Dict[str, Any]])
async def stock_screener(
    sector: Optional[str] = Query(None, description="Filter by sector (e.g., 'Technology')"),
    min_market_cap: Optional[float] = Query(None, gt=0, description="Minimum Market Capitalization"),
    max_market_cap: Optional[float] = Query(None, gt=0, description="Maximum Market Capitalization"),
    
    # Valuation Filters
    max_trailing_pe: Optional[float] = Query(None, gt=0, description="Maximum Trailing P/E Ratio"),
    max_forward_pe: Optional[float] = Query(None, gt=0, description="Maximum Forward P/E Ratio"),
    max_pb: Optional[float] = Query(None, gt=0, description="Maximum Price-to-Book Ratio"),
    max_ps: Optional[float] = Query(None, gt=0, description="Maximum Price-to-Sales Ratio"),
    
    # Dividend Filters
    min_dividend_yield: Optional[float] = Query(None, ge=0, description="Minimum Dividend Yield (e.g., 0.02 for 2%)"),
    max_payout_ratio: Optional[float] = Query(None, ge=0, description="Maximum Dividend Payout Ratio (e.g., 0.6 for 60%)"),
    
    # Profitability Filters
    min_profit_margins: Optional[float] = Query(None, description="Minimum Net Profit Margins (e.g., 0.1 for 10%)"),
    min_gross_margins: Optional[float] = Query(None, description="Minimum Gross Margins (e.g., 0.2 for 20%)"),
    min_operating_margins: Optional[float] = Query(None, description="Minimum Operating Margins (e.g., 0.15 for 15%)"),
    min_roe: Optional[float] = Query(None, description="Minimum Return on Equity (e.g., 0.15 for 15%)"),
    min_roa: Optional[float] = Query(None, description="Minimum Return on Assets (e.g., 0.05 for 5%)"),

    # Growth Filters
    min_revenue_growth: Optional[float] = Query(None, description="Minimum Annual Revenue Growth (e.g., 0.1 for 10%)"),
    min_earnings_growth: Optional[float] = Query(None, description="Minimum Annual Earnings Growth (e.g., 0.05 for 5%)"),
    min_earnings_quarterly_growth: Optional[float] = Query(None, description="Minimum Quarterly Earnings Growth (e.g., 0.02 for 2%)"),
    
    # Liquidity & Debt Filters
    min_current_ratio: Optional[float] = Query(None, gt=0, description="Minimum Current Ratio (e.g., 1.5)"),
    max_debt_to_equity: Optional[float] = Query(None, ge=0, description="Maximum Debt-to-Equity Ratio (e.g., 1.0)"),
    
    min_trailing_eps: Optional[float] = Query(None, description="Minimum Trailing EPS"),
    
    limit: int = 50,
    offset: int = 0, # Added offset for pagination
    supabase: Client = Depends(get_supabase_client)
):
    """
    Screen stocks based on various financial criteria.
    Combines data from multiple tables for comprehensive filtering.
    """
    
    # Step 1: Get a base list of companies based on sector filter (if any)
    # and select the required fields (ticker, longname, sector)
    company_info_query = supabase.table("company_info").select("ticker, longname, sector")
    if sector:
        company_info_query = company_info_query.eq("sector", sector)
    
    company_info_response = company_info_query.execute()
    
    if hasattr(company_info_response, "error") and company_info_response.error:
        raise HTTPException(status_code=500, detail=f"Database error fetching company info: {company_info_response.error}")
    
    if not company_info_response.data:
        return []
    
    # Create a map for company info for quick lookup
    company_info_map = {item["ticker"]: item for item in company_info_response.data}
    all_tickers = list(company_info_map.keys())

    if not all_tickers:
        return []

    # Step 2: Fetch all relevant data for all tickers in *one batch*
    # This is much more efficient than fetching data ticker by ticker in a loop.
    
    def fetch_table_data(table_name: str, tickers: List[str]):
        response = supabase.table(table_name).select("*").in_("ticker", tickers).execute()
        if hasattr(response, "error") and response.error:
            raise HTTPException(status_code=500, detail=f"Database error fetching {table_name}: {response.error}")
        return {item["ticker"]: item for item in response.data}

    finance_map = fetch_table_data("company_finance", all_tickers)
    valuation_map = fetch_table_data("company_valuation", all_tickers)
    dividend_map = fetch_table_data("company_dividend", all_tickers)
    growth_map = fetch_table_data("company_growth", all_tickers)
    profitabilities_map = fetch_table_data("company_profitabilities", all_tickers)
    liquidity_map = fetch_table_data("company_liquidity", all_tickers)

    # Step 3: Apply all filters to the collected data
    filtered_stocks = []
    
    for ticker in all_tickers:
        info_data = company_info_map.get(ticker, {})
        finance_data = finance_map.get(ticker, {})
        valuation_data = valuation_map.get(ticker, {})
        dividend_data = dividend_map.get(ticker, {})
        growth_data = growth_map.get(ticker, {})
        profitabilities_data = profitabilities_map.get(ticker, {})
        liquidity_data = liquidity_map.get(ticker, {})

        # Apply Market Cap filters
        if min_market_cap is not None and (not finance_data.get("marketcap") or finance_data["marketcap"] < min_market_cap):
            continue
        if max_market_cap is not None and (not finance_data.get("marketcap") or finance_data["marketcap"] > max_market_cap):
            continue

        # Apply Valuation Filters
        if max_trailing_pe is not None and (not valuation_data.get("trailingpe") or valuation_data["trailingpe"] > max_trailing_pe):
            continue
        if max_forward_pe is not None and (not valuation_data.get("forwardpe") or valuation_data["forwardpe"] > max_forward_pe):
            continue
        if max_pb is not None and (not valuation_data.get("pricetobook") or valuation_data["pricetobook"] > max_pb):
            continue
        if max_ps is not None and (not valuation_data.get("pricetosalestrailing12months") or valuation_data["pricetosalestrailing12months"] > max_ps):
            continue

        # Apply Dividend Filters
        if min_dividend_yield is not None and (not dividend_data.get("dividendyield") or dividend_data["dividendyield"] < min_dividend_yield):
            continue
        if max_payout_ratio is not None and (not dividend_data.get("payoutratio") or dividend_data["payoutratio"] > max_payout_ratio):
            continue

        # Apply Profitability Filters
        if min_profit_margins is not None and (not finance_data.get("profitmargins") or finance_data["profitmargins"] < min_profit_margins):
            continue
        if min_gross_margins is not None and (not finance_data.get("grossmargins") or finance_data["grossmargins"] < min_gross_margins):
            continue
        if min_operating_margins is not None and (not finance_data.get("operatingmargins") or finance_data["operatingmargins"] < min_operating_margins):
            continue
        if min_roe is not None and (not profitabilities_data.get("returnonequity") or profitabilities_data["returnonequity"] < min_roe):
            continue
        if min_roa is not None and (not profitabilities_data.get("returnonassets") or profitabilities_data["returnonassets"] < min_roa):
            continue

        # Apply Growth Filters
        if min_revenue_growth is not None and (not growth_data.get("revenuegrowth") or growth_data["revenuegrowth"] < min_revenue_growth):
            continue
        if min_earnings_growth is not None and (not growth_data.get("earningsgrowth") or growth_data["earningsgrowth"] < min_earnings_growth):
            continue
        if min_earnings_quarterly_growth is not None and (not growth_data.get("earningsquarterlygrowth") or growth_data["earningsquarterlygrowth"] < min_earnings_quarterly_growth):
            continue
        
        # Apply Liquidity & Debt Filters
        if min_current_ratio is not None and (not liquidity_data.get("currentratio") or liquidity_data["currentratio"] < min_current_ratio):
            continue
        if max_debt_to_equity is not None and (not liquidity_data.get("debttoequity") or liquidity_data["debttoequity"] > max_debt_to_equity):
            continue
        
        # Apply EPS Filter
        if min_trailing_eps is not None and (not finance_data.get("trailingeps") or finance_data["trailingeps"] < min_trailing_eps):
            continue

        # If all filters passed, add to results
        filtered_stocks.append({
            "ticker": ticker,
            "name": info_data.get("longname"),
            "sector": info_data.get("sector"),
            "marketcap": finance_data.get("marketcap"),
            "trailingpe": valuation_data.get("trailingpe"),
            "forwardpe": valuation_data.get("forwardpe"),
            "pricetobook": valuation_data.get("pricetobook"),
            "pricetosalestrailing12months": valuation_data.get("pricetosalestrailing12months"),
            "dividendyield": dividend_data.get("dividendyield"),
            "payoutratio": dividend_data.get("payoutratio"),
            "profitmargins": finance_data.get("profitmargins"),
            "grossmargins": finance_data.get("grossmargins"),
            "operatingmargins": finance_data.get("operatingmargins"),
            "returnonequity": profitabilities_data.get("returnonequity"),
            "returnonassets": profitabilities_data.get("returnonassets"),
            "revenuegrowth": growth_data.get("revenuegrowth"),
            "earningsgrowth": growth_data.get("earningsgrowth"),
            "earningsquarterlygrowth": growth_data.get("earningsquarterlygrowth"),
            "currentratio": liquidity_data.get("currentratio"),
            "debttoequity": liquidity_data.get("debttoequity"),
            "trailingeps": finance_data.get("trailingeps"),
        })
    
    # Step 4: Sort and paginate the results
    # Sort by market cap (descending) as a default useful sort
    filtered_stocks.sort(key=lambda x: x.get("marketcap") or 0, reverse=True)
    
    # Apply offset and limit for pagination
    return filtered_stocks[offset:offset + limit]