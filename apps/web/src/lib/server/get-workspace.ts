import { createServerFn } from '@tanstack/react-start'

export const getWorkspace = createServerFn({ method: 'GET' }).handler(async () => {
  return {
    id: 'local-workspace',
    name: 'Local Workspace',
  }
})
