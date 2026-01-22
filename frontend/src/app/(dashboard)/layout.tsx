import React from "react";
import Link from "next/link";
import { verifySession } from "@/lib/dal";
import { logout } from "@/app/actions/auth";
import { getClients } from "@/app/actions/clients";
import { Button } from "@/components/ui/button";
import { ClientSelector } from "@/components/client-selector";

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
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <Link href="/dashboard">
                <h1 className="text-2xl font-bold text-gray-900">
                  Product Content Generator
                </h1>
              </Link>
              <ClientSelector clients={clients} />
            </div>
            <nav className="flex items-center gap-4">
              <Link href="/clients" className="text-sm text-gray-600 hover:text-gray-900">
                Clients
              </Link>
              <Link href="/settings" className="text-sm text-gray-600 hover:text-gray-900">
                Settings
              </Link>
              <form action={logout}>
                <Button type="submit" variant="outline" size="sm">
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
  );
}
