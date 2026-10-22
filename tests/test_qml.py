"""Optional UI smoke test: python3 -m unittest discover -s tests -v."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import unittest

try:
    from PySide6.QtCore import QUrl, QObject, QRectF
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickWindow, QQuickItem
    from PySide6.QtTest import QTest
    HAS_QT = True
except ImportError:
    HAS_QT = False


@unittest.skipUnless(HAS_QT, 'PySide6 is required for the optional QML smoke test')
class WidgetTests(unittest.TestCase):
    def test_two_providers_render_and_themes_are_independent(self):
        app = QGuiApplication.instance() or QGuiApplication([])
        engine = QQmlApplicationEngine()
        ui = (Path(__file__).resolve().parents[1] / 'contents/ui').as_uri()
        engine.loadData(('''import QtQuick
import QtQuick.Window
import "UI_PATH"
Window {
    visible: true; width: 510; height: 300
    PixelTheme { id: retro; objectName: "retroTheme"; activeThemeId: "retro_pixel" }
    PixelTheme { id: rounded; objectName: "roundedTheme"; activeThemeId: "material3" }
    PixelWindow { objectName: "agy"; x: 12; y: 12; width: 237; height: 276;
        theme: retro; provider: "antigravity"; titleText: "antigravity.sh";
        statusText: "спит"; enableAnimation: false }
    PixelWindow { objectName: "codex"; x: 261; y: 12; width: 237; height: 276;
        theme: rounded; provider: "codex"; titleText: "codex.sh";
        statusText: "работает"; enableAnimation: false }
}'''.replace('UI_PATH', ui)).encode(), QUrl('file:///tmp/widget-smoke.qml'))
        self.assertTrue(engine.rootObjects(), 'QML components must load')
        window = engine.rootObjects()[0]
        QTest.qWait(100)
        self.assertFalse(window.grabWindow().isNull())
        self.assertEqual(window.findChild(QObject, 'agy').property('provider'), 'antigravity')
        codex = window.findChild(QObject, 'codex')
        self.assertEqual(codex.property('provider'), 'codex')
        rounded = window.findChild(QObject, 'roundedTheme')
        rounded.setProperty('activeThemeId', 'cyberpunk')
        self.assertEqual(window.findChild(QObject, 'retroTheme').property('activeThemeId'), 'retro_pixel')
        self.assertEqual(rounded.property('activeThemeId'), 'cyberpunk')
        # Switching an existing instance must replace its logo without affecting its neighbour.
        before = window.grabWindow().copy(280, 50, 200, 100)
        codex.setProperty('provider', 'antigravity')
        QTest.qWait(100)
        after = window.grabWindow().copy(280, 50, 200, 100)
        self.assertNotEqual(before, after)
        window.close()
        engine.deleteLater()
        app.processEvents()

    def test_layout_fits_default_and_small_sizes_for_both_logos(self):
        app = QGuiApplication.instance() or QGuiApplication([])
        engine = QQmlApplicationEngine()
        ui = (Path(__file__).resolve().parents[1] / 'contents/ui').as_uri()
        engine.loadData(('''import QtQuick
import QtQuick.Window
import "UI_PATH"
Window {
    visible: true; width: 300; height: 320
    PixelWindow { objectName: "card"; width: 256; height: 288;
        showExactPercent: true; showResetTimes: true;
        bar1Percent: 99; bar1Exact: 99.4; bar1Reset: "4ч 45м";
        bar2Percent: 56; bar2Exact: 55.9; bar2Reset: "1д 15ч" }
}'''.replace('UI_PATH', ui)).encode(), QUrl('file:///tmp/widget-layout-smoke.qml'))
        self.assertTrue(engine.rootObjects())
        window = engine.rootObjects()[0]
        card = window.findChild(QQuickItem, 'card')
        for selected in ('antigravity', 'codex'):
            card.setProperty('provider', selected)
            for width, height in ((256, 288), (250, 280), (220, 215), (160, 160)):
                card.setWidth(width)
                card.setHeight(height)
                for mascot in ('auto', 'large'):
                    card.setProperty('mascotSize', mascot)
                    QTest.qWait(30)
                    for name in ('quotaBar1', 'quotaBar2', 'mascotSlot'):
                        item = card.findChild(QQuickItem, name)
                        self.assertIsNotNone(item)
                        rect = item.mapRectToItem(card, QRectF(0, 0, item.width(), item.height()))
                        self.assertGreaterEqual(rect.left(), 0, (selected, width, height, name))
                        self.assertLessEqual(rect.right(), width, (selected, width, height, name))
                        self.assertLessEqual(rect.bottom(), height-4, (selected, width, height, name))
        window.close()
        engine.deleteLater()
        app.processEvents()


if __name__ == '__main__':
    unittest.main()
