'use client'

import { useState, useTransition } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'

// Available attributes for AI tasks
const AVAILABLE_ATTRIBUTES = [
  { id: 'product_name', label: 'Product Name', alwaysMandatory: true },
  { id: 'description', label: 'Original Description', alwaysMandatory: false },
  { id: 'product_type', label: 'Product Type', alwaysMandatory: false },
  { id: 'option_name', label: 'Option Name', alwaysMandatory: false },
  { id: 'country_of_origin', label: 'Country of Origin', alwaysMandatory: false },
  { id: 'made_to_order', label: 'Made to Order', alwaysMandatory: false },
  { id: 'sku', label: 'SKU', alwaysMandatory: false },
  { id: 'images', label: 'Image URLs', alwaysMandatory: false },
] as const

// Default prompts (fallbacks when no saved value exists)
// Note: Character limits are enforced separately via the Length Settings below
const DEFAULT_SYSTEM_PROMPT = `You are an expert product copywriter for online marketplaces. You create compelling, SEO-optimized content that drives sales while maintaining brand voice and accuracy.`

const DEFAULT_TASK1_PROMPT = `Craft a product title using relevant keywords from the product information and following this format: "Existing Product Name | Relevant Keyword #1 | Relevant Keyword #2" (e.g., "Octopus Figurine | Antique Brass Figure | Miniature Display")`

const DEFAULT_TASK2_PROMPT = `Craft a product description based on the product title above following this format for product "Octopus Figurine | Antique Brass Figure | Miniature Display":

1. 160-character hook that captures the product's overall essence and value (e.g., "Bring a touch of ocean-inspired charm to any space with the Antique Brass Octopus Figurine, a brass figure that captures nature's beauty in miniature form.")

2. 2-sentence description of the product that sums up what it is, how it was created, and what it is used for (e.g., "The Octopus Figurine is carefully sculpted using brass and given an antique finish to elevate modern interiors with a hint of nautical allure. Each detail, from the textured tentacles to the vintage metallic finish, is meticulously crafted to highlight the artistry and craftsmanship behind Kiyo Home's nature-inspired creations.")

3. 1-sentence comprehensive use-case for the product, start the sentence with this phrase: "Perfect as (a/an) [usage] for [target consumers/users]" (e.g., "Perfect as a desk ornament, console tables, workspace displays, shelf accent, giftable keepsake, or just to generally add a coastal charm anywhere one can think of.")

4. List of key features (make them concise, readable, and digestible) - (e.g., "Key Features:
* Antique brass finish with detailed tentacle design
* Compact and lightweight for easy placement and styling
* Doubles as a collectible or conversation piece
* Smooth base ensures safe placement on surface)

5. List of construction materials used ("Made In:," "Materials Used:," etc.) - (e.g., "Construction & Materials:
* Dimensions: 1.89 in x 2.17 in (4.8 cm x 5.5 cm)
* Weight: 30 g
* Material: Solid brass
* Finish: Antique-style polish for an aged look")

6. List of style guide ("Colors:," "Style:," Theme:," "Occasion:," "Seasonality,: etc.) - (e.g., "Style Guide:
* Colors: Antique brass
* Style: Nautical, vintage, and artisanal
* Theme: Ocean-inspired, nature-focused, and tranquil
* Occasion: Everyday décor, gifting, or display use
* Seasonality: Year-round collectible suitable for timeless interiors)

7. List of eco-friendly information (ONLY ADD THIS WHEN RELEVANT! REMOVE OTHERWISE!)

8. List of retailer information ("Why We Made This:," "Why You'll Love This:," "Pairs Well With:," "Suitable for Retailers Such As:") - I want this section to be retailer-focused, as in it should align with the goals of a retailer who will stock up on the product, which is TO SELL

9. Brand story (e.g., "Kiyo Home was founded on the belief that your home should be as unique as you are, a place that inspires and nurtures. Rooted in a love for nature and timeless design, the brand curates décor and lighting that bring warmth and tranquility into your space.")

10. Punchy CTA to encourage retailers to stock up on the product so they can sell (e.g., "Add the Octopus Figurine to your retail collection and offer your customers a sustainable, artful accent that enhances every space with charm and sophistication.")

Additional Notes:

#1 Create the product description copy seamless and continuous that I can simply copy and paste
#2 Don't add heading categories to your generated except for the following sections: Key Features, Construction & Materials, Style Guide, Eco-friendly Information, and Retailer Information, and add bullet points for these sections
#3 Make the prose less stylistic and keep it straightforward while still demonstrating the value that retailers (and their customers) will get when they stock up on the item
#4 Use proper noun when addressing the item to sell
#5 No bold letters! No em dashes!

Here is an example product description for a different product but can be used as a starting point:

"Sleek, timeless, and effortlessly elevated, the Josie Twist Herringbone Bracelet is a waterproof, tarnish-proof essential designed for modern everyday wear.

This bracelet features a subtle twist on the classic herringbone pattern, crafted from 316L stainless steel and coated in 18K gold PVD for enduring shine and hypoallergenic comfort.

Wear it solo as a minimalist statement or layer it with other gold pieces for a polished, trend-forward look that transitions seamlessly from day to night.

Key Features:

- Elegant herringbone chain with a modern twist detail
- Waterproof, tarnish-proof, and hypoallergenic
- 316L stainless steel with durable 18K gold PVD finish
- Adjustable fit: 6.5" + 1.25" extender with secure clasp
- Designed in Vancouver, crafted in South Korea
- Lightweight, comfortable, and built for all-day wear

Construction & Materials:

- Made in South Korea
- Materials Used: 316L Stainless Steel, 18K Gold PVD Coating
- Dimensions: 6.5" + 1.25" Extender
- Care: Waterproof and tarnish-proof; simply wipe clean after wear

Style Guide:

- Colors: Gold
- Style: Minimalist, classic, and refined
- Theme: Everyday luxury and effortless confidence
- Occasion: Daily wear, work, gifting, travel, or layering collections
- Seasonality: Year-round essential with high gifting appeal

Retailer Information:

- Why We Made This: To offer a versatile waterproof bracelet that embodies timeless design and everyday practicality.
- Why You'll Love This: It's a proven bestseller material combination (18K Gold PVD on stainless steel), appealing to customers who want long-lasting jewelry that requires zero maintenance.
- Pairs Well With: Waterproof hoops, minimalist necklaces, or mixed metal stacks.
- Suitable for Retailers Such As: Fashion boutiques, gift shops, jewelry retailers, and lifestyle stores seeking durable, high-margin essentials that perform well year-round.

Lover's Tempo is a women-founded, Vancouver-based jewelry brand creating delicate, design-led pieces that bring a little romance to everyday life. Every collection is crafted to spark delight through thoughtful design, ethical production, and accessible luxury.

Offer effortless shine, year-round wearability, and unbeatable value to your customers with the Josie Twist Herringbone Bracelet."`

