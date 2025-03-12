import sqlite3

# Connect to the SQLite database
db_path = "data/chat_history.db"  # Change to your actual database file
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Fetch all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Print all tables and their contents
for table in tables:
    table_name = table[0]
    print(f"\nTable: {table_name}")
    
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    # Print column names
    columns = [desc[0] for desc in cursor.description]
    print(columns)
    
    # Print rows
    for row in rows:
        print(row)

# Close connection
conn.close()
