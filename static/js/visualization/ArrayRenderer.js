/**
 * AI-EVER Phase 4 - ArrayRenderer.js
 * Renders Array data structures with GSAP animations.
 */
class ArrayRenderer {
    constructor(container) {
        this.container = container;
        this.arrays = {}; // Track DOM elements for each array by variable name
    }

    async handleEvent(event) {
        const { type, source, metadata } = event;
        
        switch (type) {
            case "ArrayCreated":
                return this.createArray(source, metadata.value);
            case "ArrayUpdated":
                return this.updateArray(source, metadata.previous, metadata.current);
            case "ArrayDeleted":
                return this.deleteArray(source);
        }
    }

    async createArray(varName, valueList) {
        // Create container for this array
        const wrapper = document.createElement("div");
        wrapper.className = "array-wrapper";
        wrapper.id = `array-${varName}`;
        wrapper.style.display = "flex";
        wrapper.style.alignItems = "center";
        wrapper.style.margin = "10px";
        wrapper.style.padding = "10px";
        wrapper.style.border = "1px solid #444";
        wrapper.style.borderRadius = "8px";
        wrapper.style.backgroundColor = "#1e1e1e";

        // Label
        const label = document.createElement("div");
        label.textContent = `${varName} = `;
        label.style.marginRight = "10px";
        label.style.color = "#88aaff";
        label.style.fontWeight = "bold";
        wrapper.appendChild(label);

        // Elements
        const elementsContainer = document.createElement("div");
        elementsContainer.style.display = "flex";
        this.arrays[varName] = { wrapper, elementsContainer, elements: [] };

        for (let i = 0; i < valueList.length; i++) {
            const el = this.createArrayElement(valueList[i], i);
            elementsContainer.appendChild(el);
            this.arrays[varName].elements.push(el);
        }

        wrapper.appendChild(elementsContainer);
        this.container.appendChild(wrapper);

        // Animate entrance
        await GSAPAnimations.fadeIn(wrapper, 0.5);
    }

    createArrayElement(val, index) {
        const box = document.createElement("div");
        box.className = "array-element";
        box.style.width = "40px";
        box.style.height = "40px";
        box.style.display = "flex";
        box.style.alignItems = "center";
        box.style.justifyContent = "center";
        box.style.border = "2px solid #555";
        box.style.marginRight = "5px";
        box.style.backgroundColor = "#2d2d2d";
        box.style.color = "#fff";
        box.style.borderRadius = "4px";
        box.style.position = "relative";
        
        const text = document.createElement("span");
        text.textContent = val;
        box.appendChild(text);

        const idxLabel = document.createElement("span");
        idxLabel.textContent = index;
        idxLabel.style.position = "absolute";
        idxLabel.style.bottom = "-20px";
        idxLabel.style.fontSize = "10px";
        idxLabel.style.color = "#888";
        box.appendChild(idxLabel);

        return box;
    }

    async updateArray(varName, prevList, currList) {
        const arrayData = this.arrays[varName];
        if (!arrayData) return;

        const container = arrayData.elementsContainer;
        
        // Very basic naive diffing for Phase 1 MVP
        // If lengths match, check for value changes
        if (prevList.length === currList.length) {
            const promises = [];
            for (let i = 0; i < currList.length; i++) {
                if (prevList[i] !== currList[i]) {
                    const el = arrayData.elements[i];
                    el.firstChild.textContent = currList[i];
                    promises.push(GSAPAnimations.highlight(el, "#4caf50", 0.6));
                }
            }
            await Promise.all(promises);
        } else {
            // Re-render entirely if size changes (for now)
            container.innerHTML = "";
            arrayData.elements = [];
            for (let i = 0; i < currList.length; i++) {
                const el = this.createArrayElement(currList[i], i);
                container.appendChild(el);
                arrayData.elements.push(el);
            }
            await GSAPAnimations.highlight(container, "#ff9800", 0.4);
        }
    }

    async deleteArray(varName) {
        const arrayData = this.arrays[varName];
        if (!arrayData) return;
        
        await GSAPAnimations.fadeOut(arrayData.wrapper, 0.4);
        if (arrayData.wrapper.parentNode) {
            arrayData.wrapper.parentNode.removeChild(arrayData.wrapper);
        }
        delete this.arrays[varName];
    }
    
    reset() {
        this.arrays = {};
    }
}
window.AIEVERArrayRenderer = ArrayRenderer;
