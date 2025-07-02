// OffscreenCanvas worker – flow‑field motion + scroll push + glow/twinkle (fixed)
// -----------------------------------------------------------------------------
//  • Organic motion from a time‑evolving flow field.
//  • Scroll wheel nudges particles up/down (separate damped component).
//  • Particles fade in, trail, glow/twinkle, then fade out when off‑screen or
//    life expires. No wrapping.

// ===== Tunables ==============================================================
const POP_NORMAL = 80;

const ACCENT_BASE = 0.05; // 5% base chance for accent particles

const TRAIL_MAX = 30;
const TRAIL_FADE_FACTOR = 0.94;
const BASE_LIFE = 180;
const LIFE_VARIANCE = 120;
const FADE_FRAMES = 45;

// Flow field
const RESOLUTION = 20; // px per cell
const FLOW_SPEED = 2; // animation speed
const INTENSITY_BASE = 0.01; // steering force per frame
const COMPLEXITY = 1; // wobble amount

// Scroll physics
const SCROLL_SCALE = 0.003; // wheel px → vy impulse
const IMPULSE_DECAY = 0.9; // shared impulse decay
const DAMP_FACTOR = 0.92; // per‑particle damping of scrollVy
const MAX_SCROLL_VY = 5; // clamp scroll‑induced vy

// Performance optimizations
const SIN_LOOKUP_SIZE = 1024;
const sinLookup = new Float32Array(SIN_LOOKUP_SIZE);
const cosLookup = new Float32Array(SIN_LOOKUP_SIZE);

// Pre-calculate sin/cos lookup tables for faster trigonometry
for (let i = 0; i < SIN_LOOKUP_SIZE; i++) {
  const angle = (i / SIN_LOOKUP_SIZE) * Math.PI * 2;
  sinLookup[i] = Math.sin(angle);
  cosLookup[i] = Math.cos(angle);
}

