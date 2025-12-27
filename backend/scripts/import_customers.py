import pandas as pd
import psycopg2
import os
from psycopg2.extras import execute_values

DATABASE_URL = os.environ.get("DATABASE_URL")

def import_customers():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("Loading customer CSV...")
    df = pd.read_csv("attached_assets/customer_master_1766811382724.csv")
    
    print(f"Importing {len(df)} customers...")
    
    customers_data = []
    for _, row in df.iterrows():
        customers_data.append((
            row['customer_id'],
            row['first_name'],
            row['last_name'],
            row['email'],
            row['phone_number'] if pd.notna(row['phone_number']) else None,
            row['date_of_birth'] if pd.notna(row['date_of_birth']) else None,
            row['gender'] if pd.notna(row['gender']) else None,
            row['preferred_channel'] if pd.notna(row['preferred_channel']) else None,
            row['marketing_opt_in'] if pd.notna(row['marketing_opt_in']) else False,
            row['vip_flag'] if pd.notna(row['vip_flag']) else False,
            int(row['lifetime_value_cents']) if pd.notna(row['lifetime_value_cents']) else 0,
            int(row['avg_order_value_cents']) if pd.notna(row['avg_order_value_cents']) else 0,
            int(row['total_orders']) if pd.notna(row['total_orders']) else 0,
            row['preferred_store_id'] if pd.notna(row['preferred_store_id']) else None,
            row['notes'] if pd.notna(row['notes']) else None,
            'password123'
        ))
    
    insert_sql = """
        INSERT INTO customers (
            customer_id, first_name, last_name, email, phone_number,
            date_of_birth, gender, preferred_channel, marketing_opt_in, vip_flag,
            lifetime_value_cents, avg_order_value_cents, total_orders,
            preferred_store_id, notes, password
        ) VALUES %s
        ON CONFLICT (customer_id) DO NOTHING
    """
    
    execute_values(cursor, insert_sql, customers_data, page_size=1000)
    conn.commit()
    print(f"Imported {len(customers_data)} customers")
    
    print("\nLoading address CSV...")
    df_addr = pd.read_csv("attached_assets/customer_address_1766811382723.csv")
    
    print(f"Importing {len(df_addr)} addresses...")
    
    addresses_data = []
    for _, row in df_addr.iterrows():
        addresses_data.append((
            row['address_id'],
            row['customer_id'],
            row['label'] if pd.notna(row['label']) else None,
            row['address_line1'],
            row['address_line2'] if pd.notna(row['address_line2']) else None,
            row['city'],
            row['state'] if pd.notna(row['state']) else None,
            row['postal_code'] if pd.notna(row['postal_code']) else None,
            row['country'] if pd.notna(row['country']) else 'USA',
            row['is_default_shipping'] if pd.notna(row['is_default_shipping']) else False,
            row['is_default_billing'] if pd.notna(row['is_default_billing']) else False,
        ))
    
    insert_addr_sql = """
        INSERT INTO customer_addresses (
            address_id, customer_id, label, address_line1, address_line2,
            city, state, postal_code, country, is_default_shipping, is_default_billing
        ) VALUES %s
        ON CONFLICT (address_id) DO NOTHING
    """
    
    execute_values(cursor, insert_addr_sql, addresses_data, page_size=1000)
    conn.commit()
    print(f"Imported {len(addresses_data)} addresses")
    
    cursor.close()
    conn.close()
    print("\nImport complete!")

if __name__ == "__main__":
    import_customers()
