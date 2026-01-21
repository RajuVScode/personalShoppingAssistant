import { useState } from "react";
import { Heart } from "lucide-react";
import "../styles/product-image-gallery.css";

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

  const thumbnailHeight = displayImages.length * 80 + (displayImages.length - 1) * 8;

  return (
    <div className="gallery-container" id="gallery-container">
      <div className="gallery-thumbnails" id="gallery-thumbnails">
        {displayImages.map((img, idx) => (
          <div
            key={idx}
            onClick={() => setSelectedImageIndex(idx)}
            className={`gallery-thumbnail ${selectedImageIndex === idx ? 'gallery-thumbnail--selected' : ''}`}
            id={`gallery-thumbnail-${idx}`}
            data-testid={`thumbnail-${idx}`}
          >
            <img
              src={img}
              alt={`${productName} view ${idx + 1}`}
              className="gallery-thumbnail-img"
              onError={handleThumbnailError}
            />
          </div>
        ))}
      </div>
      
      <div className="gallery-main" id="gallery-main">
        <div
          className="gallery-main-image-wrapper"
          id="gallery-main-image-wrapper"
          style={{ height: `${thumbnailHeight}px` }}
          onMouseEnter={() => setIsZooming(true)}
          onMouseLeave={() => setIsZooming(false)}
          onMouseMove={handleMouseMove}
        >
          <img
            src={mainImage}
            alt={productName}
            className={`gallery-main-image ${isZooming ? 'gallery-main-image--zooming' : ''}`}
            id="gallery-main-image"
            style={isZooming ? {
              transformOrigin: `${zoomPosition.x}% ${zoomPosition.y}%`
            } : undefined}
            onError={handleMainImageError}
          />
          {isZooming && (
            <div
              className="gallery-zoom-indicator"
              id="gallery-zoom-indicator"
              style={{
                left: `calc(${zoomPosition.x}% - 40px)`,
                top: `calc(${zoomPosition.y}% - 50px)`,
              }}
            />
          )}
          {isLoading && (
            <div className="gallery-loading-overlay" id="gallery-loading-overlay">
              <div className="gallery-loading-spinner" />
            </div>
          )}
        </div>
        
        <button
          onClick={() => setIsFavorite(!isFavorite)}
          className="gallery-favorite-btn"
          id="gallery-favorite-btn"
          data-testid="btn-favorite"
        >
          <Heart className={`gallery-favorite-icon ${isFavorite ? 'gallery-favorite-icon--active' : ''}`} />
        </button>
      </div>
    </div>
  );
}
