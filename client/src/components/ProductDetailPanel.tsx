
import { useState, useEffect } from "react";
import { X, ShoppingCart, Check, Zap, Package } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SizeChartModal } from "./SizeChartModal";
import { ProductImageGallery } from "./ProductImageGallery";

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

interface ProductDetails {
  id: number;
  name: string;
  description?: string;
  category?: string;
  subcategory?: string;
  price?: number;
  brand?: string;
  gender?: string;
  sizes_available?: string[];
  colors: string[];
  color_images: Record<string, string[]>;
  tags?: string[];
  image_url?: string;
  in_stock?: boolean;
  rating?: number;
  material?: string;
  season?: string;
  care_instructions?: string;
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
  const [productDetails, setProductDetails] = useState<ProductDetails | null>(null);
  const [selectedColor, setSelectedColor] = useState<string | null>(null);
  const [currentImages, setCurrentImages] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setSelectedSize(null);
    setShowSizeChart(false);
    setSelectedColor(null);
    setProductDetails(null);
    setCurrentImages([]);
    
    if (product?.id) {
      fetchProductDetails(product.id);
    }
  }, [product?.id]);

  useEffect(() => {
    if (productDetails && selectedColor && productDetails.color_images[selectedColor]) {
      setCurrentImages(productDetails.color_images[selectedColor]);
    }
  }, [selectedColor, productDetails]);

  const fetchProductDetails = async (productId: number) => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/products/${productId}`);
      if (response.ok) {
        const data = await response.json();
        setProductDetails(data);
        if (data.colors && data.colors.length > 0) {
          setSelectedColor(data.colors[0]);
          setCurrentImages(data.color_images[data.colors[0]] || []);
        }
      }
    } catch (error) {
      console.error("Failed to fetch product details:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen || !product) return null;

  const displayImages = currentImages.length > 0 ? currentImages : [product.image_url || ""];
  const colors = productDetails?.colors || [];

  return (
    <>
      <div 
        className={`fixed inset-0 z-[60] flex items-center justify-end bg-black/50 transition-opacity duration-300 ${isAnimating ? 'opacity-100' : 'opacity-0'}`}
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
        data-testid="product-detail-modal-overlay"
      >
        <div className={`bg-white w-[400px] h-full shadow-2xl flex flex-col overflow-hidden transition-transform duration-300 ease-in-out ${isAnimating ? 'translate-x-0' : 'translate-x-full'}`}>
          <div className="bg-[#1565C0] text-white px-3 py-2 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Package className="w-4 h-4" />
              <span className="font-semibold text-sm">Product Details</span>
            </div>
            <button 
              onClick={onClose}
              className="text-white hover:bg-white/10 p-1 rounded"
              data-testid="btn-close-product-detail"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            <div className="p-4">
              <ProductImageGallery
                images={displayImages}
                productName={product.name}
                isLoading={isLoading}
              />
            </div>
            
            <div className="px-4 pb-4 space-y-4">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">{productDetails?.brand || product.brand}</p>
                <h2 className="text-sm font-bold text-gray-900 mt-0.5">{product.name}</h2>
              </div>
              
              {(productDetails?.rating || product.rating) && (
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <span 
                        key={star} 
                        className={`text-lg ${star <= (productDetails?.rating || product.rating || 0) ? 'text-yellow-400' : 'text-gray-300'}`}
                      >
                        ★
                      </span>
                    ))}
                  </div>
                  <span className="text-sm text-gray-500">{productDetails?.rating || product.rating} out of 5</span>
                </div>
              )}
              
              {(productDetails?.price || product.price) && (
                <div className="text-base font-bold text-gray-900">
                  ${(productDetails?.price || product.price || 0).toFixed(2)}
                </div>
              )}
              
              {colors.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-semibold text-xs text-gray-900">SELECT COLOR</span>
                    <span className="text-xs text-gray-500">{selectedColor}</span>
                  </div>
                  <div className="flex gap-1.5 flex-wrap">
                    {colors.map((color) => {
                      const colorMap: Record<string, string> = {
                        'black': '#000000',
                        'white': '#ffffff',
                        'navy': '#001f3f',
                        'navy blue': '#001f3f',
                        'brown': '#8b4513',
                        'burgundy': '#800020',
                        'charcoal': '#36454f',
                        'cream': '#fffdd0',
                        'camel': '#c19a6b',
                        'tan': '#d2b48c',
                        'olive': '#808000',
                        'forest green': '#228b22',
                        'yellow': '#ffff00',
                        'red': '#ff0000',
                        'khaki': '#f0e68c',
                        'stone': '#928e85',
                        'champagne': '#f7e7ce',
                        'gray': '#808080',
                        'sage': '#bcb88a',
                        'gold/green': '#b8860b',
                        'silver/blue': '#87ceeb',
                        'black/gray': '#2f2f2f',
                        'forest': '#228b22',
                        'default': '#e5e7eb',
                      };
                      const bgColor = colorMap[color.toLowerCase()] || '#e5e7eb';
                      const isSelected = selectedColor === color;
                      const isLight = ['white', 'cream', 'yellow', 'champagne', 'khaki'].includes(color.toLowerCase());
                      
                      return (
                        <button
                          key={color}
                          onClick={() => setSelectedColor(color)}
                          className={`w-7 h-7 rounded-full border-2 transition-all ${
                            isSelected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-300'
                          }`}
                          style={{ backgroundColor: bgColor }}
                          title={color}
                          data-testid={`color-${color.toLowerCase().replace(/\s+/g, '-')}`}
                        >
                          {isSelected && (
                            <Check className={`w-3.5 h-3.5 mx-auto ${isLight ? 'text-gray-800' : 'text-white'}`} />
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
              
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-semibold text-xs text-gray-900">SELECT SIZE</span>
                  <button 
                    className="text-xs text-pink-500 hover:underline font-medium" 
                    onClick={() => setShowSizeChart(true)}
                    data-testid="btn-size-chart"
                  >
                    Size Chart
                  </button>
                </div>
                <div className="flex gap-1.5 flex-wrap">
                  {['S', 'M', 'L', 'XL', 'XXL'].map((size) => (
                    <button
                      key={size}
                      onClick={() => setSelectedSize(size)}
                      className={`w-10 h-8 border rounded-md text-xs font-medium transition-colors ${
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
              
              <div className="flex gap-2 flex-wrap">
                {(productDetails?.category || product.category) && (
                  <span className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full">
                    {productDetails?.category || product.category}
                  </span>
                )}
                {(productDetails?.subcategory || product.subcategory) && (
                  <span className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full">
                    {productDetails?.subcategory || product.subcategory}
                  </span>
                )}
              </div>
              
              {(productDetails?.description || product.description) && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Description</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    {productDetails?.description || product.description}
                  </p>
                </div>
              )}
              
              {productDetails?.material && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">Material</h3>
                  <p className="text-gray-600 text-sm">{productDetails.material}</p>
                </div>
              )}
              
              {productDetails?.care_instructions && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">Care Instructions</h3>
                  <p className="text-gray-600 text-sm">{productDetails.care_instructions}</p>
                </div>
              )}
            </div>
          </div>
          
          <div className="p-3 border-t bg-white">
            <div className="flex gap-2">
              <Button
                className={`flex-1 h-9 text-white text-xs font-semibold rounded-[6px] ${
                  isInCart(product.id) 
                    ? 'bg-green-600 hover:bg-green-700' 
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
                onClick={() => onAddToCart(product)}
                data-testid="btn-add-cart-detail"
              >
                {isInCart(product.id) ? (
                  <>
                    <Check className="h-4 w-4 mr-1.5" />
                    Added to Cart
                  </>
                ) : (
                  <>
                    <ShoppingCart className="h-4 w-4 mr-1.5" />
                    Add to Cart
                  </>
                )}
              </Button>
              <Button
                className="flex-1 h-9 text-white text-xs font-semibold rounded-[6px] hover:opacity-90 border-0"
                style={{ backgroundColor: '#C9A961' }}
                data-testid="btn-buy-now"
              >
                <Zap className="h-4 w-4 mr-1.5" />
                Buy Now
              </Button>
            </div>
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
