import { app } from "../../../scripts/app.js";

/**
 * APZmedia Audio Equalizer - Visual EQ Editor Widget
 * DaVinci Resolve style parametric EQ with draggable control points
 */

class EQEditorWidget {
    constructor(node, inputName, inputData) {
        this.node = node;
        this.name = inputName;
        this.value = inputData[1]?.default || "[]";

        // Canvas dimensions
        this.width = 320;
        this.height = 200;

        // Create container
        this.container = document.createElement("div");
        this.container.style.width = `${this.width}px`;
        this.container.style.height = `${this.height}px`;
        this.container.style.background = "#1a1a1a";
        this.container.style.borderRadius = "4px";
        this.container.style.position = "relative";
        this.container.style.overflow = "hidden";

        // Create canvas
        this.canvas = document.createElement("canvas");
        this.canvas.width = this.width;
        this.canvas.height = this.height;
        this.canvas.style.cursor = "crosshair";
        this.container.appendChild(this.canvas);

        this.ctx = this.canvas.getContext("2d");

        // EQ bands state (default to 3 bands like Resolve)
        this.bands = [
            { freq: 100, gain: 0, q: 0.71, type: "low_shelf", enabled: true },
            { freq: 1000, gain: 0, q: 1.0, type: "peak", enabled: true },
            { freq: 10000, gain: 0, q: 0.71, type: "high_shelf", enabled: true }
        ];

        this.selectedBand = null;
        this.dragging = false;
        this.dragStartY = 0;
        this.dragStartQ = 0;

        // Colors for each band (Resolve style)
        this.bandColors = [
            "#ff6b6b", // Red - Low
            "#4ecdc4", // Teal - Mid
            "#45b7d1", // Blue - High
            "#96ceb4", // Green
            "#ffeaa7", // Yellow
            "#dfe6e9", // Gray
        ];

        // Parse initial value
        this.parseBands(this.value);

        // Event listeners
        this.canvas.addEventListener("mousedown", this.onMouseDown.bind(this));
        this.canvas.addEventListener("mousemove", this.onMouseMove.bind(this));
        this.canvas.addEventListener("mouseup", this.onMouseUp.bind(this));
        this.canvas.addEventListener("mouseleave", this.onMouseUp.bind(this));
        this.canvas.addEventListener("wheel", this.onWheel.bind(this));
        this.canvas.addEventListener("dblclick", this.onDoubleClick.bind(this));

        // Context menu for band options
        this.canvas.addEventListener("contextmenu", this.onContextMenu.bind(this));

        // Sync with widget values
        this.syncWithWidgets();

        // Initial draw
        this.draw();
    }

    syncWithWidgets() {
        // Store references to sync widgets
        this.syncWidgets = {
            selected_band: null,
            band_frequency: null,
            band_gain: null,
            band_q: null,
            band_type: null,
        };

        // Find the sync widgets after a short delay (widgets are created after node)
        setTimeout(() => {
            if (this.node && this.node.widgets) {
                this.node.widgets.forEach(widget => {
                    if (widget.name === "selected_band") {
                        this.syncWidgets.selected_band = widget;
                    } else if (widget.name === "band_frequency") {
                        this.syncWidgets.band_frequency = widget;
                    } else if (widget.name === "band_gain") {
                        this.syncWidgets.band_gain = widget;
                    } else if (widget.name === "band_q") {
                        this.syncWidgets.band_q = widget;
                    } else if (widget.name === "band_type") {
                        this.syncWidgets.band_type = widget;
                    }
                });

                // Hook into widget value changes
                Object.keys(this.syncWidgets).forEach(key => {
                    const widget = this.syncWidgets[key];
                    if (widget) {
                        const originalCallback = widget.callback;
                        widget.callback = (value) => {
                            this.updateFromWidget(key, value);
                            if (originalCallback) originalCallback(value);
                        };
                    }
                });

                // Initialize widget values from first band
                this.updateWidgetsFromBand(0);
            }
        }, 100);
    }

