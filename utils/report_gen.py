import csv
import io
from database.connection import get_db_connection

def generate_csv_report(society_id):
    """
    Generates a CSV string containing all financial transactions 
    (Maintenance, Other Income, and Expenses) for a specific society.
    """
    # Use StringIO to create the file in memory (RAM), not on the hard drive
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 1. Write the Header Row
    writer.writerow(['Date', 'Transaction Type', 'Category / Source', 'Amount', 'Details'])
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 2. Fetch Miscellaneous Income (Donations, etc.)
        cur.execute("""
            SELECT income_date, 'Other Income', source_name, amount, description 
            FROM other_income 
            WHERE society_id = %s
        """, (society_id,))
        for row in cur.fetchall():
            writer.writerow(row)
            
        # 3. Fetch Expenses (Repairs, Salaries, etc.)
        cur.execute("""
            SELECT expense_date, 'Expense', category, amount, description 
            FROM expenses 
            WHERE society_id = %s
        """, (society_id,))
        for row in cur.fetchall():
            writer.writerow(row)
            
        # 4. Fetch Paid Maintenance (Treated as Income)
        cur.execute("""
            SELECT m.created_at::date, 'Maintenance', f.flat_number, m.amount, m.month || ' ' || m.year
            FROM maintenance m
            JOIN flats f ON m.flat_id = f.id
            JOIN blocks b ON f.block_id = b.id
            WHERE b.society_id = %s AND m.status = 'paid'
        """, (society_id,))
        for row in cur.fetchall():
            writer.writerow(row)

    except Exception as e:
        print(f"Error generating CSV data: {e}")
    finally:
        cur.close()
        conn.close()
        
    return output.getvalue()
