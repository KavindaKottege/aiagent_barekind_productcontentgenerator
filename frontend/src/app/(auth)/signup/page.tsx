import { Metadata } from "next";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SignupForm } from "@/components/forms/signup-form";
import { signup } from "@/app/actions/auth";

export const metadata: Metadata = {
  title: "Sign Up - SEO Content Generator",
  description: "Create your account",
};

export default function SignupPage() {
  return (
    <Card>
      <CardHeader>
        <h2 className="text-2xl font-semibold text-gray-900">
          Create your account
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          Get started with professional product content generation
        </p>
      </CardHeader>
      <CardContent>
        <SignupForm action={signup} />
      </CardContent>
    </Card>
  );
}