    updateFromWidget(widgetName, value) {
        if (this.selectedBand === null) return;

        const band = this.bands[this.selectedBand];
        if (!band) return;

        switch (widgetName) {
            case "selected_band":
                this.selectedBand = Math.max(0, Math.min(this.bands.length - 1, Math.round(value)));
                this.updateWidgetsFromBand(this.selectedBand);
                break;
            case "band_frequency":
                band.freq = Math.max(20, Math.min(20000, value));
                break;
            case "band_gain":
                band.gain = Math.max(-24, Math.min(24, value));
                break;
            case "band_q":
                band.q = Math.max(0.1, Math.min(10, value));
                break;
            case "band_type":
                band.type = value;
                break;
        }

        this.draw();
        this.node.onWidgetChanged?.(this.name, this.serializeBands());
    }

    updateWidgetsFromBand(bandIndex) {
        if (bandIndex < 0 || bandIndex >= this.bands.length) return;

        const band = this.bands[bandIndex];
        if (!band) return;

        if (this.syncWidgets.selected_band) {
            this.syncWidgets.selected_band.value = bandIndex;
        }
        if (this.syncWidgets.band_frequency) {
            this.syncWidgets.band_frequency.value = band.freq;
        }
        if (this.syncWidgets.band_gain) {
            this.syncWidgets.band_gain.value = band.gain;
        }
        if (this.syncWidgets.band_q) {
            this.syncWidgets.band_q.value = band.q;
        }
        if (this.syncWidgets.band_type) {
            this.syncWidgets.band_type.value = band.type;
        }

        // Mark widgets as dirty to trigger UI update
        if (this.node) {
            this.node.setDirtyCanvas(true, false);
        }
    }

    parseBands(jsonStr) {
        try {
            const parsed = JSON.parse(jsonStr);
            if (Array.isArray(parsed) && parsed.length > 0) {
                this.bands = parsed.map(band => ({
                    freq: Math.max(20, Math.min(20000, band.freq || 1000)),
                    gain: Math.max(-24, Math.min(24, band.gain || 0)),
                    q: Math.max(0.1, Math.min(10, band.q || 1.0)),
                    type: ["peak", "low_shelf", "high_shelf", "low_pass", "high_pass"].includes(band.type) ? band.type : "peak",
                    enabled: band.enabled !== false
                }));
            }
        } catch (e) {
            console.log("[APZmedia EQ] Using default bands");
        }
    }

    serializeBands() {
        return JSON.stringify(this.bands);
    }

    // Convert frequency (20-20000 Hz) to x position
    freqToX(freq) {
        const logFreq = Math.log10(Math.max(20, Math.min(20000, freq)));
        const logMin = Math.log10(20);
        const logMax = Math.log10(20000);
        return ((logFreq - logMin) / (logMax - logMin)) * this.width;
    }

    // Convert x position to frequency
    xToFreq(x) {
        const logMin = Math.log10(20);
        const logMax = Math.log10(20000);
        const logFreq = logMin + (x / this.width) * (logMax - logMin);
        return Math.pow(10, logFreq);
    }

    // Convert gain (-24 to +24 dB) to y position
    gainToY(gain) {
        return (this.height / 2) - (gain / 24) * (this.height / 2 - 10);
    }

    // Convert y position to gain
    yToGain(y) {
        return ((this.height / 2 - y) / (this.height / 2 - 10)) * 24;
    }

