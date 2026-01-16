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
      className="overflow-hidden hover:shadow-lg transition-shadow flex flex-col rounded-[6px]"
      data-testid={`card-product-${product.id}`}
    >
      <div 
        className="relative cursor-pointer"
        onClick={() => onProductClick(product)}
        data-testid={`product-image-${product.id}`}
      >
        <ImageSlider 
          productId={product.id}
          primaryImageUrl={product.image_url}
        />

        <button
          onClick={handleWishlistClick}
          className="absolute top-2 right-2 w-7 h-7 bg-white rounded-full shadow-sm flex items-center justify-center hover:bg-gray-50 transition-colors"
          data-testid={`btn-wishlist-${product.id}`}
        >
          <Heart 
            className={`w-4 h-4 ${isWishlisted ? 'fill-red-500 text-red-500' : 'text-gray-400'}`} 
          />
        </button>

        <button
          onClick={handleViewSimilarClick}
          className="absolute bottom-2 right-2 w-8 h-8 bg-white rounded-full shadow-sm flex items-center justify-center hover:bg-gray-50 transition-colors"
          data-testid={`btn-view-similar-${product.id}`}
        >
          <Copy className="w-4 h-4 text-gray-500" />
        </button>

        {product.rating && (
          <div className="absolute bottom-2 left-2 bg-white px-2 py-1 rounded-[4px] shadow-sm flex items-center gap-1">
            <span className="text-sm font-medium">{product.rating}</span>
            <span className="text-teal-500 text-sm">★</span>
            <span className="text-gray-400 text-xs">|</span>
            <span className="text-xs text-gray-500">250</span>
          </div>
        )}
      </div>
      
      <div className="p-3 flex flex-col flex-1">
        <p className="font-semibold text-sm line-clamp-1">
          {product.brand}
        </p>
        <span className="text-xs text-muted-foreground mt-1 line-clamp-1">
          {product.name}
        </span>
        <div className="flex items-center gap-2 mt-2">
          {product.price && (
            <span className="font-bold text-sm">
              ${product.price}
            </span>
          )}
        </div>
      </div>
      
      {children}
    </Card>
  );
}
