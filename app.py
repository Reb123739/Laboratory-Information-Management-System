import streamlit as st
import sqlite3
import random
import string
import pandas as pd
from datetime import date, datetime
from fpdf import FPDF

DB_NAME = "lims.db"

st.set_page_config(page_title="LIMS", page_icon="🧪", layout="wide")

def check_login(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM user WHERE username = ? AND password = ?",
        (username, password)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_patient(name, date_registered):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO patient (name, date_registered) VALUES (?, ?)",
        (name, date_registered)
    )
    conn.commit()
    conn.close()

def get_all_patients():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, date_registered FROM patient")
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_test_request(patient_id, test_type, date_requested):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO test_request (patient_id, test_type, date_requested) VALUES (?, ?, ?)",
        (patient_id, test_type, date_requested)
    )
    conn.commit()
    conn.close()

def get_all_test_requests():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT test_request.id, patient.name, test_request.test_type, test_request.date_requested
        FROM test_request
        JOIN patient ON test_request.patient_id = patient.id
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def generate_specimen_code():
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"SPC-{suffix}"

def add_specimen(test_id, specimen_code, status, last_updated):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO specimen (test_id, specimen_code, status, last_updated) VALUES (?, ?, ?, ?)",
        (test_id, specimen_code, status, last_updated)
    )
    conn.commit()
    conn.close()

def get_all_specimens():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT specimen.id, patient.name, test_request.test_type, specimen.specimen_code,
               specimen.status, specimen.last_updated
        FROM specimen
        JOIN test_request ON specimen.test_id = test_request.id
        JOIN patient ON test_request.patient_id = patient.id
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_specimen_status(specimen_id, new_status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE specimen SET status = ?, last_updated = ? WHERE id = ?",
        (new_status, str(datetime.now()), specimen_id)
    )
    conn.commit()
    conn.close()

def add_result(specimen_id, result_value, validated, date_tested):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO result (specimen_id, result_value, validated, date_tested) VALUES (?, ?, ?, ?)",
        (specimen_id, result_value, validated, date_tested)
    )
    conn.commit()
    conn.close()

