import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import App from './App'
import { AuthProvider } from './contexts/AuthContext'

describe('ChargeMate application', () => {
  it('renders the public landing page', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>,
    )

    expect(
      screen.getByRole('heading', { name: /Power your journey/i }),
    ).toBeInTheDocument()

    const registerLinks = screen.getAllByRole('link', {
      name: /Get started/i,
    })

    expect(registerLinks.length).toBeGreaterThan(0)
    expect(registerLinks[0]).toHaveAttribute('href', '/register')
  })
})
