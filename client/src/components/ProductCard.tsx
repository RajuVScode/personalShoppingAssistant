import { useState, useEffect, useRef } from "react";
import { Heart, Copy } from "lucide-react";
import { Card } from "@/components/ui/card";

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

const IMAGE_COUNT = 4;
const SLIDE_INTERVAL = 1800;

export function ProductCard({ product, onProductClick, shoppingMode, children }: ProductCardProps) {
  const [isHovering, setIsHovering] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isWishlisted, setIsWishlisted] = useState(false);
  const [imagesLoaded, setImagesLoaded] = useState<boolean[]>([true, false, false, false]);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const productImages = [
    product.image_url || `https://picsum.photos/seed/${product.id}-1/400/300`,
    `https://picsum.photos/seed/${product.id}-2/400/300`,
    `https://picsum.photos/seed/${product.id}-3/400/300`,
    `https://picsum.photos/seed/${product.id}-4/400/300`,
  ];

  useEffect(() => {
    productImages.forEach((src, idx) => {
      if (idx === 0) return;
      const img = new Image();
      img.onload = () => {
        setImagesLoaded(prev => {
          const newState = [...prev];
          newState[idx] = true;
          return newState;
        });
      };
      img.src = src;
    });
  }, [product.id]);

  useEffect(() => {
    if (isHovering && imagesLoaded.every(Boolean)) {
      intervalRef.current = setInterval(() => {
        setCurrentImageIndex((prev) => (prev + 1) % IMAGE_COUNT);
      }, SLIDE_INTERVAL);
    } else if (!isHovering) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setCurrentImageIndex(0);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isHovering, imagesLoaded]);

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
        onMouseEnter={() => setIsHovering(true)}
        onMouseLeave={() => setIsHovering(false)}
        data-testid={`product-image-${product.id}`}
      >
        <div className="w-full aspect-[4/3] bg-muted overflow-hidden relative">
          <img
            src={productImages[currentImageIndex]}
            alt={product.name}
            className="w-full h-full object-cover transition-opacity duration-300"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.onerror = null;
              target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300' viewBox='0 0 400 300'%3E%3Crect fill='%23f3f4f6' width='400' height='300'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-family='system-ui' font-size='14' fill='%239ca3af'%3EImage unavailable%3C/text%3E%3C/svg%3E";
            }}
          />
          
          {isHovering && (
            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
              {productImages.map((_, idx) => (
                <div
                  key={idx}
                  className={`w-1.5 h-1.5 rounded-full transition-colors ${
                    idx === currentImageIndex ? 'bg-white' : 'bg-white/50'
                  }`}
                />
              ))}
            </div>
          )}
        </div>

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
