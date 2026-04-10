import { app } from "../../../scripts/app.js";

/**
 * APZmedia Audio Region Selector
 *
 * Interactive timeline canvas for selecting an inpaint region.
 * - Drag the red handles to move start / end boundaries
 * - Drag the shaded region to shift both handles together
 * - Click a word button to snap the region to that word's timing
 * - The region_start_ms / region_end_ms float widgets and
 *   region_start_frame / region_end_frame int widgets all stay in sync.
 */

class AudioRegionSelectorWidget {
    constructor(node, inputName, initialJson) {
        this.node = node;
        this.name = inputName;

        // State
        this.wordTimes = [];
        this.totalDurationMs = 10000; // default; refined from word times
        this.regionStartMs = 0;
        this.regionEndMs = 500;
        this.fps = 24;

        // Drag state
        this.dragging = null; // "start" | "end" | "region" | null
        this.dragAnchorX = 0;
        this.dragAnchorStartMs = 0;
        this.dragAnchorEndMs = 0;

        // Canvas dimensions
        this.W = 400;
        this.H = 80;

        // ---- Build DOM -------------------------------------------------- //
        this.container = document.createElement("div");
        this.container.style.cssText = [
            `width:${this.W}px`,
            "background:#1a1a1a",
            "border-radius:4px",
            "padding:4px",
            "box-sizing:border-box",
            "user-select:none",
        ].join(";");

        // Timeline canvas
        this.canvas = document.createElement("canvas");
        this.canvas.width = this.W;
        this.canvas.height = this.H;
        this.canvas.style.cssText = "display:block;cursor:col-resize;border-radius:3px;";
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext("2d");

        // Word buttons row
        this.wordRow = document.createElement("div");
        this.wordRow.style.cssText = [
            "display:flex",
            "flex-wrap:wrap",
            "gap:3px",
            "margin-top:5px",
            "max-height:52px",
            "overflow-y:auto",
            "padding-right:2px",
        ].join(";");
        this.container.appendChild(this.wordRow);

        // ---- Events ----------------------------------------------------- //
        this.canvas.addEventListener("mousedown", this._onMouseDown.bind(this));
        this.canvas.addEventListener("mousemove", this._onMouseMove.bind(this));
        this.canvas.addEventListener("mouseup", this._onMouseUp.bind(this));
        this.canvas.addEventListener("mouseleave", this._onMouseUp.bind(this));

        // ---- Init ------------------------------------------------------- //
        this._parseAndApplyJson(initialJson || "[]");
        this._syncWithWidgets();
        this._draw();
    }

    // -------------------------------------------------------------------- //
    //  Public API (called by ComfyUI DOM widget serialisation)              //
    // -------------------------------------------------------------------- //

    getValue() {
        // We store word_times_json as our serialisable value so the backend
        // can reconstruct the word list.
        return JSON.stringify(this.wordTimes);
    }

    setValue(v) {
        this._parseAndApplyJson(v);
        this._draw();
    }

    // -------------------------------------------------------------------- //
    //  Internal helpers                                                      //
    // -------------------------------------------------------------------- //

    _parseAndApplyJson(jsonStr) {
        try {
            const parsed = JSON.parse(jsonStr);
            if (Array.isArray(parsed)) {
                this.wordTimes = parsed;
                if (parsed.length > 0) {
                    const lastEnd = parsed[parsed.length - 1].end * 1000;
                    this.totalDurationMs = Math.max(this.totalDurationMs, lastEnd * 1.1);
                }
                this._buildWordButtons();
            }
        } catch (_) { /* invalid JSON — keep previous state */ }
    }

    _buildWordButtons() {
        this.wordRow.innerHTML = "";
        this.wordTimes.forEach((wt) => {
            const btn = document.createElement("button");
            btn.textContent = (wt.word || "").trim();
            btn.title = `${(wt.start * 1000).toFixed(0)}ms – ${(wt.end * 1000).toFixed(0)}ms`;
            btn.style.cssText = [
                "font-size:10px",
                "padding:2px 6px",
                "background:#2a2a2a",
                "color:#ccc",
                "border:1px solid #555",
                "border-radius:3px",
                "cursor:pointer",
                "line-height:1.4",
            ].join(";");
            btn.addEventListener("mouseenter", () => { btn.style.background = "#3a3a3a"; });
            btn.addEventListener("mouseleave", () => { btn.style.background = "#2a2a2a"; });
            btn.addEventListener("click", () => {
                this.regionStartMs = wt.start * 1000;
                this.regionEndMs   = wt.end * 1000;
                this._notifyChange();
                this._draw();
            });
            this.wordRow.appendChild(btn);
        });
    }

