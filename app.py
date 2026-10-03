import streamlit as st
import sqlite3
import random
import string
import pandas as pd
from datetime import date, datetime
from fpdf import FPDF
import hashlib

DB_NAME = "lims.db"

st.set_page_config(
    page_title="LIMS",
    page_icon="🧪",
    layout="wide"
)


# =========================================================
# DATABASE SETUP
# =========================================================

def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("PRAGMA table_info(user)")
    columns = [column[1] for column in cursor.fetchall()]

    if "full_name" not in columns:
        cursor.execute(
            "ALTER TABLE user ADD COLUMN full_name TEXT"
        )

    conn.commit()
    conn.close()


setup_database()


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# USER REGISTRATION
# =========================================================

def register_user(full_name, username, password):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        username = username.strip().lower()

        hashed_password = hash_password(password)

        cursor.execute(
            """
            INSERT INTO user
            (full_name, username, password)
            VALUES (?, ?, ?)
            """,
            (
                full_name.strip(),
                username,
                hashed_password
            )
        )

        conn.commit()

        return True, "Account created successfully."

    except sqlite3.IntegrityError:

        return False, "Username already exists."

    finally:

        conn.close()


# =========================================================
# USER LOGIN
# =========================================================

def check_login(username, password):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    username = username.strip().lower()

    hashed_password = hash_password(password)

    # -----------------------------------------------------
    # Check hashed password
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT id, full_name, username
        FROM user
        WHERE username = ?
        AND password = ?
        """,
        (
            username,
            hashed_password
        )
    )

    result = cursor.fetchone()

    # -----------------------------------------------------
    # Check old plain-text password
    # This keeps existing accounts working.
    # -----------------------------------------------------

    if result is None:

        cursor.execute(
            """
            SELECT id, full_name, username
            FROM user
            WHERE username = ?
            AND password = ?
            """,
            (
                username,
                password
            )
        )

        result = cursor.fetchone()

        # -------------------------------------------------
        # Upgrade old password to hashed password
        # -------------------------------------------------

        if result is not None:

            cursor.execute(
                """
                UPDATE user
                SET password = ?
                WHERE id = ?
                """,
                (
                    hashed_password,
                    result[0]
                )
            )

            conn.commit()

    conn.close()

    return result


# =========================================================
# PATIENT FUNCTIONS
# =========================================================

def add_patient(name, date_registered):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO patient
        (name, date_registered)
        VALUES (?, ?)
        """,
        (
            name,
            date_registered
        )
    )

    conn.commit()
    conn.close()


def get_all_patients():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, date_registered
        FROM patient
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


# =========================================================
# TEST REQUEST FUNCTIONS
# =========================================================

def add_test_request(
    patient_id,
    test_type,
    date_requested
):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO test_request
        (patient_id, test_type, date_requested)
        VALUES (?, ?, ?)
        """,
        (
            patient_id,
            test_type,
            date_requested
        )
    )

    conn.commit()
    conn.close()


def get_all_test_requests():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            test_request.id,
            patient.name,
            test_request.test_type,
            test_request.date_requested
        FROM test_request
        JOIN patient
        ON test_request.patient_id = patient.id
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


# =========================================================
# SPECIMEN FUNCTIONS
# =========================================================

def generate_specimen_code():

    suffix = ''.join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=6
        )
    )

    return f"SPC-{suffix}"


def add_specimen(
    test_id,
    specimen_code,
    status,
    last_updated
):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO specimen
        (test_id, specimen_code, status, last_updated)
        VALUES (?, ?, ?, ?)
        """,
        (
            test_id,
            specimen_code,
            status,
            last_updated
        )
    )

    conn.commit()
    conn.close()


def get_all_specimens():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            specimen.id,
            patient.name,
            test_request.test_type,
            specimen.specimen_code,
            specimen.status,
            specimen.last_updated
        FROM specimen
        JOIN test_request
        ON specimen.test_id = test_request.id
        JOIN patient
        ON test_request.patient_id = patient.id
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def update_specimen_status(
    specimen_id,
    new_status
):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE specimen
        SET status = ?,
            last_updated = ?
        WHERE id = ?
        """,
        (
            new_status,
            str(datetime.now()),
            specimen_id
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# RESULT FUNCTIONS
# =========================================================

def add_result(
    specimen_id,
    result_value,
    validated,
    date_tested
):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO result
        (specimen_id, result_value, validated, date_tested)
        VALUES (?, ?, ?, ?)
        """,
        (
            specimen_id,
            result_value,
            validated,
            date_tested
        )
    )

    conn.commit()
    conn.close()


