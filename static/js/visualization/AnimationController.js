/**
 * AI-EVER Phase 4 - AnimationController.js
 * Synchronizes execution steps with GSAP animations.
 */
class AnimationController {
    constructor(vizManager) {
        this.vizManager = vizManager;
        this.isAnimating = false;
    }

    async playStep(step) {
        // If there are no animation events for this step, just return immediately.
        const events = step.animation_events || [];
        if (events.length === 0) return;

        this.isAnimating = true;

        // Process all events in sequence (or parallel, depending on event logic)
        for (const event of events) {
            await this.vizManager.processEvent(event);
        }

        this.isAnimating = false;
    }
}
window.AIEVERAnimationController = AnimationController;
