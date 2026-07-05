/**
 * AI-EVER Phase 4 - VisualizationManager.js
 * Manages active renderers and delegates events to them.
 */
class VisualizationManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.warn(`[VisualizationManager] Container ${containerId} not found.`);
        }
        this.renderers = {}; // e.g. "ArrayVisualizer" -> ArrayRenderer instance
    }

    registerRenderer(eventSourceType, renderer) {
        this.renderers[eventSourceType] = renderer;
    }

    async processEvent(event) {
        // Find a renderer that handles this type of event (e.g. "ArrayCreated")
        // We do basic string matching for Phase 1
        let renderer = null;
        if (event.type.startsWith("Array")) {
            renderer = this.renderers["ArrayVisualizer"];
        }
        else if (event.type.startsWith("Tree") || event.type.startsWith("Node") || event.type.startsWith("Pointer")) {
            renderer = this.renderers["GraphVisualizer"];
        }

        if (renderer && renderer.handleEvent) {
            await renderer.handleEvent(event);
        } else {
            console.log(`[VisualizationManager] Unhandled event: ${event.type}`);
        }
    }
    
    reset() {
        this.container.innerHTML = "";
        Object.values(this.renderers).forEach(r => {
            if (r.reset) r.reset();
        });
    }
}
window.AIEVERVisualizationManager = VisualizationManager;
