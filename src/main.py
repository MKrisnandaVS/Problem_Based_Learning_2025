from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List, Optional
from pydantic import BaseModel
import pandas as pd
import os
from datetime import datetime
from supabase import create_client, Client
import math
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Stock Market Analytics API",
    description="API for accessing stock market data and company financial information",
    version="1.0.0"
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client setup
def get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured")
    
    return create_client(supabase_url, supabase_key)

# Pydantic models for data validation and response serialization
class StockPrice(BaseModel):
    datetime: datetime
    ticker: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    timeframe: Optional[str] = None

class CompanyInfo(BaseModel):
    ticker: str
    address1: Optional[str] = None
    sector: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    longname: Optional[str] = None
    longbusinesssummary: Optional[str] = None

class CompanyFinance(BaseModel):
    ticker: str
    marketcap: Optional[float] = None
    shareoutstanding: Optional[float] = None
    totalrevenue: Optional[float] = None
    netincometocommon: Optional[float] = None
    profitmargins: Optional[float] = None
    trailingeps: Optional[float] = None
    forwardeps: Optional[float] = None
    grossmargins: Optional[float] = None
    operatingmargins: Optional[float] = None
    operatingcashflow: Optional[float] = None
    freecashflow: Optional[float] = None

class CompanyValuation(BaseModel):
    ticker: str
    trailingpe: Optional[float] = None
    forwardpe: Optional[float] = None
    pegratio: Optional[float] = None
    pricetobook: Optional[float] = None
    pricetosalestrailing12months: Optional[float] = None

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

