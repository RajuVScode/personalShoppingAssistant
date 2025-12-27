from backend.database.connection import SessionLocal
from backend.database.models import Product
from backend.rag.vector_store import ProductVectorStore

def build_vector_index():
    db = SessionLocal()
    try:
        products = db.query(Product).filter(Product.in_stock == True).all()
        
        product_data = [{
            "id": p.id,
            "name": p.name,
            "description": p.description or "",
            "category": p.category or "",
            "subcategory": p.subcategory or "",
            "price": p.price or 0,
            "brand": p.brand or "",
            "gender": p.gender or "unisex",
            "colors": p.colors or [],
            "tags": p.tags or [],
            "image_url": p.image_url or "",
            "in_stock": p.in_stock,
            "rating": p.rating or 0,
            "material": p.material or "",
            "season": p.season or ""
        } for p in products]
        
        print(f"Building vector index for {len(product_data)} products...")
        
        vector_store = ProductVectorStore()
        vector_store.create_index(product_data)
        
        print("Vector index built successfully!")
        
    finally:
        db.close()

if __name__ == "__main__":
    build_vector_index()