const DEFAULT_TASK3_PROMPT = `You are reviewing a product title written for this brand. Your role is to act as a strict editor, brand guardian, and compliance checker.

Review the product title below against the brands product title, brand story and description and complies with all the checks below.
If it does comply, then suggest that it is rejected and also pass back your suggested description which is an edited version of the generated description that complies with all of the below requirements.

Review the product title below against the brands product title brand story and description.

Evaluate the title on the following criteria:
    1.    Structure
Confirm it follows this format exactly:
Product Name | Primary Keyword | Secondary Keyword
    2.    Keyword quality
Check that keywords are specific, SEO Friendly, and shopper-friendly.
    3.    Clarity and hierarchy
Confirm the core product name is immediately clear and not overshadowed by descriptors.
    4.    Brand alignment
Assess whether the title feels connected to the brand story information. It doesnt have to be super close, but consider it
    5.    Readability
Confirm it sounds natural when read out loud and avoids robotic phrasing.`

const DEFAULT_TASK4_PROMPT = `You are reviewing a wholesale product description written for this brand. Your role is to act as a strict editor, brand guardian, and compliance checker.

Review the full output and check if the generated description complies with all the checks below.
If it does comply, then suggest that it is rejected and also pass back your suggested description which is an edited version of the generated description that complies with all of the below requirements. Do NOT rewrite everything from scratch unless absolutely necessary. Instead, identify issues and make precise corrections so the final copy fully meets the original prompt requirements.

Step 1: Structural & Compliance Check

Confirm the following and correct anything that is wrong:
    •    All required sections appear in the correct order.
    •    Paragraph 9 copies the Brand Story & CTA word-for-word with no edits.
    •    Paragraphs 10 and 11 exist and are formatted as single-line, comma-separated keyword lists.
    •    Paragraphs 10 and 11 each contain exactly 7 keyword phrases.

Step 2: Language & Style Audit

Check for common issues and fix them:
    •    Remove any bold text.
    •    Remove any em dashes and replace with periods or commas.
    •    Reduce overly poetic or vague language. Keep it clear, grounded, and retail-focused.
    •    Ensure the product name is treated as a proper noun throughout.
    •    Remove filler adjectives that do not help sell the product.

Step 3: Content Accuracy & Consistency

Verify that:
    •    Materials, dimensions, finishes, and country of origin match the input exactly. If these details do not exist in the input ensure that that the generated description has not made them up.
    •    Eco-friendly claims only appear if supported by the input.
    •    Use cases align with how a retailer would realistically merchandise the item.
    •    No features, benefits, or claims are invented or exaggerated.

Step 4: Retailer Lens Check
Ensure:
    •    The copy speaks to retailers, not just end consumers.
    •    Benefits emphasize ease of selling, gifting appeal, display value, and upsell potential.
    •    Language supports wholesale goals such as repeat orders, add-on sales, and broad customer appeal.`

