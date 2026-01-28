import { Metadata } from "next";
import { getUser } from "@/lib/dal";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export const metadata: Metadata = {
  title: "Dashboard - SEO Content Generator",
  description: "Your dashboard",
};

export default async function DashboardPage() {
  const user = await getUser();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">
          Welcome, {user.name}
        </h2>
        <p className="text-gray-600 mt-1">
          Logged in as {user.email}
        </p>
      </div>

      <Card>
        <CardHeader>
          <h3 className="text-xl font-semibold text-gray-900">
            Account Information
          </h3>
        </CardHeader>
        <CardContent>
          <dl className="space-y-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">User ID</dt>
              <dd className="text-sm text-gray-900">{user.id}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Role</dt>
              <dd className="text-sm text-gray-900">
                {user.is_admin ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                    Admin
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    User
                  </span>
                )}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">
                Member since
              </dt>
              <dd className="text-sm text-gray-900">
                {new Date(user.created_at).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h3 className="text-xl font-semibold text-gray-900">
            Getting Started
          </h3>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">
            Product content generation features will be available in upcoming phases.
            Stay tuned for AI-powered content creation tools!
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
