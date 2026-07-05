/**
 * AI-EVER Phase 4 - GraphRenderer.js
 * Uses Cytoscape.js to render Trees, Linked Lists, and general Graphs.
 */
class GraphRenderer {
    constructor(container) {
        this.container = container;
        
        // Ensure container has a wrapper for cytoscape
        this.cyContainer = document.createElement("div");
        this.cyContainer.style.width = "100%";
        this.cyContainer.style.height = "400px";
        this.container.appendChild(this.cyContainer);

        this.cy = window.cytoscape({
            container: this.cyContainer,
            elements: [],
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': '#2196f3',
                        'label': 'data(label)',
                        'color': '#fff',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'font-size': '12px',
                        'width': '40px',
                        'height': '40px',
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 2,
                        'line-color': '#9dbaea',
                        'target-arrow-color': '#9dbaea',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'label': 'data(label)',
                        'font-size': '10px',
                        'color': '#fff',
                        'text-rotation': 'autorotate'
                    }
                }
            ],
            layout: {
                name: 'preset'
            },
            userZoomingEnabled: false,
            userPanningEnabled: false,
        });
        
        this.nodes = new Set();
        this.edges = new Set();
    }

    async handleEvent(event) {
        const { type, source, metadata } = event;
        
        if (type === "TreeNodeCreated" || type === "NodeCreated") {
            return this.addNode(source, metadata.value);
        }
        else if (type === "TreeNodeUpdated" || type === "NodeUpdated") {
            return this.updateNode(source, metadata);
        }
        else if (type === "TreePointerMoved" || type === "PointerMoved") {
            return this.updateEdge(source, metadata);
        }
    }

    async addNode(id, valueDict) {
        if (this.nodes.has(id)) return;
        
        // Find label
        const val = valueDict.val !== undefined ? valueDict.val : (valueDict.value !== undefined ? valueDict.value : id);
        
        this.cy.add({
            group: 'nodes',
            data: { id: String(id), label: String(val) },
            position: { x: 200 + Math.random()*50, y: 100 + Math.random()*50 }
        });
        this.nodes.add(id);
        
        this.applyLayout();
    }

    async updateNode(id, metadata) {
        if (!this.nodes.has(id)) return;
        const node = this.cy.getElementById(String(id));
        if (node) {
            node.data('label', String(metadata.current));
            
            // GSAP highlight animation on cytoscape node isn't straightforward without a plugin, 
            // but we can animate its style
            node.animate({
                style: { 'background-color': '#4caf50' }
            }, {
                duration: 300,
                complete: () => {
                    node.animate({ style: { 'background-color': '#2196f3' } }, { duration: 300 });
                }
            });
            // We await a timeout matching animation duration to sync GSAP-like timeline
            await new Promise(r => setTimeout(r, 600));
        }
    }

    async updateEdge(sourceId, metadata) {
        const ptrName = metadata.pointer;
        const targetId = metadata.current;
        
        // Remove old edge if exists
        const edgeId = `${sourceId}-${ptrName}`;
        const oldEdge = this.cy.getElementById(edgeId);
        if (oldEdge.length > 0) {
            this.cy.remove(oldEdge);
            this.edges.delete(edgeId);
        }
        
        if (targetId) {
            this.cy.add({
                group: 'edges',
                data: { id: edgeId, source: String(sourceId), target: String(targetId), label: ptrName }
            });
            this.edges.add(edgeId);
            this.applyLayout();
        }
    }

    applyLayout() {
        // Use breadthfirst layout for trees, dagre is better but breadthfirst is built-in
        const layout = this.cy.layout({
            name: 'breadthfirst',
            directed: true,
            padding: 10,
            spacingFactor: 1.2,
            animate: true,
            animationDuration: 400
        });
        layout.run();
    }
    
    reset() {
        this.cy.elements().remove();
        this.nodes.clear();
        this.edges.clear();
    }
}
window.AIEVERGraphRenderer = GraphRenderer;
