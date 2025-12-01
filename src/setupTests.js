import '@testing-library/jest-dom';

// MSW server (optional, used if mocks/server is present)
let server;
try {
  // eslint-disable-next-line global-require
  server = require('./mocks/server').server;
} catch (e) {
  // no server available
}

if (server) {
  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());
}

// matchMedia mock
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// IntersectionObserver mock
class MockIntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  value: MockIntersectionObserver,
});

// Fetch mock (basic)
if (!global.fetch) {
  global.fetch = jest.fn();
}
