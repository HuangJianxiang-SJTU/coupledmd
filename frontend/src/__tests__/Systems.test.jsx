import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

const mockSystems = [
  {
    system_id: 'Gi_6CMO', pdb_id: '6CMO', receptor_name: 'Beta-2 adrenergic receptor',
    receptor_gene: 'ADRB2', g_protein_family: 'Gi', ligand_chem_id: 'BU1',
    total_sampling_ns: 1500, trajectory_type: 'membrane_embedded',
    structural_provenance: 'experimental',
  },
  {
    system_id: 'Gs_7JVQ', pdb_id: '7JVQ', receptor_name: 'Glucagon receptor',
    receptor_gene: 'GCGR', g_protein_family: 'Gs', ligand_chem_id: 'GLU',
    total_sampling_ns: 1500, trajectory_type: 'membrane_embedded',
    structural_provenance: 'experimental',
  },
]

vi.mock('../api', () => ({
  api: {
    systems: () => Promise.resolve({ total: 2, systems: mockSystems, limit: 200, offset: 0 }),
  },
}))

import Systems from '../pages/Systems'

describe('Systems page', () => {
  it('renders system rows', async () => {
    render(<Systems navigate={() => {}} />)

    expect(await screen.findByText('Gi_6CMO')).toBeInTheDocument()
    expect(screen.getByText('Gs_7JVQ')).toBeInTheDocument()
  })

  it('renders family filter pills', () => {
    render(<Systems navigate={() => {}} />)

    expect(screen.getByText('Gi')).toBeInTheDocument()
    expect(screen.getByText('Gs')).toBeInTheDocument()
    expect(screen.getByText('Gq')).toBeInTheDocument()
    expect(screen.getByText('G12-13')).toBeInTheDocument()
  })

  it('renders search input', () => {
    render(<Systems navigate={() => {}} />)

    expect(screen.getByPlaceholderText('Search gene, receptor, PDB ID, ligand…')).toBeInTheDocument()
  })

  it('renders total count', async () => {
    render(<Systems navigate={() => {}} />)

    expect(await screen.findByText(/2/)).toBeInTheDocument()
  })
})
