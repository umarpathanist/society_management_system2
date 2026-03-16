# import os
# import csv
# from database.connection import get_db_connection

# def seed_data():
#     """
#     Automated database seeder. 
#     Reads CSV files from 'csv_data' folder and populates PostgreSQL.
#     """
#     # Dynamic path to ensure it finds the csv_data folder inside the database directory
#     base_path = os.path.join(os.path.dirname(__file__), 'csv_data')
    
#     conn = get_db_connection()
#     cur = conn.cursor()

#     # Define tables and their corresponding CSV files in strict order
#     files_to_load = [
#         ('roles', 'roles.csv'),
#         ('societies', 'societies.csv'),
#         ('users', 'users.csv'),
#         ('blocks', 'blocks.csv'),
#         ('flats', 'flats.csv')
#     ]

#     try:
#         print("--- Starting Seeding Process ---")

#         # 1. Clean existing data (CASCADE handles dependencies)
#         cur.execute("TRUNCATE roles, societies, users, blocks, flats RESTART IDENTITY CASCADE;")
#         print("✅ Database truncated and IDs reset.")

#         for table_name, file_name in files_to_load:
#             file_path = os.path.join(base_path, file_name)
            
#             if not os.path.exists(file_path):
#                 print(f"⚠️ Skipping: {file_name} (File not found at {file_path})")
#                 continue

#             with open(file_path, 'r', encoding='utf-8') as f:
#                 reader = csv.DictReader(f)
#                 columns = reader.fieldnames
                
#                 # Dynamic SQL Generation
#                 col_names = ', '.join(columns)
#                 placeholders = ', '.join(['%s'] * len(columns))
#                 query = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
                
#                 for row in reader:
#                     processed_values = []
#                     for col in columns:
#                         val = row[col].strip()
                        
#                         # Data Type Conversion Logic
#                         if val.upper() == 'NULL' or val == '':
#                             processed_values.append(None)
#                         elif val.upper() == 'TRUE':
#                             processed_values.append(True)
#                         elif val.upper() == 'FALSE':
#                             processed_values.append(False)
#                         else:
#                             processed_values.append(val)
                    
#                     cur.execute(query, processed_values)
            
#             print(f"✅ Successfully loaded {file_name} into '{table_name}' table.")

#         # 2. Synchronize Postgres Sequences
#         # This prevents "Duplicate Key" errors when you try to add new data from the UI later.
#         for table_name, _ in files_to_load:
#             cur.execute(f"""
#                 SELECT setval(
#                     pg_get_serial_sequence('{table_name}', 'id'), 
#                     COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1, 
#                     false
#                 );
#             """)

#         conn.commit()
#         print("\n🏆 Database seeding completed successfully!")

#     except Exception as e:
#         print(f"\n❌ SEEDING FAILED: {e}")
#         conn.rollback()
#     finally:
#         cur.close()
#         conn.close()

# if __name__ == "__main__":
#     seed_data()

import os
import csv
from dotenv import load_dotenv # ADD THIS
from database.connection import get_db_connection

load_dotenv() # ADD THIS

def seed_data():
    """
    Automated database seeder. 
    Reads CSV files from 'csv_data' folder and populates PostgreSQL.
    Updated to include admin_societies and maintenance data.
    """
    # Dynamic path resolution to find 'csv_data' folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.join(script_dir, 'csv_data')
    
    conn = get_db_connection()
    cur = conn.cursor()

    # THE CRITICAL ORDER: Tables must be loaded in this specific order 
    # to avoid Foreign Key "relation does not exist" errors.
    files_to_load = [
        ('roles', 'roles.csv'),
        ('societies', 'societies.csv'),
        ('users', 'users.csv'),
        ('admin_societies', 'admin_societies.csv'),
        ('blocks', 'blocks.csv'),
        ('flats', 'flats.csv'),
        ('maintenance', 'maintenance.csv')
    ]

    try:
        print("--- [STARTING DATABASE SEEDING] ---")

        # 1. CLEAN ALL TABLES: 
        # RESTART IDENTITY resets the ID counters to 1.
        # CASCADE ensures all linked rows are removed together.
        all_tables = [t[0] for t in files_to_load]
        cur.execute(f"TRUNCATE {', '.join(all_tables)} RESTART IDENTITY CASCADE;")
        print("✅ All existing data cleared and ID sequences reset.")

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
                        
                        # Handle NULLs and Boolean Logic
                        if val.upper() == 'NULL' or val == '':
                            processed_values.append(None)
                        elif val.upper() == 'TRUE':
                            processed_values.append(True)
                        elif val.upper() == 'FALSE':
                            processed_values.append(False)
                        else:
                            processed_values.append(val)
                    
                    cur.execute(query, processed_values)
            
            print(f"✅ Successfully imported: {file_name} -> {table_name}")

        # 2. SYNCHRONIZE SEQUENCES:
        # Crucial for Postgres! This tells the DB that the next ID should start 
        # after the highest ID we just imported from the CSV.
        for table_name in all_tables:
            cur.execute(f"""
                SELECT setval(
                    pg_get_serial_sequence('{table_name}', 'id'), 
                    COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1, 
                    false
                );
            """)

        conn.commit()
        print("\n🏆 SUCCESS: Database seeding completed without errors!")

    except Exception as e:
        print(f"\n❌ SEEDING FAILED: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == "__main__":
    seed_data()
