import { describe, it, expect, vi, afterEach } from 'vitest'
import { fetchRaces, fetchPrediction, ApiError } from '../src/api/client'

function mockFetch(status: number, body: unknown) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('fetchRaces', () => {
  it('requests the races endpoint with the year and returns parsed data', async () => {
    const data = [{ name: 'Madrid', round: 14, date: '2026-09-13', status: 'current' }]
    const f = mockFetch(200, data)
    vi.stubGlobal('fetch', f)

    const result = await fetchRaces(2026)
    expect(result).toEqual(data)
    expect(f).toHaveBeenCalledWith('/races?year=2026')
  })

  it('throws on a non-ok response', async () => {
    vi.stubGlobal('fetch', mockFetch(500, {}))
    await expect(fetchRaces(2026)).rejects.toThrow(/Could not load race schedule/)
  })
})

describe('fetchPrediction', () => {
  it('POSTs race/year/force_refresh and returns parsed data', async () => {
    const data = { race: 'Italy', year: 2026, predictions: [] }
    const f = mockFetch(200, data)
    vi.stubGlobal('fetch', f)

    const result = await fetchPrediction('Italy', 2026, false)
    expect(result).toEqual(data)
    const [url, opts] = f.mock.calls[0]
    expect(url).toBe('/predict')
    expect(opts.method).toBe('POST')
    expect(JSON.parse(opts.body)).toEqual({ race: 'Italy', year: 2026, force_refresh: false })
  })

  it('throws ApiError with status and server detail on failure', async () => {
    vi.stubGlobal('fetch', mockFetch(404, { detail: 'No qualifying data found' }))
    await expect(fetchPrediction('Madrid', 2026)).rejects.toMatchObject({
      status: 404,
      message: 'No qualifying data found',
    })
  })

  it('ApiError carries the status code', async () => {
    vi.stubGlobal('fetch', mockFetch(404, { detail: 'nope' }))
    try {
      await fetchPrediction('Madrid', 2026)
      expect.unreachable('should have thrown')
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError)
      expect((e as ApiError).status).toBe(404)
    }
  })
})
