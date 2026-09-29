import sqlite3

DB_NAME = "lims.db"

def get_connection():
    """Opens a connection to the database file (creates it if it doesn't exist yet)."""
    return sqlite3.connect(DB_NAME)

def create_tables():
    """Creates all the tables we designed, if they don't already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # PATIENT
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date_registered TEXT NOT NULL
        )
    """)

    # USER (for login)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    # TEST REQUEST
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_request (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            test_type TEXT NOT NULL,
            date_requested TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patient (id)
        )
    """)

    # SPECIMEN
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS specimen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            specimen_code TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'received',
            last_updated TEXT NOT NULL,
            FOREIGN KEY (test_id) REFERENCES test_request (id)
        )
    """)

    # RESULT
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS result (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            specimen_id INTEGER NOT NULL,
            result_value TEXT NOT NULL,
            validated INTEGER NOT NULL DEFAULT 0,
            date_tested TEXT NOT NULL,
            FOREIGN KEY (specimen_id) REFERENCES specimen (id)
        )
    """)

    conn.commit()
    conn.close()
    print("Tables created successfully.")

if __name__ == "__main__":
    create_tables()