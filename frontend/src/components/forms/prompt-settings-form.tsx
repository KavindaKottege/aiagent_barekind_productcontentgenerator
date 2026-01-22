'use client'

import { useActionState } from 'react'
import { ChevronsUpDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  updatePromptSettings,
  type PromptSettings,
  type PromptSettingsActionState,
} from '@/app/actions/settings'

interface PromptSettingsFormProps {
  initialSettings: PromptSettings
}

const PROMPT_INFO = {
  system: {
    title: 'System Prompt',
    description: 'Sets the AI\'s role and overall behavior. This is the foundation for all generations.',
    example: `You are an expert product copywriter for e-commerce brands. You write compelling, SEO-friendly product titles and descriptions that:
- Highlight key product benefits
- Use natural, conversational language
- Include relevant keywords without keyword stuffing
- Match the brand's voice and tone
- Stay within character limits`,
    tips: [
      'Define the AI\'s role clearly (e.g., "expert product copywriter")',
      'List key behaviors and constraints',
      'Mention brand voice alignment',
      'Keep it concise but comprehensive',
    ],
  },
  task1: {
    title: 'Task 1 Prompt (Title Generation)',
    description: 'Instructions for generating product titles. Focus on format, length, and style requirements.',
    example: `Generate a product title for the following product:

Product Name: {product_name}
Product Type: {product_type}
Brand: {brand_name}

Requirements:
- Length: 30-60 characters
- Include the product type
- Make it descriptive and searchable
- Avoid promotional language like "Best" or "Amazing"

Return only the title, no explanation.`,
    tips: [
      'Use {placeholders} for dynamic product data',
      'Specify character limits clearly',
      'List what to include and avoid',
      'End with "Return only the title"',
    ],
  },
  task2: {
    title: 'Task 2 Prompt (Description Generation)',
    description: 'Instructions for generating product descriptions. Include formatting and content requirements.',
    example: `Generate a product description for the following product:

Product Name: {product_name}
Current Description: {current_description}
Brand Story: {brand_story}
Brand Guidelines: {guidelines}

Requirements:
- Length: 2000-3000 characters
- Start with a hook that captures attention
- Include key features and benefits
- Mention materials, dimensions, or specifications if available
- End with a call to action
- Use the brand's tone: {tone}

Return only the description, no explanation.`,
    tips: [
      'Reference brand story and guidelines',
      'Specify structure (hook, features, CTA)',
      'Include length requirements',
      'Mention tone alignment',
    ],
  },
}

function PromptInfoSection({
  type,
}: {
  type: 'system' | 'task1' | 'task2'
}) {
  const info = PROMPT_INFO[type]

  return (
    <Collapsible className="mb-2">
      <CollapsibleTrigger asChild>
        <Button variant="ghost" size="sm" className="w-full justify-between p-2 h-auto">
          <span className="text-sm text-gray-500">View examples and tips</span>
          <ChevronsUpDown className="h-4 w-4" />
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-2 p-4 bg-gray-50 rounded-md text-sm">
        <div className="space-y-4">
          <div>
            <h4 className="font-medium mb-1">Example:</h4>
            <pre className="whitespace-pre-wrap text-xs bg-white p-3 rounded border overflow-x-auto">
              {info.example}
            </pre>
          </div>
          <div>
            <h4 className="font-medium mb-1">Tips:</h4>
            <ul className="list-disc list-inside space-y-1 text-gray-600">
              {info.tips.map((tip, i) => (
                <li key={i}>{tip}</li>
              ))}
            </ul>
          </div>
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}

export function PromptSettingsForm({ initialSettings }: PromptSettingsFormProps) {
  const [state, formAction, pending] = useActionState<PromptSettingsActionState, FormData>(
    updatePromptSettings,
    { errors: {} }
  )

  return (
    <form action={formAction}>
      <Card>
        <CardHeader>
          <CardTitle>Default Prompt Settings</CardTitle>
          <CardDescription>
            Configure the default AI prompts used for content generation. These can be overridden per-client.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {state.errors?._form && (
            <div className="p-3 bg-red-50 text-red-600 rounded-md text-sm">
              {state.errors._form.join(', ')}
            </div>
          )}

          {state.success && (
            <div className="p-3 bg-green-50 text-green-600 rounded-md text-sm">
              Prompts saved successfully!
            </div>
          )}

          {/* System Prompt */}
          <div className="space-y-2">
            <Label htmlFor="default_system_prompt">{PROMPT_INFO.system.title}</Label>
            <p className="text-sm text-gray-500">{PROMPT_INFO.system.description}</p>
            <PromptInfoSection type="system" />
            <Textarea
              id="default_system_prompt"
              name="default_system_prompt"
              defaultValue={initialSettings.default_system_prompt ?? ''}
              placeholder="Enter the system prompt..."
              rows={6}
              className="font-mono text-sm"
            />
          </div>

          {/* Task 1 Prompt */}
          <div className="space-y-2">
            <Label htmlFor="default_task1_prompt">{PROMPT_INFO.task1.title}</Label>
            <p className="text-sm text-gray-500">{PROMPT_INFO.task1.description}</p>
            <PromptInfoSection type="task1" />
            <Textarea
              id="default_task1_prompt"
              name="default_task1_prompt"
              defaultValue={initialSettings.default_task1_prompt ?? ''}
              placeholder="Enter the Task 1 prompt..."
              rows={8}
              className="font-mono text-sm"
            />
          </div>

          {/* Task 2 Prompt */}
          <div className="space-y-2">
            <Label htmlFor="default_task2_prompt">{PROMPT_INFO.task2.title}</Label>
            <p className="text-sm text-gray-500">{PROMPT_INFO.task2.description}</p>
            <PromptInfoSection type="task2" />
            <Textarea
              id="default_task2_prompt"
              name="default_task2_prompt"
              defaultValue={initialSettings.default_task2_prompt ?? ''}
              placeholder="Enter the Task 2 prompt..."
              rows={10}
              className="font-mono text-sm"
            />
          </div>
        </CardContent>
        <CardFooter>
          <Button type="submit" disabled={pending}>
            {pending ? 'Saving...' : 'Save Prompts'}
          </Button>
        </CardFooter>
      </Card>
    </form>
  )
}