    // ---- Coordinate helpers -------------------------------------------- //

    _msToX(ms) {
        const dur = Math.max(1, this.totalDurationMs);
        return Math.max(0, Math.min(this.W, (ms / dur) * this.W));
    }

    _xToMs(x) {
        const dur = Math.max(1, this.totalDurationMs);
        return Math.max(0, Math.min(dur, (x / this.W) * dur));
    }

    _clientToCanvasX(e) {
        const rect = this.canvas.getBoundingClientRect();
        return e.clientX - rect.left;
    }

    // ---- Drawing -------------------------------------------------------- //

    _draw() {
        const ctx = this.ctx;
        const W = this.W, H = this.H;

        // Background
        ctx.fillStyle = "#1a1a1a";
        ctx.fillRect(0, 0, W, H);

        // Centre line
        ctx.fillStyle = "#333";
        ctx.fillRect(0, H / 2 - 1, W, 2);

        // Word tick marks
        ctx.fillStyle = "#ffcc66";
        this.wordTimes.forEach((wt) => {
            const x = this._msToX(wt.start * 1000);
            ctx.fillRect(x, 0, 1, 10);
        });

        // Region fill
        const x0 = this._msToX(this.regionStartMs);
        const x1 = this._msToX(this.regionEndMs);
        ctx.fillStyle = "rgba(255,107,107,0.25)";
        ctx.fillRect(x0, 0, x1 - x0, H);

        // Handles
        const HANDLE_W = 4;
        ctx.fillStyle = "#ff6b6b";
        ctx.fillRect(x0 - HANDLE_W / 2, 0, HANDLE_W, H);
        ctx.fillRect(x1 - HANDLE_W / 2, 0, HANDLE_W, H);

        // Triangle arrows on handles
        ctx.fillStyle = "#fff";
        this._drawTriangle(ctx, x0 + 1, H / 2, "right", 5);
        this._drawTriangle(ctx, x1 - 1, H / 2, "left", 5);

        // Labels
        ctx.font = "10px sans-serif";
        ctx.fillStyle = "#ccc";
        ctx.textAlign = "left";
        ctx.fillText(`${this.regionStartMs.toFixed(0)} ms`, x0 + 5, 14);
        ctx.textAlign = "right";
        ctx.fillText(`${this.regionEndMs.toFixed(0)} ms`, x1 - 5, 14);

        const durMs = this.regionEndMs - this.regionStartMs;
        ctx.fillStyle = "#888";
        ctx.textAlign = "center";
        ctx.fillText(`${durMs.toFixed(0)} ms  ·  ${(durMs * this.fps / 1000).toFixed(1)} fr`,
                     W / 2, H - 5);
    }

    _drawTriangle(ctx, x, y, dir, size) {
        ctx.beginPath();
        if (dir === "right") {
            ctx.moveTo(x,        y - size);
            ctx.lineTo(x + size, y);
            ctx.lineTo(x,        y + size);
        } else {
            ctx.moveTo(x,        y - size);
            ctx.lineTo(x - size, y);
            ctx.lineTo(x,        y + size);
        }
        ctx.closePath();
        ctx.fill();
    }

    // ---- Mouse events --------------------------------------------------- //

    _onMouseDown(e) {
        const x  = this._clientToCanvasX(e);
        const x0 = this._msToX(this.regionStartMs);
        const x1 = this._msToX(this.regionEndMs);
        const HIT = 8; // pixels

        if (Math.abs(x - x0) <= HIT) {
            this.dragging = "start";
        } else if (Math.abs(x - x1) <= HIT) {
            this.dragging = "end";
        } else if (x > x0 + HIT && x < x1 - HIT) {
            this.dragging = "region";
            this.dragAnchorX        = x;
            this.dragAnchorStartMs  = this.regionStartMs;
            this.dragAnchorEndMs    = this.regionEndMs;
        }
    }

    _onMouseMove(e) {
        if (!this.dragging) return;
        const x = this._clientToCanvasX(e);

        if (this.dragging === "start") {
            this.regionStartMs = Math.min(this._xToMs(x), this.regionEndMs - 10);
        } else if (this.dragging === "end") {
            this.regionEndMs = Math.max(this._xToMs(x), this.regionStartMs + 10);
        } else if (this.dragging === "region") {
            const deltaMs = this._xToMs(x) - this._xToMs(this.dragAnchorX);
            const dur = this.dragAnchorEndMs - this.dragAnchorStartMs;
            this.regionStartMs = Math.max(0, this.dragAnchorStartMs + deltaMs);
            this.regionEndMs   = Math.min(this.totalDurationMs, this.regionStartMs + dur);
        }

        this._draw();
        this._notifyChange();
    }

