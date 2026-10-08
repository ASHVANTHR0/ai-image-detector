import axios from 'axios'

export const MAX_UPLOAD_MB = 15
export const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']

const http = axios.create({ baseURL: '/api/v1', timeout: 120000 })

export function errorMessage(err) {
  if (!err.response) {
    return 'Cannot reach the backend. Start it with run.bat (or uvicorn on port 8000) and try again.'
  }
  const detail = err.response.data?.detail
  const text = typeof detail === 'string' ? detail : null
  switch (err.response.status) {
    case 413: return text ?? `The file is too large (maximum ${MAX_UPLOAD_MB} MB).`
    case 415: return text ?? 'Unsupported file format. Use JPG, PNG, WEBP or BMP.'
    case 400: return text ?? 'The image is corrupt or too small.'
    case 404: return 'Not found.'
    case 429: return 'Too many requests. Please wait a minute.'
    case 503: return 'The detection model is not loaded on the server. Check the backend window for errors.'
    default: return text ?? `Server error (${err.response.status}).`
  }
}

export const api = {
  health: () => http.get('/health').then((r) => r.data),
  detect: (file, onProgress) => {
    const form = new FormData()
    form.append('image', file)
    return http
      .post('/detect', form, {
        onUploadProgress: (e) => onProgress?.(e.total ? Math.round((e.loaded / e.total) * 100) : 0),
      })
      .then((r) => r.data)
  },
  detections: (params) => http.get('/detections', { params }).then((r) => r.data),
  detection: (id) => http.get(`/detections/${id}`).then((r) => r.data),
  statistics: () => http.get('/statistics').then((r) => r.data),
  evaluation: () => http.get('/evaluation').then((r) => r.data),
}
