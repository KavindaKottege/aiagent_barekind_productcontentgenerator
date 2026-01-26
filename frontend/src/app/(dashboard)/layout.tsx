import React from "react";
import Link from "next/link";
import Image from "next/image";
import { verifySession } from "@/lib/dal";
import { logout } from "@/app/actions/auth";
import { getClients } from "@/app/actions/clients";
import { Button } from "@/components/ui/button";
import { ClientSelector } from "@/components/client-selector";
import { ClientProvider } from "@/lib/client-context";
import { UploadButtonWrapper } from "@/components/upload-button-wrapper";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Verify session - will redirect to /login if not authenticated
  await verifySession();

  // Fetch clients for selector
  const clients = await getClients();

  return (
    <ClientProvider>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-brand-dark shadow-sm border-b border-brand-dark-hover">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6">
                <Link href="/dashboard" className="flex items-center gap-3">
                  <Image
                    src="/candidfounders-logo-white.png"
                    alt="Candid Founders"
                    width={140}
                    height={32}
                    priority
                  />
                  <span className="text-gray-500">|</span>
                  <h1 className="text-xl font-semibold text-white">
                    SEO Content Generator
                  </h1>
                </Link>
                <ClientSelector clients={clients} />
                <UploadButtonWrapper clients={clients} />
              </div>
              <nav className="flex items-center gap-4">
                <Link href="/products" className="text-sm text-gray-300 hover:text-white">
                  Products
                </Link>
                <Link href="/review" className="text-sm text-gray-300 hover:text-white">
                  Review
                </Link>
                <Link href="/clients" className="text-sm text-gray-300 hover:text-white">
                  Clients
                </Link>
                <Link href="/settings" className="text-sm text-gray-300 hover:text-white">
                  Settings
                </Link>
                <form action={logout}>
                  <Button type="submit" variant="ghost" size="sm" className="text-gray-300 hover:text-white hover:bg-white/10">
                    Log out
                  </Button>
                </form>
              </nav>
            </div>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </div>
    </ClientProvider>
  );
}