    // Calculate biquad frequency response for a single band
    calculateBandResponse(freq, band, sampleRate = 48000) {
        const f = freq;
        const fc = band.freq;
        const gain = band.gain;
        const Q = band.q;
        const A = Math.pow(10, gain / 40);

        const w0 = 2 * Math.PI * fc / sampleRate;
        const cosw0 = Math.cos(w0);
        const sinw0 = Math.sin(w0);
        const alpha = sinw0 / (2 * Q);

        let b0, b1, b2, a0, a1, a2;

        switch (band.type) {
            case "peak":
                b0 = 1 + alpha * A;
                b1 = -2 * cosw0;
                b2 = 1 - alpha * A;
                a0 = 1 + alpha / A;
                a1 = -2 * cosw0;
                a2 = 1 - alpha / A;
                break;
            case "low_shelf":
                const sqrtA = Math.sqrt(A);
                b0 = A * ((A + 1) - (A - 1) * cosw0 + 2 * sqrtA * alpha);
                b1 = 2 * A * ((A - 1) - (A + 1) * cosw0);
                b2 = A * ((A + 1) - (A - 1) * cosw0 - 2 * sqrtA * alpha);
                a0 = (A + 1) + (A - 1) * cosw0 + 2 * sqrtA * alpha;
                a1 = -2 * ((A - 1) + (A + 1) * cosw0);
                a2 = (A + 1) + (A - 1) * cosw0 - 2 * sqrtA * alpha;
                break;
            case "high_shelf":
                const sqrtA2 = Math.sqrt(A);
                b0 = A * ((A + 1) + (A - 1) * cosw0 + 2 * sqrtA2 * alpha);
                b1 = -2 * A * ((A - 1) + (A + 1) * cosw0);
                b2 = A * ((A + 1) + (A - 1) * cosw0 - 2 * sqrtA2 * alpha);
                a0 = (A + 1) - (A - 1) * cosw0 + 2 * sqrtA2 * alpha;
                a1 = 2 * ((A - 1) - (A + 1) * cosw0);
                a2 = (A + 1) - (A - 1) * cosw0 - 2 * sqrtA2 * alpha;
                break;
            case "low_pass":
                b0 = (1 - cosw0) / 2;
                b1 = 1 - cosw0;
                b2 = (1 - cosw0) / 2;
                a0 = 1 + alpha;
                a1 = -2 * cosw0;
                a2 = 1 - alpha;
                break;
            case "high_pass":
                b0 = (1 + cosw0) / 2;
                b1 = -(1 + cosw0);
                b2 = (1 + cosw0) / 2;
                a0 = 1 + alpha;
                a1 = -2 * cosw0;
                a2 = 1 - alpha;
                break;
            default:
                return 0;
        }

        // Normalize
        b0 /= a0; b1 /= a0; b2 /= a0;
        a1 /= a0; a2 /= a0;

        // Calculate response at frequency f
        const w = 2 * Math.PI * f / sampleRate;
        const cw = Math.cos(w);
        const sw = Math.sin(w);

        const numReal = b0 + b1 * cw + b2 * (2 * cw * cw - 1);
        const numImag = b1 * sw + b2 * 2 * cw * sw;
        const denReal = 1 + a1 * cw + a2 * (2 * cw * cw - 1);
        const denImag = a1 * sw + a2 * 2 * cw * sw;

        const numMag = Math.sqrt(numReal * numReal + numImag * numImag);
        const denMag = Math.sqrt(denReal * denReal + denImag * denImag);

        return 20 * Math.log10(numMag / denMag + 1e-15);
    }

    // Calculate total frequency response
    calculateTotalResponse(freq) {
        let totalGain = 0;
        for (const band of this.bands) {
            if (band.enabled) {
                totalGain += this.calculateBandResponse(freq, band);
            }
        }
        return totalGain;
    }

