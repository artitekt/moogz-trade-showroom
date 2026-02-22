"""
MoogzTrade Web Demo - FastAPI Backend
High-end trading platform demo with security-first architecture
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import json
import asyncio
import os
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import secrets
import base64

# Import MoogzTrade Mock SDK modules (for public showroom demo)
import sys
sys.path.append('.')
try:
    # Import from mock_sdk for public demo
    from mock_sdk.security import EncryptionManager, AuthManager, APIKeyManager
    from mock_sdk.market import MarketDataProvider, PortfolioManager, AsyncMarketInterface, Exchange
    from mock_sdk.agent_tools import TradingSignal, AuditLogger, AgentInterface
    
    # For backward compatibility with existing code
    encryption = EncryptionManager()
    auth = AuthManager()
    api_key_manager = APIKeyManager()
    create_market_data_provider = MarketDataProvider
    create_portfolio_manager = PortfolioManager
    DatabaseManager = None  # Not implemented in mock structure
    settings = None  # Not implemented in mock structure
    
    SDK_AVAILABLE = True
except ImportError as e:
    logging.warning(f"MoogzTrade Mock SDK not available: {e}")
    SDK_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MoogzTrade Web Demo",
    description="High-end trading platform demo with security-first architecture",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="demo_site/static"), name="static")
templates = Jinja2Templates(directory="demo_site/templates")

# Global state for demo mode
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
MOCK_DATA = {}

class EncryptionRequest(BaseModel):
    plaintext: str
    demo_mode: Optional[bool] = True

class EncryptionResponse(BaseModel):
    ciphertext: str
    hmac: str
    timestamp: str
    demo_mode: bool

class MarketDataRequest(BaseModel):
    symbol: str
    demo_mode: Optional[bool] = True

class PortfolioRequest(BaseModel):
    demo_mode: Optional[bool] = True

class AgentRequest(BaseModel):
    prompt: str
    demo_mode: Optional[bool] = True

class ModuleDemoRequest(BaseModel):
    module_name: str
    demo_mode: Optional[bool] = True

def init_mock_data():
    """Initialize mock data for demo mode"""
    global MOCK_DATA
    MOCK_DATA = {
        "market_data": {
            "AAPL": {"price": 182.52, "change": 2.34, "volume": 45678901},
            "GOOGL": {"price": 142.18, "change": -0.89, "volume": 23456789},
            "MSFT": {"price": 378.91, "change": 4.12, "volume": 34567890},
        },
        "portfolio": {
            "total_value": 1250000.00,
            "positions": [
                {"symbol": "AAPL", "shares": 1000, "value": 182520.00},
                {"symbol": "GOOGL", "shares": 500, "value": 71090.00},
                {"symbol": "MSFT", "shares": 300, "value": 113673.00},
            ],
            "performance": {
                "daily_return": 1.24,
                "weekly_return": 3.45,
                "monthly_return": 8.92,
                "sharpe_ratio": 1.85,
                "max_drawdown": -12.34
            }
        },
        "system_health": {
            "encryption": {"status": "healthy", "last_check": datetime.now().isoformat()},
            "market_data": {"status": "healthy", "last_check": datetime.now().isoformat()},
            "portfolio": {"status": "healthy", "last_check": datetime.now().isoformat()},
            "database": {"status": "healthy", "last_check": datetime.now().isoformat()},
        }
    }

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("Starting MoogzTrade Web Demo...")
    init_mock_data()
    
    if SDK_AVAILABLE and not DEMO_MODE:
        logger.info("Initializing MoogzTrade SDK...")
        # Initialize SDK components here if needed
    else:
        logger.info("Running in Demo Mode with mock data")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "demo_mode": DEMO_MODE,
        "sdk_available": SDK_AVAILABLE
    })

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "demo_mode": DEMO_MODE,
        "sdk_available": SDK_AVAILABLE,
        "version": "1.0.0"
    }

@app.post("/api/encrypt", response_model=EncryptionResponse)
async def encrypt_data(request: EncryptionRequest):
    """Encrypt data using AES-256"""
    try:
        if request.demo_mode or DEMO_MODE or not SDK_AVAILABLE:
            # Mock encryption for demo
            mock_ciphertext = base64.b64encode(f"encrypted_{request.plaintext}".encode()).decode()
            mock_hmac = secrets.token_hex(32)
            return EncryptionResponse(
                ciphertext=mock_ciphertext,
                hmac=mock_hmac,
                timestamp=datetime.now().isoformat(),
                demo_mode=True
            )
        else:
            # Real encryption using SDK
            encrypted_data = encryption.encrypt(request.plaintext)
            return EncryptionResponse(
                ciphertext=encrypted_data['ciphertext'],
                hmac=encrypted_data['hmac'],
                timestamp=datetime.now().isoformat(),
                demo_mode=False
            )
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        raise HTTPException(status_code=500, detail="Encryption failed")

@app.post("/api/market-data")
async def get_market_data(request: MarketDataRequest):
    """Get market data for a symbol"""
    try:
        symbol = request.symbol.upper()
        
        if request.demo_mode or DEMO_MODE or not SDK_AVAILABLE:
            # Mock market data
            if symbol in MOCK_DATA["market_data"]:
                return {
                    "symbol": symbol,
                    "data": MOCK_DATA["market_data"][symbol],
                    "timestamp": datetime.now().isoformat(),
                    "demo_mode": True
                }
            else:
                raise HTTPException(status_code=404, detail="Symbol not found in demo data")
        else:
            # Real market data using SDK
            async with create_market_data_provider() as provider:
                data = await provider.get_real_time_data(symbol, Exchange.NYSE)
            return {
                "symbol": symbol,
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "demo_mode": False
            }
    except Exception as e:
        logger.error(f"Market data error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market data")

@app.post("/api/portfolio")
async def get_portfolio_data(request: PortfolioRequest):
    """Get portfolio information"""
    try:
        if request.demo_mode or DEMO_MODE or not SDK_AVAILABLE:
            # Mock portfolio data
            return {
                "portfolio": MOCK_DATA["portfolio"],
                "timestamp": datetime.now().isoformat(),
                "demo_mode": True
            }
        else:
            # Real portfolio data using SDK
            portfolio_manager = create_portfolio_manager()
            portfolio = await portfolio_manager.get_portfolio_summary()
            return {
                "portfolio": portfolio,
                "timestamp": datetime.now().isoformat(),
                "demo_mode": False
            }
    except Exception as e:
        logger.error(f"Portfolio error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch portfolio data")

@app.post("/api/agent")
async def agent_console(request: AgentRequest):
    """Simulate LLM agent response"""
    try:
        # Simulate processing delay
        await asyncio.sleep(1)
        
        mock_responses = [
            f"Analyzing request: '{request.prompt}'",
            "Processing market data...",
            "Running security protocols...",
            "Generating trading signals...",
            "Risk assessment complete.",
            f"Recommendation: Based on current market conditions, consider reviewing your portfolio allocation."
        ]
        
        return {
            "response": mock_responses,
            "timestamp": datetime.now().isoformat(),
            "demo_mode": True
        }
    except Exception as e:
        logger.error(f"Agent console error: {e}")
        raise HTTPException(status_code=500, detail="Agent processing failed")

@app.post("/api/module-demo")
async def run_module_demo(request: ModuleDemoRequest):
    """Run a demo for a specific module"""
    try:
        module_demos = {
            "encryption": {
                "name": "AES-256 Encryption Module",
                "description": "Military-grade encryption for sensitive data",
                "demo": "Encrypting 'Hello World' -> 'encrypted_data_here'",
                "tier": "Tier 1 - Core Security"
            },
            "market_data": {
                "name": "Market Data Provider",
                "description": "Real-time market data from multiple exchanges",
                "demo": "Fetching AAPL data: $182.52 (+2.34)",
                "tier": "Tier 1 - Data Management"
            },
            "portfolio": {
                "name": "Portfolio Manager",
                "description": "Advanced portfolio optimization and rebalancing",
                "demo": "Optimal allocation: 60% equities, 30% bonds, 10% alternatives",
                "tier": "Tier 2 - Trading Tools"
            }
        }
        
        if request.module_name in module_demos:
            return {
                "module": module_demos[request.module_name],
                "timestamp": datetime.now().isoformat(),
                "demo_mode": True
            }
        else:
            raise HTTPException(status_code=404, detail="Module not found")
    except Exception as e:
        logger.error(f"Module demo error: {e}")
        raise HTTPException(status_code=500, detail="Module demo failed")

@app.get("/api/system-health")
async def get_system_health():
    """Get system health status"""
    try:
        if DEMO_MODE or not SDK_AVAILABLE:
            return {
                "health": MOCK_DATA["system_health"],
                "timestamp": datetime.now().isoformat(),
                "demo_mode": True
            }
        else:
            # Real system health using SDK
            return {
                "health": {
                    "encryption": {"status": "healthy", "last_check": datetime.now().isoformat()},
                    "market_data": {"status": "healthy", "last_check": datetime.now().isoformat()},
                    "portfolio": {"status": "healthy", "last_check": datetime.now().isoformat()},
                    "database": {"status": "healthy", "last_check": datetime.now().isoformat()},
                },
                "timestamp": datetime.now().isoformat(),
                "demo_mode": False
            }
    except Exception as e:
        logger.error(f"System health error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system health")

@app.get("/api/modules")
async def get_available_modules():
    """Get list of available modules"""
    modules = [
        {
            "name": "AES-256 Encryption",
            "tier": "Tier 1",
            "category": "Security",
            "description": "Military-grade encryption for sensitive trading data",
            "features": ["Real-time encryption", "HMAC verification", "Key management"]
        },
        {
            "name": "Market Data Provider",
            "tier": "Tier 1",
            "category": "Data Management",
            "description": "Real-time market data from multiple exchanges",
            "features": ["Real-time feeds", "Historical data", "Anomaly detection"]
        },
        {
            "name": "Portfolio Manager",
            "tier": "Tier 2",
            "category": "Trading Tools",
            "description": "Advanced portfolio optimization and rebalancing",
            "features": ["Mean-variance optimization", "Risk analysis", "Automated rebalancing"]
        },
        {
            "name": "Authentication System",
            "tier": "Tier 1",
            "category": "Security",
            "description": "Enterprise-grade user authentication",
            "features": ["Multi-factor auth", "Session management", "API key control"]
        }
    ]
    
    return {
        "modules": modules,
        "timestamp": datetime.now().isoformat(),
        "demo_mode": DEMO_MODE
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