# Root endpoint with API documentation link
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Stock Market API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #333; }
                a { color: #0066cc; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>Stock Market Analytics API</h1>
            <p>Welcome to the Stock Market Analytics API. Access financial data and company information.</p>
            <p><a href="/docs">API Documentation</a> - Interactive API documentation and testing</p>
            <p><a href="/redoc">ReDoc Documentation</a> - Alternative API documentation</p>
        </body>
    </html>
    """

# Stock Price endpoints
@app.get("/stock-prices/", response_model=List[StockPrice])
async def get_stock_prices(
    ticker: Optional[str] = None,
    timeframe: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    supabase: Client = Depends(get_supabase_client)
):
    query = supabase.table("stock_prices").select("*")
    
    if ticker:
        query = query.eq("ticker", ticker)
    if timeframe:
        query = query.eq("timeframe", timeframe)
    
    query = query.order("datetime", desc=True).limit(limit).offset(offset)
    
    response = query.execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    return response.data

@app.get("/stock-prices/{ticker}", response_model=List[StockPrice])
async def get_stock_price_by_ticker(
    ticker: str,
    timeframe: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    supabase: Client = Depends(get_supabase_client)
):
    query = supabase.table("stock_prices").select("*").eq("ticker", ticker)
    
    if timeframe:
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

# Company Info endpoints
@app.get("/company-info/", response_model=List[CompanyInfo])
async def get_all_company_info(
    sector: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    supabase: Client = Depends(get_supabase_client)
):
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
    response = supabase.table("company_info").select("*").eq("ticker", ticker).execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Company info not found for ticker {ticker}")
    
    return response.data[0]

# Company Finance endpoints
@app.get("/company-finance/", response_model=List[CompanyFinance])
async def get_all_company_finance(
    min_market_cap: Optional[float] = None,
    limit: int = 100,
    offset: int = 0,
    supabase: Client = Depends(get_supabase_client)
):
    query = supabase.table("company_finance").select("*")
    
    if min_market_cap:
        query = query.gte("marketcap", min_market_cap)
    
    query = query.limit(limit).offset(offset)
    
    response = query.execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    return response.data

@app.get("/company-finance/{ticker}", response_model=CompanyFinance)
async def get_company_finance_by_ticker(
    ticker: str,
    supabase: Client = Depends(get_supabase_client)
):
    response = supabase.table("company_finance").select("*").eq("ticker", ticker).execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Company finance data not found for ticker {ticker}")
    
    return response.data[0]

# Company Valuation endpoints
@app.get("/company-valuation/", response_model=List[CompanyValuation])
async def get_all_company_valuation(
    max_pe: Optional[float] = None,
    limit: int = 100,
    offset: int = 0,
    supabase: Client = Depends(get_supabase_client)
):
    query = supabase.table("company_valuation").select("*")
    
    if max_pe:
        query = query.lte("trailingpe", max_pe)
    
    query = query.limit(limit).offset(offset)
    
    response = query.execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    return response.data

@app.get("/company-valuation/{ticker}", response_model=CompanyValuation)
async def get_company_valuation_by_ticker(
    ticker: str,
    supabase: Client = Depends(get_supabase_client)
):
    response = supabase.table("company_valuation").select("*").eq("ticker", ticker).execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Company valuation not found for ticker {ticker}")
    
    return response.data[0]

# Company Dividend endpoints
@app.get("/company-dividend/", response_model=List[CompanyDividend])
async def get_all_company_dividend(
    min_yield: Optional[float] = None,
    limit: int = 100,
    offset: int = 0,
    supabase: Client = Depends(get_supabase_client)
):
    query = supabase.table("company_dividend").select("*")
    
    if min_yield:
        query = query.gte("dividendyield", min_yield)
    
    query = query.limit(limit).offset(offset)
    
    response = query.execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    return response.data

@app.get("/company-dividend/{ticker}", response_model=CompanyDividend)
async def get_company_dividend_by_ticker(
    ticker: str,
    supabase: Client = Depends(get_supabase_client)
):
    response = supabase.table("company_dividend").select("*").eq("ticker", ticker).execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Company dividend not found for ticker {ticker}")
    
    return response.data[0]

# Company Growth endpoints
@app.get("/company-growth/", response_model=List[CompanyGrowth])
async def get_all_company_growth(
    min_revenue_growth: Optional[float] = None,
    limit: int = 100,
    offset: int = 0,
    supabase: Client = Depends(get_supabase_client)
):
    query = supabase.table("company_growth").select("*")
    
    if min_revenue_growth:
        query = query.gte("revenuegrowth", min_revenue_growth)
    
    query = query.limit(limit).offset(offset)
    
    response = query.execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    return response.data

@app.get("/company-growth/{ticker}", response_model=CompanyGrowth)
async def get_company_growth_by_ticker(
    ticker: str,
    supabase: Client = Depends(get_supabase_client)
):
    response = supabase.table("company_growth").select("*").eq("ticker", ticker).execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Company growth data not found for ticker {ticker}")
    
    return response.data[0]

# Company Profitabilities endpoints
@app.get("/company-profitabilities/", response_model=List[CompanyProfitabilities])
async def get_all_company_profitabilities(
    min_roe: Optional[float] = None,
    limit: int = 100,
    offset: int = 0,
    supabase: Client = Depends(get_supabase_client)
):
    query = supabase.table("company_profitabilities").select("*")
    
    if min_roe:
        query = query.gte("returnonequity", min_roe)
    
    query = query.limit(limit).offset(offset)
    
    response = query.execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    return response.data

@app.get("/company-profitabilities/{ticker}", response_model=CompanyProfitabilities)
async def get_company_profitabilities_by_ticker(
    ticker: str,
    supabase: Client = Depends(get_supabase_client)
):
    response = supabase.table("company_profitabilities").select("*").eq("ticker", ticker).execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Company profitabilities not found for ticker {ticker}")
    
    return response.data[0]

# Company Liquidity endpoints
@app.get("/company-liquidity/", response_model=List[CompanyLiquidity])
async def get_all_company_liquidity(
    min_current_ratio: Optional[float] = None,
    limit: int = 100,
    offset: int = 0,
    supabase: Client = Depends(get_supabase_client)
):
    query = supabase.table("company_liquidity").select("*")
    
    if min_current_ratio:
        query = query.gte("currentratio", min_current_ratio)
    
    query = query.limit(limit).offset(offset)
    
    response = query.execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    return response.data

@app.get("/company-liquidity/{ticker}", response_model=CompanyLiquidity)
async def get_company_liquidity_by_ticker(
    ticker: str,
    supabase: Client = Depends(get_supabase_client)
):
    response = supabase.table("company_liquidity").select("*").eq("ticker", ticker).execute()
    
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Company liquidity not found for ticker {ticker}")
    
    return response.data[0]

# Comprehensive company data endpoint (joining all tables)
@app.get("/company/{ticker}")
async def get_comprehensive_company_data(
    ticker: str,
    supabase: Client = Depends(get_supabase_client)
):
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

# Dashboard HTML endpoint that provides a UI for the data
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stock Market Dashboard</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            .dashboard-card {
                height: 300px;
                overflow: hidden;
            }
        </style>
    </head>
    <body class="bg-gray-100">
        <div class="container mx-auto px-4 py-8">
            <header class="mb-8">
                <h1 class="text-3xl font-bold text-gray-800">Stock Market Dashboard</h1>
                <p class="text-gray-600">Financial and Stock Data Analysis</p>
            </header>
            
            <div class="mb-6">
                <label for="ticker" class="block text-sm font-medium text-gray-700">Select Ticker:</label>
                <div class="mt-1 flex">
                    <input type="text" id="ticker" placeholder="Enter ticker symbol (e.g., AAPL)" 
                           class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md">
                    <button onclick="loadData()" class="ml-3 inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
                        Load Data
                    </button>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                <!-- Company Info Card -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4 text-gray-800">Company Info</h2>
                    <div id="company-info" class="text-sm">
                        <p class="text-gray-500">Select a ticker to view company information</p>
                    </div>
                </div>
                
                <!-- Stock Price Chart Card -->
                <div class="bg-white rounded-lg shadow-md p-6 dashboard-card">
                    <h2 class="text-xl font-semibold mb-4 text-gray-800">Price History</h2>
                    <canvas id="price-chart"></canvas>
                </div>
                
                <!-- Key Financial Metrics Card -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4 text-gray-800">Key Financial Metrics</h2>
                    <div id="financial-metrics" class="text-sm">
                        <p class="text-gray-500">Select a ticker to view financial metrics</p>
                    </div>
                </div>
                
                <!-- Valuation Metrics Card -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4 text-gray-800">Valuation Metrics</h2>
                    <div id="valuation-metrics" class="text-sm">
                        <p class="text-gray-500">Select a ticker to view valuation metrics</p>
                    </div>
                </div>
                
                <!-- Growth Metrics Card -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4 text-gray-800">Growth Metrics</h2>
                    <div id="growth-metrics" class="text-sm">
                        <p class="text-gray-500">Select a ticker to view growth metrics</p>
                    </div>
                </div>
                
                <!-- Profitability & Liquidity Card -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4 text-gray-800">Profitability & Liquidity</h2>
                    <div id="profitability-liquidity" class="text-sm">
                        <p class="text-gray-500">Select a ticker to view profitability & liquidity metrics</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow-md p-6 mb-8">
                <h2 class="text-xl font-semibold mb-4 text-gray-800">Recent Price Data</h2>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Open</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">High</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Low</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Close</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Volume</th>
                            </tr>
                        </thead>
                        <tbody id="price-table-body" class="bg-white divide-y divide-gray-200">
                            <tr>
                                <td colspan="6" class="px-6 py-4 text-sm text-gray-500 text-center">Select a ticker to view price data</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
            let priceChart = null;
            
            async function loadData() {
                const ticker = document.getElementById('ticker').value.trim().toUpperCase();
                if (!ticker) {
                    alert('Please enter a ticker symbol');
                    return;
                }
                
                try {
                    // Load comprehensive company data
                    const companyResponse = await fetch(`/company/${ticker}`);
                    if (!companyResponse.ok) {
                        throw new Error(`Error fetching company data: ${companyResponse.statusText}`);
                    }
                    const companyData = await companyResponse.json();
                    
                    // Load stock price data
                    const priceResponse = await fetch(`/stock-prices/${ticker}?limit=30&timeframe=1d`);
                    if (!priceResponse.ok) {
                        throw new Error(`Error fetching price data: ${priceResponse.statusText}`);
                    }
                    const priceData = await priceResponse.json();
                    
                    // Update UI with the data
                    updateCompanyInfo(companyData.info);
                    updateFinancialMetrics(companyData.finance);
                    updateValuationMetrics(companyData.valuation);
                    updateGrowthMetrics(companyData.growth);
                    updateProfitabilityLiquidity(companyData.profitabilities, companyData.liquidity);
                    updatePriceTable(priceData);
                    updatePriceChart(priceData);
                    
                } catch (error) {
                    console.error('Error loading data:', error);
                    alert(`Error loading data: ${error.message}`);
                }
            }
            
            function updateCompanyInfo(info) {
                const container = docume    nt.getElementById('company-info');
                if (!info) {
                    container.innerHTML = '<p class="text-red-500">No company info available</p>';
                    return;
                }
                
                container.innerHTML = `
                    <p class="font-medium">${info.longname || info.ticker}</p>
                    <p class="text-gray-600">${info.sector || 'N/A'}</p>
                    <p class="mt-2">${info.longbusinesssummary ? info.longbusinesssummary.substring(0, 200) + '...' : 'No summary available'}</p>
                    <p class="mt-2">
                        <strong>Website:</strong> ${info.website || 'N/A'}<br>
                        <strong>Phone:</strong> ${info.phone || 'N/A'}
                    </p>
                `;
            }
            
            function updateFinancialMetrics(finance) {
                const container = document.getElementById('financial-metrics');
                if (!finance) {
                    container.innerHTML = '<p class="text-red-500">No financial data available</p>';
                    return;
                }
                
                container.innerHTML = `
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <p><strong>Market Cap:</strong> ${formatValue(finance.marketcap, true)}</p>
                            <p><strong>Revenue:</strong> ${formatValue(finance.totalrevenue, true)}</p>
                            <p><strong>Net Income:</strong> ${formatValue(finance.netincometocommon, true)}</p>
                            <p><strong>EPS (TTM):</strong> ${formatValue(finance.trailingeps)}</p>
                        </div>
                        <div>
                            <p><strong>Profit Margin:</strong> ${formatPercentage(finance.profitmargins)}</p>
                            <p><strong>Gross Margin:</strong> ${formatPercentage(finance.grossmargins)}</p>
                            <p><strong>Op. Margin:</strong> ${formatPercentage(finance.operatingmargins)}</p>
                            <p><strong>Free Cash Flow:</strong> ${formatValue(finance.freecashflow, true)}</p>
                        </div>
                    </div>
                `;
            }
            
            function updateValuationMetrics(valuation) {
                const container = document.getElementById('valuation-metrics');
                if (!valuation) {
                    container.innerHTML = '<p class="text-red-500">No valuation data available</p>';
                    return;
                }
                
                container.innerHTML = `
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <p><strong>P/E (TTM):</strong> ${formatValue(valuation.trailingpe)}</p>
                            <p><strong>Forward P/E:</strong> ${formatValue(valuation.forwardpe)}</p>
                        </div>
                        <div>
                            <p><strong>PEG Ratio:</strong> ${formatValue(valuation.pegratio)}</p>
                            <p><strong>Price/Book:</strong> ${formatValue(valuation.pricetobook)}</p>
                            <p><strong>P/S (TTM):</strong> ${formatValue(valuation.pricetosalestrailing12months)}</p>
                        </div>
                    </div>
                `;
            }
            
            function updateGrowthMetrics(growth) {
                const container = document.getElementById('growth-metrics');
                if (!growth) {
                    container.innerHTML = '<p class="text-red-500">No growth data available</p>';
                    return;
                }
                
                container.innerHTML = `
                    <div>
                        <p><strong>Revenue Growth:</strong> ${formatPercentage(growth.revenuegrowth)}</p>
                        <p><strong>Earnings Growth:</strong> ${formatPercentage(growth.earningsgrowth)}</p>
                        <p><strong>Earnings Growth (QoQ):</strong> ${formatPercentage(growth.earningsquarterlygrowth)}</p>
                    </div>
                `;
            }
            
            function updateProfitabilityLiquidity(profitabilities, liquidity) {
                const container = document.getElementById('profitability-liquidity');
                
                let profitabilityHtml = '<p class="text-red-500">No profitability data available</p>';
                if (profitabilities) {
                    profitabilityHtml = `
                        <div class="mb-3">
                            <p><strong>Return on Equity:</strong> ${formatPercentage(profitabilities.returnonequity)}</p>
                            <p><strong>Return on Assets:</strong> ${formatPercentage(profitabilities.returnonassets)}</p>
                        </div>
                    `;
                }
                
                let liquidityHtml = '<p class="text-red-500">No liquidity data available</p>';
                if (liquidity) {
                    liquidityHtml = `
                        <div>
                            <p><strong>Current Ratio:</strong> ${formatValue(liquidity.currentratio)}</p>
                            <p><strong>Total Cash:</strong> ${formatValue(liquidity.totalcash, true)}</p>
                            <p><strong>Total Debt:</strong> ${formatValue(liquidity.totaldebt, true)}</p>
                            <p><strong>Debt to Equity:</strong> ${formatValue(liquidity.debttoequity)}</p>
                        </div>
                    `;
                }
                
                container.innerHTML = profitabilityHtml + liquidityHtml;
            }
            
            function updatePriceTable(priceData) {
                const tableBody = document.getElementById('price-table-body');
                if (!priceData || priceData.length === 0) {
                    tableBody.innerHTML = '<tr><td colspan="6" class="px-6 py-4 text-sm text-gray-500 text-center">No price data available</td></tr>';
                    return;
                }
                
                let html = '';
                // Reverse the data to show most recent first
                const sortedData = [...priceData].sort((a, b) => new Date(b.datetime) - new Date(a.datetime));
                
                for (const price of sortedData.slice(0, 10)) {
                    const date = new Date(price.datetime).toLocaleDateString();
                    html += `
                        <tr>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${date}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${price.open?.toFixed(2) || 'N/A'}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${price.high?.toFixed(2) || 'N/A'}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${price.low?.toFixed(2) || 'N/A'}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${price.close?.toFixed(2) || 'N/A'}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${price.volume?.toLocaleString() || 'N/A'}</td>
                        </tr>
                    `;
                }
                
                tableBody.innerHTML = html;
            }
            
            function updatePriceChart(priceData) {
                if (!priceData || priceData.length === 0) {
                    return;
                }
                
                // Sort data by date (oldest to newest)
                const sortedData = [...priceData].sort((a, b) => new Date(a.datetime) - new Date(b.datetime));
                
                const dates = sortedData.map(item => new Date(item.datetime).toLocaleDateString());
                const closePrices = sortedData.map(item => item.close);
                const volumes = sortedData.map(item => item.volume);
                
                const ctx = document.getElementById('price-chart').getContext('2d');
                
                // Destroy existing chart if it exists
                if (priceChart) {
                    priceChart.destroy();
                }
                
                priceChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: dates,
                        datasets: [
                            {
                                label: 'Close Price',
                                data: closePrices,
                                borderColor: 'rgb(75, 192, 192)',
                                tension: 0.1,
                                yAxisID: 'y'
                            },
                            {
                                label: 'Volume',
                                data: volumes,
                                type: 'bar',
                                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                                borderColor: 'rgb(54, 162, 235)',
                                borderWidth: 1,
                                yAxisID: 'y1'
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        interaction: {
                            mode: 'index',
                            intersect: false
                        },
                        scales: {
                            y: {
                                type: 'linear',
                                display: true,
                                position: 'left',
                                title: {
                                    display: true,
                                    text: 'Price'
                                }
                            },
                            y1: {
                                type: 'linear',
                                display: true,
                                position: 'right',
                                title: {
                                    display: true,
                                    text: 'Volume'
                                },
                                grid: {
                                    drawOnChartArea: false
                                }
                            }
                        }
                    }
                });
            }
            
            function formatValue(value, isCurrency = false) {
                if (value === null || value === undefined || isNaN(value)) {
                    return 'N/A';
                }
                
                if (isCurrency) {
                    // Format as currency with abbreviated values (K, M, B)
                    if (Math.abs(value) >= 1.0e+12) {
                        return '$' + (value / 1.0e+12).toFixed(2) + 'T';
                    } else if (Math.abs(value) >= 1.0e+9) {
                        return '$' + (value / 1.0e+9).toFixed(2) + 'B';
                    } else if (Math.abs(value) >= 1.0e+6) {
                        return '$' + (value / 1.0e+6).toFixed(2) + 'M';
                    } else if (Math.abs(value) >= 1.0e+3) {
                        return '$' + (value / 1.0e+3).toFixed(2) + 'K';
                    } else {
                        return '$' + value.toFixed(2);
                    }
                } else {
                    // Format as number with 2 decimal places
                    return value.toFixed(2);
                }
            }
            
            function formatPercentage(value) {
                if (value === null || value === undefined || isNaN(value)) {
                    return 'N/A';
                }
                
                return (value * 100).toFixed(2) + '%';
            }
        </script>
    </body>
    </html>
    """

# Compare companies endpoint
@app.get("/compare-companies")
async def compare_companies(
    tickers: str = Query(..., description="Comma-separated list of ticker symbols"),
    supabase: Client = Depends(get_supabase_client)
):
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    
    if not ticker_list:
        raise HTTPException(status_code=400, detail="No tickers provided")
    
    result = []
    
    for ticker in ticker_list:
        # Get data from each table for the specified ticker
        info_response = supabase.table("company_info").select("*").eq("ticker", ticker).execute()
        finance_response = supabase.table("company_finance").select("*").eq("ticker", ticker).execute()
        valuation_response = supabase.table("company_valuation").select("*").eq("ticker", ticker).execute()
        growth_response = supabase.table("company_growth").select("*").eq("ticker", ticker).execute()
        profitabilities_response = supabase.table("company_profitabilities").select("*").eq("ticker", ticker).execute()
        
        # Check if we found data for this ticker
        if not info_response.data:
            continue
        
        # Combine all data into a single company object
        company = {
            "ticker": ticker,
            "name": info_response.data[0].get("longname", ticker) if info_response.data else ticker,
            "sector": info_response.data[0].get("sector") if info_response.data else None,
            # Financial metrics
            "marketCap": finance_response.data[0].get("marketcap") if finance_response.data else None,
            "revenue": finance_response.data[0].get("totalrevenue") if finance_response.data else None,
            "eps": finance_response.data[0].get("trailingeps") if finance_response.data else None,
            "profitMargin": finance_response.data[0].get("profitmargins") if finance_response.data else None,
            # Valuation metrics
            "pe": valuation_response.data[0].get("trailingpe") if valuation_response.data else None,
            "forwardPe": valuation_response.data[0].get("forwardpe") if valuation_response.data else None,
            "priceToBook": valuation_response.data[0].get("pricetobook") if valuation_response.data else None,
            # Growth metrics
            "revenueGrowth": growth_response.data[0].get("revenuegrowth") if growth_response.data else None,
            "earningsGrowth": growth_response.data[0].get("earningsgrowth") if growth_response.data else None,
            # Profitability metrics
            "roe": profitabilities_response.data[0].get("returnonequity") if profitabilities_response.data else None,
            "roa": profitabilities_response.data[0].get("returnonassets") if profitabilities_response.data else None,
        }
        
        result.append(company)
    
    if not result:
        raise HTTPException(status_code=404, detail="No data found for the provided tickers")
    
    return result

# Sector analysis endpoint
@app.get("/sector-analysis/{sector}")
async def sector_analysis(
    sector: str,
    supabase: Client = Depends(get_supabase_client)
):
    # Get all companies in the specified sector
    company_info_response = supabase.table("company_info").select("*").eq("sector", sector).execute()
    
    if hasattr(company_info_response, "error") and company_info_response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {company_info_response.error}")
    
    if not company_info_response.data:
        raise HTTPException(status_code=404, detail=f"No companies found in sector: {sector}")
    
    # Get tickers for all companies in the sector
    tickers = [company["ticker"] for company in company_info_response.data]
    
    # For each ticker, get financial and valuation data
    sector_data = []
    
    for ticker in tickers:
        finance_response = supabase.table("company_finance").select("*").eq("ticker", ticker).execute()
        valuation_response = supabase.table("company_valuation").select("*").eq("ticker", ticker).execute()
        
        company_data = next((c for c in company_info_response.data if c["ticker"] == ticker), {})
        finance_data = finance_response.data[0] if finance_response.data else {}
        valuation_data = valuation_response.data[0] if valuation_response.data else {}
        
        sector_data.append({
            "ticker": ticker,
            "name": company_data.get("longname", ticker),
            "marketCap": finance_data.get("marketcap"),
            "revenue": finance_data.get("totalrevenue"),
            "profitMargin": finance_data.get("profitmargins"),
            "pe": valuation_data.get("trailingpe"),
            "priceToBook": valuation_data.get("pricetobook")
        })
    
    # Calculate sector averages
    valid_pe_values = [company["pe"] for company in sector_data if company["pe"] is not None]
    valid_pb_values = [company["priceToBook"] for company in sector_data if company["priceToBook"] is not None]
    valid_margin_values = [company["profitMargin"] for company in sector_data if company["profitMargin"] is not None]
    
    sector_averages = {
        "sector": sector,
        "companyCount": len(sector_data),
        "averagePE": sum(valid_pe_values) / len(valid_pe_values) if valid_pe_values else None,
        "medianPE": sorted(valid_pe_values)[len(valid_pe_values) // 2] if valid_pe_values else None,
        "averagePB": sum(valid_pb_values) / len(valid_pb_values) if valid_pb_values else None,
        "averageProfitMargin": sum(valid_margin_values) / len(valid_margin_values) if valid_margin_values else None,
        "companies": sector_data
    }
    
    return sector_averages

# Stock screener endpoint
@app.get("/stock-screener")
async def stock_screener(
    min_market_cap: Optional[float] = None,
    max_pe: Optional[float] = None,
    min_dividend_yield: Optional[float] = None,
    min_profit_margin: Optional[float] = None,
    sector: Optional[str] = None,
    limit: int = 20,
    supabase: Client = Depends(get_supabase_client)
):
    # Start with all companies
    base_query = supabase.table("company_info").select("ticker, longname, sector")
    
    # Apply sector filter if provided
    if sector:
        base_query = base_query.eq("sector", sector)
    
    # Get base list of companies
    base_response = base_query.execute()
    
    if hasattr(base_response, "error") and base_response.error:
        raise HTTPException(status_code=500, detail=f"Database error: {base_response.error}")
    
    if not base_response.data:
        return []
    
    # Get all tickers
    all_tickers = [company["ticker"] for company in base_response.data]
    
    # Apply additional filters by fetching data for each category and filtering
    results = []
    
    for ticker in all_tickers:
        # Get financial data
        finance_response = supabase.table("company_finance").select("*").eq("ticker", ticker).execute()
        valuation_response = supabase.table("company_valuation").select("*").eq("ticker", ticker).execute()
        dividend_response = supabase.table("company_dividend").select("*").eq("ticker", ticker).execute()
        
        finance_data = finance_response.data[0] if finance_response.data else {}
        valuation_data = valuation_response.data[0] if valuation_response.data else {}
        dividend_data = dividend_response.data[0] if dividend_response.data else {}
        
        # Apply filters
        if min_market_cap and (not finance_data.get("marketcap") or finance_data.get("marketcap") < min_market_cap):
            continue
            
        if max_pe and valuation_data.get("trailingpe") and valuation_data.get("trailingpe") > max_pe:
            continue
            
        if min_dividend_yield and (not dividend_data.get("dividendyield") or dividend_data.get("dividendyield") < min_dividend_yield):
            continue
            
        if min_profit_margin and (not finance_data.get("profitmargins") or finance_data.get("profitmargins") < min_profit_margin):
            continue
        
        # Get company info
        company_info = next((c for c in base_response.data if c["ticker"] == ticker), {})
        
        # Add to results if passed all filters
        results.append({
            "ticker": ticker,
            "name": company_info.get("longname", ticker),
            "sector": company_info.get("sector"),
            "marketCap": finance_data.get("marketcap"),
            "pe": valuation_data.get("trailingpe"),
            "dividendYield": dividend_data.get("dividendyield"),
            "profitMargin": finance_data.get("profitmargins")
        })
    
    # Sort by market cap (descending) and limit results
    results.sort(key=lambda x: x.get("marketCap") or 0, reverse=True)
    return results[:limit]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)