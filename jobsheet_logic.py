import os
import re
import sys
import sqlite3
from datetime import datetime, date
from typing import Optional, Dict, Any, List

try:
    from fpdf import FPDF, XPos, YPos
except ImportError:
    print("Missing dependency 'fpdf2'. Install with: pip install fpdf2")
    sys.exit(1)

DB_PATH = "jobsheet.db"
OUTPUT_DIR = "receipts"

# --- Customize your shop header here ---
SHOP_NAME = "Orbit Enterprises"
SHOP_ADDRESS = "NO:5/321, LIC COLONY, NEAR HOTEL VASANTHAM, OPP TO NEW BUS STAND, SALEM-636004"
SHOP_PHONE = "Tel: 9095022199, 934422199"
# ---------------------------------------

def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.execute("PRAGMA busy_timeout = 10000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobsheet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            date TEXT,
            daily_counter INTEGER,
            customer_name TEXT,
            phone TEXT,
            model TEXT,
            serial TEXT,
            symptom TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn

def normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    return digits

def get_daily_next_counter(conn: sqlite3.Connection, d: date) -> int:
    d_str = d.isoformat()
    cur = conn.execute("SELECT COALESCE(MAX(daily_counter), 0) FROM jobsheet WHERE date = ?", (d_str,))
    max_ctr = cur.fetchone()[0] or 0
    return max_ctr + 1

def generate_code(d: date, daily_counter: int) -> str:
    return f"{d.strftime('%Y%m%d')}-{daily_counter:03d}"

def insert_jobsheet(conn: sqlite3.Connection, record: Dict[str, Any]) -> int:
    columns = ",".join(record.keys())
    placeholders = ",".join(["?"] * len(record))
    cur = conn.execute(
        f"INSERT INTO jobsheet ({columns}) VALUES ({placeholders})",
        list(record.values())
    )
    conn.commit()
    return cur.lastrowid

def fetch_jobs_by(conn: sqlite3.Connection, customer: Optional[str], phone: Optional[str], serial: Optional[str]) -> List[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM jobsheet WHERE 1=1"
    params = []
    if customer:
        query += " AND customer_name LIKE ?"
        params.append(f"%{customer.strip()}%")
    if phone:
        digits = normalize_phone(phone)
        query += " AND phone LIKE ?"
        params.append(f"%{digits}%")
    if serial:
        query += " AND serial LIKE ?"
        params.append(f"%{serial.strip()}%")
    query += " ORDER BY datetime(created_at) DESC"
    cur = conn.execute(query, params)
    return cur.fetchall()

class _A4TwoCopyPDF(FPDF):
    def header(self):
        pass

def _draw_copy(pdf: _A4TwoCopyPDF, label: str, meta: Dict[str, str]):
    left_margin = 10
    right_margin = 200
    top = pdf.get_y()
    box_height = 135
    pdf.set_line_width(0.3)
    pdf.rect(left_margin, top, right_margin - left_margin, box_height)
    pdf.set_xy(left_margin + 2, top + 3)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, f"{SHOP_NAME}  -  {label}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, f"{SHOP_ADDRESS}", ln=1)
    pdf.cell(0, 5, f"Phone: {SHOP_PHONE}", ln=1)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 6, f"Jobsheet Code: {meta['code']}", border=0)
    pdf.cell(0, 6, f"Timestamp: {meta['created_at']}", ln=1)
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(60, 8, "Field", 1, 0, "C")
    pdf.cell(0, 8, "Value", 1, 1, "C")

    pdf.set_font("Helvetica", "", 10)
    def row(key, val):
        start_x = pdf.get_x()
        start_y = pdf.get_y()
        pdf.multi_cell(60, 8, key, border=1)
        end_x = pdf.get_x()
        end_y = pdf.get_y()
        pdf.set_xy(start_x + 60, start_y)
        height = end_y - start_y
        x = pdf.get_x()
        y = pdf.get_y()
        w = 130
        before_y = pdf.get_y()
        pdf.multi_cell(w, 8, val or "-", border=0)
        after_y = pdf.get_y()
        used_h = after_y - before_y
        h = max(height, used_h) or 8
        pdf.rect(x, y, w, h)
        pdf.set_xy(start_x, max(end_y, y + h))
    row("Customer Name", meta["customer_name"])
    row("Phone", meta["phone"])
    row("Printer Model", meta["model"])
    row("Serial Number", meta["serial"])
    row("Reported Symptom", meta["symptom"])
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 5, "Note: Keep this receipt safe. Present it when collecting your device.", ln=1)
    pdf.ln(1)

def generate_pdf(record: Dict[str, Any], output_dir: str = OUTPUT_DIR) -> str:
    os.makedirs(output_dir, exist_ok=True)
    safe_customer = re.sub(r"[^A-Za-z0-9_-]+", "_", record["customer_name"]).strip("_") or "customer"
    filename = f"jobsheet_{record['code']}_{safe_customer}.pdf"
    path = os.path.join(output_dir, filename)
    pdf = _A4TwoCopyPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False, margin=10)
    pdf.add_page()
    meta = {
        "code": record["code"],
        "created_at": record["created_at"],
        "customer_name": record["customer_name"],
        "phone": record["phone"],
        "model": record["model"],
        "serial": record["serial"],
        "symptom": record["symptom"],
    }
    pdf.set_y(10)
    _draw_copy(pdf, "Company Copy", meta)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.2)
    pdf.line(10, 147, 200, 147)
    pdf.set_y(150)
    _draw_copy(pdf, "Customer Copy", meta)
    pdf.output(path)
    return path
