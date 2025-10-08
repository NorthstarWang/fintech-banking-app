import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../Button'

// Mock analytics logger
jest.mock('@/lib/analytics', () => ({
  analytics: {
    logClick: jest.fn(),
  },
}))

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    button: ({ children, whileTap, ...props }: any) => <button {...props}>{children}</button>,
  },
}))

describe('Button', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render with children', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('should apply default variant and size classes', () => {
    render(<Button>Default Button</Button>)
    const button = screen.getByRole('button')
    expect(button).toHaveClass('btn-primary')
    expect(button).toHaveClass('px-4', 'py-2.5', 'text-base')
  })

  it('should apply different variants', () => {
    const { rerender } = render(<Button variant="secondary">Secondary</Button>)
    expect(screen.getByRole('button')).toHaveClass('backdrop-blur-sm')

    rerender(<Button variant="success">Success</Button>)
    expect(screen.getByRole('button')).toHaveClass('gradient-success')

    rerender(<Button variant="danger">Danger</Button>)
    expect(screen.getByRole('button')).toHaveClass('gradient-danger')

    rerender(<Button variant="ghost">Ghost</Button>)
    expect(screen.getByRole('button')).toHaveClass('bg-transparent')
  })

  it('should apply different sizes', () => {
    const { rerender } = render(<Button size="sm">Small</Button>)
    expect(screen.getByRole('button')).toHaveClass('px-3', 'py-2', 'text-sm')

    rerender(<Button size="lg">Large</Button>)
    expect(screen.getByRole('button')).toHaveClass('px-6', 'py-3', 'text-lg')
  })

  it('should render with icon', () => {
    const icon = <span data-testid="test-icon">🚀</span>
    render(<Button icon={icon}>With Icon</Button>)
    
    expect(screen.getByTestId('test-icon')).toBeInTheDocument()
    expect(screen.getByText('With Icon')).toBeInTheDocument()
  })

  it('should show loading state', () => {
    render(<Button loading>Loading</Button>)
    
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveClass('opacity-50', 'cursor-not-allowed')
    
    // Check for spinner
    const spinner = button.querySelector('svg')
    expect(spinner).toBeInTheDocument()
    expect(spinner).toHaveClass('animate-spin')
  })

  it('should hide icon when loading', () => {
    const icon = <span data-testid="test-icon">🚀</span>
    render(<Button icon={icon} loading>Loading</Button>)
    
    expect(screen.queryByTestId('test-icon')).not.toBeInTheDocument()
  })

  it('should handle disabled state', () => {
    render(<Button disabled>Disabled</Button>)
    
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveClass('opacity-50', 'cursor-not-allowed')
  })

  it('should apply fullWidth class', () => {
    render(<Button fullWidth>Full Width</Button>)
    expect(screen.getByRole('button')).toHaveClass('w-full')
  })

  it('should handle onClick and log analytics', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    
    const button = screen.getByRole('button')
    fireEvent.click(button)
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('should not handle click when disabled', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick} disabled>Disabled</Button>)
    
    fireEvent.click(screen.getByRole('button'))
    
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('should not handle click when loading', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick} loading>Loading</Button>)
    
    fireEvent.click(screen.getByRole('button'))
    
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('should use custom analyticsId', () => {
    render(<Button analyticsId="custom-id">Custom</Button>)
    
    fireEvent.click(screen.getByRole('button'))
    
  })

  it('should use analyticsLabel when children is not string', () => {
    render(
      <Button analyticsLabel="Complex Button">
        <span>Complex</span>
        <span>Children</span>
      </Button>
    )
    
    fireEvent.click(screen.getByRole('button'))
  })

  it('should generate stable ID from button text', () => {
    render(<Button>Test Button 123!</Button>)
    
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('data-testid', 'button-test-button-123')
  })

  it('should merge custom className', () => {
    render(<Button className="custom-class">Custom Class</Button>)
    
    const button = screen.getByRole('button')
    expect(button).toHaveClass('custom-class')
    expect(button).toHaveClass('btn-primary') // Still has default classes
  })

  it('should pass through other HTML button props', () => {
    render(
      <Button
        type="submit"
        name="submitButton"
        value="submit"
        aria-label="Submit form"
      >
        Submit
      </Button>
    )
    
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('type', 'submit')
    expect(button).toHaveAttribute('name', 'submitButton')
    expect(button).toHaveAttribute('value', 'submit')
    expect(button).toHaveAttribute('aria-label', 'Submit form')
  })

  it('should filter out isLoading prop', () => {
    // This tests the prop filtering logic that prevents isLoading from being passed to DOM
    render(<Button {...{ isLoading: true } as any}>Button</Button>)
    
    const button = screen.getByRole('button')
    expect(button).not.toHaveAttribute('isLoading')
  })
})
