from flask import Flask, render_template, request, send_file, flash
import os
from jobsheet_logic import init_db, insert_jobsheet, fetch_jobs_by, generate_pdf, get_daily_next_counter, generate_code
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for flash messages

# Initialize DB connection
conn = init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        try:
            customer_name = request.form["customer_name"]
            phone = request.form["phone"]
            model = request.form["model"]
            serial = request.form["serial"]
            symptom = request.form["symptom"]

            today = date.today()
            daily_counter = get_daily_next_counter(conn, today)
            code = generate_code(today, daily_counter)
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            record = {
                "code": code,
                "date": today.isoformat(),
                "daily_counter": daily_counter,
                "customer_name": customer_name,
                "phone": phone,
                "model": model,
                "serial": serial,
                "symptom": symptom,
                "created_at": created_at
            }

            insert_jobsheet(conn, record)
            pdf_path = generate_pdf(record)

            flash(f"Jobsheet created! Code: {code}", "success")
            return send_file(pdf_path, as_attachment=True)

        except Exception as e:
            flash(f"Error: {e}", "danger")

    return render_template("create.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    results = []
    if request.method == "POST":
        customer = request.form.get("customer")
        phone = request.form.get("phone")
        serial = request.form.get("serial")
        results = fetch_jobs_by(conn, customer, phone, serial)
    return render_template("search.html", results=results)

if __name__ == "__main__":
    app.run(debug=True)
