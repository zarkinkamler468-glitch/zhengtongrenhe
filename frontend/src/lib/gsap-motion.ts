import gsap from "gsap";

export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function staggerReveal(
  container: HTMLElement | null,
  selector: string,
  options?: { y?: number; stagger?: number; duration?: number; delay?: number }
) {
  if (!container || prefersReducedMotion()) return;
  const targets = container.querySelectorAll<HTMLElement>(selector);
  if (!targets.length) return;

  const { y = 18, stagger = 0.07, duration = 0.45, delay = 0 } = options ?? {};
  gsap.from(targets, {
    opacity: 0,
    y,
    duration,
    stagger,
    delay,
    ease: "power2.out",
    clearProps: "transform",
  });
}

export function fadeUp(el: HTMLElement | null, options?: gsap.TweenVars) {
  if (!el || prefersReducedMotion()) return;
  gsap.from(el, {
    opacity: 0,
    y: 16,
    duration: 0.45,
    ease: "power2.out",
    clearProps: "transform",
    ...options,
  });
}

export function revealIn(el: HTMLElement | null, options?: gsap.TweenVars) {
  if (!el || prefersReducedMotion()) return;
  gsap.from(el, {
    opacity: 0,
    y: 12,
    duration: 0.35,
    ease: "power2.out",
    clearProps: "transform",
    ...options,
  });
}

export function animateModalIn(overlay: HTMLElement, panel: HTMLElement) {
  if (prefersReducedMotion()) return;
  gsap.fromTo(overlay, { opacity: 0 }, { opacity: 1, duration: 0.22, ease: "power1.out" });
  gsap.fromTo(
    panel,
    { opacity: 0, y: 28, scale: 0.97 },
    { opacity: 1, y: 0, scale: 1, duration: 0.38, ease: "power3.out", clearProps: "transform" }
  );
}

export function animateModalOut(
  overlay: HTMLElement,
  panel: HTMLElement,
  onComplete: () => void
): gsap.core.Timeline {
  if (prefersReducedMotion()) {
    onComplete();
    return gsap.timeline();
  }
  const tl = gsap.timeline({ onComplete });
  tl.to(panel, { opacity: 0, y: 16, scale: 0.98, duration: 0.22, ease: "power2.in" }).to(
    overlay,
    { opacity: 0, duration: 0.18, ease: "power1.in" },
    "-=0.1"
  );
  return tl;
}
