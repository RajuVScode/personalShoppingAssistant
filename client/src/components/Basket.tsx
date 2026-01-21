import { useState, useCallback, useMemo, memo, createContext, useContext, ReactNode } from "react";
import { ShoppingCart, ShoppingBag, X, Trash2, ChevronDown, Package, Store, CalendarDays } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import "../styles/basket.css";

interface Product {
  id: number;
  name: string;
  brand?: string;
  price?: number;
  image_url?: string;
  [key: string]: unknown;
}

interface CartItem {
  product: Product;
  quantity: number;
}

interface CartItemRowProps {
  item: CartItem;
  isSelected: boolean;
  onToggleSelect: (productId: number) => void;
  onUpdateQuantity: (productId: number, delta: number) => void;
  onRemove: (productId: number) => void;
}

const CartItemRow = memo(function CartItemRow({ 
  item, 
  isSelected, 
  onToggleSelect, 
  onUpdateQuantity, 
  onRemove 
}: CartItemRowProps) {
  return (
    <div className="basket-item" id={`basket-item-${item.product.id}`} data-testid={`cart-item-${item.product.id}`}>
      <div className="basket-item-content">
        <div className="basket-item-checkbox">
          <Checkbox
            checked={isSelected}
            onCheckedChange={() => onToggleSelect(item.product.id)}
            className="basket-checkbox"
            data-testid={`checkbox-cart-${item.product.id}`}
          />
        </div>
        {item.product.image_url && (
          <div className="basket-item-image">
            <img
              src={item.product.image_url}
              alt={item.product.name}
              className="basket-item-img"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.onerror = null;
                target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'%3E%3Crect fill='%23f3f4f6' width='64' height='64'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-family='system-ui' font-size='8' fill='%239ca3af'%3ENo image%3C/text%3E%3C/svg%3E";
              }}
            />
          </div>
        )}
        <div className="basket-item-details">
          <div className="basket-item-info">
            <p className="basket-item-name">{item.product.name}</p>
            {item.product.brand && (
              <p className="basket-item-brand">{item.product.brand}</p>
            )}
          </div>
          <div className="basket-item-price-row">
            <span className="basket-item-price">
              ${((item.product.price || 0) * item.quantity).toFixed(2)}
            </span>
          </div>
          <div className="basket-item-actions">
            <div className="basket-quantity-control">
              <button
                onClick={() => onUpdateQuantity(item.product.id, -1)}
                className="basket-quantity-btn basket-quantity-btn--decrease"
                id={`basket-decrease-${item.product.id}`}
                data-testid={`btn-decrease-${item.product.id}`}
              >
                −
              </button>
              <span className="basket-quantity-value">
                {item.quantity}
              </span>
              <button
                onClick={() => onUpdateQuantity(item.product.id, 1)}
                className="basket-quantity-btn basket-quantity-btn--increase"
                id={`basket-increase-${item.product.id}`}
                data-testid={`btn-increase-${item.product.id}`}
              >
                +
              </button>
            </div>
            <button
              onClick={() => onRemove(item.product.id)}
              className="basket-remove-btn"
              id={`basket-remove-${item.product.id}`}
              data-testid={`btn-remove-cart-${item.product.id}`}
            >
              <Trash2 className="basket-remove-icon" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
});

interface BasketContextType {
  cartItems: Map<number, CartItem>;
  selectedCartItems: Set<number>;
  cartItemsArray: CartItem[];
  totalItems: number;
  totalPrice: number;
  selectedItemsCount: number;
  addToCart: (product: Product) => void;
  removeFromCart: (productId: number) => void;
  toggleCartItemSelection: (productId: number) => void;
  updateQuantity: (productId: number, delta: number) => void;
  isInCart: (productId: number) => boolean;
  openBasket: () => void;
  closeBasket: () => void;
}

const BasketContext = createContext<BasketContextType | null>(null);

export function useBasket() {
  const context = useContext(BasketContext);
  if (!context) {
    throw new Error("useBasket must be used within a BasketProvider");
  }
  return context;
}

interface BasketProviderProps {
  children: ReactNode;
}

