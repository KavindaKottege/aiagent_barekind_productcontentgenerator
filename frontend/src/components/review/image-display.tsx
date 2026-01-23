'use client'

import { useState } from 'react'
import Lightbox from 'yet-another-react-lightbox'
import 'yet-another-react-lightbox/styles.css'

interface ImageDisplayProps {
  images: string[]
}

export function ImageDisplay({ images }: ImageDisplayProps) {
  const [lightboxOpen, setLightboxOpen] = useState(false)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [brokenImages, setBrokenImages] = useState<Set<number>>(new Set())

  if (!images || images.length === 0) {
    return (
      <div className="w-full h-64 bg-gray-100 rounded flex items-center justify-center">
        <p className="text-gray-400">No images available</p>
      </div>
    )
  }

  const handleImageError = (index: number) => {
    setBrokenImages(prev => new Set(prev).add(index))
  }

  const handleThumbnailClick = (index: number) => {
    setCurrentIndex(index)
  }

  const handleMainImageClick = () => {
    setLightboxOpen(true)
  }

  const slides = images.map(src => ({ src }))

  return (
    <div className="space-y-3">
      {/* Main image display */}
      <div
        className="w-full h-96 bg-gray-100 rounded overflow-hidden cursor-zoom-in"
        onClick={handleMainImageClick}
      >
        {brokenImages.has(currentIndex) ? (
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-center">
              <p className="text-gray-400 mb-2">Image unavailable</p>
              <p className="text-xs text-gray-300">Click to view in lightbox</p>
            </div>
          </div>
        ) : (
          <img
            src={images[currentIndex]}
            alt={`Product image ${currentIndex + 1}`}
            className="w-full h-full object-contain"
            onError={() => handleImageError(currentIndex)}
          />
        )}
      </div>

      {/* Thumbnail strip */}
      {images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {images.map((src, index) => (
            <button
              key={index}
              onClick={() => handleThumbnailClick(index)}
              className={`flex-shrink-0 w-16 h-16 rounded border-2 overflow-hidden transition-all ${
                currentIndex === index
                  ? 'border-blue-500 ring-2 ring-blue-200'
                  : 'border-gray-200 hover:border-gray-400'
              }`}
            >
              {brokenImages.has(index) ? (
                <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                  <span className="text-xs text-gray-400">✕</span>
                </div>
              ) : (
                <img
                  src={src}
                  alt={`Thumbnail ${index + 1}`}
                  className="w-full h-full object-cover"
                  onError={() => handleImageError(index)}
                />
              )}
            </button>
          ))}
        </div>
      )}

      {/* Lightbox */}
      <Lightbox
        open={lightboxOpen}
        close={() => setLightboxOpen(false)}
        slides={slides}
        index={currentIndex}
        on={{
          view: ({ index }) => setCurrentIndex(index),
        }}
      />
    </div>
  )
}
