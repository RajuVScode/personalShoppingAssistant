import os
import numpy as np
from typing import List, Dict, Any
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

class ProductVectorStore:
    def __init__(self):
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT', '')
        deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini')
        
        if endpoint and not endpoint.startswith('http'):
            endpoint, deployment = deployment, endpoint
        
        embedding_deployment = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-3-small')
        
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=endpoint,
            azure_deployment=embedding_deployment,
            api_key=os.getenv('AZURE_OPENAI_API_KEY', ''),
            api_version='2024-02-15-preview'
        )
        self.vector_store = None
        self.index_path = "backend/rag/product_index"
    
    def create_index(self, products: List[Dict[str, Any]]):
        documents = []
        for product in products:
            content = f"""
            Product: {product.get('name', '')}
            Category: {product.get('category', '')} - {product.get('subcategory', '')}
            Description: {product.get('description', '')}
            Brand: {product.get('brand', '')}
            Price: ${product.get('price', 0)}
            Colors: {', '.join(product.get('colors', []))}
            Tags: {', '.join(product.get('tags', []))}
            """
            
            doc = Document(
                page_content=content.strip(),
                metadata={
                    "id": product.get("id"),
                    "name": product.get("name"),
                    "category": product.get("category"),
                    "subcategory": product.get("subcategory"),
                    "price": product.get("price"),
                    "brand": product.get("brand"),
                    "gender": product.get("gender"),
                    "image_url": product.get("image_url"),
                    "in_stock": product.get("in_stock", True),
                    "rating": product.get("rating", 0)
                }
            )
            documents.append(doc)
        
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        self.vector_store.save_local(self.index_path)
    
    def load_index(self):
        try:
            self.vector_store = FAISS.load_local(
                self.index_path, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            return True
        except Exception:
            return False
    
    def search(self, query: str, k: int = 5, filters: Dict = None) -> List[Dict[str, Any]]:
        if not self.vector_store:
            if not self.load_index():
                return []
        
        results = self.vector_store.similarity_search_with_score(query, k=k*2)
        
        products = []
        for doc, score in results:
            metadata = doc.metadata
            
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
            
            products.append({
                **metadata,
                "relevance_score": float(score),
                "description": doc.page_content
            })
            
            if len(products) >= k:
                break
        
        return products
