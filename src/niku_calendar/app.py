from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths, QTimer, QUrl, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .controller import CalendarController
from .repository import CalendarRepository


def _resource(relative: str) -> Path:
    return Path(__file__).resolve().parent / relative


def _show_panel(window: object, tray: QSystemTrayIcon, controller: CalendarController, *, toggle: bool = False) -> None:
    if toggle and window.isVisible():
        window.hide()
        return
    controller.refresh()
    screen = QApplication.screenAt(tray.geometry().center()) or QApplication.primaryScreen()
    available = screen.availableGeometry()
    x = max(available.left() + 12, available.right() - window.width() - 12)
    y = max(available.top() + 12, available.bottom() - window.height() - 12)
    window.setPosition(x, y)
    window.show()
    window.raise_()
    window.requestActivate()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Niku Calendar")
    app.setOrganizationName("JaviHuh")
    app.setQuitOnLastWindowClosed(False)

    server_name = "niku-calendar-javihuh"
    peer = QLocalSocket()
    peer.connectToServer(server_name)
    if peer.waitForConnected(250):
        peer.write(b"show")
        peer.waitForBytesWritten(250)
        return 0
    QLocalServer.removeServer(server_name)
    instance_server = QLocalServer(app)
    if not instance_server.listen(server_name):
        return 1

    data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation))
    repository = CalendarRepository(data_dir / "niku-calendar.db")
    repository.prune_reminders()
    controller = CalendarController(repository)

    icon = QIcon(str(_resource("assets/niku-cat.svg")))
    app.setWindowIcon(icon)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("calendarController", controller)
    engine.load(QUrl.fromLocalFile(str(_resource("qml/Main.qml"))))
    if not engine.rootObjects():
        repository.close()
        return 1
    window = engine.rootObjects()[0]

    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("Niku Calendar")
    menu = QMenu()
    open_action = QAction(controller.text("openCalendar"), menu)
    add_action = QAction(controller.text("newActivity"), menu)
    quit_action = QAction(controller.text("quit"), menu)
    menu.addAction(open_action)
    menu.addAction(add_action)
    menu.addSeparator()
    menu.addAction(quit_action)
    tray.setContextMenu(menu)

    def translate_menu() -> None:
        open_action.setText(controller.text("openCalendar"))
        add_action.setText(controller.text("newActivity"))
        quit_action.setText(controller.text("quit"))

    controller.languageChanged.connect(translate_menu)

    open_action.triggered.connect(lambda: _show_panel(window, tray, controller))

    def add_activity() -> None:
        controller.newActivity()
        if not window.isVisible():
            _show_panel(window, tray, controller)

    add_action.triggered.connect(add_activity)
    quit_action.triggered.connect(app.quit)
    tray.activated.connect(
        lambda reason: _show_panel(window, tray, controller, toggle=True)
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick)
        else None
    )
    controller.reminderDue.connect(
        lambda title, message: tray.showMessage(title, message, icon, 8000)
    )
    app.aboutToQuit.connect(repository.close)
    tray.show()

    def show_from_peer() -> None:
        socket = instance_server.nextPendingConnection()
        socket.waitForReadyRead(100)
        _show_panel(window, tray, controller)
        socket.disconnectFromServer()

    instance_server.newConnection.connect(show_from_peer)

    reminder_timer = QTimer(app)
    reminder_timer.setTimerType(Qt.TimerType.VeryCoarseTimer)
    reminder_timer.setInterval(60_000)
    reminder_timer.timeout.connect(controller.checkReminders)
    reminder_timer.timeout.connect(controller.refresh)
    reminder_timer.start()
    controller.checkReminders()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
