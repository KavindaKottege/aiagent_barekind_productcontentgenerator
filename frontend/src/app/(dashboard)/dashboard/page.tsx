import { Metadata } from "next";
import Link from "next/link";
import { getUser } from "@/lib/dal";
import { getClients } from "@/app/actions/clients";
import { Card, CardContent } from "@/components/ui/card";
import {
  Users,
  Upload,
  Sparkles,
  Package,
  CheckCircle,
  Settings,
  ArrowRight,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Dashboard - SEO Content Generator",
  description: "Your dashboard",
};

export default async function DashboardPage() {
  const user = await getUser();
  const clients = await getClients();

  const isNewUser = clients.length === 0;

  return (
    <div className="animate-fade-in space-y-8">
      {isNewUser ? (
        <NewUserDashboard userName={user.name} />
      ) : (
        <ReturningUserDashboard
          userName={user.name}
          isAdmin={user.is_admin}
        />
      )}
    </div>
  );
}

function NewUserDashboard({ userName }: { userName: string }) {
  const steps = [
    {
      number: 1,
      title: "Create a Client",
      description:
        "Set up your first client profile with brand voice and guidelines",
      icon: Users,
      href: "/clients",
      cta: "Create Client",
      active: true,
    },
    {
      number: 2,
      title: "Upload Products",
      description: "Upload your Faire Excel file with product data",
      icon: Upload,
      href: null,
      cta: null,
      active: false,
    },
    {
      number: 3,
      title: "Generate Content",
      description: "AI generates optimized titles and descriptions",
      icon: Sparkles,
      href: null,
      cta: null,
      active: false,
    },
  ];

  return (
    <>
      <div className="text-center pt-8 pb-2">
        <h2 className="text-3xl font-bold text-gray-900">
          Welcome to SEO Content Generator
          {userName ? `, ${userName}` : ""}
        </h2>
        <p className="text-gray-500 mt-3 text-lg">
          Get started in three simple steps
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
        {steps.map((step) => {
          const Icon = step.icon;
          return (
            <Card
              key={step.number}
              className={`relative rounded-xl p-6 ${
                step.active
                  ? "ring-2 ring-brand-blue shadow-md"
                  : "opacity-50"
              }`}
            >
              <CardContent className="flex flex-col items-center text-center space-y-4 px-0 py-0">
                <div
                  className={`flex items-center justify-center w-10 h-10 rounded-full text-sm font-bold ${
                    step.active
                      ? "bg-brand-blue text-white"
                      : "bg-gray-200 text-gray-500"
                  }`}
                >
                  {step.number}
                </div>
                <div
                  className={`flex items-center justify-center w-12 h-12 rounded-lg ${
                    step.active
                      ? "bg-brand-blue-light text-brand-blue"
                      : "bg-gray-100 text-gray-400"
                  }`}
                >
                  <Icon className="w-6 h-6" />
                </div>
                <div>
                  <h3
                    className={`text-lg font-semibold ${
                      step.active ? "text-gray-900" : "text-gray-400"
                    }`}
                  >
                    {step.title}
                  </h3>
                  <p
                    className={`text-sm mt-1 ${
                      step.active ? "text-gray-600" : "text-gray-400"
                    }`}
                  >
                    {step.description}
                  </p>
                </div>
                {step.active && step.href && step.cta && (
                  <Link
                    href={step.href}
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-blue text-white text-sm font-medium rounded-lg hover:bg-brand-blue-hover transition-colors"
                  >
                    {step.cta}
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </>
  );
}

function ReturningUserDashboard({
  userName,
  isAdmin,
}: {
  userName: string;
  isAdmin: boolean;
}) {
  const quickActions = [
    {
      title: "Products",
      description: "View and manage your product catalog",
      icon: Package,
      href: "/products",
    },
    {
      title: "Review",
      description: "Review and approve generated content",
      icon: CheckCircle,
      href: "/review",
    },
    {
      title: "Clients",
      description: "Manage client profiles and brand settings",
      icon: Users,
      href: "/clients",
    },
    ...(isAdmin
      ? [
          {
            title: "Settings",
            description: "Configure AI generation settings",
            icon: Settings,
            href: "/settings",
          },
        ]
      : []),
  ];

  return (
    <>
      <div>
        <h2 className="text-3xl font-bold text-gray-900">
          Welcome back, {userName}
        </h2>
        <p className="text-gray-500 mt-1">
          Pick up where you left off
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {quickActions.map((action) => {
          const Icon = action.icon;
          return (
            <Link key={action.title} href={action.href}>
              <Card className="card-hover rounded-xl p-6 group cursor-pointer">
                <CardContent className="flex items-center gap-5 px-0 py-0">
                  <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-gray-100 text-gray-600 group-hover:bg-brand-blue-light group-hover:text-brand-blue transition-colors">
                    <Icon className="w-6 h-6" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {action.title}
                    </h3>
                    <p className="text-sm text-gray-500 mt-0.5">
                      {action.description}
                    </p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-300 group-hover:text-gray-500 transition-colors" />
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </>
  );
}
