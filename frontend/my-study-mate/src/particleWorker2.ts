// OffscreenCanvas worker – flow‑field motion + scroll push + glow/twinkle (fixed)
// -----------------------------------------------------------------------------
//  • Organic motion from a time‑evolving flow field.
//  • Scroll wheel nudges particles up/down (separate damped component).
//  • Particles fade in, trail, glow/twinkle, then fade out when off‑screen or
//    life expires. No wrapping.

// ===== Tunables ==============================================================
const POP_NORMAL = 120; // Increased from 80 for richer particle field

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

    // update & draw with illumination effects
    this.particles = this.particles.filter((p) => {
      const alive = p.update(this.flowField);
      if (alive) {
        // Calculate illumination for non-accent particles
        if (!p.isAccentParticle) {
          p.calculateIllumination(this.particles.filter(accent => accent.isAccentParticle));
        }
        p.draw(this.ctx);
      }
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
  private maxSize: number = 6; // Reduced from 8 for more balanced foreground particles
  private minSize: number;
  private sizeNorm: number;
  private isAccent: boolean;
  private life = 0;
  private maxLife: number;
  private trail: { x: number; y: number; alpha: number }[] = [];
  private static accentHues = [185, 315, 35];
  private speedFactor: number;
  
  // Illumination properties
  private illuminationAlpha = 0;
  private illuminationHue = 0;

  constructor(w: number, h: number) {
    this.maxX = w;
    this.maxY = h;
    this.x = Math.random() * w;
    this.y = Math.random() * h;
    this.vx = (Math.random() - 0.5) * 0.8;
    this.vy = (Math.random() - 0.5) * 0.8;

    // ── Accent roll (fixed 5% chance) ──
    this.isAccent = Math.random() < ACCENT_BASE;

    // Create three depth tiers for better depth perception
    if (this.isAccent) {
      // Foreground particles: large, prominent
      this.minSize = 3;
      this.size = Math.pow(Math.random(), 0.3) * (this.maxSize - this.minSize) + this.minSize; // 3-6px
    } else {
      // Background and mid-ground particles
      const isBackground = Math.random() < 0.3; // 30% chance for background particles
      if (isBackground) {
        // Background particles: tiny, distant
        this.minSize = 0.5;
        this.size = Math.pow(Math.random(), 0.8) * 0.5 + this.minSize; // 0.5-1px
      } else {
        // Mid-ground particles: normal depth
        this.minSize = 1.5;
        this.size = Math.pow(Math.random(), 0.5) * 2.5 + this.minSize; // 1.5-4px
      }
    }
    
    this.sizeNorm = (this.size - 0.5) / (this.maxSize - 0.5); // Normalize across full range

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
    // Adjust alpha based on particle tier for better depth perception
    if (this.isAccent) {
      // Foreground: bright and prominent
      this.baseAlpha = 0.5 + easedNorm * 1;
    } else if (this.size < 1.2) {
      // Background: subtle but more visible than before
      this.baseAlpha = 0.03 + easedNorm * 0.15; // Reverted to original range
    } else {
      // Mid-ground: moderate visibility, more prominent
      this.baseAlpha = 0.08 + easedNorm * 0.4; // Reverted to original range
    }
  }

  // Public getters for nexus access
  get isAccentParticle(): boolean { return this.isAccent; }
  get position(): { x: number; y: number } { return { x: this.x, y: this.y }; }
  get particleHue(): number { return this.hue; }
  get particleSize(): number { return this.size; }

  applyImpulse(dVy: number) {
    // Apply different scroll sensitivity based on particle type
    let scrollMultiplier = 1;
    if (!this.isAccent) {
      // Non-accent particles get more scroll push for better interaction
      scrollMultiplier = 1.5; // 50% more sensitive to scroll
    }
    
    this.scrollVy += dVy * this.sizeNorm * scrollMultiplier;
    if (this.scrollVy > MAX_SCROLL_VY) this.scrollVy = MAX_SCROLL_VY;
    if (this.scrollVy < -MAX_SCROLL_VY) this.scrollVy = -MAX_SCROLL_VY;
  }

  // Calculate illumination effects from nearby accent particles
  calculateIllumination(accentParticles: QuantumParticle[]) {
    this.illuminationAlpha = 0;
    this.illuminationHue = this.hue; // Default to original hue
    
    const maxIlluminationDistance = 80; // pixels
    let totalIllumination = 0;
    let weightedHue = 0;
    let totalWeight = 0;
    
    for (const accent of accentParticles) {
      const dx = accent.position.x - this.x;
      const dy = accent.position.y - this.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance < maxIlluminationDistance) {
        // Falloff: closer = stronger illumination
        const falloff = 1 - (distance / maxIlluminationDistance);
        const illuminationStrength = falloff * falloff; // Quadratic falloff
        
        // Factor in the accent particle's size (larger = more illumination)
        const sizeFactor = accent.particleSize / 6; // Normalize by max accent size
        
        // Factor in the receiving particle's size (larger particles catch more light)
        const receiverSizeFactor = 0.5 + (this.sizeNorm * 0.5); // Range: 0.5x to 1.0x light reception
        
        const finalIllumination = illuminationStrength * sizeFactor * receiverSizeFactor * 0.7;
        
        totalIllumination += finalIllumination;
        
        // Blend colors based on illumination strength
        const weight = finalIllumination;
        weightedHue += accent.particleHue * weight;
        totalWeight += weight;
      }
    }
    
    // Apply receiver size factor to overall illumination caps too
    const receiverBonus = 0.5 + (this.sizeNorm * 0.5);
    this.illuminationAlpha = Math.min(totalIllumination, 0.8 * receiverBonus); // Closer particles can get brighter
    
    if (totalWeight > 0) {
      // Closer particles also get more color blending
      const blendFactor = Math.min(totalIllumination * 2, 0.8 * receiverBonus);
      this.illuminationHue = this.hue * (1 - blendFactor) + (weightedHue / totalWeight) * blendFactor;
    }
  }

  update(field: number[]): boolean {
    this.life++;
    this.scrollVy *= DAMP_FACTOR * this.sizeNorm;

    // flow influence with perspective-based movement speed
    const cols = Math.floor(this.maxX / RESOLUTION);
    const fx = Math.floor(this.x / RESOLUTION);
    const fy = Math.floor(this.y / RESOLUTION);
    const idx = (fy * cols + fx) * 2;
    if (field[idx] !== undefined) {
      // Perspective effect: larger particles (closer) move faster through flow field
      const perspectiveScale = 0.2 + (this.sizeNorm * 0.6); // Changed from 0.3 + 0.7, now 0.2x to 0.8x speed
      const fScale = INTENSITY_BASE * this.speedFactor * perspectiveScale;
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

    // move with perspective-based speed
    const perspectiveMovement = 0.2 + (this.sizeNorm * 0.6); // Reduced from 0.3 + 0.7 for slower non-accent movement
    this.x += this.vx * perspectiveMovement;
    this.y += (this.vy * perspectiveMovement) + this.scrollVy;

    // early fade if off‑screen
    if (this.life <= this.maxLife) {
      if (this.x < 0 || this.x > this.maxX || this.y < 0 || this.y > this.maxY)
        this.life = this.maxLife;
    }

    // trail (only for accent particles)
    if (this.isAccent) {
      this.trail.unshift({ x: this.x, y: this.y, alpha: 1 });
      this.trail.forEach((t) => (t.alpha *= TRAIL_FADE_FACTOR));
      const trailCap = TRAIL_MAX * 1.5;
      if (this.trail.length > trailCap) this.trail.pop();
    }

    return this.life < this.maxLife + FADE_FRAMES;
  }

  draw(ctx: OffscreenCanvasRenderingContext2D) {
    const phaseAlpha = this.alpha();
    if (phaseAlpha <= 0) return;
    
    let effAlpha: number;
    
    if (this.isAccent) {
      // Accent particles keep their twinkling
      const twinkleBase = 1;
      const twinkleAmp = 0.3;
      const twinkle = twinkleBase + twinkleAmp * fastSin(this.life * 0.1 + this.hue);
      effAlpha = phaseAlpha * twinkle;
    } else {
      // Non-accent particles have steady brightness (no twinkling)
      effAlpha = phaseAlpha;
    }

    // Only accent particles get glow effects
    if (this.isAccent) {
      const glowScale = 6;
      const glowR = this.size * glowScale;

      // glow & twinkle (reduced intensity for accent particles)
      const grad = ctx.createRadialGradient(
        this.x,
        this.y,
        0,
        this.x,
        this.y,
        glowR
      );
      grad.addColorStop(0, `hsla(${this.hue},100%,70%,${effAlpha * 0.15})`); // Reduced from 0.3
      grad.addColorStop(1, `hsla(${this.hue},100%,70%,0)`);
      ctx.beginPath();
      ctx.fillStyle = grad;
      ctx.arc(this.x, this.y, glowR, 0, Math.PI * 2);
      ctx.fill();
    }

    // Only accent particles get trail rendering (COMMENTED OUT FOR TESTING)
    /*
    if (this.isAccent && this.trail.length > 1) {
      ctx.lineWidth = this.size;
      
      let currentAlpha = -1;
      let batchStart = -1;
      
      // Use finer quantization for accent particles
      const quantizationSteps = 20; // 0.05 increments
      
      for (let i = 0; i < this.trail.length - 1; i++) {
        const segA = Math.min(this.trail[i].alpha, this.trail[i + 1].alpha) * phaseAlpha;
        if (segA < 0.02) break; // Early exit for very faint segments
        
        // Quantize alpha to reduce stroke operations
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
    */

    // core particle (all particles get this)
    ctx.beginPath();
    if (this.isAccent) {
      // Accent particles use their original color and alpha
      ctx.fillStyle = `hsla(${this.hue},100%,70%,${effAlpha})`;
    } else {
      // Non-accent particles use illumination effects, but fade them with particle death
      const illuminationFade = phaseAlpha / this.baseAlpha; // Ratio of current to max alpha
      const fadedIlluminationAlpha = this.illuminationAlpha * illuminationFade;
      const finalAlpha = effAlpha + fadedIlluminationAlpha;
      const saturation = fadedIlluminationAlpha > 0.02 ? 100 : 60; // More saturated when illuminated
      ctx.fillStyle = `hsla(${this.illuminationHue},${saturation}%,70%,${finalAlpha})`;
    }
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
