import Image from "next/image";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-brand-dark">
      <Image
        src="/candidfounders-logo-white.png"
        alt="Candid Founders"
        width={200}
        height={45}
        priority
        className="mb-6"
      />
      <h1 className="text-4xl font-bold text-white">SEO Content Generator</h1>
      <p className="mt-4 text-gray-400">Setting up...</p>
    </main>
  )
}
