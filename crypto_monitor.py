import time
import threading
import requests
import json
try:
    import yfinance as yf # type: ignore
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich import box

# Cache untuk Crypto dan Saham
MARKET_DATA_CACHE = {
    'crypto': {},
    'stock': {}
}

# Top 10 Crypto Market Cap
WATCHLIST = {
    'BTC': {'name': 'Bitcoin', 'target_high': 100000},
    'ETH': {'name': 'Ethereum', 'target_high': 4000},
    'BNB': {'name': 'Binance Coin'},
    'SOL': {'name': 'Solana'},
    'XRP': {'name': 'Ripple'},
    'DOGE': {'name': 'Dogecoin'},
    'ADA': {'name': 'Cardano'},
    'TRX': {'name': 'TRON'},
    'AVAX': {'name': 'Avalanche'},
    'LINK': {'name': 'Chainlink'}
}

STOCKS = {
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft',
    'TSLA': 'Tesla',
    'GOOGL': 'Alphabet',
    'BBCA.JK': 'BCA (ID)'
}

def fetch_crypto_worker():
    global MARKET_DATA_CACHE
    
    # Ambil USDT pairs dan USDTBIDR untuk konversi akurat
    symbols = [f"{sym}USDT" for sym in WATCHLIST.keys()]
    symbols.append("USDTBIDR")
    
    symbols_json = json.dumps(symbols).replace(" ", "")
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbols={symbols_json}"
    
    while True:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                parsed_data = {}
                usdt_to_idr = 15500 # Fallback awal
                
                # Pertama, cari nilai kurs USDT ke IDR
                for item in data:
                    if item['symbol'] == 'USDTBIDR':
                        usdt_to_idr = float(item['lastPrice'])
                        break
                        
                for item in data:
                    sym = item['symbol']
                    if sym == 'USDTBIDR':
                        continue
                        
                    base_coin = sym.replace('USDT', '')
                    usd_price = float(item['lastPrice'])
                    
                    parsed_data[base_coin] = {
                        'usd': usd_price,
                        'idr': usd_price * usdt_to_idr,
                        'usd_24h_change': float(item['priceChangePercent'])
                    }
                
                MARKET_DATA_CACHE['crypto'] = parsed_data
        except Exception:
            pass
        
        # Real-time update setiap 1.5 detik
        time.sleep(1.5)

def fetch_stock_worker():
    global MARKET_DATA_CACHE
    while True:
        if YFINANCE_AVAILABLE:
            try:
                stock_symbols = list(STOCKS.keys())
                tickers = yf.Tickers(" ".join(stock_symbols))
                stock_data = {}
                for sym in stock_symbols:
                    try:
                        info = tickers.tickers[sym].info
                        price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                        prev_close = info.get('previousClose', info.get('regularMarketPreviousClose', 0))
                        if price and prev_close:
                            change_pct = ((price - prev_close) / prev_close) * 100
                        else:
                            change_pct = 0.0
                        stock_data[sym] = {'price': price, 'change': change_pct}
                    except Exception:
                        stock_data[sym] = {'price': 0, 'change': 0}
                
                MARKET_DATA_CACHE['stock'] = stock_data
            except Exception:
                pass
        
        # Saham update setiap 15 detik
        time.sleep(15)

threading.Thread(target=fetch_crypto_worker, daemon=True).start()
threading.Thread(target=fetch_stock_worker, daemon=True).start()

def get_crypto_info():
    table = Table(box=box.SIMPLE, show_header=True, expand=True)
    table.add_column("Aset", style="bold cyan")
    table.add_column("Harga (USD)", justify="right", style="white")
    table.add_column("Harga (IDR)", justify="right", style="white")
    table.add_column("24h %", justify="right")
    
    crypto_data = MARKET_DATA_CACHE.get('crypto', {})
    
    if not crypto_data:
        table.add_row("Loading data...", "", "", "")
    else:
        for cid, info in WATCHLIST.items():
            if cid in crypto_data:
                data = crypto_data[cid]
                usd = data.get('usd', 0)
                idr = data.get('idr', 0)
                change = data.get('usd_24h_change', 0)
                
                color = "green" if change >= 0 else "red"
                symbol = "▲" if change >= 0 else "▼"
                
                table.add_row(
                    f"{cid} ({info['name']})",
                    f"${usd:,.2f}",
                    f"Rp {idr:,.0f}",
                    f"[{color}]{symbol} {abs(change):.2f}%[/{color}]"
                )
                
    return Panel(table, title="[cyan]Cryptocurrency (Live)", border_style="cyan")

def get_stock_info():
    table = Table(box=box.SIMPLE, show_header=True, expand=True)
    table.add_column("Saham", style="bold yellow")
    table.add_column("Perusahaan", style="white")
    table.add_column("Harga", justify="right", style="white")
    table.add_column("Harian %", justify="right")
    
    stock_data = MARKET_DATA_CACHE.get('stock', {})
    
    if not YFINANCE_AVAILABLE:
        table.add_row("Modul yfinance tidak tersedia.", "Jalankan 'pip install yfinance'", "", "")
    elif not stock_data:
        table.add_row("Loading data...", "", "", "")
    else:
        for sym, name in STOCKS.items():
            if sym in stock_data:
                data = stock_data[sym]
                price = data.get('price', 0)
                change = data.get('change', 0)
                
                color = "green" if change >= 0 else "red"
                symbol = "▲" if change >= 0 else "▼"
                
                # Format currency correctly based on symbol
                currency = "Rp" if ".JK" in sym else "$"
                
                table.add_row(
                    sym,
                    name,
                    f"{currency}{price:,.2f}",
                    f"[{color}]{symbol} {abs(change):.2f}%[/{color}]"
                )
                
    return Panel(table, title="[yellow]Saham / Stock Market", border_style="yellow")

def get_watchlist_alerts():
    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_column("Pesan")
    
    crypto_data = MARKET_DATA_CACHE.get('crypto', {})
    alerts_found = False
    
    if crypto_data:
        for cid, info in WATCHLIST.items():
            if 'target_high' in info and cid in crypto_data:
                current_price = crypto_data[cid].get('usd', 0)
                if current_price >= info['target_high']:
                    table.add_row(f"[bold red]ALARM![/bold red] {cid} menembus target ${info['target_high']:,.0f} (Sekarang: ${current_price:,.0f})")
                    alerts_found = True
                    
    if not alerts_found:
        table.add_row("[dim]Semua aset dalam batas normal. Tidak ada alert.[/dim]")
        
    return Panel(table, title="[red]Notifikasi & Watchlist", border_style="red")

def make_crypto_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=8),
        Layout(name="upper", ratio=3),
        Layout(name="lower", ratio=1),
        Layout(name="footer", size=1)
    )
    layout["upper"].split_row(
        Layout(name="crypto", ratio=1),
        Layout(name="stock", ratio=1)
    )
    layout["lower"].update(get_watchlist_alerts())
    return layout

def update_crypto_layout(layout, header_panel):
    layout["header"].update(header_panel)
    layout["crypto"].update(get_crypto_info())
    layout["stock"].update(get_stock_info())
    layout["lower"].update(get_watchlist_alerts())