def get_all_results():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            result.id,
            patient.name,
            test_request.test_type,
            specimen.specimen_code,
            result.result_value,
            result.validated,
            result.date_tested
        FROM result
        JOIN specimen
        ON result.specimen_id = specimen.id
        JOIN test_request
        ON specimen.test_id = test_request.id
        JOIN patient
        ON test_request.patient_id = patient.id
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


# =========================================================
# REPORT DATA
# =========================================================

def get_full_report():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            patient.name AS Patient,
            test_request.test_type AS Test,
            specimen.specimen_code AS Specimen,
            specimen.status AS Status,
            result.result_value AS Result,
            result.validated AS Validated,
            result.date_tested AS Date_Tested
        FROM patient
        JOIN test_request
        ON test_request.patient_id = patient.id
        JOIN specimen
        ON specimen.test_id = test_request.id
        LEFT JOIN result
        ON result.specimen_id = specimen.id
        ORDER BY patient.name
    """)

    rows = cursor.fetchall()

    columns = [
        description[0]
        for description in cursor.description
    ]

    conn.close()

    return columns, rows


# =========================================================
# PDF REPORT
# =========================================================

def generate_patient_pdf(
    patient_name,
    records,
    generated_by
):

    pdf = FPDF()
    pdf.add_page()

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    pdf.set_font(
        "Helvetica",
        "B",
        16
    )

    pdf.cell(
        0,
        10,
        "Laboratory Report",
        new_x="LMARGIN",
        new_y="NEXT",
        align="C"
    )

    pdf.ln(3)

    # -----------------------------------------------------
    # PATIENT INFORMATION
    # -----------------------------------------------------

    pdf.set_font(
        "Helvetica",
        "",
        11
    )

    pdf.cell(
        0,
        8,
        f"Patient: {patient_name}",
        new_x="LMARGIN",
        new_y="NEXT"
    )

    pdf.cell(
        0,
        8,
        f"Date Generated: {date.today()}",
        new_x="LMARGIN",
        new_y="NEXT"
    )

    pdf.ln(4)

    # -----------------------------------------------------
    # RESULT TABLE
    # -----------------------------------------------------

    col_widths = [
        40,
        35,
        25,
        45,
        25
    ]

    headers = [
        "Test",
        "Specimen",
        "Status",
        "Result",
        "Validated"
    ]

    pdf.set_font(
        "Helvetica",
        "B",
        10
    )

    for width, header in zip(
        col_widths,
        headers
    ):

        pdf.cell(
            width,
            8,
            header,
            border=1
        )

    pdf.ln()

    pdf.set_font(
        "Helvetica",
        "",
        10
    )

    for record in records:

        pdf.cell(
            col_widths[0],
            8,
            str(record.get("Test", "")),
            border=1
        )

        pdf.cell(
            col_widths[1],
            8,
            str(record.get("Specimen", "")),
            border=1
        )

        pdf.cell(
            col_widths[2],
            8,
            str(record.get("Status", "")),
            border=1
        )

        result_value = record.get("Result")

        if (
            result_value is None
            or str(result_value).strip() == ""
        ):

            result_text = "Not entered"

        else:

            result_text = str(result_value)

        pdf.cell(
            col_widths[3],
            8,
            result_text,
            border=1
        )

        validated = record.get("Validated")

        if validated == 1:

            validated_text = "Yes"

        elif validated == 0:

            validated_text = "No"

        else:

            validated_text = "Not entered"

        pdf.cell(
            col_widths[4],
            8,
            validated_text,
            border=1
        )

        pdf.ln()

    # -----------------------------------------------------
    # REPORT GENERATOR
    # -----------------------------------------------------

    pdf.ln(10)

    pdf.set_font(
        "Helvetica",
        "",
        10
    )

    pdf.cell(
        0,
        7,
        f"Report Generated By: {generated_by}",
        new_x="LMARGIN",
        new_y="NEXT"
    )

    pdf.cell(
        0,
        7,
        "Laboratory Information Management System",
        new_x="LMARGIN",
        new_y="NEXT"
    )

    return bytes(pdf.output())


# =========================================================
# LOGIN AND SIGNUP SCREEN
# =========================================================

def login_screen():

    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(
                135deg,
                #e6f2ff 0%,
                #ffffff 100%
            );
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(
        [1, 1.2, 1]
    )

    with col2:

        st.markdown("""
            <h2 style="text-align:center; margin-bottom:5px;">
                Laboratory Information Management System
            </h2>

            <p style="text-align:center; color:gray; font-size:15px;">
                Secure Laboratory Information and Records Management
            </p>
        """, unsafe_allow_html=True)

        login_tab, signup_tab = st.tabs(
            [
                "🔐 Log In",
                "📝 Sign Up"
            ]
        )

        # =================================================
        # LOG IN
        # =================================================

        with login_tab:

            with st.container(border=True):

                username = st.text_input(
                    "Username",
                    key="login_username"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    key="login_password"
                )

                st.write("")

                if st.button(
                    "Log In",
                    use_container_width=True,
                    type="primary"
                ):

                    if (
                        username.strip() == ""
                        or password == ""
                    ):

                        st.error(
                            "Please enter your username and password."
                        )

                    else:

                        user = check_login(
                            username,
                            password
                        )

                        if user:

                            st.session_state.logged_in = True

                            st.session_state.user_id = user[0]

                            st.session_state.user_full_name = (
                                user[1]
                                if user[1]
                                else user[2]
                            )

                            st.session_state.username = user[2]

                            st.rerun()

                        else:

                            st.error(
                                "Incorrect username or password."
                            )

        # =================================================
        # SIGN UP
        # =================================================

        with signup_tab:

            with st.container(border=True):

                full_name = st.text_input(
                    "Full Name",
                    placeholder="Enter your full name",
                    key="signup_full_name"
                )

                username = st.text_input(
                    "Create Username",
                    placeholder="Choose a username",
                    key="signup_username"
                )

                password = st.text_input(
                    "Create Password",
                    type="password",
                    key="signup_password"
                )

                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    key="signup_confirm_password"
                )

                st.write("")

                if st.button(
                    "Create Account",
                    use_container_width=True,
                    type="primary"
                ):

                    if not full_name.strip():

                        st.error(
                            "Please enter your full name."
                        )

                    elif not username.strip():

                        st.error(
                            "Please enter a username."
                        )

                    elif not password:

                        st.error(
                            "Please create a password."
                        )

                    elif len(password) < 6:

                        st.error(
                            "Password must be at least 6 characters."
                        )

                    elif password != confirm_password:

                        st.error(
                            "Passwords do not match."
                        )

                    else:

                        success, message = register_user(
                            full_name,
                            username,
                            password
                        )

                        if success:

                            st.success(message)

                            st.info(
                                "You can now log in using your new account."
                            )

                        else:

                            st.error(message)


# =========================================================
# PATIENT REGISTRATION
# =========================================================

def patient_registration_screen():

    st.header("Patient Registration")

    with st.form("patient_form"):

        name = st.text_input(
            "Patient Name"
        )

        reg_date = st.date_input(
            "Date Registered",
            value=date.today()
        )

        submitted = st.form_submit_button(
            "Register Patient"
        )

        if submitted:

            if name.strip() == "":

                st.error(
                    "Please enter a patient name."
                )

            else:

                add_patient(
                    name,
                    str(reg_date)
                )

                st.success(
                    f"Patient '{name}' registered successfully."
                )

    st.subheader(
        "Registered Patients"
    )

    patients = get_all_patients()

    if patients:

        st.table(patients)

    else:

        st.write(
            "No patients registered yet."
        )


# =========================================================
# TEST REQUEST
# =========================================================

def test_request_screen():

    st.header("Test Request")

    patients = get_all_patients()

    if not patients:

        st.warning(
            "No patients registered yet. "
            "Please register a patient first."
        )

        return

    patient_options = {
        f"{p[1]} (ID {p[0]})": p[0]
        for p in patients
    }

    with st.form("test_form"):

        selected_patient = st.selectbox(
            "Select Patient",
            list(patient_options.keys())
        )

        test_type = st.text_input(
            "Test Type (e.g. Blood Test, Urine Test)"
        )

        req_date = st.date_input(
            "Date Requested",
            value=date.today()
        )

        submitted = st.form_submit_button(
            "Create Test Request"
        )

        if submitted:

            if test_type.strip() == "":

                st.error(
                    "Please enter a test type."
                )

            else:

                patient_id = patient_options[
                    selected_patient
                ]

                add_test_request(
                    patient_id,
                    test_type,
                    str(req_date)
                )

                st.success(
                    f"Test request '{test_type}' "
                    f"created for {selected_patient}."
                )

    st.subheader(
        "All Test Requests"
    )

    requests = get_all_test_requests()

    if requests:

        st.table(requests)

    else:

        st.write(
            "No test requests yet."
        )


# =========================================================
# SPECIMEN TRACKING
# =========================================================

def specimen_tracking_screen():

    st.header(
        "Specimen Tracking"
    )

    requests = get_all_test_requests()

    if not requests:

        st.warning(
            "No test requests yet. "
            "Please create a test request first."
        )

        return

    request_options = {
        f"{r[1]} — {r[2]} "
        f"(Request ID {r[0]})": r[0]
        for r in requests
    }

    st.subheader(
        "Register a New Specimen"
    )

    with st.form("specimen_form"):

        selected_request = st.selectbox(
            "Select Test Request",
            list(request_options.keys())
        )

        submitted = st.form_submit_button(
            "Create Specimen"
        )

        if submitted:

            test_id = request_options[
                selected_request
            ]

            code = generate_specimen_code()

            add_specimen(
                test_id,
                code,
                "received",
                str(datetime.now())
            )

            st.success(
                f"Specimen {code} created "
                f"and marked as 'received'."
            )

    st.subheader(
        "Update Specimen Status"
    )

    specimens = get_all_specimens()

    if specimens:

        specimen_options = {
            f"{s[3]} — {s[1]} "
            f"({s[2]}) — currently: {s[4]}": s[0]
            for s in specimens
        }

        selected_specimen = st.selectbox(
            "Select Specimen to Update",
            list(specimen_options.keys())
        )

        new_status = st.selectbox(
            "New Status",
            [
                "received",
                "in progress",
                "completed"
            ]
        )

        if st.button(
            "Update Status"
        ):

            specimen_id = specimen_options[
                selected_specimen
            ]

            update_specimen_status(
                specimen_id,
                new_status
            )

            st.success(
                "Specimen status updated."
            )

            st.rerun()

    st.subheader(
        "All Specimens"
    )

    specimens = get_all_specimens()

    if specimens:

        st.table(specimens)

    else:

        st.write(
            "No specimens yet."
        )


# =========================================================
# RESULT ENTRY
# =========================================================

def result_entry_screen():

    st.header(
        "Result Entry"
    )

    specimens = get_all_specimens()

    if not specimens:

        st.warning(
            "No specimens yet. "
            "Please create a specimen first."
        )

        return

    specimen_options = {
        f"{s[3]} — {s[1]} "
        f"({s[2]}) — status: {s[4]}": s[0]
        for s in specimens
    }

    with st.form("result_form"):

        selected_specimen = st.selectbox(
            "Select Specimen",
            list(specimen_options.keys())
        )

        result_value = st.text_input(
            "Result (e.g. Normal, 5.6 mg/dL)"
        )

        validated = st.checkbox(
            "Mark as validated (reviewed)"
        )

        test_date = st.date_input(
            "Date Tested",
            value=date.today()
        )

        submitted = st.form_submit_button(
            "Save Result"
        )

        if submitted:

            if result_value.strip() == "":

                st.error(
                    "Please enter a result value."
                )

            else:

                specimen_id = specimen_options[
                    selected_specimen
                ]

                add_result(
                    specimen_id,
                    result_value,
                    int(validated),
                    str(test_date)
                )

                st.success(
                    "Result saved successfully."
                )

    st.subheader(
        "All Results"
    )

    results = get_all_results()

    if results:

        st.table(results)

    else:

        st.write(
            "No results yet."
        )


# =========================================================
# REPORT
# =========================================================

def report_screen():

    st.header(
        "Laboratory Report"
    )

    columns, rows = get_full_report()

    if not rows:

        st.write(
            "No data to report yet."
        )

        return

    df = pd.DataFrame(
        rows,
        columns=columns
    )

    # -----------------------------------------------------
    # Display validation status clearly
    # -----------------------------------------------------

    df["Validated"] = df[
        "Validated"
    ].map(
        {
            1: "Yes",
            0: "No"
        }
    )

    # Records with no result have no validation status.
    df["Validated"] = df["Validated"].fillna(
        "Not entered"
    )

    # -----------------------------------------------------
    # Display results
    # -----------------------------------------------------

    st.subheader(
        "All Records"
    )

    patient_filter = st.text_input(
        "Filter by patient name (optional)"
    )

    filtered_df = df

    if patient_filter.strip() != "":

        filtered_df = df[
            df["Patient"].str.contains(
                patient_filter,
                case=False,
                na=False
            )
        ]

    st.dataframe(
        filtered_df,
        use_container_width=True
    )

    # -----------------------------------------------------
    # CSV DOWNLOAD
    # -----------------------------------------------------

    csv = filtered_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Full Table as CSV",
        data=csv,
        file_name="lims_report.csv",
        mime="text/csv"
    )

    st.divider()

    # -----------------------------------------------------
    # PDF REPORT
    # -----------------------------------------------------

    st.subheader(
        "Generate a Printable PDF Report for One Patient"
    )

    unique_patients = sorted(
        df["Patient"].dropna().unique()
    )

    if not unique_patients:

        st.write(
            "No patients available for PDF generation."
        )

        return

    selected_patient = st.selectbox(
        "Select Patient",
        unique_patients,
        key="pdf_patient"
    )

    if st.button(
        "Generate PDF Report",
        type="primary"
    ):

        patient_records = df[
            df["Patient"] == selected_patient
        ].copy()

        # Convert display value back for PDF generation.
        patient_records["Validated"] = (
            patient_records["Validated"].replace(
                {
                    "Yes": 1,
                    "No": 0,
                    "Not entered": None
                }
            )
        )

        patient_records = patient_records.to_dict(
            "records"
        )

        # Get the name of the currently logged-in user.
        generated_by = st.session_state.get(
            "user_full_name",
            "LIMS User"
        )

        pdf_bytes = generate_patient_pdf(
            selected_patient,
            patient_records,
            generated_by
        )

        st.success(
            f"Report generated by {generated_by}."
        )

        st.download_button(
            label=(
                f"Download {selected_patient}'s "
                f"PDF Report"
            ),
            data=pdf_bytes,
            file_name=(
                f"{selected_patient.replace(' ', '_')}"
                "_report.pdf"
            ),
            mime="application/pdf"
        )


# =========================================================
# MAIN APP LOGIC
# =========================================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False


if not st.session_state.logged_in:

    login_screen()

else:

    # =====================================================
    # SIDEBAR
    # =====================================================

    st.sidebar.title(
        "🧪 LIMS Menu"
    )

    st.sidebar.success(
        f"Logged in as:\n"
        f"{st.session_state.user_full_name}"
    )

    page = st.sidebar.radio(
        "Go to",
        [
            "Patient Registration",
            "Test Request",
            "Specimen Tracking",
            "Result Entry",
            "Report"
        ]
    )

    st.sidebar.divider()

    if st.sidebar.button(
        "🚪 Log Out",
        use_container_width=True
    ):

        for key in [
            "logged_in",
            "user_id",
            "user_full_name",
            "username"
        ]:

            if key in st.session_state:

                del st.session_state[key]

        st.session_state.logged_in = False

        st.rerun()

    # =====================================================
    # PAGE ROUTING
    # =====================================================

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