    draw() {
        const ctx = this.ctx;
        const w = this.width;
        const h = this.height;
        const padding = { top: 10, right: 10, bottom: 20, left: 30 };
        const graphW = w - padding.left - padding.right;
        const graphH = h - padding.top - padding.bottom;
        const cy = padding.top + graphH / 2;

        // Clear background
        ctx.fillStyle = "#1a1a1a";
        ctx.fillRect(0, 0, w, h);

        // Draw grid
        ctx.strokeStyle = "#333";
        ctx.lineWidth = 1;

        // Vertical grid lines (frequency octaves: 31, 63, 125, 250, 500, 1k, 2k, 4k, 8k, 16k)
        const freqs = [31, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000];
        for (const f of freqs) {
            const x = padding.left + (this.freqToX(f) / this.width) * graphW;
            ctx.beginPath();
            ctx.moveTo(x, padding.top);
            ctx.lineTo(x, h - padding.bottom);
            ctx.stroke();

            // Frequency labels
            ctx.fillStyle = "#666";
            ctx.font = "9px sans-serif";
            ctx.textAlign = "center";
            const label = f >= 1000 ? `${f/1000}k` : `${f}`;
            ctx.fillText(label, x, h - 5);
        }

        // Horizontal grid lines (dB)
        ctx.textAlign = "right";
        ctx.fillStyle = "#666";
        for (let db = -18; db <= 18; db += 6) {
            const y = cy - (db / 24) * (graphH / 2);
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(w - padding.right, y);
            ctx.stroke();

            // dB labels
            ctx.fillText(`${db}dB`, padding.left - 3, y + 3);
        }

        // Draw 0dB line (center) more prominently
        ctx.strokeStyle = "#555";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(padding.left, cy);
        ctx.lineTo(w - padding.right, cy);
        ctx.stroke();

        // Draw individual band curves (faint)
        for (let i = 0; i < this.bands.length; i++) {
            const band = this.bands[i];
            if (!band.enabled) continue;

            ctx.strokeStyle = this.bandColors[i % this.bandColors.length] + "40"; // 25% opacity
            ctx.lineWidth = 1;
            ctx.beginPath();

            for (let x = 0; x < graphW; x += 2) {
                const freq = this.xToFreq((x / graphW) * this.width);
                const gain = this.calculateBandResponse(freq, band);
                const y = cy - (gain / 24) * (graphH / 2);

                if (x === 0) {
                    ctx.moveTo(padding.left + x, y);
                } else {
                    ctx.lineTo(padding.left + x, y);
                }
            }
            ctx.stroke();
        }

        // Draw total frequency response curve
        ctx.strokeStyle = "#4ecca3";
        ctx.lineWidth = 2.5;
        ctx.beginPath();

        for (let x = 0; x < graphW; x += 2) {
            const freq = this.xToFreq((x / graphW) * this.width);
            const gain = this.calculateTotalResponse(freq);
            const y = cy - (gain / 24) * (graphH / 2);

            if (x === 0) {
                ctx.moveTo(padding.left + x, Math.max(padding.top, Math.min(h - padding.bottom, y)));
            } else {
                ctx.lineTo(padding.left + x, Math.max(padding.top, Math.min(h - padding.bottom, y)));
            }
        }
        ctx.stroke();

        // Draw control points
        for (let i = 0; i < this.bands.length; i++) {
            const band = this.bands[i];
            const x = padding.left + (this.freqToX(band.freq) / this.width) * graphW;
            const y = cy - (band.gain / 24) * (graphH / 2);

            // Clip to graph area
            const cx = Math.max(padding.left, Math.min(w - padding.right, x));
            const cy_pos = Math.max(padding.top, Math.min(h - padding.bottom, y));

            const isSelected = i === this.selectedBand;
            const color = this.bandColors[i % this.bandColors.length];

            // Draw Q indicator (circle radius represents Q)
            if (isSelected && band.type === "peak") {
                ctx.strokeStyle = color + "60";
                ctx.lineWidth = 1;
                ctx.beginPath();
                const qRadius = 10 + band.q * 5;
                ctx.arc(cx, cy_pos, qRadius, 0, Math.PI * 2);
                ctx.stroke();
            }

            // Draw control point
            ctx.fillStyle = band.enabled ? color : "#555";
            ctx.beginPath();
            ctx.arc(cx, cy_pos, isSelected ? 7 : 5, 0, Math.PI * 2);
            ctx.fill();

            // Draw highlight
            ctx.fillStyle = "rgba(255,255,255,0.3)";
            ctx.beginPath();
            ctx.arc(cx - 2, cy_pos - 2, isSelected ? 3 : 2, 0, Math.PI * 2);
            ctx.fill();

            // Draw shadow
            ctx.fillStyle = "rgba(0,0,0,0.3)";
            ctx.beginPath();
            ctx.arc(cx + 1, cy_pos + 1, isSelected ? 7 : 5, 0, Math.PI * 2);
            ctx.fill();
        }

        // Draw info text for selected band
        if (this.selectedBand !== null) {
            const band = this.bands[this.selectedBand];
            ctx.fillStyle = "#fff";
            ctx.font = "10px sans-serif";
            ctx.textAlign = "left";
            const freqLabel = band.freq >= 1000 ?
                `${(band.freq/1000).toFixed(1)}kHz` :
                `${Math.round(band.freq)}Hz`;
            ctx.fillText(
                `${freqLabel} | ${band.gain > 0 ? '+' : ''}${band.gain.toFixed(1)}dB | Q:${band.q.toFixed(2)}`,
                padding.left + 5, padding.top + 12
            );
        }
    }

    onMouseDown(e) {
        e.preventDefault();
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const padding = { top: 10, right: 10, bottom: 20, left: 30 };
        const graphW = this.width - padding.left - padding.right;
        const graphH = this.height - padding.top - padding.bottom;
        const cy = padding.top + graphH / 2;

        // Find closest band
        let closestDist = Infinity;
        let closestBand = -1;

        for (let i = 0; i < this.bands.length; i++) {
            const band = this.bands[i];
            const bx = padding.left + (this.freqToX(band.freq) / this.width) * graphW;
            const by = cy - (band.gain / 24) * (graphH / 2);
            const dist = Math.sqrt((x - bx) ** 2 + (y - by) ** 2);

            if (dist < closestDist && dist < 20) {
                closestDist = dist;
                closestBand = i;
            }
        }

        if (closestBand >= 0) {
            this.selectedBand = closestBand;
            this.dragging = true;
            this.dragStartY = y;
            this.dragStartQ = this.bands[closestBand].q;
            this.draw();

            // Update widgets to reflect selected band
            this.updateWidgetsFromBand(this.selectedBand);

            // Notify node of value change
            this.node.onWidgetChanged?.(this.name, this.serializeBands());
        } else {
            this.selectedBand = null;
            this.draw();
        }
    }

