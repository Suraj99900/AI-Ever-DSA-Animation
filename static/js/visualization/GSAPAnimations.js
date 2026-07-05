/**
 * AI-EVER Phase 4 - GSAPAnimations.js
 * Library of reusable GSAP animation effects.
 */
class GSAPAnimations {
    static fadeIn(element, duration = 0.5) {
        return gsap.fromTo(element, 
            { opacity: 0, scale: 0.8 }, 
            { opacity: 1, scale: 1, duration: duration, ease: "back.out(1.7)" }
        );
    }

    static fadeOut(element, duration = 0.5) {
        return gsap.to(element, { opacity: 0, scale: 0.8, duration: duration });
    }

    static move(element, x, y, duration = 0.5) {
        return gsap.to(element, { x: x, y: y, duration: duration, ease: "power2.inOut" });
    }

    static highlight(element, color = "#ffeb3b", duration = 0.5) {
        const tl = gsap.timeline();
        tl.to(element, { backgroundColor: color, duration: duration / 2 })
          .to(element, { backgroundColor: "", duration: duration / 2 });
        return tl;
    }
}
window.GSAPAnimations = GSAPAnimations;
