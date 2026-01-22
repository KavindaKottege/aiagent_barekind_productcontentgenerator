import { z } from "zod";

// Signup schema matching backend Pydantic models
export const signupSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[a-zA-Z]/, "Password must contain at least one letter")
    .regex(/[0-9]/, "Password must contain at least one number"),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

// Login schema
export const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
});

// Client schema
export const clientSchema = z.object({
  brand_name: z.string().min(1, "Brand name is required").max(255),
  story: z.string().optional().nullable(),
  tone: z.string().max(255).optional().nullable(),
  language: z.string().max(100).optional().nullable(),
  guidelines: z.string().optional().nullable(),
  system_prompt: z.string().optional().nullable(),
  task1_prompt: z.string().optional().nullable(),
  task2_prompt: z.string().optional().nullable(),
});

// Type exports
export type SignupInput = z.infer<typeof signupSchema>;
export type LoginInput = z.infer<typeof loginSchema>;
export type ClientFormData = z.infer<typeof clientSchema>;