    _onMouseUp() {
        this.dragging = null;
    }

    // ---- Widget sync ---------------------------------------------------- //

    _notifyChange() {
        const sw = this._sw;
        if (!sw) return;

        const startMs = Math.round(this.regionStartMs * 10) / 10;
        const endMs   = Math.round(this.regionEndMs   * 10) / 10;

        if (sw.region_start_ms)    sw.region_start_ms.value    = startMs;
        if (sw.region_end_ms)      sw.region_end_ms.value      = endMs;
        if (sw.region_start_frame) sw.region_start_frame.value = Math.round(startMs * this.fps / 1000);
        if (sw.region_end_frame)   sw.region_end_frame.value   = Math.round(endMs   * this.fps / 1000);

        if (this.node) this.node.setDirtyCanvas(true, false);
    }

    _syncWithWidgets() {
        this._sw = {
            region_start_ms:    null,
            region_end_ms:      null,
            region_start_frame: null,
            region_end_frame:   null,
            fps:                null,
        };

        // Widgets are created asynchronously — poll once after a short delay.
        setTimeout(() => {
            if (!this.node?.widgets) return;

            this.node.widgets.forEach((w) => {
                if (this._sw.hasOwnProperty(w.name)) {
                    this._sw[w.name] = w;
                }
            });

            // Read initial values from existing widgets
            if (this._sw.region_start_ms)
                this.regionStartMs = parseFloat(this._sw.region_start_ms.value) || 0;
            if (this._sw.region_end_ms)
                this.regionEndMs   = parseFloat(this._sw.region_end_ms.value)   || 500;
            if (this._sw.fps)
                this.fps           = parseInt(this._sw.fps.value)                || 24;

            // Hook into value changes so the canvas updates when the user
            // edits a numeric widget directly.
            const self = this;

            const hook = (name, fn) => {
                const w = self._sw[name];
                if (!w) return;
                const orig = w.callback;
                w.callback = (v) => { fn(v); if (orig) orig(v); };
            };

            hook("region_start_ms", (v) => {
                self.regionStartMs = parseFloat(v) || 0;
                self._updateFrameWidgets();
                self._draw();
            });
            hook("region_end_ms", (v) => {
                self.regionEndMs = parseFloat(v) || 0;
                self._updateFrameWidgets();
                self._draw();
            });
            hook("region_start_frame", (v) => {
                self.regionStartMs = (parseInt(v) || 0) / self.fps * 1000;
                if (self._sw.region_start_ms)
                    self._sw.region_start_ms.value =
                        Math.round(self.regionStartMs * 10) / 10;
                self._draw();
            });
            hook("region_end_frame", (v) => {
                self.regionEndMs = (parseInt(v) || 0) / self.fps * 1000;
                if (self._sw.region_end_ms)
                    self._sw.region_end_ms.value =
                        Math.round(self.regionEndMs * 10) / 10;
                self._draw();
            });
            hook("fps", (v) => {
                self.fps = parseInt(v) || 24;
                self._updateFrameWidgets();
                self._draw();
            });

            self._draw();
        }, 100);
    }

    _updateFrameWidgets() {
        if (this._sw.region_start_frame)
            this._sw.region_start_frame.value =
                Math.round(this.regionStartMs * this.fps / 1000);
        if (this._sw.region_end_frame)
            this._sw.region_end_frame.value =
                Math.round(this.regionEndMs * this.fps / 1000);
    }
}

// ========================================================================== //
//  ComfyUI extension registration                                             //
// ========================================================================== //

app.registerExtension({
    name: "apzmedia.audio_region_selector",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData.name !== "APZ_AudioRegionSelector") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;

        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);

            // Replace the word_times_json text widget with the canvas widget.
            const idx = this.widgets?.findIndex((w) => w.name === "word_times_json");
            if (idx == null || idx < 0) return;

            const originalWidget = this.widgets[idx];
            const selector = new AudioRegionSelectorWidget(
                this,
                "word_times_json",
                originalWidget.value ?? "[]"
            );

            const domWidget = this.addDOMWidget(
                "word_times_json",
                "custom",
                selector.container,
                {
                    serialize: true,
                    getValue: () => selector.getValue(),
                    setValue: (v) => selector.setValue(v),
                }
            );

            domWidget._selector = selector;
            originalWidget.type = "hidden";
        };
    },
});

console.log("[APZmedia] Audio Region Selector extension loaded");
