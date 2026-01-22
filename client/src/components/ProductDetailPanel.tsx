/**
 * ProductDetailPanel Component
 * 
 * A sliding panel that displays detailed product information.
 * Features include:
 * - Product image gallery with zoom functionality
 * - Color selection with dynamic image updates
 * - Size selection with size chart reference
 * - Add to cart functionality with visual feedback
 * - Product specifications (material, care instructions, etc.)
 * 
 * The panel slides in from the right side of the chat widget
 * when a user clicks on a product card for more details.
 */

import { useState, useEffect } from "react";
import { X, ShoppingCart, Check, Zap, Package } from "lucide-react";
import { SizeChartModal } from "./SizeChartModal";
import { ProductImageGallery } from "./ProductImageGallery";
import api from "@/lib/api";
import "../styles/product-detail.css";

/**
 * Basic product info passed from the product card.
 */
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
  [key: string]: unknown;
}

/**
 * Extended product details fetched from the API.
 * Includes color-specific images and full specifications.
 */
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

/**
 * Props for the ProductDetailPanel component.
 */
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
      const data = await api.getProduct<ProductDetails>(productId);
      setProductDetails(data);
      if (data.colors && data.colors.length > 0) {
        setSelectedColor(data.colors[0]);
        setCurrentImages(data.color_images[data.colors[0]] || []);
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

  const lightColors = ['white', 'cream', 'yellow', 'champagne', 'khaki'];

  return (
    <>
      <div 
        className={`product-detail-overlay ${isAnimating ? 'product-detail-overlay--visible' : 'product-detail-overlay--hidden'}`}
        id="product-detail-overlay"
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
        data-testid="product-detail-modal-overlay"
      >
        <div 
          className={`product-detail-panel ${isAnimating ? 'product-detail-panel--visible' : 'product-detail-panel--hidden'}`}
          id="product-detail-panel"
        >
          <div className="product-detail-header" id="product-detail-header">
            <div className="product-detail-header-title">
              <Package className="product-detail-header-icon" id="product-detail-header-icon" />
              <span className="product-detail-header-text">Product Details</span>
            </div>
            <button 
              onClick={onClose}
              className="product-detail-close-btn"
              id="product-detail-close-btn"
              data-testid="btn-close-product-detail"
            >
              <X className="product-detail-close-icon" id="product-detail-close-icon" />
            </button>
          </div>
          
          <div className="product-detail-content" id="product-detail-content">
            <div className="product-detail-image-section">
              <ProductImageGallery
                images={displayImages}
                productName={product.name}
                isLoading={isLoading}
              />
            </div>
            
            <div className="product-detail-info" id="product-detail-info">
              <div>
                <p className="product-detail-brand" id="product-detail-brand">
                  {productDetails?.brand || product.brand}
                </p>
                <h2 className="product-detail-name" id="product-detail-name">
                  {product.name}
                </h2>
              </div>
              
              {(productDetails?.rating || product.rating) && (
                <div className="product-detail-rating" id="product-detail-rating">
                  <div className="product-detail-stars">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <span 
                        key={star} 
                        className={`product-detail-star ${star <= (productDetails?.rating || product.rating || 0) ? 'product-detail-star--filled' : 'product-detail-star--empty'}`}
                      >
                        ★
                      </span>
                    ))}
                  </div>
                  <span className="product-detail-rating-text">
                    {productDetails?.rating || product.rating} out of 5
                  </span>
                </div>
              )}
              
              {(productDetails?.price || product.price) && (
                <div className="product-detail-price" id="product-detail-price">
                  ${(productDetails?.price || product.price || 0).toFixed(2)}
                </div>
              )}
              
              {colors.length > 0 && (
                <div className="product-detail-section" id="product-detail-color-section">
                  <div className="product-detail-section-header">
                    <span className="product-detail-section-label">SELECT COLOR</span>
                    <span className="product-detail-section-value">{selectedColor}</span>
                  </div>
                  <div className="product-detail-colors">
                    {colors.map((color) => {
                      const bgColor = colorMap[color.toLowerCase()] || '#e5e7eb';
                      const isSelected = selectedColor === color;
                      const isLight = lightColors.includes(color.toLowerCase());
                      
                      return (
                        <button
                          key={color}
                          onClick={() => setSelectedColor(color)}
                          className={`product-detail-color-btn ${isSelected ? 'product-detail-color-btn--selected' : ''}`}
                          id={`product-detail-color-${color.toLowerCase().replace(/\s+/g, '-')}`}
                          style={{ backgroundColor: bgColor }}
                          title={color}
                          data-testid={`color-${color.toLowerCase().replace(/\s+/g, '-')}`}
                        >
                          {isSelected && (
                            <Check className={`product-detail-color-check ${isLight ? 'product-detail-color-check--light' : 'product-detail-color-check--dark'}`} />
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
              
              <div className="product-detail-section" id="product-detail-size-section">
                <div className="product-detail-section-header">
                  <span className="product-detail-section-label">SELECT SIZE</span>
                  <button 
                    className="product-detail-size-chart-link" 
                    id="product-detail-size-chart-link"
                    onClick={() => setShowSizeChart(true)}
                    data-testid="btn-size-chart"
                  >
                    Size Chart
                  </button>
                </div>
                <div className="product-detail-sizes">
                  {['S', 'M', 'L', 'XL', 'XXL'].map((size) => (
                    <button
                      key={size}
                      onClick={() => setSelectedSize(size)}
                      className={`product-detail-size-btn ${selectedSize === size ? 'product-detail-size-btn--selected' : ''}`}
                      id={`product-detail-size-${size}`}
                      data-testid={`btn-size-${size}`}
                    >
                      {size}
                    </button>
                  ))}
                </div>
              </div>
              
              <div className="product-detail-tags" id="product-detail-tags">
                {(productDetails?.category || product.category) && (
                  <span className="product-detail-tag">
                    {productDetails?.category || product.category}
                  </span>
                )}
                {(productDetails?.subcategory || product.subcategory) && (
                  <span className="product-detail-tag">
                    {productDetails?.subcategory || product.subcategory}
                  </span>
                )}
              </div>
              
              {(productDetails?.description || product.description) && (
                <div className="product-detail-description-section" id="product-detail-description">
                  <h3 className="product-detail-description-title">Description</h3>
                  <p className="product-detail-description-text">
                    {productDetails?.description || product.description}
                  </p>
                </div>
              )}
              
              {productDetails?.material && (
                <div className="product-detail-description-section" id="product-detail-material">
                  <h3 className="product-detail-spec-title">Material</h3>
                  <p className="product-detail-spec-text">{productDetails.material}</p>
                </div>
              )}
              
              {productDetails?.care_instructions && (
                <div className="product-detail-description-section" id="product-detail-care">
                  <h3 className="product-detail-spec-title">Care Instructions</h3>
                  <p className="product-detail-spec-text">{productDetails.care_instructions}</p>
                </div>
              )}
            </div>
          </div>
          
          <div className="product-detail-footer" id="product-detail-footer">
            <div className="product-detail-footer-buttons">
              <button
                className={`product-detail-action-btn product-detail-cart-btn ${isInCart(product.id) ? 'product-detail-cart-btn--added' : ''}`}
                id="product-detail-add-cart-btn"
                onClick={() => onAddToCart(product)}
                data-testid="btn-add-cart-detail"
              >
                {isInCart(product.id) ? (
                  <>
                    <Check className="product-detail-btn-icon" />
                    Added to Cart
                  </>
                ) : (
                  <>
                    <ShoppingCart className="product-detail-btn-icon" />
                    Add to Cart
                  </>
                )}
              </button>
              <button
                className="product-detail-action-btn product-detail-buy-btn"
                id="product-detail-buy-btn"
                data-testid="btn-buy-now"
              >
                <Zap className="product-detail-btn-icon" />
                Buy Now
              </button>
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
