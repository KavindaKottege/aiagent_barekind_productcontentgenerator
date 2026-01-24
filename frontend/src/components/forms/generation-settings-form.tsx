"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  updateGenerationSettings,
  GenerationSettings,
} from "@/app/actions/settings";

interface GenerationSettingsFormProps {
  initialSettings: GenerationSettings;
}

export function GenerationSettingsForm({
  initialSettings,
}: GenerationSettingsFormProps) {
  const [model, setModel] = useState(initialSettings.ai_model);
  const [temperature, setTemperature] = useState(
    initialSettings.ai_temperature
  );
  const [softCap, setSoftCap] = useState(initialSettings.generation_soft_cap);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);
    setSuccess(false);

    const result = await updateGenerationSettings({
      ai_model: model,
      ai_temperature: temperature,
      generation_soft_cap: softCap,
    });

    setIsSaving(false);

    if (result.success) {
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } else {
      setError(result.error || "Failed to save settings");
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Generation Settings</CardTitle>
        <CardDescription>
          Configure the AI model behavior and cost controls for content
          generation.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Model Selection */}
          <div className="space-y-2">
            <Label htmlFor="model">AI Model</Label>
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger>
                <SelectValue placeholder="Select model" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gpt-5.2">GPT-5.2 (Recommended)</SelectItem>
                <SelectItem value="gpt-5.2-pro">
                  GPT-5.2 Pro (Higher quality, higher cost)
                </SelectItem>
                <SelectItem value="gpt-4o">GPT-4o (Legacy)</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-gray-500">
              GPT-5.2 offers the best balance of quality and cost for product
              content.
            </p>
          </div>

          {/* Temperature */}
          <div className="space-y-2">
            <Label htmlFor="temperature">Temperature ({temperature})</Label>
            <div className="flex items-center gap-4">
              <Input
                type="range"
                id="temperature"
                min="0"
                max="1"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(e.target.value)}
                className="flex-1"
              />
              <Input
                type="number"
                value={temperature}
                onChange={(e) => setTemperature(e.target.value)}
                min="0"
                max="1"
                step="0.1"
                className="w-20"
              />
            </div>
            <p className="text-sm text-gray-500">
              Lower values (0.0-0.3) produce more consistent, predictable
              content. Higher values (0.7-1.0) produce more creative, varied
              content. Recommended: 0.7 for product descriptions.
            </p>
          </div>

          {/* Soft Cap */}
          <div className="space-y-2">
            <Label htmlFor="softCap">Cost Soft Cap ($)</Label>
            <div className="flex items-center gap-2">
              <span className="text-gray-500">$</span>
              <Input
                type="number"
                id="softCap"
                value={softCap}
                onChange={(e) => setSoftCap(e.target.value)}
                min="0"
                step="0.01"
                className="w-32"
              />
            </div>
            <p className="text-sm text-gray-500">
              Generation will pause when costs reach this amount. Users can
              choose to continue or stop. Set to 0 to disable the soft cap (not
              recommended).
            </p>
          </div>

          {/* Error/Success Messages */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {error}
            </div>
          )}
          {success && (
            <div className="p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
              Settings saved successfully!
            </div>
          )}

          {/* Submit */}
          <Button type="submit" disabled={isSaving}>
            {isSaving ? "Saving..." : "Save Settings"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