// Attributes available for generation tasks
const TASK1_ATTRIBUTES = ['product_name', 'description', 'images']
const TASK2_ATTRIBUTES = ['product_name', 'description', 'images', 'country_of_origin']

// Task definitions
const TASKS = [
  {
    id: 'task1',
    title: 'Task 1: Product Title Generation',
    description: 'Generate SEO-optimized product titles',
    hasLength: true,
    defaultPrompt: DEFAULT_TASK1_PROMPT,
    availableAttributes: TASK1_ATTRIBUTES,
  },
  {
    id: 'task2',
    title: 'Task 2: Product Description Generation',
    description: 'Generate compelling product descriptions',
    hasLength: true,
    defaultPrompt: DEFAULT_TASK2_PROMPT,
    availableAttributes: TASK2_ATTRIBUTES,
  },
  {
    id: 'task3',
    title: 'Task 3: Generated Title Review',
    description: 'AI review of generated titles for quality',
    hasLength: false,
    defaultPrompt: DEFAULT_TASK3_PROMPT,
    availableAttributes: null, // All attributes available
  },
  {
    id: 'task4',
    title: 'Task 4: Generated Description Review',
    description: 'AI review of generated descriptions for quality',
    hasLength: false,
    defaultPrompt: DEFAULT_TASK4_PROMPT,
    availableAttributes: null, // All attributes available
  },
] as const

export interface TaskSettings {
  default_system_prompt: string | null
  default_task1_prompt: string | null
  default_task2_prompt: string | null
  default_task3_prompt: string | null
  default_task4_prompt: string | null
  task1_default_attributes: string[] | null
  task1_mandatory_attributes: string[] | null
  task2_default_attributes: string[] | null
  task2_mandatory_attributes: string[] | null
  task3_default_attributes: string[] | null
  task3_mandatory_attributes: string[] | null
  task4_default_attributes: string[] | null
  task4_mandatory_attributes: string[] | null
  task1_min_length: number | null
  task1_max_length: number | null
  task1_target_length: number | null
  task2_min_length: number | null
  task2_max_length: number | null
  task2_target_length: number | null
}

interface AiTaskSettingsFormProps {
  initialSettings: TaskSettings
  onSave: (settings: Partial<TaskSettings>) => Promise<{ success: boolean; error?: string }>
}

type TaskId = 'task1' | 'task2' | 'task3' | 'task4'

