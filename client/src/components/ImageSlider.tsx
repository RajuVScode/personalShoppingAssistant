import { useState, useEffect, useRef } from "react";

interface ImageSliderProps {
  productId: number;
  primaryImageUrl?: string;
  imageCount?: number;
  slideInterval?: number;
  aspectRatio?: string;
}

export function ImageSlider({ 
  productId, 
  primaryImageUrl,
  imageCount = 4,
  slideInterval = 1800,
  aspectRatio = "aspect-[4/3]"
}: ImageSliderProps) {
  const [isHovering, setIsHovering] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const productImages = primaryImageUrl 
    ? [primaryImageUrl] 
    : [`https://loremflickr.com/400/300/fashion,product?lock=${productId}`];

  useEffect(() => {
    productImages.forEach((src, idx) => {
      if (idx === 0) return;
      const img = new Image();
      img.src = src;
    });
  }, [productId]);

  useEffect(() => {
    if (isHovering) {
      intervalRef.current = setInterval(() => {
        setCurrentImageIndex((prev) => (prev + 1) % imageCount);
      }, slideInterval);
    } else {
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
  }, [isHovering, imageCount, slideInterval]);

  return (
    <div 
      className={`w-full ${aspectRatio} bg-muted overflow-hidden relative`}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      <img
        src={productImages[currentImageIndex]}
        alt="Product"
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
  );
}
