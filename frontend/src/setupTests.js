import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Global mocks for smoke testing to prevent crashes
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useParams: () => ({ id: '1', pk: '1', uid: 'mockuid', token: 'mocktoken' }),
    useLocation: () => ({ pathname: '/', search: '' }),
  };
});

// Mock ResizeObserver which is not available in jsdom
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