def get_all_results():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT result.id, patient.name, test_request.test_type, specimen.specimen_code,
               result.result_value, result.validated, result.date_tested
        FROM result
        JOIN specimen ON result.specimen_id = specimen.id
        JOIN test_request ON specimen.test_id = test_request.id
        JOIN patient ON test_request.patient_id = patient.id
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_full_report():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT patient.name AS Patient,
               test_request.test_type AS Test,
               specimen.specimen_code AS Specimen,
               specimen.status AS Status,
               result.result_value AS Result,
               result.validated AS Validated,
               result.date_tested AS Date_Tested
        FROM patient
        JOIN test_request ON test_request.patient_id = patient.id
        JOIN specimen ON specimen.test_id = test_request.id
        LEFT JOIN result ON result.specimen_id = specimen.id
        ORDER BY patient.name
    """)
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    conn.close()
    return columns, rows

def generate_patient_pdf(patient_name, records):
    """Builds a one-patient lab report as a PDF and returns it as bytes."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Laboratory Report", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Patient: {patient_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Date Generated: {date.today()}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    col_widths = [40, 35, 25, 45, 25]
    headers = ["Test", "Specimen", "Status", "Result", "Validated"]

    pdf.set_font("Helvetica", "B", 10)
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 8, h, border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    for r in records:
        pdf.cell(col_widths[0], 8, str(r.get("Test", "")), border=1)
        pdf.cell(col_widths[1], 8, str(r.get("Specimen", "")), border=1)
        pdf.cell(col_widths[2], 8, str(r.get("Status", "")), border=1)
        result_val = r.get("Result")
        pdf.cell(col_widths[3], 8, str(result_val) if result_val else "Pending", border=1)
        pdf.cell(col_widths[4], 8, str(r.get("Validated", "")), border=1)
        pdf.ln()

    return bytes(pdf.output())

def login_screen():
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #e6f2ff 0%, #ffffff 100%);
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(
            """
            <div style="text-align:center; margin-top:60px; margin-bottom:20px;">
                <div style="font-size:48px;">🧪</div>
                <h2 style="margin-bottom:0;">Laboratory Information<br>Management System</h2>
                <p style="color:gray;">Please sign in to continue</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        with st.container(border=True):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            st.write("")
            if st.button("Log In", use_container_width=True, type="primary"):
                if check_login(username, password):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

def patient_registration_screen():
    st.header("Patient Registration")
    with st.form("patient_form"):
        name = st.text_input("Patient Name")
        reg_date = st.date_input("Date Registered", value=date.today())
        submitted = st.form_submit_button("Register Patient")
        if submitted:
            if name.strip() == "":
                st.error("Please enter a patient name.")
            else:
                add_patient(name, str(reg_date))
                st.success(f"Patient '{name}' registered successfully.")

    st.subheader("Registered Patients")
    patients = get_all_patients()
    if patients:
        st.table(patients)
    else:
        st.write("No patients registered yet.")

def test_request_screen():
    st.header("Test Request")
    patients = get_all_patients()
    if not patients:
        st.warning("No patients registered yet. Please register a patient first.")
        return

    patient_options = {f"{p[1]} (ID {p[0]})": p[0] for p in patients}
    with st.form("test_form"):
        selected_patient = st.selectbox("Select Patient", list(patient_options.keys()))
        test_type = st.text_input("Test Type (e.g. Blood Test, Urine Test)")
        req_date = st.date_input("Date Requested", value=date.today())
        submitted = st.form_submit_button("Create Test Request")
        if submitted:
            if test_type.strip() == "":
                st.error("Please enter a test type.")
            else:
                patient_id = patient_options[selected_patient]
                add_test_request(patient_id, test_type, str(req_date))
                st.success(f"Test request '{test_type}' created for {selected_patient}.")

    st.subheader("All Test Requests")
    requests = get_all_test_requests()
    if requests:
        st.table(requests)
    else:
        st.write("No test requests yet.")

def specimen_tracking_screen():
    st.header("Specimen Tracking")
    requests = get_all_test_requests()
    if not requests:
        st.warning("No test requests yet. Please create a test request first.")
        return

    request_options = {f"{r[1]} — {r[2]} (Request ID {r[0]})": r[0] for r in requests}
    st.subheader("Register a New Specimen")
    with st.form("specimen_form"):
        selected_request = st.selectbox("Select Test Request", list(request_options.keys()))
        submitted = st.form_submit_button("Create Specimen")
        if submitted:
            test_id = request_options[selected_request]
            code = generate_specimen_code()
            add_specimen(test_id, code, "received", str(datetime.now()))
            st.success(f"Specimen {code} created and marked as 'received'.")

    st.subheader("Update Specimen Status")
    specimens = get_all_specimens()
    if specimens:
        specimen_options = {f"{s[3]} — {s[1]} ({s[2]}) — currently: {s[4]}": s[0] for s in specimens}
        selected_specimen = st.selectbox("Select Specimen to Update", list(specimen_options.keys()))
        new_status = st.selectbox("New Status", ["received", "in progress", "completed"])
        if st.button("Update Status"):
            specimen_id = specimen_options[selected_specimen]
            update_specimen_status(specimen_id, new_status)
            st.success("Specimen status updated.")
            st.rerun()

    st.subheader("All Specimens")
    specimens = get_all_specimens()
    if specimens:
        st.table(specimens)
    else:
        st.write("No specimens yet.")

def result_entry_screen():
    st.header("Result Entry")

    specimens = get_all_specimens()
    if not specimens:
        st.warning("No specimens yet. Please create a specimen first.")
        return

    specimen_options = {f"{s[3]} — {s[1]} ({s[2]}) — status: {s[4]}": s[0] for s in specimens}

    with st.form("result_form"):
        selected_specimen = st.selectbox("Select Specimen", list(specimen_options.keys()))
        result_value = st.text_input("Result (e.g. Normal, 5.6 mg/dL)")
        validated = st.checkbox("Mark as validated (reviewed)")
        test_date = st.date_input("Date Tested", value=date.today())
        submitted = st.form_submit_button("Save Result")

        if submitted:
            if result_value.strip() == "":
                st.error("Please enter a result value.")
            else:
                specimen_id = specimen_options[selected_specimen]
                add_result(specimen_id, result_value, int(validated), str(test_date))
                st.success("Result saved successfully.")

    st.subheader("All Results")
    results = get_all_results()
    if results:
        st.table(results)
    else:
        st.write("No results yet.")

def report_screen():
    st.header("Laboratory Report")

    columns, rows = get_full_report()

    if not rows:
        st.write("No data to report yet.")
        return

    df = pd.DataFrame(rows, columns=columns)
    df["Validated"] = df["Validated"].map({1: "Yes", 0: "No", None: "Pending"})

    st.subheader("All Records")
    patient_filter = st.text_input("Filter by patient name (optional)")
    filtered_df = df
    if patient_filter.strip() != "":
        filtered_df = df[df["Patient"].str.contains(patient_filter, case=False, na=False)]

    st.dataframe(filtered_df, use_container_width=True)

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Full Table as CSV",
        data=csv,
        file_name="lims_report.csv",
        mime="text/csv",
    )

    st.divider()
    st.subheader("Generate a Printable PDF Report for One Patient")
    unique_patients = sorted(df["Patient"].unique())
    selected_patient = st.selectbox("Select Patient", unique_patients, key="pdf_patient")

    if st.button("Generate PDF Report"):
        patient_records = df[df["Patient"] == selected_patient].to_dict("records")
        pdf_bytes = generate_patient_pdf(selected_patient, patient_records)
        st.download_button(
            label=f"Download {selected_patient}'s PDF Report",
            data=pdf_bytes,
            file_name=f"{selected_patient.replace(' ', '_')}_report.pdf",
            mime="application/pdf",
        )

# --- Main app logic ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_screen()
else:
    st.sidebar.title("🧪 LIMS Menu")
    page = st.sidebar.radio("Go to", ["Patient Registration", "Test Request", "Specimen Tracking", "Result Entry", "Report"])

    if page == "Patient Registration":
        patient_registration_screen()
    elif page == "Test Request":
        test_request_screen()
    elif page == "Specimen Tracking":
        specimen_tracking_screen()
    elif page == "Result Entry":
        result_entry_screen()
    elif page == "Report":
        report_screen()