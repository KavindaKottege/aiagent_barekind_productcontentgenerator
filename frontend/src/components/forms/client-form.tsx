'use client'

import { useActionState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { createClient, updateClient, type Client, type ClientActionState } from '@/app/actions/clients'

interface ClientFormProps {
  client?: Client
}

export function ClientForm({ client }: ClientFormProps) {
  const isEditing = !!client

  // Bind clientId for update action
  const boundUpdateClient = client
    ? updateClient.bind(null, client.id)
    : createClient

  const [state, formAction, pending] = useActionState<ClientActionState, FormData>(
    boundUpdateClient,
    { errors: {} }
  )

  return (
    <form action={formAction}>
      <Card>
        <CardHeader>
          <CardTitle>{isEditing ? 'Edit Client' : 'Create Client'}</CardTitle>
        </CardHeader>
        <CardContent>
          {state.errors?._form && (
            <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-md text-sm">
              {state.errors._form.join(', ')}
            </div>
          )}

          <Tabs defaultValue="brand" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="brand">Brand & Guidelines</TabsTrigger>
              <TabsTrigger value="prompts">Custom Prompts (Optional)</TabsTrigger>
            </TabsList>

            <TabsContent value="brand" className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label htmlFor="brand_name">Brand Name *</Label>
                <Input
                  id="brand_name"
                  name="brand_name"
                  defaultValue={client?.brand_name ?? ''}
                  required
                  placeholder="e.g., Acme Products"
                />
                {state.errors?.brand_name && (
                  <p className="text-sm text-red-600">{state.errors.brand_name[0]}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="story">Brand Story</Label>
                <Textarea
                  id="story"
                  name="story"
                  defaultValue={client?.story ?? ''}
                  placeholder="Tell the story of this brand..."
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="tone">Tone</Label>
                  <Input
                    id="tone"
                    name="tone"
                    defaultValue={client?.tone ?? ''}
                    placeholder="e.g., Professional, Friendly"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="language">Language</Label>
                  <Input
                    id="language"
                    name="language"
                    defaultValue={client?.language ?? ''}
                    placeholder="e.g., English"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="guidelines">Guidelines</Label>
                <Textarea
                  id="guidelines"
                  name="guidelines"
                  defaultValue={client?.guidelines ?? ''}
                  placeholder="Specific guidelines for content generation..."
                  rows={4}
                />
              </div>
            </TabsContent>

            <TabsContent value="prompts" className="space-y-4 mt-4">
              <p className="text-sm text-gray-500 mb-4">
                Leave these blank to use app-level default prompts. Only set custom prompts if this client needs different instructions.
              </p>

              <div className="space-y-2">
                <Label htmlFor="system_prompt">System Prompt Override</Label>
                <Textarea
                  id="system_prompt"
                  name="system_prompt"
                  defaultValue={client?.system_prompt ?? ''}
                  placeholder="Custom system prompt for this client..."
                  rows={4}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="task1_prompt">Task 1 Prompt Override</Label>
                <Textarea
                  id="task1_prompt"
                  name="task1_prompt"
                  defaultValue={client?.task1_prompt ?? ''}
                  placeholder="Custom Task 1 prompt for this client..."
                  rows={4}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="task2_prompt">Task 2 Prompt Override</Label>
                <Textarea
                  id="task2_prompt"
                  name="task2_prompt"
                  defaultValue={client?.task2_prompt ?? ''}
                  placeholder="Custom Task 2 prompt for this client..."
                  rows={4}
                />
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button type="button" variant="outline" onClick={() => window.history.back()}>
            Cancel
          </Button>
          <Button type="submit" disabled={pending}>
            {pending ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Client'}
          </Button>
        </CardFooter>
      </Card>
    </form>
  )
}