// Fast sin/cos using lookup tables
function fastSin(angle: number): number {
  const normalized = ((angle % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2);
  const index = Math.floor((normalized / (Math.PI * 2)) * SIN_LOOKUP_SIZE) % SIN_LOOKUP_SIZE;
  return sinLookup[index];
}

function fastCos(angle: number): number {
  const normalized = ((angle % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2);
  const index = Math.floor((normalized / (Math.PI * 2)) * SIN_LOOKUP_SIZE) % SIN_LOOKUP_SIZE;
  return cosLookup[index];
}
// ============================================================================

let nexus: QuantumNexus | null = null;

self.onmessage = (e) => {
  if (e.data.canvas) {
    const { canvas, width, height, dpr } = e.data;
    const ctx = (canvas as OffscreenCanvas).getContext("2d");
    if (!ctx) return;
    (canvas as OffscreenCanvas).width = width;
    (canvas as OffscreenCanvas).height = height;
    ctx.scale(dpr, dpr);
    nexus = new QuantumNexus(ctx, width / dpr, height / dpr);
    return;
  }

  if (!nexus) return;

  switch (e.data.type) {
    case "scroll":
      nexus.addScrollImpulse(-e.data.dy * SCROLL_SCALE);
      break;
    case "explode":
      nexus.explode();
      break;
  }
};

// ───────────────── QuantumNexus ──────────────────────────────────────────────
class QuantumNexus {
  private ctx: OffscreenCanvasRenderingContext2D;
  private width: number;
  private height: number;
  private particles: QuantumParticle[] = [];
  private flowField: number[] = [];
  private time = 0;
  private impulse = 0;

  constructor(ctx: OffscreenCanvasRenderingContext2D, w: number, h: number) {
    this.ctx = ctx;
    this.width = w;
    this.height = h;
    this.initFlowField();
    this.spawn(POP_NORMAL);
    this.animate();
  }

  // public controls
  addScrollImpulse(dy: number) {
    this.impulse += dy;
  }

  private initFlowField() {
    const cols = Math.floor(this.width / RESOLUTION);
    const rows = Math.floor(this.height / RESOLUTION);
    this.flowField = new Array(cols * rows * 2).fill(0);
  }

  private updateFlowField() {
    const cols = Math.floor(this.width / RESOLUTION);
    const rows = Math.floor(this.height / RESOLUTION);
    let yoff = this.time * FLOW_SPEED * 0.001;
    for (let y = 0; y < rows; y++) {
      let xoff = this.time * FLOW_SPEED * 0.001;
      for (let x = 0; x < cols; x++) {
        const idx = (y * cols + x) * 2;
        const ang = fastSin(xoff) * fastCos(yoff) * Math.PI * 2;
        this.flowField[idx] = fastCos(ang);
        this.flowField[idx + 1] = fastSin(ang);
        xoff += 0.1;
      }
      yoff += 0.1;
    }
  }

  private spawn(n: number) {
    while (n--)
      this.particles.push(
        new QuantumParticle(this.width, this.height)
      );
  }

  // ── Explosion: radial impulse from center ───────────────────────────
  explode() {
    const cx = this.width / 2,
      cy = this.height / 2;
    this.particles.forEach((p) => {
      const dx = p["x"] - cx,
        dy = p["y"] - cy;
      const dist = Math.hypot(dx, dy) || 1;
      const impulse = 3 + Math.random();
      p["vx"] += (dx / dist) * impulse;
      p["vy"] += (dy / dist) * impulse;
    });
  }

  private animate = () => {
    this.ctx.clearRect(0, 0, this.width, this.height);
    this.time++;
    this.updateFlowField();

    // distribute impulse then decay
    if (this.impulse !== 0) {
      this.particles.forEach((p) => p.applyImpulse(this.impulse));
      this.impulse *= IMPULSE_DECAY;
      if (Math.abs(this.impulse) < 0.001) this.impulse = 0;
    }

    // update & draw
    this.particles = this.particles.filter((p) => {
      const alive = p.update(this.flowField);
      if (alive) p.draw(this.ctx);
      return alive;
    });
    
    // maintain desired population
    if (this.particles.length < POP_NORMAL && this.time % 2 === 0) {
      this.particles.push(new QuantumParticle(this.width, this.height));
    }
    
    self.requestAnimationFrame(this.animate);
  };
}

// ───────────────── QuantumParticle ───────────────────────────────────────────
class QuantumParticle {
  private maxX: number;
  private maxY: number;
  private x: number;
  private y: number;
  private vx: number;
  private vy: number;
  private scrollVy = 0;
  private size: number;
  private hue: number;
  private baseAlpha: number;
  private maxSize: number = 2;
  private minSize: number;
  private sizeNorm: number;
  private isAccent: boolean;
  private life = 0;
  private maxLife: number;
  private trail: { x: number; y: number; alpha: number }[] = [];
  private static accentHues = [185, 315, 35];
  private speedFactor: number;

  constructor(w: number, h: number) {
    this.maxX = w;
    this.maxY = h;
    this.x = Math.random() * w;
    this.y = Math.random() * h;
    this.vx = (Math.random() - 0.5) * 0.8;
    this.vy = (Math.random() - 0.5) * 0.8;

    // ── Accent roll (fixed 5% chance) ──
    this.isAccent = Math.random() < ACCENT_BASE;

    this.minSize = this.isAccent ? 2.5 : 1;
    this.size = Math.pow(Math.random(), 0.5) * this.maxSize + this.minSize;
    this.sizeNorm = (this.size - this.minSize) / this.maxSize;

    if (this.isAccent) {
      this.hue =
        QuantumParticle.accentHues[
          Math.floor(Math.random() * QuantumParticle.accentHues.length)
        ];
      this.maxLife = (BASE_LIFE + Math.random() * LIFE_VARIANCE) * 1.5; // longer life
    } else {
      this.hue = 180 + Math.random() * 80;
      this.maxLife = BASE_LIFE + Math.random() * LIFE_VARIANCE;
    }

    this.speedFactor =
      (0.8 + this.sizeNorm * 0.2) * (this.isAccent ? 2 : 1);

    const easedNorm = Math.pow(this.sizeNorm, 2.5);
    this.baseAlpha =
      (this.isAccent ? 0.5 : 0.05) + easedNorm * (this.isAccent ? 1 : 0.3);
  }

  applyImpulse(dVy: number) {
    this.scrollVy += dVy * this.sizeNorm;
    if (this.scrollVy > MAX_SCROLL_VY) this.scrollVy = MAX_SCROLL_VY;
    if (this.scrollVy < -MAX_SCROLL_VY) this.scrollVy = -MAX_SCROLL_VY;
  }

  update(field: number[]): boolean {
    this.life++;
    this.scrollVy *= DAMP_FACTOR * this.sizeNorm;

    // flow influence
    const cols = Math.floor(this.maxX / RESOLUTION);
    const fx = Math.floor(this.x / RESOLUTION);
    const fy = Math.floor(this.y / RESOLUTION);
    const idx = (fy * cols + fx) * 2;
    if (field[idx] !== undefined) {
      const fScale = INTENSITY_BASE * this.speedFactor;
      this.vx += field[idx] * fScale;
      this.vy += field[idx + 1] * fScale;
    }

    // wobble rotate
    const ang =
      Math.atan2(this.vy, this.vx) +
      fastSin(this.life * 0.05) * COMPLEXITY * 0.05;
    const spd = Math.hypot(this.vx, this.vy);
    this.vx = fastCos(ang) * spd;
    this.vy = fastSin(ang) * spd;

    // move
    this.x += this.vx;
    this.y += this.vy + this.scrollVy;

    // early fade if off‑screen
    if (this.life <= this.maxLife) {
      if (this.x < 0 || this.x > this.maxX || this.y < 0 || this.y > this.maxY)
        this.life = this.maxLife;
    }

    // trail
    this.trail.unshift({ x: this.x, y: this.y, alpha: 1 });
    this.trail.forEach((t) => (t.alpha *= TRAIL_FADE_FACTOR));
    const trailCap = this.isAccent ? TRAIL_MAX * 1.5 : TRAIL_MAX;
    if (this.trail.length > trailCap) this.trail.pop();

    return this.life < this.maxLife + FADE_FRAMES;
  }

  draw(ctx: OffscreenCanvasRenderingContext2D) {
    const phaseAlpha = this.alpha();
    if (phaseAlpha <= 0) return;
    const twinkleBase = this.isAccent ? 1 : 0.8;
    const twinkleAmp = this.isAccent ? 0.3 : 0.2;
    const twinkle =
      twinkleBase + twinkleAmp * fastSin(this.life * 0.1 + this.hue);
    const effAlpha = phaseAlpha * twinkle;

    const glowScale = this.isAccent ? 6 : 4;
    const glowR = this.size * glowScale;

    // glow & twinkle
    const grad = ctx.createRadialGradient(
      this.x,
      this.y,
      0,
      this.x,
      this.y,
      glowR
    );
    grad.addColorStop(0, `hsla(${this.hue},100%,70%,${effAlpha * 0.3})`);
    grad.addColorStop(1, `hsla(${this.hue},100%,70%,0)`);
    ctx.beginPath();
    ctx.fillStyle = grad;
    ctx.arc(this.x, this.y, glowR, 0, Math.PI * 2);
    ctx.fill();

    // Optimized trail rendering with gradient fading - batch similar alpha segments
    if (this.trail.length > 1) {
      ctx.lineWidth = this.size * (this.isAccent ? 1 : 0.6);
      
      let currentAlpha = -1;
      let batchStart = -1;
      
      // Use finer quantization for accent particles (more visible gradient steps)
      const quantizationSteps = this.isAccent ? 20 : 10; // 0.05 vs 0.1 increments
      
      for (let i = 0; i < this.trail.length - 1; i++) {
        const segA = Math.min(this.trail[i].alpha, this.trail[i + 1].alpha) * phaseAlpha;
        if (segA < 0.02) break; // Early exit for very faint segments
        
        // Quantize alpha to reduce stroke operations (finer for accent particles)
        const quantizedAlpha = Math.round(segA * quantizationSteps) / quantizationSteps;
        
        if (quantizedAlpha !== currentAlpha) {
          // Draw the previous batch if it exists
          if (batchStart >= 0) {
            ctx.strokeStyle = `hsla(${this.hue},100%,70%,${currentAlpha})`;
            ctx.stroke();
          }
          
          // Start new batch
          currentAlpha = quantizedAlpha;
          batchStart = i;
          ctx.beginPath();
          ctx.moveTo(this.trail[i].x, this.trail[i].y);
        }
        
        ctx.lineTo(this.trail[i + 1].x, this.trail[i + 1].y);
      }
      
      // Draw the final batch
      if (batchStart >= 0 && currentAlpha > 0) {
        ctx.strokeStyle = `hsla(${this.hue},100%,70%,${currentAlpha})`;
        ctx.stroke();
      }
    }

    // core
    ctx.beginPath();
    ctx.fillStyle = `hsla(${this.hue},100%,70%,${effAlpha})`;
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fill();
  }

  private alpha(): number {
    if (this.life < FADE_FRAMES)
      return (this.life / FADE_FRAMES) * this.baseAlpha;
    if (this.life <= this.maxLife) return this.baseAlpha;
    const t = 1 - Math.min((this.life - this.maxLife) / FADE_FRAMES, 1);
    return t * this.baseAlpha;
  }
}
