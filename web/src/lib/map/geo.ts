/** Web Mercator helpers shared by the baked assets and the 3D scene. */

export function lonToU(lon: number): number {
  return (lon + 180) / 360;
}

export function latToV(lat: number): number {
  const s = Math.sin((lat * Math.PI) / 180);
  return 0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI);
}

/** Ground metres per Mercator unit at a latitude. */
export function metresPerUnit(lat: number): number {
  return 40_075_016.686 * Math.cos((lat * Math.PI) / 180);
}

export type Ring = Array<[number, number]>; // [lon, lat]

export function ringCentroid(ring: Ring): [number, number] {
  let a = 0;
  let cx = 0;
  let cy = 0;
  for (let i = 0; i < ring.length - 1; i++) {
    const [x0, y0] = ring[i];
    const [x1, y1] = ring[i + 1];
    const f = x0 * y1 - x1 * y0;
    a += f;
    cx += (x0 + x1) * f;
    cy += (y0 + y1) * f;
  }
  if (a === 0) return ring[0];
  return [cx / (3 * a), cy / (3 * a)];
}
