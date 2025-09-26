#!/usr/bin/env python3
"""
Trading API MCP Server - Interface with trading platforms
WARNING: This is for educational purposes only. Real trading involves significant risk.
"""


import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp.server import Server
import requests
from ib_insync import IB, Stock, Contract, Order



class IBManager:
    """Interactive Brokers API Manager"""
    
    def __init__(self):
        self.ib = IB()
        self.connected = False
    
    async def connect(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1):
        """Connect to Interactive Brokers TWS/Gateway"""
        try:
            self.ib.connect(host, port, clientId=client_id)
            self.connected = True
            return f"Connected to IB at {host}:{port}"
        except Exception as e:
            return f"Failed to connect to IB: {str(e)}"
    
    async def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary"""
        if not self.connected:
            return {"error": "Not connected to IB"}
        
        try:
            summary = self.ib.accountSummary()
            return {item.tag: item.value for item in summary}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_positions(self) -> List[Dict]:
        """Get current positions"""
        if not self.connected:
            return [{"error": "Not connected to IB"}]
        
        try:
            positions = self.ib.positions()
            return [
                {
                    "contract": str(pos.contract),
                    "position": pos.position,
                    "marketPrice": pos.marketPrice,
                    "marketValue": pos.marketValue,
                    "averageCost": pos.averageCost,
                    "unrealizedPNL": pos.unrealizedPNL,
                }
                for pos in positions
            ]
        except Exception as e:
            return [{"error": str(e)}]
    
    async def place_order(self, symbol: str, action: str, quantity: int, order_type: str = "MKT"):
        """Place trading order"""
        if not self.connected:
            return {"error": "Not connected to IB"}
        
        try:
            contract = Stock(symbol, "SMART", "USD")
            order = Order(action, quantity, order_type)
            
            trade = self.ib.placeOrder(contract, order)
            return {
                "orderId": trade.order.orderId,
                "symbol": symbol,
                "action": action,
                "quantity": quantity,
                "orderType": order_type,
                "status": "submitted"
            }
        except Exception as e:
            return {"error": str(e)}



class NinjaTraderManager:
    """NinjaTrader API Manager"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            response = requests.get(f"{self.base_url}/account")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def get_positions(self) -> List[Dict]:
        """Get current positions"""
        try:
            response = requests.get(f"{self.base_url}/positions")
            return response.json()
        except Exception as e:
            return [{"error": str(e)}]
    
    async def place_order(self, instrument: str, action: str, quantity: int, order_type: str = "MARKET"):
        """Place order via NinjaTrader"""
        try:
            payload = {
                "instrument": instrument,
                "action": action,
                "quantity": quantity,
                "orderType": order_type
            }
            response = requests.post(f"{self.base_url}/orders", json=payload)
            return response.json()
        except Exception as e:
            return {"error": str(e)}



# Initialize managers
ib_manager = IBManager()
nt_manager = NinjaTraderManager()

# MCP Server
server = Server("trading-api-mcp")


# Interactive Brokers Tools
@server.tool()
async def ib_connect(host: str = "127.0.0.1", port: int = 7497, client_id: int = 1) -> str:
    """Connect to Interactive Brokers TWS/Gateway"""
    result = await ib_manager.connect(host, port, client_id)
    return result

@server.tool()
async def ib_get_account_summary() -> str:
    """Get IB account summary"""
    result = await ib_manager.get_account_summary()
    return json.dumps(result, indent=2)

@server.tool()
async def ib_get_positions() -> str:
    """Get IB positions"""
    result = await ib_manager.get_positions()
    return json.dumps(result, indent=2)

@server.tool()
async def ib_place_order(symbol: str, action: str, quantity: int, order_type: str = "MKT") -> str:
    """Place order via Interactive Brokers (BUY/SELL)"""
    result = await ib_manager.place_order(symbol, action, quantity, order_type)
    return json.dumps(result, indent=2)

# NinjaTrader Tools
@server.tool()
async def nt_get_account() -> str:
    """Get NinjaTrader account info"""
    result = await nt_manager.get_account_info()
    return json.dumps(result, indent=2)

@server.tool()
async def nt_get_positions() -> str:
    """Get NinjaTrader positions"""
    result = await nt_manager.get_positions()
    return json.dumps(result, indent=2)

@server.tool()
async def nt_place_order(instrument: str, action: str, quantity: int, order_type: str = "MARKET") -> str:
    """Place order via NinjaTrader"""
    result = await nt_manager.place_order(instrument, action, quantity, order_type)
    return json.dumps(result, indent=2)

# Risk Management Tools
@server.tool()
async def calculate_position_size(account_balance: float, risk_percent: float, entry_price: float, stop_loss: float) -> str:
    """Calculate position size based on risk management"""
    try:
        risk_amount = account_balance * (risk_percent / 100)
        price_diff = abs(entry_price - stop_loss)
        position_size = int(risk_amount / price_diff)
        
        result = {
            "account_balance": account_balance,
            "risk_percent": risk_percent,
            "risk_amount": risk_amount,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "price_difference": price_diff,
            "recommended_position_size": position_size
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error calculating position size: {str(e)}"


async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as streams:
        await server.run(*streams)



if __name__ == "__main__":
    asyncio.run(main())
