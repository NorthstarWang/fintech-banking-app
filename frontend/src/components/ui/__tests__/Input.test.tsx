import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Input } from '../Input'

// Mock analytics logger
jest.mock('@/lib/analytics', () => ({
  analytics: {
    logFormField: jest.fn(),
  },
}))

describe('Input', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render basic input', () => {
    render(<Input placeholder="Enter text" />)
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument()
  })

  it('should render with label', () => {
    render(<Input label="Email Address" />)
    
    const label = screen.getByText('Email Address')
    const input = screen.getByLabelText('Email Address')
    
    expect(label).toBeInTheDocument()
    expect(input).toBeInTheDocument()
    expect(label).toHaveAttribute('for', 'input-email-address')
    expect(input).toHaveAttribute('id', 'input-email-address')
  })

  it('should render required indicator with label', () => {
    render(<Input label="Username" required />)
    
    const requiredIndicator = screen.getByText('Username').querySelector('.field-required')
    expect(requiredIndicator).toBeInTheDocument()
  })

  it('should render with icon', () => {
    const icon = <span data-testid="test-icon">📧</span>
    render(<Input icon={icon} placeholder="Email" />)
    
    expect(screen.getByTestId('test-icon')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Email')).toHaveClass('pl-11')
  })

  it('should render error message', () => {
    render(<Input error="Invalid email address" />)
    
    const errorMessage = screen.getByText('Invalid email address')
    expect(errorMessage).toBeInTheDocument()
    expect(errorMessage).toHaveClass('text-[var(--primary-red)]')
  })

  it('should render helper text when no error', () => {
    render(<Input helperText="Enter your email" />)
    
    const helperText = screen.getByText('Enter your email')
    expect(helperText).toBeInTheDocument()
    expect(helperText).toHaveClass('text-[var(--text-2)]')
  })

  it('should not render helper text when error exists', () => {
    render(<Input error="Invalid input" helperText="Enter valid data" />)
    
    expect(screen.queryByText('Enter valid data')).not.toBeInTheDocument()
    expect(screen.getByText('Invalid input')).toBeInTheDocument()
  })

  it('should apply fullWidth class', () => {
    const { container } = render(<Input fullWidth />)
    const wrapper = container.firstChild
    expect(wrapper).toHaveClass('w-full')
  })

  it('should handle focus event and log analytics', () => {
    const handleFocus = jest.fn()
    render(<Input label="Username" onFocus={handleFocus} />)
    
    const input = screen.getByLabelText('Username')
    fireEvent.focus(input)
    
    expect(handleFocus).toHaveBeenCalledTimes(1)
  })

  it('should handle change event and log analytics', async () => {
    const handleChange = jest.fn()
    const user = userEvent.setup()
    
    render(<Input label="Email" onChange={handleChange} />)
    
    const input = screen.getByLabelText('Email')
    await user.type(input, 'test')
    
    expect(handleChange).toHaveBeenCalled()
  })

  it('should forward ref', () => {
    const ref = React.createRef<HTMLInputElement>()
    render(<Input ref={ref} />)
    
    expect(ref.current).toBeInstanceOf(HTMLInputElement)
  })

  it('should use custom id when provided', () => {
    render(<Input id="custom-input-id" label="Custom" />)
    
    const input = screen.getByLabelText('Custom')
    expect(input).toHaveAttribute('id', 'custom-input-id')
    expect(input).toHaveAttribute('data-testid', 'custom-input-id')
  })

  it('should use analyticsId when provided', () => {
    render(<Input analyticsId="analytics-input" />)
    
    const input = screen.getByRole('textbox')
    expect(input).toHaveAttribute('data-testid', 'analytics-input')
  })

  it('should generate ID from name when no label', () => {
    render(<Input name="email-field" />)
    
    const input = screen.getByRole('textbox')
    expect(input).toHaveAttribute('data-testid', 'email-field')
  })

  it('should use fallback ID when no identifiers provided', () => {
    render(<Input />)
    
    const input = screen.getByRole('textbox')
    expect(input).toHaveAttribute('data-testid', 'input-field')
  })

  it('should merge custom className', () => {
    render(<Input className="custom-class" />)
    
    const input = screen.getByRole('textbox')
    expect(input).toHaveClass('custom-class')
    expect(input).toHaveClass('rounded-lg') // Still has default classes
  })

  it('should apply error styles when error prop is provided', () => {
    render(<Input error="Error message" />)
    
    const input = screen.getByRole('textbox')
    expect(input).toHaveClass('field-error')
  })

  it('should pass through HTML input props', () => {
    render(
      <Input
        type="email"
        name="userEmail"
        placeholder="Enter email"
        disabled
        readOnly
        maxLength={50}
        aria-describedby="email-help"
      />
    )
    
    const input = screen.getByRole('textbox')
    expect(input).toHaveAttribute('type', 'email')
    expect(input).toHaveAttribute('name', 'userEmail')
    expect(input).toHaveAttribute('placeholder', 'Enter email')
    expect(input).toBeDisabled()
    expect(input).toHaveAttribute('readOnly')
    expect(input).toHaveAttribute('maxLength', '50')
    expect(input).toHaveAttribute('aria-describedby', 'email-help')
  })

  it('should use analyticsLabel for analytics when provided', () => {
    render(<Input analyticsLabel="Custom Analytics Label" onFocus={jest.fn()} />)
    
    const input = screen.getByRole('textbox')
    fireEvent.focus(input)
  })

  it('should handle complex label with special characters', () => {
    render(<Input label="Email (Required) - Personal" />)
    
    const input = screen.getByLabelText('Email (Required) - Personal')
    expect(input).toHaveAttribute('id', 'input-email-(required)---personal')
  })
})
