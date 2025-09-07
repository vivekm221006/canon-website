# Printer Jobsheet Console App (Local-Only)

A tiny Python console application for a printer repair shop to intake devices, save a local record in SQLite, and generate a one-page PDF receipt (Company Copy + Customer Copy). **No cloud or third-party services** are used.

## What it does

- **Create jobsheet**: Enter customer (name, phone), printer (model, serial), and symptom.
- **Validate & save**: Verifies required fields and enforces a 10-digit phone number. Saves to local `jobsheet.db`.
- **Auto-generate code**: `YYYYMMDD-XXX` using a **daily counter**.
- **Generate receipt**: Produces an A4 PDF with two sections (Company Copy & Customer Copy) including shop header, timestamp, code, and a details table. Tries to open the PDF automatically.
- **Search**: Find records by partial **name**, **phone digits**, or **serial**.

## Install & Run (from source)

1. Install Python 3.9+
2. In a terminal:
   ```bash
   cd printer_jobsheet_app
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate

   pip install -r requirements.txt
   python app.py
   ```

## Build a Windows `.exe` (no cloud)

Use **PyInstaller** to create a single-file executable you can run on your Windows machine **without Python installed**.

1. In your activated virtual environment:
   ```bash
   pip install pyinstaller
   ```
2. Build the exe:
   ```bash
   pyinstaller --onefile --name PrinterJobsheet app.py
   ```
3. Your exe will appear under `dist/PrinterJobsheet.exe`.

> Tip: You can double-click the exe, or run from `cmd`/PowerShell: `.\dist\PrinterJobsheet.exe`

### macOS/Linux binary (optional)

```bash
pip install pyinstaller
pyinstaller --onefile --name printer_jobsheet app.py
# Binary at dist/printer_jobsheet
```

## Customize the shop header

Edit the constants near the top of `app.py`:
```python
SHOP_NAME = "Your Printer Service Center"
SHOP_ADDRESS = "123, Main Road, Your City - 600000"
SHOP_PHONE = "+91-90000 00000"
```

## Database schema

`jobsheet` table:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `code` TEXT UNIQUE (`YYYYMMDD-XXX`)
- `date` TEXT (`YYYY-MM-DD`)
- `daily_counter` INTEGER (1,2,3... per date)
- `customer_name`, `phone`, `model`, `serial`, `symptom`
- `created_at` TEXT (local timestamp)

SQLite file: `jobsheet.db` (created in project directory on first run).

## Receipt file naming

```
receipts/jobsheet_<code>_<customer>.pdf
```

Customer name is sanitized to safe filename characters.

## Why this is useful

- Fast intake at the counter
- Consistent receipts for customers
- Simple on-disk database for quick lookups and audits

## Limitations / Next steps

- No edit/delete/status tracking (e.g., Received→Repair→Ready).
- Basic phone validation (India 10-digit assumption).
- Single-user console app (local-only).
- Potential enhancements: email/WhatsApp PDF share, GST/invoice fields, technician assignment, export to CSV, backup/restore.

## Troubleshooting

- If you see: `Missing dependency 'fpdf2'`, run `pip install fpdf2`.
- If the PDF does not auto-open, check the generated path printed in the console and open it manually.
- If building an exe, Windows Defender/SmartScreen may show a warning for unsigned apps. Choose "Run anyway" if you trust your own build.
