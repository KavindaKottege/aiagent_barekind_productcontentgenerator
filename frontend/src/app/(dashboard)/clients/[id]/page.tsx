import { notFound } from 'next/navigation'
import { getClient } from '@/app/actions/clients'
import { ClientForm } from '@/components/forms/client-form'

interface EditClientPageProps {
  params: Promise<{ id: string }>
}

export default async function EditClientPage({ params }: EditClientPageProps) {
  const { id } = await params
  const client = await getClient(id)

  if (!client) {
    notFound()
  }

  return (
    <div className="max-w-2xl mx-auto">
      <ClientForm client={client} />
    </div>
  )
}
