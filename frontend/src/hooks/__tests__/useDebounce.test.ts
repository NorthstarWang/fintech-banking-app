import { renderHook, act } from '@testing-library/react'
import { useDebounce } from '../useDebounce'

describe('useDebounce', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('should return initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 500))
    expect(result.current).toBe('initial')
  })

  it('should debounce value changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 500 },
      }
    )

    expect(result.current).toBe('initial')

    // Update the value
    rerender({ value: 'updated', delay: 500 })

    // Value should not change immediately
    expect(result.current).toBe('initial')

    // Advance timers by 500ms
    act(() => {
      jest.advanceTimersByTime(500)
    })

    // Now the value should be updated
    expect(result.current).toBe('updated')
  })

  it('should cancel previous timeout on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 500 },
      }
    )

    // Make multiple rapid changes
    rerender({ value: 'change1', delay: 500 })
    act(() => {
      jest.advanceTimersByTime(200)
    })

    rerender({ value: 'change2', delay: 500 })
    act(() => {
      jest.advanceTimersByTime(200)
    })

    rerender({ value: 'change3', delay: 500 })

    // Value should still be initial
    expect(result.current).toBe('initial')

    // Advance past the debounce delay
    act(() => {
      jest.advanceTimersByTime(500)
    })

    // Should have the last value
    expect(result.current).toBe('change3')
  })

  it('should work with different data types', () => {
    // Test with number
    const { result: numberResult } = renderHook(() => useDebounce(42, 100))
    expect(numberResult.current).toBe(42)

    // Test with object
    const testObj = { name: 'test', value: 123 }
    const { result: objectResult } = renderHook(() => useDebounce(testObj, 100))
    expect(objectResult.current).toBe(testObj)

    // Test with array
    const testArray = [1, 2, 3]
    const { result: arrayResult } = renderHook(() => useDebounce(testArray, 100))
    expect(arrayResult.current).toBe(testArray)
  })

  it('should handle delay changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 1000 },
      }
    )

    rerender({ value: 'updated', delay: 500 })

    // Advance by 500ms (new delay)
    act(() => {
      jest.advanceTimersByTime(500)
    })

    expect(result.current).toBe('updated')
  })

  it('should cleanup timeout on unmount', () => {
    const clearTimeoutSpy = jest.spyOn(global, 'clearTimeout')
    
    const { unmount, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 500 },
      }
    )

    // Trigger a debounce
    rerender({ value: 'updated', delay: 500 })

    // Unmount before timeout completes
    unmount()

    expect(clearTimeoutSpy).toHaveBeenCalled()
  })
})