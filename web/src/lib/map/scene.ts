/** The 3D Cholsey map (Phase 9, ADR-0018). Rebuilt from the `web-map-render`
 * prototype: a terrain block with baked OSM imagery, a drag/flick/pinch rig,
 * and layers that raise the real parish polygons by their real values. All
 * numbers shown come from the server-rendered DOM; this file only draws. */
import * as THREE from "three";
import { latToV, lonToU, metresPerUnit, ringCentroid, type Ring } from "./geo";
import type { BakedSite, LayerConfig, MapAssets } from "./types";

export interface PinScreen {
  code: string;
  x: number;
  y: number;
  visible: boolean;
}

export interface SceneOptions {
  reducedMotion: boolean;
  onPins: (pins: PinScreen[]) => void;
}

export interface SceneHandle {
  setLayer(layer: LayerConfig): void;
  setActive(active: boolean): void;
  setAuto(on: boolean): void;
  rotate(dyaw: number, dpitch: number): void;
  zoom(factor: number): void;
  dispose(): void;
}

const CHOLSEY = "E04012474";
const GREEN = 0x0b5d3b;
const GREY = 0xa9b3bd;
const PRISM_MAX_KM = 2.4;
const ease = (t: number) => 1 - Math.pow(1 - Math.min(1, Math.max(0, t)), 3);

