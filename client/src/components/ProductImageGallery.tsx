import { useState } from "react";
import { Heart } from "lucide-react";

interface ProductImageGalleryProps {
  images: string[];
  productName: string;
  isLoading?: boolean;
}

export function ProductImageGallery({ 
  images, 
  productName,
  isLoading = false 
}: ProductImageGalleryProps) {
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [isZooming, setIsZooming] = useState(false);
  const [zoomPosition, setZoomPosition] = useState({ x: 50, y: 50 });
  const [isFavorite, setIsFavorite] = useState(false);

  const displayImages = images.length > 0 ? images : [""];
  const mainImage = displayImages[selectedImageIndex] || displayImages[0];

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setZoomPosition({ x, y });
  };

  const handleThumbnailError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const target = e.target as HTMLImageElement;
    target.onerror = null;
    target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Crect fill='%23f3f4f6' width='100' height='100'/%3E%3C/svg%3E";
  };

  const handleMainImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const target = e.target as HTMLImageElement;
    target.onerror = null;
    target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='500' viewBox='0 0 400 500'%3E%3Crect fill='%23f3f4f6' width='400' height='500'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-family='system-ui' font-size='14' fill='%239ca3af'%3EImage unavailable%3C/text%3E%3C/svg%3E";
  };

  return (
    <div className="flex gap-3">
      <div className="flex flex-col gap-2 w-16">
        {displayImages.map((img, idx) => (
          <div
            key={idx}
            onClick={() => setSelectedImageIndex(idx)}
            className={`w-16 h-20 border-2 rounded cursor-pointer overflow-hidden ${
              selectedImageIndex === idx ? 'border-blue-500' : 'border-gray-200'
            }`}
            data-testid={`thumbnail-${idx}`}
          >
            <img
              src={img}
              alt={`${productName} view ${idx + 1}`}
              className="w-full h-full object-cover"
              onError={handleThumbnailError}
            />
          </div>
        ))}
      </div>
      
      <div className="flex-1 relative">
        <div
          className="w-full aspect-[4/5] max-h-[320px] bg-gray-100 rounded-lg overflow-hidden cursor-none relative"
          onMouseEnter={() => setIsZooming(true)}
          onMouseLeave={() => setIsZooming(false)}
          onMouseMove={handleMouseMove}
        >
          <img
            src={mainImage}
            alt={productName}
            className={`w-full h-full object-cover transition-transform duration-200 ${
              isZooming ? 'scale-150' : 'scale-100'
            }`}
            style={isZooming ? {
              transformOrigin: `${zoomPosition.x}% ${zoomPosition.y}%`
            } : undefined}
            onError={handleMainImageError}
          />
          {isZooming && (
            <div
              className="absolute pointer-events-none border-2 border-gray-400 bg-white/20"
              style={{
                width: '80px',
                height: '100px',
                left: `calc(${zoomPosition.x}% - 40px)`,
                top: `calc(${zoomPosition.y}% - 50px)`,
              }}
            />
          )}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/50">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
        
        <button
          onClick={() => setIsFavorite(!isFavorite)}
          className="absolute top-3 right-3 w-10 h-10 bg-white rounded-full shadow-md flex items-center justify-center hover:bg-gray-50"
          data-testid="btn-favorite"
        >
          <Heart className={`w-5 h-5 ${isFavorite ? 'fill-red-500 text-red-500' : 'text-gray-400'}`} />
        </button>
      </div>
    </div>
  );
}