export function BasketProvider({ children }: BasketProviderProps) {
  const [cartItems, setCartItems] = useState<Map<number, CartItem>>(new Map());
  const [selectedCartItems, setSelectedCartItems] = useState<Set<number>>(new Set());
  const [showBasket, setShowBasket] = useState(false);
  const [isBasketAnimating, setIsBasketAnimating] = useState(false);
  const [shouldRenderBasket, setShouldRenderBasket] = useState(false);
  const [showCheckout, setShowCheckout] = useState(false);
  const [isCheckoutAnimating, setIsCheckoutAnimating] = useState(false);
  const [shouldRenderCheckout, setShouldRenderCheckout] = useState(false);

  const addToCart = useCallback((product: Product) => {
    setCartItems((prev) => {
      const newMap = new Map(prev);
      if (newMap.has(product.id)) {
        newMap.delete(product.id);
        setSelectedCartItems((prevSelected) => {
          const newSelected = new Set(prevSelected);
          newSelected.delete(product.id);
          return newSelected;
        });
      } else {
        newMap.set(product.id, { product, quantity: 1 });
        setSelectedCartItems((prevSelected) => {
          const newSelected = new Set(prevSelected);
          newSelected.add(product.id);
          return newSelected;
        });
      }
      return newMap;
    });
  }, []);

  const removeFromCart = useCallback((productId: number) => {
    setCartItems((prev) => {
      const newMap = new Map(prev);
      newMap.delete(productId);
      return newMap;
    });
    setSelectedCartItems((prev) => {
      const newSelected = new Set(prev);
      newSelected.delete(productId);
      return newSelected;
    });
  }, []);

  const toggleCartItemSelection = useCallback((productId: number) => {
    setSelectedCartItems((prev) => {
      const newSelected = new Set(prev);
      if (newSelected.has(productId)) {
        newSelected.delete(productId);
      } else {
        newSelected.add(productId);
      }
      return newSelected;
    });
  }, []);

  const updateQuantity = useCallback((productId: number, delta: number) => {
    setCartItems((prev) => {
      const item = prev.get(productId);
      if (!item) return prev;
      const newQuantity = item.quantity + delta;
      if (newQuantity < 1) return prev;
      const newMap = new Map(prev);
      newMap.set(productId, { ...item, quantity: newQuantity });
      return newMap;
    });
  }, []);

  const isInCart = useCallback((productId: number) => {
    return cartItems.has(productId);
  }, [cartItems]);

  const openBasket = useCallback(() => {
    setShowBasket(true);
    setShouldRenderBasket(true);
    setTimeout(() => {
      setIsBasketAnimating(true);
    }, 50);
  }, []);

  const closeBasket = useCallback(() => {
    setIsBasketAnimating(false);
    setIsCheckoutAnimating(false);
    setTimeout(() => {
      setShouldRenderBasket(false);
      setShowBasket(false);
      setShouldRenderCheckout(false);
      setShowCheckout(false);
    }, 300);
  }, []);

  const openCheckout = useCallback(() => {
    setShowCheckout(true);
    setShouldRenderCheckout(true);
    setTimeout(() => {
      setIsCheckoutAnimating(true);
    }, 50);
  }, []);

  const closeCheckout = useCallback(() => {
    setIsCheckoutAnimating(false);
    setTimeout(() => {
      setShouldRenderCheckout(false);
      setShowCheckout(false);
    }, 300);
  }, []);

  const cartItemsArray = useMemo(() => Array.from(cartItems.values()), [cartItems]);

  const totalItems = useMemo(() => 
    cartItemsArray.reduce((sum, item) => sum + item.quantity, 0),
    [cartItemsArray]
  );

  const totalPrice = useMemo(() => 
    cartItemsArray
      .filter(item => selectedCartItems.has(item.product.id))
      .reduce((sum, item) => sum + (item.product.price || 0) * item.quantity, 0),
    [cartItemsArray, selectedCartItems]
  );

  const selectedItemsCount = useMemo(() => 
    cartItemsArray
      .filter(item => selectedCartItems.has(item.product.id))
      .reduce((sum, item) => sum + item.quantity, 0),
    [cartItemsArray, selectedCartItems]
  );

  const contextValue: BasketContextType = {
    cartItems,
    selectedCartItems,
    cartItemsArray,
    totalItems,
    totalPrice,
    selectedItemsCount,
    addToCart,
    removeFromCart,
    toggleCartItemSelection,
    updateQuantity,
    isInCart,
    openBasket,
    closeBasket,
  };

  return (
    <BasketContext.Provider value={contextValue}>
      {children}
      
      {shouldRenderBasket && (
        <div 
          className={`basket-overlay ${isBasketAnimating ? 'basket-overlay--visible' : ''}`}
          id="basket-overlay"
          onClick={(e) => {
            if (e.target === e.currentTarget) closeBasket();
          }}
          data-testid="cart-modal-overlay"
        >
          <div 
            className={`basket-modal ${isBasketAnimating ? 'basket-modal--visible' : ''}`}
            id="basket-modal"
          >
            <div className="basket-header" id="basket-header">
              <div className="basket-header-title">
                <ShoppingCart className="basket-header-icon" />
                <span className="basket-header-text">Shopping Cart</span>
                <span className="basket-header-count" id="basket-item-count">
                  {totalItems} items
                </span>
              </div>
              <button 
                onClick={closeBasket}
                className="basket-close-btn"
                id="basket-close-btn"
                data-testid="btn-close-cart"
              >
                <X className="basket-close-icon" />
              </button>
            </div>
            
            <div className="basket-body" id="basket-body">
              {cartItems.size === 0 ? (
                <div className="basket-empty" id="basket-empty">
                  <ShoppingCart className="basket-empty-icon" />
                  <p className="basket-empty-title">Your cart is empty</p>
                  <p className="basket-empty-subtitle">Add products from recommendations</p>
                </div>
              ) : (
                <div className="basket-items-list">
                  {cartItemsArray.map((item) => (
                    <CartItemRow
                      key={item.product.id}
                      item={item}
                      isSelected={selectedCartItems.has(item.product.id)}
                      onToggleSelect={toggleCartItemSelection}
                      onUpdateQuantity={updateQuantity}
                      onRemove={removeFromCart}
                    />
                  ))}
                </div>
              )}
            </div>
            
            {cartItems.size > 0 && (
              <div className="basket-footer" id="basket-footer">
                <div className="basket-summary-row">
                  <span className="basket-summary-label">Selected Items:</span>
                  <span className="basket-summary-value">{selectedItemsCount} of {totalItems}</span>
                </div>
                <div className="basket-total-row">
                  <span className="basket-total-label">Total</span>
                  <span className="basket-total-value" id="basket-total-price">
                    ${totalPrice.toFixed(2)}
                  </span>
                </div>
                <Button 
                  className="basket-checkout-btn"
                  id="basket-checkout-btn"
                  data-testid="btn-checkout"
                  onClick={openCheckout}
                  disabled={selectedItemsCount === 0}
                >
                  <ShoppingBag className="basket-checkout-icon" />
                  Proceed to Checkout ({selectedItemsCount})
                </Button>
              </div>
            )}

            {shouldRenderCheckout && (
              <div 
                className={`basket-checkout-sheet ${isCheckoutAnimating ? 'basket-checkout-sheet--visible' : ''}`}
                id="basket-checkout-sheet"
                data-testid="checkout-sheet"
              >
                <div className="basket-checkout-content">
                  <div className="basket-checkout-header">
                    <h3 className="basket-checkout-title">Flexible Fulfillment Options</h3>
                    <button
                      onClick={closeCheckout}
                      className="basket-checkout-toggle"
                      id="basket-checkout-toggle"
                      data-testid="btn-toggle-checkout"
                    >
                      <ChevronDown className="basket-checkout-toggle-icon" />
                    </button>
                  </div>
                  
                  <p className="basket-checkout-info">
                    Select items above to customize your order, or choose an option below:
                  </p>

                  <div className="basket-checkout-options">
                    <button
                      className="basket-option-btn basket-option-btn--primary"
                      id="basket-place-order-btn"
                      data-testid="btn-place-order"
                    >
                      <div className="basket-option-content">
                        <Package className="basket-option-icon" />
                        <span className="basket-option-text">Place Order</span>
                      </div>
                      <span className="basket-option-hint">Select items first</span>
                    </button>

                    <button
                      className="basket-option-btn basket-option-btn--secondary"
                      id="basket-click-collect-btn"
                      data-testid="btn-click-collect"
                    >
                      <div className="basket-option-content">
                        <Store className="basket-option-icon basket-option-icon--gray" />
                        <span className="basket-option-text basket-option-text--dark">Click & Collect</span>
                      </div>
                      <span className="basket-option-hint">All items to store</span>
                    </button>

                    <button
                      className="basket-option-btn basket-option-btn--secondary"
                      id="basket-book-session-btn"
                      data-testid="btn-book-session"
                    >
                      <div className="basket-option-content">
                        <CalendarDays className="basket-option-icon basket-option-icon--gray" />
                        <span className="basket-option-text basket-option-text--dark">Book Style Session</span>
                      </div>
                      <span className="basket-option-hint">Meet with stylist</span>
                    </button>
                  </div>

                  <button
                    onClick={closeCheckout}
                    className="basket-cancel-btn"
                    id="basket-cancel-btn"
                    data-testid="btn-cancel-checkout"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </BasketContext.Provider>
  );
}

export type { Product, CartItem };
