from fastmcp import FastMCP
import sqlite3

mcp = FastMCP(name="expense-tracker")

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

con = sqlite3.connect(DB_PATH, check_same_thread=False)



def initialise_db():
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            date TEXT NOT NULL,
            note TEXT
        )
    """)
    con.commit()

initialise_db()

@mcp.tool
def add_data(date, amount, category, subcategory="", note=""):
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO expenses (amount, category, subcategory, date, note)
        VALUES (?, ?, ?, ?, ?)
        """,
        (amount, category, subcategory, date, note)
    )
    con.commit()
    return {"status": "inserted"}

@mcp.tool
def list_data(start_date: str, end_date: str,category=""):
    """this tool list out data from a certain date to an end date also idf categpry is given then it finds out the sum of that particulat category"""
    cur = con.cursor()
    if category == "":
     cur.execute(
        """
        SELECT id, date, amount, category, subcategory, note
        FROM expenses
        WHERE date BETWEEN ? AND ?
        ORDER BY date
        """,
        (start_date, end_date)
    )
     rows = cur.fetchall()
     return {"count": len(rows), "data": rows}

    else:
     cur.execute(
        """
        SELECT SUM(amount)
        FROM expenses
        WHERE date BETWEEN ? AND ?
          AND category = ?
        """,
        (start_date, end_date, category)
    )
     total = cur.fetchone()[0] or 0

     return {
        "category": category,
        "sum": total
    }

@mcp.tool
def get_db_path():
    return {"db_path": DB_PATH}

@mcp.tool
def edit_data(id: int, data: dict):
    """
    Edit data provided by user as a dictionary for a given id.
    Only allowed columns will be updated.
    """
    cur = con.cursor()

    # Step 1: Check row exists
    cur.execute("SELECT * FROM expenses WHERE id = ?", (id,))
    row = cur.fetchone()
    if row is None:
        return {"message": "Not a valid row id"}

    # Step 2: Prepare update
    updates = []
    params = []
    columns_updated = []

    allowed_cols = ['date', 'category', 'subcategory', 'note', 'amount']

    for col, val in data.items():
        if col not in allowed_cols:
            return {"message": f"Invalid data parameter: {col}"}
        updates.append(f"{col} = ?")
        params.append(val)
        columns_updated.append(col)

    if len(updates) == 0:
        return {"message": "No data provided for any field"}

    # Step 3: Execute update
    params.append(id)
    sql = f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?"
    cur.execute(sql, params)
    con.commit()

    # Step 4: Return result
    return {"status": "updated", "fields_updated": columns_updated}

@mcp.tool
def delete_data(filters: dict):
    """
    Delete rows based on the fields provided in a dictionary.
    Allowed fields: 'id', 'category', 'date'
    """
    cur = con.cursor()

    allowed_cols = ["id", "category", "date"]

    # Step 1: Validate filters
    conditions = []
    params = []

    for col, val in filters.items():
        if col not in allowed_cols:
            return {"message": f"Cannot delete based on field: {col}"}
        conditions.append(f"{col} = ?")
        params.append(val)

    if not conditions:
        return {"message": "No valid fields provided for deletion"}

    # Step 2: Check if any rows exist
    check_sql = f"SELECT * FROM expenses WHERE {' AND '.join(conditions)}"
    cur.execute(check_sql, params)
    rows = cur.fetchall()
    if not rows:
        return {"message": "No matching rows found to delete"}

    # Step 3: Delete rows
    delete_sql = f"DELETE FROM expenses WHERE {' AND '.join(conditions)}"
    cur.execute(delete_sql, params)
    con.commit()

    return {
        "message": "Deleted successfully",
        "rows_deleted": len(rows),
        "filters_used": list(filters.keys())
    }

         

if __name__ == "__main__":
    mcp.run(transport='http',host='0.0.0.0',port=8000)
