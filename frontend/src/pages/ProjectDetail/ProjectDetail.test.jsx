import { render } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ProjectDetail from './ProjectDetail';
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

describe('ProjectDetail', () => {
  it('renders without crashing', () => {
    render(
      <BrowserRouter>
        <ProjectDetail />
      </BrowserRouter>
    );
    expect(true).toBe(true);
  });
});
