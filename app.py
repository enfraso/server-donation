#!/usr/bin/env python3
import os, time, sqlite3, threading
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template
import psutil

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "data.sqlite3")
CONFIG = os.path.join(ROOT, "config.json")
app = Flask(__name__)

DEFAULTS = {
    "server_name": "Meu servidor",
    "electricity_brl_kwh": 0.95,
    "average_power_watts": 75,
    "internet_monthly_brl": 120.00,
    "internet_allowance_gb": 1000,
    "hardware_value_brl": 3500.00,
    "hardware_lifetime_months": 48,
    "pix_key": "danyeas@hotmail.com",
    "pix_receiver": "DOACAO SERVIDOR",
    "pix_city": "BRASILIA",
    "donation_suggestions": [5, 10, 20, 50]
}

def config():
    if not os.path.exists(CONFIG):
        with open(CONFIG, "w", encoding="utf-8") as f:
            import json; json.dump(DEFAULTS, f, indent=2, ensure_ascii=False)
    import json
    with open(CONFIG, encoding="utf-8") as f:
        c = DEFAULTS.copy()
        c.update(json.load(f))
        return c

def db():
    con = sqlite3.connect(DB, timeout=10)
    con.execute("""CREATE TABLE IF NOT EXISTS counters (
        id INTEGER PRIMARY KEY CHECK(id=1), rx INTEGER NOT NULL, tx INTEGER NOT NULL,
        total_rx INTEGER NOT NULL, total_tx INTEGER NOT NULL, updated REAL NOT NULL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)""")
    con.commit()
    return con

def traffic_totals():
    counters = psutil.net_io_counters()
    rx, tx = int(counters.bytes_recv), int(counters.bytes_sent)
    con = db()
    row = con.execute("SELECT rx, tx, total_rx, total_tx FROM counters WHERE id=1").fetchone()
    if row is None:
        con.execute("INSERT INTO counters VALUES (1, ?, ?, 0, 0, ?)", (rx, tx, time.time()))
        total_rx = total_tx = 0
    else:
        old_rx, old_tx, total_rx, total_tx = row
        # If counters reset (e.g. reboot), start a new baseline without negative traffic.
        total_rx += max(0, rx - old_rx)
        total_tx += max(0, tx - old_tx)
        con.execute("UPDATE counters SET rx=?, tx=?, total_rx=?, total_tx=?, updated=? WHERE id=1",
                    (rx, tx, total_rx, total_tx, time.time()))
    con.commit(); con.close()
    return total_rx, total_tx

def collect():
    c = config()
    rx, tx = traffic_totals()
    now = datetime.now().astimezone()
    uptime = time.time() - psutil.boot_time()
    cpu = psutil.cpu_percent(interval=0.15)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    # Estimated operating cost: configured average power, not a direct wattmeter reading.
    kwh = (c["average_power_watts"] / 1000) * (uptime / 3600)
    energy_cost = kwh * c["electricity_brl_kwh"]
    days = uptime / 86400
    internet_monthly = float(c["internet_monthly_brl"])
    allowance = max(1.0, float(c["internet_allowance_gb"]))
    traffic_gb = (rx + tx) / (1024**3)
    traffic_cost = traffic_gb * (internet_monthly / allowance)
    # Straight-line depreciation based on configured purchase/replacement value and lifetime.
    depreciation_monthly = float(c["hardware_value_brl"]) / max(1, int(c["hardware_lifetime_months"]))
    depreciation_cost = depreciation_monthly * (uptime / (86400 * 30.4375))
    return {
        "server_name": c["server_name"], "timestamp": now.isoformat(),
        "cpu_percent": cpu, "memory_percent": mem.percent,
        "memory_used_gb": round((mem.total-mem.available)/1024**3, 2),
        "memory_total_gb": round(mem.total/1024**3, 2),
        "disk_percent": disk.percent, "disk_used_gb": round(disk.used/1024**3, 1),
        "disk_total_gb": round(disk.total/1024**3, 1),
        "uptime_seconds": int(uptime),
        "rx_gb": round(rx/1024**3, 3), "tx_gb": round(tx/1024**3, 3),
        "traffic_gb": round(traffic_gb, 3),
        "energy_kwh": round(kwh, 3), "energy_cost": round(energy_cost, 2),
        "traffic_cost": round(traffic_cost, 2),
        "depreciation_cost": round(depreciation_cost, 2),
        "total_cost": round(energy_cost + traffic_cost + depreciation_cost, 2),
        "config": c
    }

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/status")
def status():
    try:
        return jsonify(collect())
    except Exception as e:
        app.logger.exception("Falha ao coletar métricas")
        return jsonify({"error": str(e)}), 500

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8787)
