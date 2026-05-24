import { renderHook, act } from '@testing-library/react'
import { useRunSession } from '@/hooks/useRunSession'

const mockPush = jest.fn()

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

describe('useRunSession', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Ensure EventSource exists on global so we can spy on it
    if (!('EventSource' in global)) {
      (global as unknown as Record<string, unknown>)['EventSource'] = jest.fn()
    }
    jest.spyOn(global, 'EventSource' as never)
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ session_id: 'test-session-001', stream_url: 'http://localhost:8000/run/test-session-001/stream' }),
    }) as jest.Mock
  })

  it('navigates to /run/:id and never opens EventSource', async () => {
    const { result } = renderHook(() => useRunSession())
    await act(async () => {
      await result.current.run('test query', '')
    })
    expect(global.EventSource).not.toHaveBeenCalled()
    expect(mockPush).toHaveBeenCalledTimes(1)
    expect(mockPush).toHaveBeenCalledWith('/run/test-session-001')
  })
})
