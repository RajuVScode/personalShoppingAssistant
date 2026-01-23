import { useState } from "react";
import { Heart, Copy } from "lucide-react";
import { ImageSlider } from "./ImageSlider";
import "../styles/product-card.css";

interface Product {
  id: number;
  name: string;
  description?: string;
  category?: string;
  subcategory?: string;
  price?: number;
  brand?: string;
  image_url?: string;
  rating?: number;
  colors?: string[];
  [key: string]: unknown;
}

interface ProductCardProps {
  product: Product;
  onProductClick: (product: Product) => void;
  shoppingMode?: "online" | "instore";
  children?: React.ReactNode;
}

export function ProductCard({ product, onProductClick, shoppingMode, children }: ProductCardProps) {
  const [isWishlisted, setIsWishlisted] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const handleWishlistClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsWishlisted(!isWishlisted);
  };

  const handleViewSimilarClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  const extractSize = (name: string): string | null => {
    const sizeMatch = name.match(/\/\s*([XSML]{1,3}|XXL|XXS|\d{1,2})\s*$/i);
    return sizeMatch ? sizeMatch[1].toUpperCase() : null;
  };

  const productSize = extractSize(product.name || '');

  return (
    <div
      className={`product-card ${isHovered ? 'product-card--hovered' : ''}`}
      id={`product-card-${product.id}`}
      data-testid={`card-product-${product.id}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div 
        className="product-card-image-container"
        id={`product-image-container-${product.id}`}
        onClick={() => onProductClick(product)}
        data-testid={`product-image-${product.id}`}
      >
        <ImageSlider 
          productId={product.id}
          primaryImageUrl={product.image_url}
        />

        <button
          onClick={handleWishlistClick}
          className="product-card-btn product-card-wishlist-btn"
          id={`product-wishlist-btn-${product.id}`}
          data-testid={`btn-wishlist-${product.id}`}
        >
          <Heart 
            className={`product-card-wishlist-icon ${isWishlisted ? 'product-card-wishlist-icon--active' : ''}`}
            id={`product-wishlist-icon-${product.id}`}
          />
        </button>

        <button
          onClick={handleViewSimilarClick}
          className="product-card-btn product-card-similar-btn"
          id={`product-similar-btn-${product.id}`}
          data-testid={`btn-view-similar-${product.id}`}
        >
          <Copy 
            className="product-card-similar-icon"
            id={`product-similar-icon-${product.id}`}
          />
        </button>

        {product.rating && (
          <div 
            className="product-card-rating"
            id={`product-rating-${product.id}`}
          >
            <span className="product-card-rating-value">{product.rating}</span>
            <span className="product-card-rating-star">★</span>
            <span className="product-card-rating-divider">|</span>
            <span className="product-card-rating-count">250</span>
          </div>
        )}

        {productSize && (
          <div 
            className="product-card-size-badge"
            id={`product-size-badge-${product.id}`}
            data-testid={`size-badge-${product.id}`}
          >
            <span className="product-card-size-label">Size</span>
            <span className="product-card-size-value">{productSize}</span>
          </div>
        )}
      </div>
      
      <div 
        className="product-card-content"
        id={`product-content-${product.id}`}
      >
        <p 
          className="product-card-brand"
          id={`product-brand-${product.id}`}
        >
          {product.brand}
        </p>
        <span 
          className="product-card-name"
          id={`product-name-${product.id}`}
        >
          {product.name}
        </span>
        <div className="product-card-price-row">
          {product.price && (
            <span 
              className="product-card-price"
              id={`product-price-${product.id}`}
            >
              ${product.price}
            </span>
          )}
        </div>
      </div>
      
      {children}
    </div>
  );
}
