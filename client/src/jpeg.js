// Second line of defence for photo checks (F61/F68): the capture path already
// re-encodes through a canvas, which drops EXIF, and this removes any metadata
// segment from the bytes that are actually sent, so a location or device tag can
// not reach the server even if that path changes.
//
// Removed: APP1 (EXIF, XMP), APP2-APP12, APP13 (IPTC) and COM comments.
// Kept: APP0 (JFIF header) and APP14 (colour transform), which decoding needs.

const KEEP_APP = new Set([0xe0, 0xee])

export function stripJpegMetadataBytes(bytes) {
  if (!(bytes?.length > 4) || bytes[0] !== 0xff || bytes[1] !== 0xd8) return bytes // not a JPEG: leave alone
  const out = [bytes.subarray(0, 2)]
  let i = 2
  while (i + 4 <= bytes.length) {
    if (bytes[i] !== 0xff) break
    const marker = bytes[i + 1]
    if (marker === 0xda || marker === 0xd9) break // start of scan or end: the rest is image data
    const len = (bytes[i + 2] << 8) | bytes[i + 3]
    if (len < 2 || i + 2 + len > bytes.length) return bytes // malformed: do not guess
    const isMeta = (marker >= 0xe1 && marker <= 0xed) || marker === 0xfe
    if (!isMeta || KEEP_APP.has(marker)) out.push(bytes.subarray(i, i + 2 + len))
    i += 2 + len
  }
  out.push(bytes.subarray(i))
  const total = out.reduce((n, p) => n + p.length, 0)
  const merged = new Uint8Array(total)
  let at = 0
  for (const p of out) {
    merged.set(p, at)
    at += p.length
  }
  return merged
}

export async function stripJpegMetadata(blob) {
  const bytes = new Uint8Array(await blob.arrayBuffer())
  return new Blob([stripJpegMetadataBytes(bytes)], { type: 'image/jpeg' })
}
