import os
import csv
from database.connection import get_db_connection

def seed_data():
    """
    Automated database seeder. 
    Reads CSV files from 'csv_data' folder and populates PostgreSQL.
    """
    # Dynamic path to ensure it finds the csv_data folder inside the database directory
    base_path = os.path.join(os.path.dirname(__file__), 'csv_data')
    
    conn = get_db_connection()
    cur = conn.cursor()

    # Define tables and their corresponding CSV files in strict order
    files_to_load = [
        ('roles', 'roles.csv'),
        ('societies', 'societies.csv'),
        ('users', 'users.csv'),
        ('blocks', 'blocks.csv'),
        ('flats', 'flats.csv')
    ]

    try:
        print("--- Starting Seeding Process ---")

        # 1. Clean existing data (CASCADE handles dependencies)
        cur.execute("TRUNCATE roles, societies, users, blocks, flats RESTART IDENTITY CASCADE;")
        print("✅ Database truncated and IDs reset.")

        for table_name, file_name in files_to_load:
            file_path = os.path.join(base_path, file_name)
            
            if not os.path.exists(file_path):
                print(f"⚠️ Skipping: {file_name} (File not found at {file_path})")
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                columns = reader.fieldnames
                
                # Dynamic SQL Generation
                col_names = ', '.join(columns)
                placeholders = ', '.join(['%s'] * len(columns))
                query = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
                
                for row in reader:
                    processed_values = []
                    for col in columns:
                        val = row[col].strip()
                        
                        # Data Type Conversion Logic
                        if val.upper() == 'NULL' or val == '':
                            processed_values.append(None)
                        elif val.upper() == 'TRUE':
                            processed_values.append(True)
                        elif val.upper() == 'FALSE':
                            processed_values.append(False)
                        else:
                            processed_values.append(val)
                    
                    cur.execute(query, processed_values)
            
            print(f"✅ Successfully loaded {file_name} into '{table_name}' table.")

        # 2. Synchronize Postgres Sequences
        # This prevents "Duplicate Key" errors when you try to add new data from the UI later.
        for table_name, _ in files_to_load:
            cur.execute(f"""
                SELECT setval(
                    pg_get_serial_sequence('{table_name}', 'id'), 
                    COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1, 
                    false
                );
            """)

        conn.commit()
        print("\n🏆 Database seeding completed successfully!")

    except Exception as e:
        print(f"\n❌ SEEDING FAILED: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed_data()