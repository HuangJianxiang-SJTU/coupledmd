import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

// Mock all page modules
vi.mock('../pages/Home', () => ({
  default: () => <div data-testid="page-home">Home</div>,
}))
vi.mock('../pages/Systems', () => ({
  default: () => <div data-testid="page-systems">Systems</div>,
}))
vi.mock('../pages/SystemDetail', () => ({
  default: () => <div data-testid="page-system-detail">SystemDetail</div>,
}))
vi.mock('../pages/AtlasBrowser', () => ({
  default: () => <div data-testid="page-atlas">AtlasBrowser</div>,
}))
vi.mock('../pages/PartnerSwitch', () => ({
  default: () => <div data-testid="page-compare">PartnerSwitch</div>,
}))
vi.mock('../pages/About', () => ({
  default: () => <div data-testid="page-about">About</div>,
}))
vi.mock('../pages/Help', () => ({
  default: () => <div data-testid="page-help">Help</div>,
}))

import App from '../App'

function renderWithHash(hash) {
  window.location.hash = hash
  return render(<App />)
}

describe('App routing', () => {
  it('renders Home at #/', () => {
    renderWithHash('#/')
    expect(screen.getByTestId('page-home')).toBeInTheDocument()
  })

  it('renders Systems at #/systems', () => {
    renderWithHash('#/systems')
    expect(screen.getByTestId('page-systems')).toBeInTheDocument()
  })

  it('renders AtlasBrowser at #/atlas', () => {
    renderWithHash('#/atlas')
    expect(screen.getByTestId('page-atlas')).toBeInTheDocument()
  })

  it('renders PartnerSwitch at #/compare', () => {
    renderWithHash('#/compare')
    expect(screen.getByTestId('page-compare')).toBeInTheDocument()
  })

  it('renders About at #/about', () => {
    renderWithHash('#/about')
    expect(screen.getByTestId('page-about')).toBeInTheDocument()
  })

  it('renders Help at #/help', () => {
    renderWithHash('#/help')
    expect(screen.getByTestId('page-help')).toBeInTheDocument()
  })

  it('renders nav links', () => {
    renderWithHash('#/')
    expect(screen.getByText('Systems')).toBeInTheDocument()
    expect(screen.getByText('Atlas')).toBeInTheDocument()
    expect(screen.getByText('Compare')).toBeInTheDocument()
    expect(screen.getByText('About')).toBeInTheDocument()
    expect(screen.getByText('Help')).toBeInTheDocument()
  })
})
