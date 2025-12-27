import pandas as pd
import psycopg2
import os
from psycopg2.extras import execute_values

DATABASE_URL = os.environ.get("DATABASE_URL")

def parse_csv_array(value):
    if pd.isna(value) or value == "":
        return []
    return [x.strip() for x in str(value).split(",") if x.strip()]

def import_preferences():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("Loading preferences CSV...")
    df = pd.read_csv("attached_assets/customer_preferences_1766813101941.csv")
    
    print(f"Importing {len(df)} customer preferences...")
    
    prefs_data = []
    for _, row in df.iterrows():
        prefs_data.append((
            row['customer_id'],
            parse_csv_array(row['categories_interested']),
            row['price_sensitivity'] if pd.notna(row['price_sensitivity']) else None,
            parse_csv_array(row['preferred_brands']),
            parse_csv_array(row['preferred_styles']),
            row['preferred_shopping_days'] if pd.notna(row['preferred_shopping_days']) else None,
        ))
    
    insert_sql = """
        INSERT INTO customer_preferences (
            customer_id, categories_interested, price_sensitivity,
            preferred_brands, preferred_styles, preferred_shopping_days
        ) VALUES %s
        ON CONFLICT (customer_id) DO UPDATE SET
            categories_interested = EXCLUDED.categories_interested,
            price_sensitivity = EXCLUDED.price_sensitivity,
            preferred_brands = EXCLUDED.preferred_brands,
            preferred_styles = EXCLUDED.preferred_styles,
            preferred_shopping_days = EXCLUDED.preferred_shopping_days
    """
    
    execute_values(cursor, insert_sql, prefs_data, page_size=1000)
    conn.commit()
    print(f"Imported {len(prefs_data)} preferences")
    
    cursor.close()
    conn.close()
    print("Import complete!")

if __name__ == "__main__":
    import_preferences()
