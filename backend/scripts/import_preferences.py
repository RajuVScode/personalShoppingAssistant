import pandas as pd
import psycopg2
import os
from psycopg2.extras import execute_values

DATABASE_URL = os.environ.get("DATABASE_URL")

def import_preferences():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("Loading customer preferences CSV...")
    df = pd.read_csv("attached_assets/customer_preferences_1766812094456.csv")
    
    print(f"Importing {len(df)} customer preferences...")
    
    prefs_data = []
    for _, row in df.iterrows():
        prefs_data.append((
            row['customer_id'],
            row['categories_interested'] if pd.notna(row['categories_interested']) else None,
            row['price_sensitivity'] if pd.notna(row['price_sensitivity']) else None,
            row['preferred_brands'] if pd.notna(row['preferred_brands']) else None,
            row['preferred_styles'] if pd.notna(row['preferred_styles']) else None,
            row['preferred_shopping_days'] if pd.notna(row['preferred_shopping_days']) else None,
        ))
    
    insert_sql = """
        INSERT INTO customer_preferences (
            customer_id, categories_interested, price_sensitivity,
            preferred_brands, preferred_styles, preferred_shopping_days
        ) VALUES %s
        ON CONFLICT DO NOTHING
    """
    
    execute_values(cursor, insert_sql, prefs_data, page_size=1000)
    conn.commit()
    print(f"Imported {len(prefs_data)} preferences")
    
    cursor.close()
    conn.close()
    print("\nImport complete!")

if __name__ == "__main__":
    import_preferences()
