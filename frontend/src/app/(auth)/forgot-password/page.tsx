"use client";

import { useState } from "react";
import { Metadata } from "next";
import Link from "next/link";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Note: Full password reset flow deferred to future phase
    setSubmitted(true);
  };

  return (
    <Card>
      <CardHeader>
        <h2 className="text-2xl font-semibold text-gray-900">
          Forgot password?
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          Enter your email to reset your password
        </p>
      </CardHeader>
      <CardContent>
        {submitted ? (
          <div className="text-center">
            <div className="p-4 bg-green-50 border border-green-200 rounded-md mb-4">
              <p className="text-sm text-green-600">
                Check your email for password reset instructions.
              </p>
            </div>
            <Link
              href="/login"
              className="text-sm text-blue-600 hover:underline"
            >
              Back to login
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <Button type="submit" className="w-full">
              Send reset link
            </Button>

            <p className="text-center text-sm text-gray-600">
              Remember your password?{" "}
              <Link href="/login" className="text-blue-600 hover:underline">
                Log in
              </Link>
            </p>
          </form>
        )}
      </CardContent>
    </Card>
  );
}
