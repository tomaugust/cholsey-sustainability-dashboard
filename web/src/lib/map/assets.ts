import type { MapAssets, MapMeta, BakedParish, BakedSite } from "./types";

export interface AssetUrls {
  meta: string;
  terrain: string;
  imagery: string;
  parishes: string;
  greenspace: string;
}

async function json<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`map asset ${url}: ${r.status}`);
  return (await r.json()) as T;
}

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`map imagery ${url} failed`));
    img.src = url;
  });
}

/** Decode the baked uint8 heightmap to metres. */
export function decodeHeights(buf: ArrayBuffer, meta: MapMeta): Float32Array {
  const { cols, rows, min_m, max_m } = meta.terrain;
  const q = new Uint8Array(buf);
  if (q.length !== cols * rows) {
    throw new Error(`terrain has ${q.length} samples, expected ${cols * rows}`);
  }
  const out = new Float32Array(q.length);
  const span = max_m - min_m;
  for (let i = 0; i < q.length; i++) out[i] = min_m + (q[i] / 255) * span;
  return out;
}

export async function loadAssets(urls: AssetUrls): Promise<MapAssets> {
  const meta = await json<MapMeta>(urls.meta);
  const [terrainBuf, imagery, parishes, greenspace] = await Promise.all([
    fetch(urls.terrain).then((r) => r.arrayBuffer()),
    loadImage(urls.imagery),
    json<{ features: BakedParish[] }>(urls.parishes),
    json<{ features: BakedSite[] }>(urls.greenspace),
  ]);
  return {
    meta,
    heights: decodeHeights(terrainBuf, meta),
    imagery,
    parishes: parishes.features,
    sites: greenspace.features,
  };
}
