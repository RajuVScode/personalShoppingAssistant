import { useState } from "react";
import { X, ShoppingCart, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SizeChartModal } from "./SizeChartModal";

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
}

interface ProductDetailPanelProps {
  product: Product | null;
  isOpen: boolean;
  isAnimating: boolean;
  onClose: () => void;
  onAddToCart: (product: Product) => void;
  isInCart: (productId: number) => boolean;
}

export function ProductDetailPanel({ 
  product, 
  isOpen, 
  isAnimating, 
  onClose, 
  onAddToCart,
  isInCart 
}: ProductDetailPanelProps) {
  const [selectedSize, setSelectedSize] = useState<string | null>(null);
  const [showSizeChart, setShowSizeChart] = useState(false);

  if (!isOpen || !product) return null;

  return (
    <>
      <div 
        className={`fixed inset-0 z-[60] flex items-center justify-end bg-black/50 transition-opacity duration-300 ${isAnimating ? 'opacity-100' : 'opacity-0'}`}
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
        data-testid="product-detail-modal-overlay"
      >
        <div className={`bg-white w-[450px] h-full shadow-2xl flex flex-col overflow-hidden transition-transform duration-300 ease-in-out ${isAnimating ? 'translate-x-0' : 'translate-x-full'}`}>
          <div className="bg-[#1565C0] text-white px-4 py-3 flex justify-between items-center">
            <span className="font-bold text-lg">Product Details</span>
            <button 
              onClick={onClose}
              className="text-white hover:bg-white/10 p-1 rounded"
              data-testid="btn-close-product-detail"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            <div className="w-full aspect-square bg-gray-100 overflow-hidden">
              {product.image_url ? (
                <img
                  src={product.image_url}
                  alt={product.name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.onerror = null;
                    target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'%3E%3Crect fill='%23f3f4f6' width='400' height='400'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-family='system-ui' font-size='14' fill='%239ca3af'%3EImage unavailable%3C/text%3E%3C/svg%3E";
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  No image available
                </div>
              )}
            </div>
            
            <div className="p-5 space-y-4">
              <div>
                <p className="text-sm text-gray-500 uppercase tracking-wide">{product.brand}</p>
                <h2 className="text-xl font-bold text-gray-900 mt-1">{product.name}</h2>
              </div>
              
              {product.rating && (
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <span 
                        key={star} 
                        className={`text-lg ${star <= product.rating! ? 'text-yellow-400' : 'text-gray-300'}`}
                      >
                        ★
                      </span>
                    ))}
                  </div>
                  <span className="text-sm text-gray-500">{product.rating} out of 5</span>
                </div>
              )}
              
              {product.price && (
                <div className="text-2xl font-bold text-gray-900">
                  ${product.price.toFixed(2)}
                </div>
              )}
              
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-gray-900">SELECT SIZE</span>
                  <button 
                    className="text-sm text-pink-500 hover:underline font-medium" 
                    onClick={() => setShowSizeChart(true)}
                    data-testid="btn-size-chart"
                  >
                    Size Chart
                  </button>
                </div>
                <div className="flex gap-2">
                  {['S', 'M', 'L', 'XL', 'XXL'].map((size) => (
                    <button
                      key={size}
                      onClick={() => setSelectedSize(size)}
                      className={`w-12 h-10 border rounded-md text-sm font-medium transition-colors ${
                        selectedSize === size 
                          ? 'border-pink-500 bg-pink-50 text-pink-600' 
                          : 'border-gray-300 text-gray-700 hover:border-gray-900 hover:bg-gray-50'
                      }`}
                      data-testid={`btn-size-${size}`}
                    >
                      {size}
                    </button>
                  ))}
                </div>
              </div>
              
              <div className="flex gap-2">
                {product.category && (
                  <span className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full">
                    {product.category}
                  </span>
                )}
                {product.subcategory && (
                  <span className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full">
                    {product.subcategory}
                  </span>
                )}
              </div>
              
              {product.description && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Description</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    {product.description}
                  </p>
                </div>
              )}
            </div>
          </div>
          
          <div className="p-4 border-t bg-white">
            <Button
              className={`w-full h-12 text-white font-semibold rounded-[6px] ${
                isInCart(product.id) 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
              onClick={() => onAddToCart(product)}
              data-testid="btn-add-cart-detail"
            >
              {isInCart(product.id) ? (
                <>
                  <Check className="h-5 w-5 mr-2" />
                  Added to Cart
                </>
              ) : (
                <>
                  <ShoppingCart className="h-5 w-5 mr-2" />
                  Add to Cart
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
      
      <SizeChartModal
        isOpen={showSizeChart}
        onClose={() => setShowSizeChart(false)}
        selectedSize={selectedSize}
        onSelectSize={setSelectedSize}
      />
    </>
  );
}
