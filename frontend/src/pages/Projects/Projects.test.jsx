import { render } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Projects from './Projects';
import { BrowserRouter } from 'react-router-dom';

vi.mock('../../App', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useAuth: () => ({
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn(),
      setIsAuthenticated: vi.fn()
    })
  };
});

describe('Projects', () => {
  it('renders without crashing', () => {
    render(
      <BrowserRouter>
        <Projects />
      </BrowserRouter>
    );
    expect(true).toBe(true);
  });
});