export function AiTaskSettingsForm({ initialSettings, onSave }: AiTaskSettingsFormProps) {
  const [isPending, startTransition] = useTransition()
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [openTasks, setOpenTasks] = useState<Set<string>>(new Set(['task1']))

  // Form state - use saved values or fall back to defaults
  const [systemPrompt, setSystemPrompt] = useState(initialSettings.default_system_prompt || DEFAULT_SYSTEM_PROMPT)
  const [task1Prompt, setTask1Prompt] = useState(initialSettings.default_task1_prompt || DEFAULT_TASK1_PROMPT)
  const [task2Prompt, setTask2Prompt] = useState(initialSettings.default_task2_prompt || DEFAULT_TASK2_PROMPT)
  const [task3Prompt, setTask3Prompt] = useState(initialSettings.default_task3_prompt || DEFAULT_TASK3_PROMPT)
  const [task4Prompt, setTask4Prompt] = useState(initialSettings.default_task4_prompt || DEFAULT_TASK4_PROMPT)

  // Attribute state - Task 1 uses product_name, description, images; Task 2 adds country_of_origin
  const allAttrIds = AVAILABLE_ATTRIBUTES.map(a => a.id)
  const [task1DefaultAttrs, setTask1DefaultAttrs] = useState<string[]>(
    initialSettings.task1_default_attributes ?? TASK1_ATTRIBUTES
  )
  const [task1MandatoryAttrs, setTask1MandatoryAttrs] = useState<string[]>(
    initialSettings.task1_mandatory_attributes ?? ['product_name']
  )
  const [task2DefaultAttrs, setTask2DefaultAttrs] = useState<string[]>(
    initialSettings.task2_default_attributes ?? TASK2_ATTRIBUTES
  )
  const [task2MandatoryAttrs, setTask2MandatoryAttrs] = useState<string[]>(
    initialSettings.task2_mandatory_attributes ?? ['product_name']
  )
  const [task3DefaultAttrs, setTask3DefaultAttrs] = useState<string[]>(
    initialSettings.task3_default_attributes ?? allAttrIds
  )
  const [task3MandatoryAttrs, setTask3MandatoryAttrs] = useState<string[]>(
    initialSettings.task3_mandatory_attributes ?? ['product_name']
  )
  const [task4DefaultAttrs, setTask4DefaultAttrs] = useState<string[]>(
    initialSettings.task4_default_attributes ?? allAttrIds
  )
  const [task4MandatoryAttrs, setTask4MandatoryAttrs] = useState<string[]>(
    initialSettings.task4_mandatory_attributes ?? ['product_name']
  )

  // Length state - use saved values or sensible defaults
  const [task1MinLength, setTask1MinLength] = useState(initialSettings.task1_min_length?.toString() ?? '30')
  const [task1MaxLength, setTask1MaxLength] = useState(initialSettings.task1_max_length?.toString() ?? '60')
  const [task1TargetLength, setTask1TargetLength] = useState(initialSettings.task1_target_length?.toString() ?? '45')
  const [task2MinLength, setTask2MinLength] = useState(initialSettings.task2_min_length?.toString() ?? '2000')
  const [task2MaxLength, setTask2MaxLength] = useState(initialSettings.task2_max_length?.toString() ?? '3000')
  const [task2TargetLength, setTask2TargetLength] = useState(initialSettings.task2_target_length?.toString() ?? '2500')

  const toggleTask = (taskId: string) => {
    setOpenTasks(prev => {
      const next = new Set(prev)
      if (next.has(taskId)) {
        next.delete(taskId)
      } else {
        next.add(taskId)
      }
      return next
    })
  }

  const getDefaultAttrs = (taskId: TaskId) => {
    switch (taskId) {
      case 'task1': return task1DefaultAttrs
      case 'task2': return task2DefaultAttrs
      case 'task3': return task3DefaultAttrs
      case 'task4': return task4DefaultAttrs
    }
  }

  const getMandatoryAttrs = (taskId: TaskId) => {
    switch (taskId) {
      case 'task1': return task1MandatoryAttrs
      case 'task2': return task2MandatoryAttrs
      case 'task3': return task3MandatoryAttrs
      case 'task4': return task4MandatoryAttrs
    }
  }

  const setDefaultAttrs = (taskId: TaskId, attrs: string[]) => {
    switch (taskId) {
      case 'task1': setTask1DefaultAttrs(attrs); break
      case 'task2': setTask2DefaultAttrs(attrs); break
      case 'task3': setTask3DefaultAttrs(attrs); break
      case 'task4': setTask4DefaultAttrs(attrs); break
    }
  }

  const setMandatoryAttrs = (taskId: TaskId, attrs: string[]) => {
    switch (taskId) {
      case 'task1': setTask1MandatoryAttrs(attrs); break
      case 'task2': setTask2MandatoryAttrs(attrs); break
      case 'task3': setTask3MandatoryAttrs(attrs); break
      case 'task4': setTask4MandatoryAttrs(attrs); break
    }
  }

  const handleDefaultChange = (taskId: TaskId, attrId: string, checked: boolean) => {
    const current = getDefaultAttrs(taskId)
    if (checked) {
      setDefaultAttrs(taskId, [...current, attrId])
    } else {
      // Can't uncheck if mandatory
      const mandatory = getMandatoryAttrs(taskId)
      if (mandatory.includes(attrId)) return
      setDefaultAttrs(taskId, current.filter(a => a !== attrId))
    }
  }

  const handleMandatoryChange = (taskId: TaskId, attrId: string, checked: boolean) => {
    const attr = AVAILABLE_ATTRIBUTES.find(a => a.id === attrId)
    if (attr?.alwaysMandatory) return // Can't change always-mandatory attributes

    const currentMandatory = getMandatoryAttrs(taskId)
    const currentDefault = getDefaultAttrs(taskId)

    if (checked) {
      setMandatoryAttrs(taskId, [...currentMandatory, attrId])
      // Also add to default if not already there
      if (!currentDefault.includes(attrId)) {
        setDefaultAttrs(taskId, [...currentDefault, attrId])
      }
    } else {
      setMandatoryAttrs(taskId, currentMandatory.filter(a => a !== attrId))
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSuccess(false)
    setError(null)

    startTransition(async () => {
      const settings: Partial<TaskSettings> = {
        default_system_prompt: systemPrompt || null,
        default_task1_prompt: task1Prompt || null,
        default_task2_prompt: task2Prompt || null,
        default_task3_prompt: task3Prompt || null,
        default_task4_prompt: task4Prompt || null,
        task1_default_attributes: task1DefaultAttrs,
        task1_mandatory_attributes: task1MandatoryAttrs,
        task2_default_attributes: task2DefaultAttrs,
        task2_mandatory_attributes: task2MandatoryAttrs,
        task3_default_attributes: task3DefaultAttrs,
        task3_mandatory_attributes: task3MandatoryAttrs,
        task4_default_attributes: task4DefaultAttrs,
        task4_mandatory_attributes: task4MandatoryAttrs,
        task1_min_length: task1MinLength ? parseInt(task1MinLength, 10) : null,
        task1_max_length: task1MaxLength ? parseInt(task1MaxLength, 10) : null,
        task1_target_length: task1TargetLength ? parseInt(task1TargetLength, 10) : null,
        task2_min_length: task2MinLength ? parseInt(task2MinLength, 10) : null,
        task2_max_length: task2MaxLength ? parseInt(task2MaxLength, 10) : null,
        task2_target_length: task2TargetLength ? parseInt(task2TargetLength, 10) : null,
      }

      const result = await onSave(settings)
      if (result.success) {
        setSuccess(true)
        setTimeout(() => setSuccess(false), 3000)
      } else {
        setError(result.error ?? 'Failed to save settings')
      }
    })
  }

  const getPromptValue = (taskId: TaskId) => {
    switch (taskId) {
      case 'task1': return task1Prompt
      case 'task2': return task2Prompt
      case 'task3': return task3Prompt
      case 'task4': return task4Prompt
    }
  }

  const setPromptValue = (taskId: TaskId, value: string) => {
    switch (taskId) {
      case 'task1': setTask1Prompt(value); break
      case 'task2': setTask2Prompt(value); break
      case 'task3': setTask3Prompt(value); break
      case 'task4': setTask4Prompt(value); break
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <Card>
        <CardHeader>
          <CardTitle>AI Task Settings</CardTitle>
          <CardDescription>
            Configure AI prompts, input attributes, and length constraints for each generation and review task.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {error && (
            <div className="p-3 bg-red-50 text-red-600 rounded-md text-sm">
              {error}
            </div>
          )}

          {success && (
            <div className="p-3 bg-green-50 text-green-600 rounded-md text-sm">
              Settings saved successfully!
            </div>
          )}

          {/* System Prompt (Global) */}
          <div className="space-y-2 pb-4 border-b">
            <Label htmlFor="system_prompt" className="text-base font-semibold">
              System Prompt (Global)
            </Label>
            <p className="text-sm text-gray-500">
              Sets the AI&apos;s role and behavior. Applied to all tasks.
            </p>
            <Textarea
              id="system_prompt"
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="You are an expert product copywriter..."
              rows={5}
              className="font-mono text-sm"
            />
          </div>

          {/* Task Sections */}
          {TASKS.map((task) => {
            const taskId = task.id as TaskId
            const isOpen = openTasks.has(taskId)
            const defaultAttrs = getDefaultAttrs(taskId)
            const mandatoryAttrs = getMandatoryAttrs(taskId)

            return (
              <Collapsible
                key={taskId}
                open={isOpen}
                onOpenChange={() => toggleTask(taskId)}
                className="border rounded-lg"
              >
                <CollapsibleTrigger asChild>
                  <button
                    type="button"
                    className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      {isOpen ? (
                        <ChevronDown className="h-5 w-5 text-gray-500" />
                      ) : (
                        <ChevronRight className="h-5 w-5 text-gray-500" />
                      )}
                      <div className="text-left">
                        <h3 className="font-semibold">{task.title}</h3>
                        <p className="text-sm text-gray-500">{task.description}</p>
                      </div>
                    </div>
                  </button>
                </CollapsibleTrigger>
                <CollapsibleContent className="px-4 pb-4 space-y-4">
                  {/* Prompt */}
                  <div className="space-y-2">
                    <Label htmlFor={`${taskId}_prompt`}>Prompt</Label>
                    <Textarea
                      id={`${taskId}_prompt`}
                      value={getPromptValue(taskId)}
                      onChange={(e) => setPromptValue(taskId, e.target.value)}
                      placeholder={`Enter the ${task.title.toLowerCase()} prompt...`}
                      rows={6}
                      className="font-mono text-sm"
                    />
                  </div>

                  {/* Attributes */}
                  <div className="space-y-2">
                    <Label>Input Attributes</Label>
                    <p className="text-sm text-gray-500">
                      Select which product attributes are used for this task.
                    </p>
                    <div className="border rounded-md overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="text-left px-3 py-2 font-medium">Attribute</th>
                            <th className="text-center px-3 py-2 font-medium w-24">Default</th>
                            <th className="text-center px-3 py-2 font-medium w-24">Mandatory</th>
                          </tr>
                        </thead>
                        <tbody>
                          {AVAILABLE_ATTRIBUTES
                            .filter((attr) => !task.availableAttributes || task.availableAttributes.includes(attr.id))
                            .map((attr) => {
                            const isDefault = defaultAttrs.includes(attr.id)
                            const isMandatory = mandatoryAttrs.includes(attr.id) || attr.alwaysMandatory
                            const defaultDisabled = isMandatory // Can't uncheck default if mandatory

                            return (
                              <tr key={attr.id} className="border-t">
                                <td className="px-3 py-2">{attr.label}</td>
                                <td className="text-center px-3 py-2">
                                  <Checkbox
                                    checked={isDefault}
                                    onCheckedChange={(checked) =>
                                      handleDefaultChange(taskId, attr.id, !!checked)
                                    }
                                    disabled={defaultDisabled}
                                  />
                                </td>
                                <td className="text-center px-3 py-2">
                                  <Checkbox
                                    checked={isMandatory}
                                    onCheckedChange={(checked) =>
                                      handleMandatoryChange(taskId, attr.id, !!checked)
                                    }
                                    disabled={attr.alwaysMandatory}
                                  />
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Length Settings (Task 1 & 2 only) */}
                  {task.hasLength && (
                    <div className="space-y-2">
                      <Label>Length Settings (characters)</Label>
                      <div className="flex gap-4">
                        <div className="flex-1">
                          <Label htmlFor={`${taskId}_min_length`} className="text-xs text-gray-500">
                            Min
                          </Label>
                          <Input
                            id={`${taskId}_min_length`}
                            type="number"
                            min="0"
                            value={taskId === 'task1' ? task1MinLength : task2MinLength}
                            onChange={(e) =>
                              taskId === 'task1'
                                ? setTask1MinLength(e.target.value)
                                : setTask2MinLength(e.target.value)
                            }
                            placeholder="0"
                          />
                        </div>
                        <div className="flex-1">
                          <Label htmlFor={`${taskId}_max_length`} className="text-xs text-gray-500">
                            Max
                          </Label>
                          <Input
                            id={`${taskId}_max_length`}
                            type="number"
                            min="0"
                            value={taskId === 'task1' ? task1MaxLength : task2MaxLength}
                            onChange={(e) =>
                              taskId === 'task1'
                                ? setTask1MaxLength(e.target.value)
                                : setTask2MaxLength(e.target.value)
                            }
                            placeholder="∞"
                          />
                        </div>
                        <div className="flex-1">
                          <Label htmlFor={`${taskId}_target_length`} className="text-xs text-gray-500">
                            Target
                          </Label>
                          <Input
                            id={`${taskId}_target_length`}
                            type="number"
                            min="0"
                            value={taskId === 'task1' ? task1TargetLength : task2TargetLength}
                            onChange={(e) =>
                              taskId === 'task1'
                                ? setTask1TargetLength(e.target.value)
                                : setTask2TargetLength(e.target.value)
                            }
                            placeholder="—"
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </CollapsibleContent>
              </Collapsible>
            )
          })}
        </CardContent>
        <CardFooter>
          <Button type="submit" disabled={isPending}>
            {isPending ? 'Saving...' : 'Save Settings'}
          </Button>
        </CardFooter>
      </Card>
    </form>
  )
}
