import pandas as pd
import os
from backend.database.connection import SessionLocal, engine, Base
from backend.database.models import Product
from sqlalchemy import text

def generate_product_image_url(category: str, subcategory: str, sku: str) -> str:
    import urllib.parse
    
    label = subcategory if subcategory else category if category else "Product"
    label = label.replace("'", "").replace('"', '')
    
    colors = {
        'dresses': '4A90A4',
        'tops': '7B68EE',
        'bottoms': '4682B4',
        'outerwear': '708090',
        'footwear': '8B4513',
        'shoes': '8B4513',
        'sneakers': '2F4F4F',
        'boots': '654321',
        'accessories': 'DAA520',
        'bags': 'A0522D',
        'jewelry': 'FFD700',
        'watches': '696969',
        'bedding': '87CEEB',
        'decor': 'DEB887',
        'pillowcases': 'B0C4DE',
        'candles': 'FFE4B5',
        'clothing': '6B8E23',
    }
    
    subcategory_lower = (subcategory or '').lower()
    category_lower = (category or '').lower()
    bg_color = colors.get(subcategory_lower) or colors.get(category_lower) or '6B8E23'
    
    encoded_label = urllib.parse.quote(label)
    return f"https://placehold.co/400x300/{bg_color}/ffffff?text={encoded_label}"

def import_product_data():
    product_master = pd.read_excel("attached_assets/product_master_clean_New_1766805486832.xlsx")
    product_variants = pd.read_excel("attached_assets/product_variants_clean_New_1766805486833.xlsx")
    pricing_master = pd.read_excel("attached_assets/pricing_master_New_1766805486831.xlsx")
    inventory = pd.read_excel("attached_assets/inventory_store_0001_0025_New_1766805486830.xlsx")
    
    print(f"Loaded {len(product_master)} product families")
    print(f"Loaded {len(product_variants)} variants")
    print(f"Loaded {len(pricing_master)} pricing records")
    print(f"Loaded {len(inventory)} inventory records")
    
    inventory_status = inventory.groupby('variant_sku').agg({
        'on_hand': 'sum',
        'inventory_status': lambda x: 'In Stock' if (x == 'In Stock').any() else 'Out of Stock'
    }).reset_index()
    
    merged = product_variants.merge(product_master, on='family_id', how='left')
    merged = merged.merge(pricing_master[['variant_sku', 'regular_price', 'promo_price']], on='variant_sku', how='left')
    merged = merged.merge(inventory_status, on='variant_sku', how='left')
    
    print(f"Merged dataset: {len(merged)} products")
    
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM products"))
        db.commit()
        print("Cleared existing products")
        
        products_added = 0
        for _, row in merged.iterrows():
            if not row.get('active', True):
                continue
                
            price = row.get('promo_price') or row.get('regular_price') or row.get('web_price') or row.get('msrp_x') or 0
            if pd.isna(price):
                price = 99.99
            
            colors = str(row.get('available_colors', '')).split(',') if pd.notna(row.get('available_colors')) else []
            colors = [c.strip() for c in colors if c.strip()]
            
            tags = str(row.get('tags', '')).split(',') if pd.notna(row.get('tags')) else []
            tags = [t.strip() for t in tags if t.strip()]
            
            sizes = str(row.get('available_sizes', '')).split(',') if pd.notna(row.get('available_sizes')) else []
            sizes = [s.strip() for s in sizes if s.strip()]
            
            gender = 'women' if row.get('department', '').lower() == 'women' else 'men' if row.get('department', '').lower() == 'men' else 'unisex'
            
            in_stock = row.get('inventory_status') == 'In Stock' if pd.notna(row.get('inventory_status')) else True
            
            material_val = row.get('material_x') or row.get('material_y') or ''
            if pd.isna(material_val):
                material_val = ''
            
            season_val = row.get('Season') or ''
            if pd.isna(season_val):
                season_val = ''
            
            care_val = row.get('care_instructions') or ''
            if pd.isna(care_val):
                care_val = ''
            
            product = Product(
                name=row.get('display_name') or row.get('family_name', 'Unknown'),
                description=row.get('long_description') or row.get('short_description', ''),
                category=row.get('category', 'Clothing'),
                subcategory=row.get('sub_category', ''),
                price=float(price),
                brand=row.get('brand', ''),
                gender=gender,
                sizes_available=sizes,
                colors=colors,
                tags=tags,
                image_url=generate_product_image_url(row.get('category', 'clothing'), row.get('sub_category', ''), row.get('variant_sku', str(products_added))),
                in_stock=in_stock,
                rating=4.0 + (hash(row.get('variant_sku', '')) % 10) / 10,
                material=str(material_val),
                season=str(season_val),
                care_instructions=str(care_val)
            )
            db.add(product)
            products_added += 1
            
            if products_added % 500 == 0:
                db.commit()
                print(f"Added {products_added} products...")
        
        db.commit()
        print(f"Successfully imported {products_added} products")
        
    finally:
        db.close()
    
    return products_added

if __name__ == "__main__":
    import_product_data()
