pragma ComponentBehavior: Bound

import QtQuick

Item {
    id: root

    property string status: "отдыхает"
    property int pixelScale: 5

    // 12 columns x 10 rows matrix matching the official Antigravity logo
    readonly property int gridCols: 12
    readonly property int gridRows: 10

    implicitWidth: gridCols * pixelScale
    implicitHeight: gridRows * pixelScale

    property real floatOffset: 0
    property int shimmerStep: 0

    // Gentle levitation animation
    SequentialAnimation {
        running: root.status !== "спит"
        loops: Animation.Infinite

        NumberAnimation {
            target: root
            property: "floatOffset"
            from: 0
            to: -3
            duration: root.status === "работает" ? 600 : 1300
            easing.type: Easing.InOutQuad
        }
        NumberAnimation {
            target: root
            property: "floatOffset"
            from: -3
            to: 0
            duration: root.status === "работает" ? 600 : 1300
            easing.type: Easing.InOutQuad
        }
    }

    // Shimmer/pulse step timer for active thinking/working states
    Timer {
        interval: 140
        running: root.status === "думает" || root.status === "работает"
        repeat: true
        onTriggered: {
            root.shimmerStep = (root.shimmerStep + 1) % 10
            canvas.requestPaint()
        }
    }

    onStatusChanged: canvas.requestPaint()
    onPixelScaleChanged: canvas.requestPaint()
    onFloatOffsetChanged: canvas.requestPaint()

    Canvas {
        id: canvas
        anchors.fill: parent
        anchors.topMargin: root.floatOffset
        renderStrategy: Canvas.Immediate
        renderTarget: Canvas.FramebufferObject

        // Exact pixel matrix extracted directly from the official Antigravity asset
        readonly property var matrix: [
            [null, null, null, null, null, "#f2922e", "#f07236", null, null, null, null, null],
            [null, null, null, null, "#dbb131", "#f6912e", "#f37337", "#f0583b", null, null, null, null],
            [null, null, null, "#9ec345", "#b5b43e", "#e2993d", "#f67a34", "#f86a35", "#ef5442", null, null, null],
            [null, null, null, "#86c64e", "#75b45e", "#cc954d", "#ef7947", "#e16652", "#e14f59", null, null, null],
            [null, null, "#7cc251", "#71c25c", "#5ca98f", "#5c91b3", "#8373b0", "#746fc3", "#995da8", "#9c5b97", null, null],
            [null, null, "#80c654", "#54b881", "#4097de", null, null, "#4a7ee4", "#706ece", "#8f64b4", null, null],
            [null, null, "#61c37d", "#43aeab", null, null, null, null, "#4a80ea", "#6c73d8", null, null],
            [null, "#6dc694", "#62bad5", "#47a8dc", null, null, null, null, "#3d89fb", "#4a81f0", "#6579e1", null],
            [null, "#6bc7a3", "#64b6f6", null, null, null, null, null, null, "#3886fb", "#4881f4", null],
            ["#67b9f4", "#64b6f6", null, null, null, null, null, null, null, null, "#3883f9", "#3d85fc"]
        ]

        onPaint: {
            const ctx = getContext("2d");
            ctx.imageSmoothingEnabled = false;
            ctx.clearRect(0, 0, width, height);

            const s = root.pixelScale;
            const rows = canvas.matrix.length;

            for (let r = 0; r < rows; r++) {
                const row = canvas.matrix[r];
                for (let c = 0; c < row.length; c++) {
                    const colorHex = row[c];
                    if (!colorHex) continue;

                    let finalColor = colorHex;

                    if (root.status === "спит") {
                        // Greyscale dimmed colors
                        finalColor = "#555562";
                    } else if (root.status === "ошибка") {
                        // Red tint error
                        finalColor = "#e63946";
                    } else if (root.status === "думает" || root.status === "работает") {
                        // Moving light wave through the arch
                        if ((r + c + root.shimmerStep) % 7 === 0) {
                            finalColor = "#ffffff";
                        }
                    }

                    ctx.fillStyle = finalColor;
                    ctx.fillRect(c * s, r * s, s, s);
                }
            }
        }
    }
}
