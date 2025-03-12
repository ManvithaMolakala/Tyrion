import sqlite3
from tabulate import tabulate  # Install with: pip install tabulate

# Connect to the SQLite database
db_path = "src/data/chat_history.db"  # Change to your actual database file
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Fetch all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Print all tables and their contents in a readable format
for table in tables:
    table_name = table[0]
    print(f"\n{'='*40}\nTable: {table_name}\n{'='*40}")
    
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    # Print table data if it contains rows
    if rows:
        columns = [desc[0] for desc in cursor.description]  # Get column names
        print(tabulate(rows, headers=columns, tablefmt="grid"))
    else:
        print("No data found.")

# Close connection
conn.close()
