import { app } from "../../../scripts/app.js";

const AUDIO_EXTS = new Set(["wav", "mp3", "flac", "ogg", "m4a", "aac", "opus", "wma"]);

function isAudioFile(file) {
    if (file.type?.startsWith("audio/")) return true;
    const ext = file.name.split(".").pop()?.toLowerCase();
    return AUDIO_EXTS.has(ext);
}

app.registerExtension({
    name: "APZmedia.AudioUpload",

    async setup() {
        // Wrap the canvas-level file handler so audio drops create our node
        const origHandleFile = app.handleFile.bind(app);

        app.handleFile = async function (file) {
            if (!isAudioFile(file)) {
                return origHandleFile(file);
            }

            // Upload the file to ComfyUI's input folder
            const formData = new FormData();
            formData.append("image", file);   // ComfyUI audio endpoint still uses "image" key
            formData.append("type", "input");
            formData.append("overwrite", "false");

            let filename;
            try {
                const resp = await fetch("/upload/audio", {
                    method: "POST",
                    body: formData,
                });
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                const data = await resp.json();
                filename = data.subfolder ? `${data.subfolder}/${data.name}` : data.name;
            } catch (err) {
                console.error("[APZmedia] Audio upload failed:", err);
                return origHandleFile(file);  // fall back to built-in handling
            }

            // Place the node where the file was dropped
            const node = LiteGraph.createNode("APZ_AudioUpload");
            if (!node) {
                console.error("[APZmedia] APZ_AudioUpload node type not registered");
                return;
            }
            node.pos = [...app.canvas.graph_mouse];
            app.graph.add(node);

            // Give LiteGraph one tick to finish building the widget list
            await new Promise((r) => requestAnimationFrame(r));

            const audioWidget = node.widgets?.find((w) => w.name === "audio");
            if (audioWidget) {
                audioWidget.value = filename;
                audioWidget.callback?.(filename);
            }

            app.graph.setDirtyCanvas(true, true);
        };
    },
});
