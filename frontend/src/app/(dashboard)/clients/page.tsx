import Link from 'next/link'
import { getClients } from '@/app/actions/clients'
import { getUser } from '@/lib/dal'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { DeleteClientButton } from './delete-client-button'

export default async function ClientsPage() {
  const [clients, user] = await Promise.all([getClients(), getUser()])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Clients</h2>
        <Link href="/clients/new">
          <Button>Create Client</Button>
        </Link>
      </div>

      {clients.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500 mb-4">No clients yet. Create your first client to get started.</p>
            <Link href="/clients/new">
              <Button>Create Your First Client</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {clients.map((client) => (
            <Card key={client.id}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-lg font-medium">
                  {client.brand_name}
                  {client.has_custom_prompts && (
                    <Badge variant="secondary" className="ml-2 text-xs">Custom</Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {client.tone && (
                  <p className="text-sm text-gray-500">Tone: {client.tone}</p>
                )}
                {client.language && (
                  <p className="text-sm text-gray-500">Language: {client.language}</p>
                )}
                <div className="flex gap-2 mt-4">
                  <Link href={`/clients/${client.id}`} className="flex-1">
                    <Button variant="outline" className="w-full" size="sm">Edit</Button>
                  </Link>
                  {user.is_admin && (
                    <DeleteClientButton clientId={client.id} clientName={client.brand_name} />
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
