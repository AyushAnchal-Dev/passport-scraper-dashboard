import sqlite3
import os

db_path = "dev_scraper.db"
if not os.path.exists(db_path):
    # Try parent directory
    db_path = "../dev_scraper.db"
    
if not os.path.exists(db_path):
    print("No dev_scraper.db found.")
else:
    print(f"Found database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    for table_tuple in tables:
        table_name = table_tuple[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"Table {table_name} count: {count}")
        
    cursor.execute("SELECT DISTINCT category FROM posts")
    categories = cursor.fetchall()
    print("Categories in DB:", [c[0] for c in categories])
    
    cursor.execute("SELECT category, COUNT(*) FROM posts GROUP BY category")
    counts = cursor.fetchall()
    print("Category counts:")
    for cat, cnt in counts:
        print(f"  {cat}: {cnt}")
        
    conn.close()
