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

// Task definitions
const TASKS = [
  {
    id: 'task1',
    title: 'Task 1: Product Title Generation',
    description: 'Generate SEO-optimized product titles',
    hasLength: true,
  },
  {
    id: 'task2',
    title: 'Task 2: Product Description Generation',
    description: 'Generate compelling product descriptions',
    hasLength: true,
  },
  {
    id: 'task3',
    title: 'Task 3: Generated Title Review',
    description: 'AI review of generated titles for quality',
    hasLength: false,
  },
  {
    id: 'task4',
    title: 'Task 4: Generated Description Review',
    description: 'AI review of generated descriptions for quality',
    hasLength: false,
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

  // Form state
  const [systemPrompt, setSystemPrompt] = useState(initialSettings.default_system_prompt ?? '')
  const [task1Prompt, setTask1Prompt] = useState(initialSettings.default_task1_prompt ?? '')
  const [task2Prompt, setTask2Prompt] = useState(initialSettings.default_task2_prompt ?? '')
  const [task3Prompt, setTask3Prompt] = useState(initialSettings.default_task3_prompt ?? '')
  const [task4Prompt, setTask4Prompt] = useState(initialSettings.default_task4_prompt ?? '')

  // Attribute state - use all attributes as defaults if not set
  const allAttrIds = AVAILABLE_ATTRIBUTES.map(a => a.id)
  const [task1DefaultAttrs, setTask1DefaultAttrs] = useState<string[]>(
    initialSettings.task1_default_attributes ?? allAttrIds
  )
  const [task1MandatoryAttrs, setTask1MandatoryAttrs] = useState<string[]>(
    initialSettings.task1_mandatory_attributes ?? ['product_name']
  )
  const [task2DefaultAttrs, setTask2DefaultAttrs] = useState<string[]>(
    initialSettings.task2_default_attributes ?? allAttrIds
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

  // Length state
  const [task1MinLength, setTask1MinLength] = useState(initialSettings.task1_min_length?.toString() ?? '')
  const [task1MaxLength, setTask1MaxLength] = useState(initialSettings.task1_max_length?.toString() ?? '')
  const [task1TargetLength, setTask1TargetLength] = useState(initialSettings.task1_target_length?.toString() ?? '')
  const [task2MinLength, setTask2MinLength] = useState(initialSettings.task2_min_length?.toString() ?? '')
  const [task2MaxLength, setTask2MaxLength] = useState(initialSettings.task2_max_length?.toString() ?? '')
  const [task2TargetLength, setTask2TargetLength] = useState(initialSettings.task2_target_length?.toString() ?? '')

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
                          {AVAILABLE_ATTRIBUTES.map((attr) => {
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
