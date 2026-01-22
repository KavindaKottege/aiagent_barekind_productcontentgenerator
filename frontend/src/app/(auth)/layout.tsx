import React from "react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Product Content Generator
          </h1>
          <p className="text-gray-600 mt-2">
            Professional product content at scale
          </p>
        </div>
        {children}
      </div>
    </div>
  );
}
