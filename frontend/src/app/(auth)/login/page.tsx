import { Metadata } from "next";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { LoginForm } from "@/components/forms/login-form";
import { login } from "@/app/actions/auth";

export const metadata: Metadata = {
  title: "Log In - Product Content Generator",
  description: "Log in to your account",
};

export default function LoginPage() {
  return (
    <Card>
      <CardHeader>
        <h2 className="text-2xl font-semibold text-gray-900">Welcome back</h2>
        <p className="text-sm text-gray-600 mt-1">
          Sign in to your account to continue
        </p>
      </CardHeader>
      <CardContent>
        <LoginForm action={login} />
      </CardContent>
    </Card>
  );
}
