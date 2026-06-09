import { render } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ChangeEmail from './ChangeEmail';
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

describe('ChangeEmail', () => {
  it('renders without crashing', () => {
    render(
      <BrowserRouter>
        <ChangeEmail />
      </BrowserRouter>
    );
    expect(true).toBe(true);
  });
});
