'use client'

// Placeholder for Task 3 - will implement full functionality
export function ImageDisplay({ images }: { images: string[] }) {
  return (
    <div className="text-center text-gray-500">
      Image display component
      <br />
      {images.length} image(s)
    </div>
  )
}
