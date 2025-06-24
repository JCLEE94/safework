// Basic test to ensure test framework works
import { describe, it, expect } from 'vitest'

describe('Basic tests', () => {
  it('should pass', () => {
    expect(1 + 1).toBe(2)
  })

  it('should handle strings', () => {
    expect('Hello World').toContain('World')
  })
})