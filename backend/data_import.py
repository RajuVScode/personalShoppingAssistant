import pandas as pd
import os
from backend.database.connection import SessionLocal, engine, Base
from backend.database.models import Product
from sqlalchemy import text

PRODUCT_IMAGES = {
    'dresses': [
        'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1539008835657-9e8e9680c956?w=400&h=300&fit=crop',
    ],
    'tops': [
        'https://images.unsplash.com/photo-1562157873-818bc0726f68?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=400&h=300&fit=crop',
    ],
    'bottoms': [
        'https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=400&h=300&fit=crop',
    ],
    'outerwear': [
        'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1548624313-0396c75e4b1a?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1544923246-77307dd628b4?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1539533018447-63fcce2678e3?w=400&h=300&fit=crop',
    ],
    'sneakers': [
        'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1600185365926-3a2ce3cdb9eb?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1605348532760-6753d2c43329?w=400&h=300&fit=crop',
    ],
    'heels': [
        'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1515347619252-60a4bf4fff4f?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1596703263926-eb0762ee17e4?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1518049362265-d5b2a6467b77?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1603808033192-082d6919d3e1?w=400&h=300&fit=crop',
    ],
    'boots': [
        'https://images.unsplash.com/photo-1542840410-3092f99611a3?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1608256246200-53e635b5b65f?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1605812860427-4024433a70fd?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1520639888713-7851133b1ed0?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1602850930554-1ba8e2c4f4c3?w=400&h=300&fit=crop',
    ],
    'loafers': [
        'https://images.unsplash.com/photo-1614252369475-531eba835eb1?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1626379953822-baec19c3accd?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1533867617858-e7b97e060509?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1582897085656-c636d006a246?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1613219557083-0b43d7b1c6a0?w=400&h=300&fit=crop',
    ],
    'sandals': [
        'https://images.unsplash.com/photo-1603487742131-4160ec999306?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1562273138-f46be4ebdf33?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1535043934128-cf0b28d52f95?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1595341888016-a392ef81b7de?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400&h=300&fit=crop',
    ],
    'bags': [
        'https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1566150905458-1bf1fc113f0d?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=300&fit=crop',
    ],
    'accessories': [
        'https://images.unsplash.com/photo-1606760227091-3dd870d97f1d?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1611923134239-b9be5816e23c?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1523170335258-f5ed11844a49?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1509941943102-10c232fc4c82?w=400&h=300&fit=crop',
    ],
    'jewelry': [
        'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1599643477877-530eb83abc8e?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1603561591411-07134e71a2a9?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1611652022419-a9419f74343d?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=400&h=300&fit=crop',
    ],
    'watches': [
        'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1533139502658-0198f920d8e8?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1539874754764-5a96559165b0?w=400&h=300&fit=crop',
    ],
    'bedding': [
        'https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1629140727571-9b5c6f6267b4?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1616627577385-5d45e3e8a8f8?w=400&h=300&fit=crop',
    ],
    'pillowcases': [
        'https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1629140727571-9b5c6f6267b4?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1616627577385-5d45e3e8a8f8?w=400&h=300&fit=crop',
    ],
    'decor': [
        'https://images.unsplash.com/photo-1616046229478-9901c5536a45?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1513519245088-0e12902e35a6?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1507089947368-19c1da9775ae?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1493857671505-72967e2e2760?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1540932239986-30128078f3c5?w=400&h=300&fit=crop',
    ],
    'candles': [
        'https://images.unsplash.com/photo-1602028915047-37269d1a73f7?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1603006905003-be475563bc59?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1608181831718-c9ffd8685cd5?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1543333995-a78aea2eee50?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1574263867128-a3d5c1b1decc?w=400&h=300&fit=crop',
    ],
    'clothing': [
        'https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1558171813-4c088753af8f?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1567401893414-76b7b1e5a7a5?w=400&h=300&fit=crop',
        'https://images.unsplash.com/photo-1441984904996-e0b6ba687e04?w=400&h=300&fit=crop',
    ],
}

def generate_product_image_url(category: str, subcategory: str, sku: str) -> str:
    subcategory_lower = (subcategory or '').lower()
    category_lower = (category or '').lower()
    
    images = PRODUCT_IMAGES.get(subcategory_lower) or \
             PRODUCT_IMAGES.get(category_lower) or \
             PRODUCT_IMAGES.get('clothing')
    
    seed = abs(hash(sku)) % len(images)
    return images[seed]

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
