import { useState } from "react";
import { Heart, Copy } from "lucide-react";
import { Card } from "@/components/ui/card";
import { ImageSlider } from "./ImageSlider";

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
}

interface ProductCardProps {
  product: Product;
  onProductClick: (product: Product) => void;
  shoppingMode?: "online" | "instore";
  children?: React.ReactNode;
}

export function ProductCard({ product, onProductClick, shoppingMode, children }: ProductCardProps) {
  const [isWishlisted, setIsWishlisted] = useState(false);

  const handleWishlistClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsWishlisted(!isWishlisted);
  };

  const handleViewSimilarClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  return (
    <Card
      className="product-card"
      data-testid={`card-product-${product.id}`}
    >
      <div 
        className="product-card__image-container"
        onClick={() => onProductClick(product)}
        data-testid={`product-image-${product.id}`}
      >
        <ImageSlider 
          productId={product.id}
          primaryImageUrl={product.image_url}
        />

        <button
          onClick={handleWishlistClick}
          className="product-card__wishlist-btn"
          data-testid={`btn-wishlist-${product.id}`}
        >
          <Heart 
            className={`icon ${isWishlisted ? 'icon--active' : ''}`} 
          />
        </button>

        <button
          onClick={handleViewSimilarClick}
          className="product-card__similar-btn"
          data-testid={`btn-view-similar-${product.id}`}
        >
          <Copy className="icon" />
        </button>

        {product.rating && (
          <div className="product-card__rating">
            <span className="product-card__rating-value">{product.rating}</span>
            <span className="product-card__rating-star">★</span>
            <span className="product-card__rating-divider">|</span>
            <span className="product-card__rating-count">250</span>
          </div>
        )}
      </div>
      
      <div className="product-card__content">
        <p className="product-card__brand">
          {product.brand}
        </p>
        <span className="product-card__name">
          {product.name}
        </span>
        <div className="product-card__price-row">
          {product.price && (
            <span className="product-card__price">
              ${product.price}
            </span>
          )}
        </div>
      </div>
      
      {children}
    </Card>
  );
}