    onMouseMove(e) {
        if (!this.dragging || this.selectedBand === null) return;

        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const padding = { top: 10, right: 10, bottom: 20, left: 30 };
        const graphW = this.width - padding.left - padding.right;
        const graphH = this.height - padding.top - padding.bottom;
        const cy = padding.top + graphH / 2;

        // Update band parameters
        const band = this.bands[this.selectedBand];

        // Frequency from x position
        const relX = (x - padding.left) / graphW;
        band.freq = Math.max(20, Math.min(20000, this.xToFreq(relX * this.width)));

        // Gain from y position
        const relY = (cy - y) / (graphH / 2);
        band.gain = Math.max(-24, Math.min(24, relY * 24));

        this.draw();

        // Notify node of value change
        this.node.onWidgetChanged?.(this.name, this.serializeBands());
    }

    onMouseUp() {
        this.dragging = false;
    }

    onWheel(e) {
        if (this.selectedBand === null) return;
        e.preventDefault();

        const band = this.bands[this.selectedBand];
        const delta = e.deltaY > 0 ? -0.1 : 0.1;

        if (band.type === "peak") {
            band.q = Math.max(0.1, Math.min(10, band.q + delta));
        }

        this.draw();
        this.node.onWidgetChanged?.(this.name, this.serializeBands());
    }

    onDoubleClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const padding = { top: 10, right: 10, bottom: 20, left: 30 };
        const graphW = this.width - padding.left - padding.right;

        // Add new band at click position
        const relX = (x - padding.left) / graphW;
        const newFreq = this.xToFreq(Math.max(0, Math.min(1, relX)) * this.width);

        if (this.bands.length < 6) {
            this.bands.push({
                freq: Math.round(newFreq),
                gain: 0,
                q: 1.0,
                type: "peak",
                enabled: true
            });
            this.selectedBand = this.bands.length - 1;
            this.draw();
            this.node.onWidgetChanged?.(this.name, this.serializeBands());
        }
    }

    onContextMenu(e) {
        if (this.selectedBand === null) return;
        e.preventDefault();

        // Simple cycle through filter types
        const types = ["peak", "low_shelf", "high_shelf", "low_pass", "high_pass"];
        const band = this.bands[this.selectedBand];
        const currentIndex = types.indexOf(band.type);
        band.type = types[(currentIndex + 1) % types.length];

        this.draw();
        this.node.onWidgetChanged?.(this.name, this.serializeBands());
    }

    getValue() {
        return this.serializeBands();
    }

    setValue(value) {
        this.parseBands(value);
        this.draw();
    }
}

// Register extension
app.registerExtension({
    name: "apzmedia.audio_equalizer",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "APZ_AudioEqualizer") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;

            nodeType.prototype.onNodeCreated = function() {
                onNodeCreated?.apply(this, arguments);

                // Find the eq_bands_json widget and replace with custom widget
                const widgetIndex = this.widgets.findIndex(w => w.name === "eq_bands_json");
                if (widgetIndex >= 0) {
                    const originalWidget = this.widgets[widgetIndex];

                    // Create custom EQ editor
                    const eqEditor = new EQEditorWidget(this, "eq_bands_json", ["STRING", { default: originalWidget.value }]);

                    // Replace widget
                    const domWidget = this.addDOMWidget("eq_bands_json", "custom", eqEditor.container, {
                        serialize: true,
                        getValue: () => eqEditor.getValue(),
                        setValue: (v) => eqEditor.setValue(v),
                    });

                    // Store reference for updates
                    domWidget.eqEditor = eqEditor;

                    // Remove original widget (it will be hidden but we keep it for serialization)
                    originalWidget.type = "hidden";
                }
            };
        }
    },
});

console.log("[APZmedia] Audio Equalizer extension loaded");
