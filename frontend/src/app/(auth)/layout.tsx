import React from "react";
import Image from "next/image";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-brand-dark px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Image
              src="/candidfounders-logo-white.png"
              alt="Candid Founders"
              width={180}
              height={40}
              priority
            />
          </div>
          <h1 className="text-3xl font-bold text-white">
            SEO Content Generator
          </h1>
          <p className="text-gray-400 mt-2">
            AI-powered SEO content for e-commerce
          </p>
        </div>
        {children}
      </div>
    </div>
  );
}
