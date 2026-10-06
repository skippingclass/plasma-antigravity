pragma ComponentBehavior: Bound

import QtQuick

Item {
    id: root

    property string status: "отдыхает"
    property int pixelScale: 2
    property color accentColor: "#4cf0a0"

    // 32x32 grid for richer pixel art detail
    readonly property int baseGridSize: 32
    implicitWidth: baseGridSize * pixelScale
    implicitHeight: baseGridSize * pixelScale

    // Levitation bounce offset
    property real floatOffset: 0
    property real pulseAlpha: 1.0
    property int sparkFrame: 0

    // Smooth floating animation
    SequentialAnimation {
        running: root.status !== "спит"
        loops: Animation.Infinite

        NumberAnimation {
            target: root
            property: "floatOffset"
            from: 0
            to: -4 * root.pixelScale
            duration: root.status === "работает" ? 700 : 1400
            easing.type: Easing.InOutQuad
        }
        NumberAnimation {
            target: root
            property: "floatOffset"
            from: -4 * root.pixelScale
            to: 0
            duration: root.status === "работает" ? 700 : 1400
            easing.type: Easing.InOutQuad
        }
    }

    // Shimmer/animation timer for active states
    Timer {
        interval: 160
        running: root.status === "думает" || root.status === "работает"
        repeat: true
        onTriggered: {
            root.sparkFrame = (root.sparkFrame + 1) % 4
            canvas.requestPaint()
        }
    }

    // Breathing pulse for resting state
    SequentialAnimation {
        running: root.status === "отдыхает"
        loops: Animation.Infinite

        NumberAnimation {
            target: root
            property: "pulseAlpha"
            from: 0.85
            to: 1.0
            duration: 1600
            easing.type: Easing.InOutSine
        }
        NumberAnimation {
            target: root
            property: "pulseAlpha"
            from: 1.0
            to: 0.85
            duration: 1600
            easing.type: Easing.InOutSine
        }
    }

    onStatusChanged: canvas.requestPaint()
    onAccentColorChanged: canvas.requestPaint()
    onPixelScaleChanged: canvas.requestPaint()
    onFloatOffsetChanged: canvas.requestPaint()

    Canvas {
        id: canvas
        anchors.fill: parent
        anchors.topMargin: root.floatOffset
        renderStrategy: Canvas.Immediate
        renderTarget: Canvas.FramebufferObject

        onPaint: {
            const ctx = getContext("2d");
            ctx.imageSmoothingEnabled = false;
            ctx.clearRect(0, 0, width, height);

            const s = root.pixelScale;
            const cx = 16;
            const cy = 16;

            let coreColor = "#ffffff";
            let glowColor = root.accentColor.toString();
            let shadowColor = "#1f3b2e";
            let eyeColor = "#222228";
            let blushColor = "#fca5a5";

            if (root.status === "спит") {
                coreColor = "#8e8e9c";
                glowColor = "#444452";
                shadowColor = "#22222a";
                eyeColor = "#2a2a34";
                blushColor = "#525260";
            } else if (root.status === "ошибка") {
                glowColor = "#ff4b4b";
                shadowColor = "#4a1212";
            } else if (root.status === "думает") {
                glowColor = "#60a5fa";
                shadowColor = "#1e3a5f";
            }

            function putPixel(x, y, color) {
                ctx.fillStyle = color;
                ctx.fillRect(Math.floor(x * s), Math.floor(y * s), s, s);
            }

            function putRect(x, y, w, h, color) {
                ctx.fillStyle = color;
                ctx.fillRect(Math.floor(x * s), Math.floor(y * s), w * s, h * s);
            }

            // 1. Floating Halo Bar above head (like reference)
            const haloY = cy - 12;
            putRect(cx - 5, haloY, 11, 2, glowColor);
            putRect(cx - 3, haloY, 7, 2, "#ffffff");

            // 2. Vertical ray of Gemini Spark
            for (let dy = -10; dy <= 10; dy++) {
                const dist = Math.abs(dy);
                let w = 0;
                if (dist <= 2) w = 3;
                else if (dist <= 5) w = 2;
                else if (dist <= 8) w = 1;
                else w = 0;

                putRect(cx - w, cy + dy, (w * 2) + 1, 1, glowColor);
            }

            // 3. Horizontal ray of Gemini Spark
            for (let dx = -10; dx <= 10; dx++) {
                const dist = Math.abs(dx);
                let h = 0;
                if (dist <= 2) h = 3;
                else if (dist <= 5) h = 2;
                else if (dist <= 8) h = 1;
                else h = 0;

                putRect(cx + dx, cy - h, 1, (h * 2) + 1, glowColor);
            }

            // 4. White core body (central diamond)
            for (let dy = -5; dy <= 5; dy++) {
                const rem = 5 - Math.abs(dy);
                putRect(cx - rem, cy + dy, (rem * 2) + 1, 1, coreColor);
            }

            // 5. Subtle core highlight
            putRect(cx - 2, cy - 2, 5, 5, "#ffffff");

            // 6. Facial expressions (eyes & blush)
            if (root.status === "отдыхает") {
                // Cute sleeping/resting eyes ^ ^
                putRect(cx - 3, cy - 1, 2, 1, eyeColor);
                putRect(cx + 2, cy - 1, 2, 1, eyeColor);

                // Pink blush cheeks (like reference!)
                putRect(cx - 4, cy + 1, 2, 2, blushColor);
                putRect(cx + 3, cy + 1, 2, 2, blushColor);

            } else if (root.status === "спит") {
                // Sleeping horizontal bars - -
                putRect(cx - 3, cy, 2, 1, eyeColor);
                putRect(cx + 2, cy, 2, 1, eyeColor);

                // Z Z z particles
                putRect(cx + 8, cy - 8, 3, 1, "#8e8e9c");
                putRect(cx + 10, cy - 11, 4, 1, "#b5b5c7");

            } else if (root.status === "думает") {
                // Focused glowing eyes
                putRect(cx - 3, cy - 1, 2, 2, eyeColor);
                putRect(cx + 2, cy - 1, 2, 2, eyeColor);
                putPixel(cx - 2, cy - 1, "#93c5fd");
                putPixel(cx + 3, cy - 1, "#93c5fd");

                // Orbiting thought sparkles
                const points = [
                    [cx + 8, cy - 7],
                    [cx + 8, cy + 7],
                    [cx - 8, cy + 7],
                    [cx - 8, cy - 7]
                ];
                const p = points[root.sparkFrame % 4];
                putRect(p[0], p[1], 2, 2, "#93c5fd");
                putPixel(p[0], p[1], "#ffffff");

            } else if (root.status === "работает") {
                // Big anime sparkles in eyes
                putRect(cx - 3, cy - 2, 2, 2, eyeColor);
                putRect(cx + 2, cy - 2, 2, 2, eyeColor);
                putPixel(cx - 3, cy - 2, glowColor);
                putPixel(cx + 2, cy - 2, glowColor);

                putRect(cx - 4, cy + 1, 2, 2, blushColor);
                putRect(cx + 3, cy + 1, 2, 2, blushColor);

                // Dynamic pulse dots
                const offset = (root.sparkFrame % 2 === 0) ? 1 : -1;
                putPixel(cx - 9, cy - 9 + offset, glowColor);
                putPixel(cx + 9, cy + 9 - offset, glowColor);

            } else if (root.status === "ошибка") {
                // X X red eyes
                putPixel(cx - 4, cy - 2, "#ff2222");
                putPixel(cx - 2, cy - 2, "#ff2222");
                putPixel(cx - 3, cy - 1, "#ff2222");
                putPixel(cx - 4, cy, "#ff2222");
                putPixel(cx - 2, cy, "#ff2222");

                putPixel(cx + 2, cy - 2, "#ff2222");
                putPixel(cx + 4, cy - 2, "#ff2222");
                putPixel(cx + 3, cy - 1, "#ff2222");
                putPixel(cx + 2, cy, "#ff2222");
                putPixel(cx + 4, cy, "#ff2222");
            }
        }
    }
}
