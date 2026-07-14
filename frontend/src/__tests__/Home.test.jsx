import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

// Mock the API module
vi.mock('../api', () => ({
  api: {
    health: () => Promise.resolve({ status: 'ok', n_systems: 208, schema_version: '1.0' }),
    families: () => Promise.resolve({
      families: [
        { family: 'Gi', n_systems: 95, n_receptors: 50, total_sampling_ns: 142500 },
        { family: 'Gs', n_systems: 65, n_receptors: 35, total_sampling_ns: 97500 },
        { family: 'Gq', n_systems: 42, n_receptors: 25, total_sampling_ns: 63000 },
        { family: 'G12-13', n_systems: 6, n_receptors: 5, total_sampling_ns: 9000 },
      ],
    }),
  },
}))

import Home from '../pages/Home'

describe('Home page', () => {
  it('renders stat cards with system count', async () => {
    render(<Home navigate={() => {}} />)

    // Wait for async data to load
    const statCards = await screen.findAllByText('208')
    expect(statCards.length).toBeGreaterThan(0)
  })

  it('renders family cards', async () => {
    render(<Home navigate={() => {}} />)

    expect(await screen.findByText('Gi')).toBeInTheDocument()
    expect(await screen.findByText('Gs')).toBeInTheDocument()
    expect(await screen.findByText('Gq')).toBeInTheDocument()
    expect(await screen.findByText('G12-13')).toBeInTheDocument()
  })

  it('renders navigation buttons', () => {
    render(<Home navigate={() => {}} />)

    expect(screen.getByText('Browse systems')).toBeInTheDocument()
    expect(screen.getByText('Explore atlas')).toBeInTheDocument()
  })
})
