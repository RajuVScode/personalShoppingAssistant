import os
import numpy as np
from typing import List, Dict, Any
import hashlib
import json

class SimpleEmbeddings:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self._word_vectors = {}
    
    def _get_word_embedding(self, word: str) -> np.ndarray:
        if word not in self._word_vectors:
            hash_bytes = hashlib.sha256(word.lower().encode()).digest()
            np.random.seed(int.from_bytes(hash_bytes[:4], 'big'))
            self._word_vectors[word] = np.random.randn(self.dimension).astype(np.float32)
            self._word_vectors[word] /= np.linalg.norm(self._word_vectors[word])
        return self._word_vectors[word]
    
    def embed_text(self, text: str) -> np.ndarray:
        words = text.lower().replace(',', ' ').replace('.', ' ').split()
        if not words:
            return np.zeros(self.dimension, dtype=np.float32)
        
        embeddings = [self._get_word_embedding(w) for w in words]
        result = np.mean(embeddings, axis=0)
        norm = np.linalg.norm(result)
        if norm > 0:
            result = result / norm
        return result
    
    def embed_documents(self, texts: List[str]) -> List[np.ndarray]:
        return [self.embed_text(text) for text in texts]


class ProductVectorStore:
    def __init__(self):
        self.embeddings = SimpleEmbeddings(dimension=384)
        self.documents: List[Dict[str, Any]] = []
        self.vectors: np.ndarray = None
        self.index_path = "backend/rag/product_index.json"
    
    def create_index(self, products: List[Dict[str, Any]]):
        self.documents = []
        vectors = []
        
        for product in products:
            content = f"""
            Product: {product.get('name', '')}
            Category: {product.get('category', '')} - {product.get('subcategory', '')}
            Description: {product.get('description', '')}
            Brand: {product.get('brand', '')}
            Price: ${product.get('price', 0)}
            Colors: {', '.join(product.get('colors', []) if isinstance(product.get('colors'), list) else [])}
            Tags: {', '.join(product.get('tags', []) if isinstance(product.get('tags'), list) else [])}
            Material: {product.get('material', '')}
            Season: {product.get('season', '')}
            """
            
            doc = {
                "content": content.strip(),
                "metadata": {
                    "id": product.get("id"),
                    "name": product.get("name"),
                    "category": product.get("category"),
                    "subcategory": product.get("subcategory"),
                    "price": product.get("price"),
                    "brand": product.get("brand"),
                    "gender": product.get("gender"),
                    "image_url": product.get("image_url"),
                    "in_stock": product.get("in_stock", True),
                    "rating": product.get("rating", 0),
                    "colors": product.get("colors", []),
                    "material": product.get("material", ""),
                    "season": product.get("season", "")
                }
            }
            self.documents.append(doc)
            vectors.append(self.embeddings.embed_text(content))
        
        self.vectors = np.array(vectors, dtype=np.float32)
        self._save_index()
        print(f"Created vector index with {len(self.documents)} products")
    
    def _save_index(self):
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        data = {
            "documents": self.documents,
            "vectors": self.vectors.tolist()
        }
        with open(self.index_path, 'w') as f:
            json.dump(data, f)
    
    def load_index(self) -> bool:
        try:
            if os.path.exists(self.index_path):
                with open(self.index_path, 'r') as f:
                    data = json.load(f)
                self.documents = data["documents"]
                self.vectors = np.array(data["vectors"], dtype=np.float32)
                return True
            return False
        except Exception:
            return False
    
    def _get_base_product_name(self, name: str) -> str:
        if " — " in name:
            return name.split(" — ")[0].strip()
        if " - Size" in name:
            return name.split(" - Size")[0].strip()
        if " (Size" in name:
            return name.split(" (Size")[0].strip()
        return name
    
    def search(self, query: str, k: int = 5, filters: Dict = None) -> List[Dict[str, Any]]:
        if self.vectors is None or len(self.documents) == 0:
            if not self.load_index():
                return []
        
        query_vector = self.embeddings.embed_text(query)
        
        similarities = np.dot(self.vectors, query_vector)
        
        indices = np.argsort(similarities)[::-1]
        
        candidates = []
        for idx in indices:
            if len(candidates) >= k * 10:
                break
                
            doc = self.documents[idx]
            metadata = doc["metadata"]
            
            if filters:
                if filters.get("budget_max") and metadata.get("price"):
                    if metadata["price"] > filters["budget_max"]:
                        continue
                if filters.get("budget_min") and metadata.get("price"):
                    if metadata["price"] < filters["budget_min"]:
                        continue
                if filters.get("category") and metadata.get("category"):
                    if filters["category"].lower() not in metadata["category"].lower():
                        continue
                if filters.get("gender") and metadata.get("gender"):
                    if filters["gender"].lower() != metadata["gender"].lower() and metadata["gender"].lower() != "unisex":
                        continue
            
            candidates.append({
                **metadata,
                "relevance_score": float(similarities[idx]),
                "description": doc["content"]
            })
        
        products = self._deduplicate_and_diversify(candidates, k)
        
        return products
    
    def _deduplicate_and_diversify(self, candidates: List[Dict[str, Any]], k: int) -> List[Dict[str, Any]]:
        seen_base_names = set()
        seen_subcategories = {}
        products = []
        
        for product in candidates:
            base_name = self._get_base_product_name(product.get("name", ""))
            subcategory = product.get("subcategory", "unknown")
            
            if base_name in seen_base_names:
                continue
            
            subcat_count = seen_subcategories.get(subcategory, 0)
            if subcat_count >= 2 and len(products) < k:
                continue
            
            seen_base_names.add(base_name)
            seen_subcategories[subcategory] = subcat_count + 1
            products.append(product)
            
            if len(products) >= k:
                break
        
        if len(products) < k:
            for product in candidates:
                if len(products) >= k:
                    break
                base_name = self._get_base_product_name(product.get("name", ""))
                if base_name not in seen_base_names:
                    seen_base_names.add(base_name)
                    products.append(product)
        
        return products