export function createScene(
  canvas: HTMLCanvasElement,
  assets: MapAssets,
  opts: SceneOptions,
): SceneHandle {
  const { meta } = assets;
  const { u0, u1, v0, v1 } = meta.bbox_uv;
  const lat0 = (meta.bbox_lonlat.north + meta.bbox_lonlat.south) / 2;
  const M = metresPerUnit(lat0) / 1000; // km per mercator unit
  const uc = (u0 + u1) / 2;
  const vc = (v0 + v1) / 2;
  const widthKm = (u1 - u0) * M;
  const depthKm = (v1 - v0) * M;
  const { cols, rows, min_m: hMin } = meta.terrain;
  const small = canvas.clientWidth < 640;
  const stride = small ? 2 : 1;
  const gc = Math.floor((cols - 1) / stride) + 1;
  const gr = Math.floor((rows - 1) / stride) + 1;

  const toXZ = (lon: number, lat: number): [number, number] => [
    (lonToU(lon) - uc) * M,
    (latToV(lat) - vc) * M,
  ];
  const heightAt = (lon: number, lat: number): number => {
    const fx = ((lonToU(lon) - u0) / (u1 - u0)) * (cols - 1);
    const fy = ((latToV(lat) - v0) / (v1 - v0)) * (rows - 1);
    const x = Math.min(cols - 1.001, Math.max(0, fx));
    const y = Math.min(rows - 1.001, Math.max(0, fy));
    const xi = Math.floor(x);
    const yi = Math.floor(y);
    const tx = x - xi;
    const ty = y - yi;
    const h = assets.heights;
    const a = h[yi * cols + xi];
    const b = h[yi * cols + xi + 1];
    const c = h[(yi + 1) * cols + xi];
    const d = h[(yi + 1) * cols + xi + 1];
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty;
  };

  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, small ? 1.5 : 2));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.5, 400);
  scene.add(new THREE.HemisphereLight(0xffffff, 0xd8d2c4, 1.7));
  const sun = new THREE.DirectionalLight(0xffffff, 2.0);
  sun.position.set(-8, 12, 7);
  scene.add(sun);

  const pivot = new THREE.Group();
  const content = new THREE.Group(); // shifted so the layer's focus sits on the pivot origin
  pivot.add(content);
  scene.add(pivot);

  // ---- Terrain block ----
  const posCount = gc * gr;
  const positions = new Float32Array(posCount * 3);
  const uvs = new Float32Array(posCount * 2);
  const baseHeights = new Float32Array(posCount);
  let k = 0;
  for (let j = 0; j < gr; j++) {
    for (let i = 0; i < gc; i++, k++) {
      const s = i / (gc - 1);
      const t = j / (gr - 1);
      const src =
        Math.min(rows - 1, j * stride) * cols + Math.min(cols - 1, i * stride);
      baseHeights[k] = assets.heights[src];
      positions[k * 3] = (s - 0.5) * widthKm;
      positions[k * 3 + 2] = (t - 0.5) * depthKm;
      uvs[k * 2] = s;
      uvs[k * 2 + 1] = 1 - t;
    }
  }
  const index: number[] = [];
  for (let j = 0; j < gr - 1; j++) {
    for (let i = 0; i < gc - 1; i++) {
      const a = j * gc + i;
      const b = a + 1;
      const c = a + gc;
      const d = c + 1;
      index.push(a, c, b, b, c, d);
    }
  }
  const topGeo = new THREE.BufferGeometry();
  topGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  topGeo.setAttribute("uv", new THREE.BufferAttribute(uvs, 2));
  topGeo.setIndex(index);

  const texCanvas = document.createElement("canvas");
  texCanvas.width = assets.imagery.naturalWidth;
  texCanvas.height = assets.imagery.naturalHeight;
  const texture = new THREE.CanvasTexture(texCanvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  const top = new THREE.Mesh(
    topGeo,
    new THREE.MeshStandardMaterial({
      map: texture,
      roughness: 0.95,
      metalness: 0,
    }),
  );
  content.add(top);

  const wallMat = new THREE.MeshStandardMaterial({
    color: 0xe4ded0,
    roughness: 1,
  });
  const wallGeo = new THREE.BufferGeometry();
  const BASE_Y = -0.35;
  const edge: number[] = [];
  for (let i = 0; i < gc; i++) edge.push(i); // north
  for (let j = 1; j < gr; j++) edge.push(j * gc + gc - 1); // east
  for (let i = gc - 2; i >= 0; i--) edge.push((gr - 1) * gc + i); // south
  for (let j = gr - 2; j >= 1; j--) edge.push(j * gc); // west
  const wallPos = new Float32Array(edge.length * 2 * 3);
  const wallIdx: number[] = [];
  for (let n = 0; n < edge.length; n++) {
    const nx = (n + 1) % edge.length;
    wallIdx.push(n * 2, n * 2 + 1, nx * 2, nx * 2, n * 2 + 1, nx * 2 + 1);
  }
  wallGeo.setAttribute("position", new THREE.BufferAttribute(wallPos, 3));
  wallGeo.setIndex(wallIdx);
  const walls = new THREE.Mesh(
    wallGeo,
    new THREE.MeshStandardMaterial({
      color: 0xe4ded0,
      roughness: 1,
      side: THREE.DoubleSide,
    }),
  );
  content.add(walls);
  const baseMesh = new THREE.Mesh(
    new THREE.PlaneGeometry(widthKm, depthKm),
    wallMat,
  );
  baseMesh.rotation.x = Math.PI / 2;
  baseMesh.position.y = BASE_Y;
  content.add(baseMesh);

  let exag = 3;
  let exagTarget = 3;
  function applyExaggeration() {
    for (let n = 0; n < posCount; n++) {
      positions[n * 3 + 1] = ((baseHeights[n] - hMin) * exag) / 1000;
    }
    topGeo.attributes.position.needsUpdate = true;
    topGeo.computeVertexNormals();
    for (let n = 0; n < edge.length; n++) {
      const v = edge[n];
      wallPos.set(
        [positions[v * 3], positions[v * 3 + 1], positions[v * 3 + 2]],
        n * 6,
      );
      wallPos.set([positions[v * 3], BASE_Y, positions[v * 3 + 2]], n * 6 + 3);
    }
    wallGeo.attributes.position.needsUpdate = true;
    wallGeo.computeVertexNormals();
  }
  applyExaggeration();

  // ---- Texture overlays per layer ----
  const parishRings = assets.parishes.map((p) => ({
    ...p,
    ring: p.geometry.coordinates[0] as Ring,
  }));
  const px = (lon: number) =>
    ((lonToU(lon) - u0) / (u1 - u0)) * texCanvas.width;
  const py = (lat: number) =>
    ((latToV(lat) - v0) / (v1 - v0)) * texCanvas.height;
  const path = (ctx: CanvasRenderingContext2D, ring: Ring) => {
    ctx.beginPath();
    ring.forEach(([lon, lat], i) =>
      i ? ctx.lineTo(px(lon), py(lat)) : ctx.moveTo(px(lon), py(lat)),
    );
    ctx.closePath();
  };
  function paintTexture(mode: LayerConfig["mode"]) {
    const ctx = texCanvas.getContext("2d")!;
    ctx.drawImage(assets.imagery, 0, 0);
    const wash = mode === "prisms" ? 0.45 : 0.55;
    ctx.fillStyle = `rgba(255,255,255,${wash})`;
    ctx.fillRect(0, 0, texCanvas.width, texCanvas.height);
    const cholsey = parishRings.find((p) => p.area_code === CHOLSEY);
    if (cholsey && mode !== "prisms") {
      ctx.save();
      path(ctx, cholsey.ring);
      ctx.clip();
      ctx.drawImage(assets.imagery, 0, 0);
      ctx.restore();
    }
    ctx.lineJoin = "round";
    for (const p of parishRings) {
      path(ctx, p.ring);
      ctx.strokeStyle =
        p.area_code === CHOLSEY ? "#0b5d3b" : "rgba(51,65,85,0.45)";
      ctx.lineWidth = p.area_code === CHOLSEY ? 7 : 2.5;
      ctx.stroke();
    }
    texture.needsUpdate = true;
  }

  // ---- Layer objects ----
  const layerGroup = new THREE.Group();
  content.add(layerGroup);
  interface Prism {
    mesh: THREE.Object3D;
    code: string;
    topY: number;
    delay: number;
  }
  let prisms: Prism[] = [];
  let pinAnchors: Array<{ code: string; local: THREE.Vector3 }> = [];
  let layerStart = performance.now();
  let focusLocal = new THREE.Vector3();
  let focusTarget = new THREE.Vector3();
  let distTarget = Math.max(widthKm, depthKm) * 1.55;
  const state = {
    yaw: 0.5,
    pitch: 0.95,
    yawVel: 0,
    dist: distTarget,
    dragging: false,
    active: true,
  };
  let AUTO = opts.reducedMotion ? 0 : 0.1;

  function ringToShape(ring: Ring): THREE.Shape {
    const pts = ring.map(([lon, lat]) => {
      const [x, z] = toXZ(lon, lat);
      return new THREE.Vector2(x, -z);
    });
    return new THREE.Shape(pts);
  }

  function clearLayer() {
    layerGroup.traverse((o) => {
      const m = o as THREE.Mesh;
      m.geometry?.dispose?.();
    });
    layerGroup.clear();
    prisms = [];
    pinAnchors = [];
  }

  function siteMeshes(sites: BakedSite[]) {
    const mat = new THREE.MeshStandardMaterial({
      color: 0x22a06b,
      roughness: 0.6,
    });
    for (const s of sites) {
      const polys =
        s.geometry.type === "Polygon"
          ? [s.geometry.coordinates as Ring[]]
          : (s.geometry.coordinates as Ring[][]);
      for (const rings of polys) {
        const ring = rings[0];
        const hs = ring.map(([lon, lat]) => heightAt(lon, lat));
        const y0 = ((Math.min(...hs) - hMin) * exag) / 1000;
        const geo = new THREE.ExtrudeGeometry(ringToShape(ring), {
          depth: 0.12,
          bevelEnabled: false,
        });
        geo.rotateX(-Math.PI / 2);
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.y = y0 - 0.01;
        layerGroup.add(mesh);
      }
    }
  }

  function setLayer(layer: LayerConfig) {
    clearLayer();
    paintTexture(layer.mode);
    exagTarget =
      layer.mode === "prisms" ? 1 : layer.mode === "greenspace" ? 4 : 3;
    layerStart = performance.now();
    const values = layer.items
      .map((i) => i.value)
      .filter((v): v is number => v !== null);
    const vmax = Math.max(...values, 0);
    const byCode = new Map(layer.items.map((i) => [i.code, i]));
    const cholsey = parishRings.find((p) => p.area_code === CHOLSEY)!;
    const [ccx, ccz] = toXZ(...ringCentroid(cholsey.ring));
    focusTarget = new THREE.Vector3(0, 0, 0);
    distTarget = Math.max(widthKm, depthKm) * 1.55;
    if (layer.mode !== "prisms") {
      focusTarget.set(-ccx * 0.6, 0, -ccz * 0.6);
      distTarget =
        Math.max(widthKm, depthKm) * (layer.mode === "greenspace" ? 0.5 : 1.25);
    }
    parishRings.forEach((p, idx) => {
      const [cx, cz] = toXZ(...ringCentroid(p.ring));
      const item = byCode.get(p.area_code);
      let topY =
        ((heightAt(...ringCentroid(p.ring)) - hMin) * 1 * exagTarget) / 1000 +
        0.05;
      if (layer.mode === "prisms" && item && item.value !== null && vmax > 0) {
        const h = Math.max(0.05, (item.value / vmax) * PRISM_MAX_KM);
        const geo = new THREE.ExtrudeGeometry(ringToShape(p.ring), {
          depth: h,
          bevelEnabled: false,
        });
        geo.rotateX(-Math.PI / 2);
        const isC = p.area_code === CHOLSEY;
        const mesh = new THREE.Mesh(
          geo,
          new THREE.MeshStandardMaterial({
            color: isC ? GREEN : GREY,
            roughness: 0.7,
          }),
        );
        const edges = new THREE.LineSegments(
          new THREE.EdgesGeometry(geo, 30),
          new THREE.LineBasicMaterial({ color: isC ? 0x06402a : 0x6b7783 }),
        );
        mesh.add(edges);
        mesh.scale.y = 0.001;
        layerGroup.add(mesh);
        prisms.push({ mesh, code: p.area_code, topY: h, delay: idx * 60 });
        topY = h + 0.08;
      }
      pinAnchors.push({
        code: p.area_code,
        local: new THREE.Vector3(cx, topY, cz),
      });
    });
    if (layer.mode === "greenspace") siteMeshes(assets.sites);
  }

  // ---- Controls ----
  const pointers = new Map<number, { x: number; y: number }>();
  let pinchStart = 0;
  let distStart = 0;
  const clampDist = (d: number) =>
    Math.min(Math.max(widthKm, depthKm) * 2.4, Math.max(2.5, d));
  const onDown = (e: PointerEvent) => {
    canvas.setPointerCapture(e.pointerId);
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      pinchStart = Math.hypot(a.x - b.x, a.y - b.y);
      distStart = state.dist;
    }
    state.dragging = true;
    state.yawVel = 0;
  };
  const onMove = (e: PointerEvent) => {
    const p = pointers.get(e.pointerId);
    if (!p) return;
    const dx = e.clientX - p.x;
    const dy = e.clientY - p.y;
    p.x = e.clientX;
    p.y = e.clientY;
    if (pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      state.dist = clampDist(
        (distStart * pinchStart) /
          Math.max(1, Math.hypot(a.x - b.x, a.y - b.y)),
      );
      distTarget = state.dist;
      return;
    }
    rotate(dx * 0.0055, dy * 0.0055);
    state.yawVel = Math.max(
      -2.5,
      Math.min(2.5, state.yawVel * 0.6 + ((dx * 0.0055) / 0.016) * 0.4),
    );
  };
  const onUp = (e: PointerEvent) => {
    if (!pointers.delete(e.pointerId)) return;
    if (!pointers.size) state.dragging = false;
  };
  const onWheel = (e: WheelEvent) => {
    if (!e.ctrlKey && !e.metaKey && Math.abs(e.deltaY) < 1) return;
    e.preventDefault();
    zoom(Math.exp(e.deltaY * 0.001));
  };
  const onKey = (e: KeyboardEvent) => {
    const step = 0.12;
    if (e.key === "ArrowLeft") rotate(-step, 0);
    else if (e.key === "ArrowRight") rotate(step, 0);
    else if (e.key === "ArrowUp") rotate(0, -step);
    else if (e.key === "ArrowDown") rotate(0, step);
    else if (e.key === "+" || e.key === "=") zoom(0.85);
    else if (e.key === "-") zoom(1.15);
    else return;
    e.preventDefault();
  };
  function rotate(dyaw: number, dpitch: number) {
    state.yaw += dyaw;
    state.pitch = Math.min(1.45, Math.max(0.2, state.pitch + dpitch));
  }
  function zoom(f: number) {
    distTarget = clampDist(distTarget * f);
  }
  canvas.addEventListener("pointerdown", onDown);
  canvas.addEventListener("pointermove", onMove);
  canvas.addEventListener("pointerup", onUp);
  canvas.addEventListener("pointercancel", onUp);
  canvas.addEventListener("wheel", onWheel, { passive: false });
  canvas.addEventListener("keydown", onKey);

  // ---- Sizing and loop ----
  function resize() {
    const w = canvas.clientWidth || 1;
    const h = canvas.clientHeight || 1;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  const ro = new ResizeObserver(resize);
  ro.observe(canvas);
  resize();

  let raf = 0;
  let last = performance.now();
  const v = new THREE.Vector3();
  function frame(now: number) {
    raf = requestAnimationFrame(frame);
    if (!state.active) {
      last = now;
      return;
    }
    const dt = Math.min((now - last) / 1000, 0.1);
    last = now;
    if (!state.dragging) {
      state.yawVel += (AUTO - state.yawVel) * (1 - Math.exp(-dt / 1.2));
      state.yaw += state.yawVel * dt;
    }
    const ease1 = 1 - Math.exp(-dt / 0.25);
    state.dist += (distTarget - state.dist) * ease1;
    focusLocal.lerp(focusTarget, ease1);
    content.position.copy(focusLocal);
    if (Math.abs(exagTarget - exag) > 0.01) {
      exag += (exagTarget - exag) * (1 - Math.exp(-dt / 0.2));
      applyExaggeration();
    }
    const elapsed = now - layerStart;
    for (const p of prisms) {
      const t = opts.reducedMotion ? 1 : ease((elapsed - p.delay) / 700);
      p.mesh.scale.y = Math.max(0.001, t);
    }
    pivot.rotation.set(state.pitch, state.yaw, 0, "XYZ");
    const aspect = camera.aspect;
    camera.position.set(0, 0, state.dist * Math.max(1, 1.0 / aspect));
    camera.lookAt(0, 0, 0);
    pivot.updateMatrixWorld(true);
    const pins: PinScreen[] = pinAnchors.map((a) => {
      const prism = prisms.find((p) => p.code === a.code);
      v.copy(a.local);
      if (prism) v.y = prism.topY * prism.mesh.scale.y + 0.08;
      content.localToWorld(v);
      v.project(camera);
      return {
        code: a.code,
        x: (v.x * 0.5 + 0.5) * canvas.clientWidth,
        y: (-v.y * 0.5 + 0.5) * canvas.clientHeight,
        visible: v.z < 1,
      };
    });
    opts.onPins(pins);
    renderer.render(scene, camera);
  }
  raf = requestAnimationFrame(frame);

  return {
    setLayer,
    setActive: (a) => {
      state.active = a;
    },
    setAuto: (on) => {
      AUTO = opts.reducedMotion || !on ? 0 : 0.1;
    },
    rotate,
    zoom,
    dispose() {
      cancelAnimationFrame(raf);
      ro.disconnect();
      canvas.removeEventListener("pointerdown", onDown);
      canvas.removeEventListener("pointermove", onMove);
      canvas.removeEventListener("pointerup", onUp);
      canvas.removeEventListener("pointercancel", onUp);
      canvas.removeEventListener("wheel", onWheel);
      canvas.removeEventListener("keydown", onKey);
      clearLayer();
      topGeo.dispose();
      wallGeo.dispose();
      texture.dispose();
      renderer.dispose();
    },
  };
}
