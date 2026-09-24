import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 500
    height: 720
    minimumWidth: 420
    minimumHeight: 560
    visible: false
    color: "transparent"
    flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    title: calendarController.calendarTitle

    readonly property color ink: "#eeeaf5"
    readonly property color muted: "#9e98ac"
    readonly property color panel: "#211e2b"
    readonly property color panelRaised: "#2a2636"
    readonly property color edge: "#3b3549"
    readonly property color accent: "#efb366"
    readonly property color accentSoft: "#3c3029"
    readonly property color danger: "#e98686"

    component NikuButton: Button {
        id: control
        property bool quiet: false
        implicitHeight: 36
        leftPadding: 13
        rightPadding: 13
        font.pixelSize: 13
        font.weight: Font.DemiBold
        contentItem: Text {
            text: control.text
            color: control.quiet ? root.ink : "#211a12"
            font: control.font
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            radius: 9
            color: control.quiet ? (control.hovered ? "#393345" : root.panelRaised)
                                 : (control.hovered ? "#f5c47f" : root.accent)
            border.color: control.quiet ? root.edge : "transparent"
        }
    }

    component NikuField: TextField {
        id: field
        color: root.ink
        placeholderTextColor: root.muted
        selectionColor: root.accent
        selectedTextColor: "#211a12"
        leftPadding: 11
        rightPadding: 11
        implicitHeight: 40
        background: Rectangle {
            color: "#181620"
            radius: 8
            border.color: field.activeFocus ? root.accent : root.edge
        }
    }

    component FieldLabel: Text {
        color: root.muted
        font.pixelSize: 11
        font.weight: Font.DemiBold
        font.capitalization: Font.AllUppercase
        font.letterSpacing: 0.7
    }

    background: Rectangle {
        color: "#17151f"
        radius: 16
        border.color: root.edge
        border.width: 1
    }

    header: Rectangle {
        height: 68
        color: "transparent"

        MouseArea {
            anchors.fill: parent
            onPressed: root.startSystemMove()
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 18
            anchors.rightMargin: 14
            spacing: 11

            Image {
                source: Qt.resolvedUrl("../assets/niku-cat.svg")
                sourceSize.width: 38
                sourceSize.height: 38
                Layout.preferredWidth: 38
                Layout.preferredHeight: 38
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 1
                Text {
                    text: calendarController.calendarTitle
                    color: root.ink
                    font.pixelSize: 18
                    font.weight: Font.Bold
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
                Text {
                    text: calendarController.encouragement
                    color: root.muted
                    font.pixelSize: 10
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
            }
            ToolButton {
                text: "⚙"
                font.pixelSize: 18
                onClicked: settingsDialog.open()
                ToolTip.visible: hovered
                ToolTip.text: calendarController.text("settings")
                contentItem: Text { text: parent.text; color: root.muted; font: parent.font; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                background: Rectangle { color: parent.hovered ? root.panelRaised : "transparent"; radius: 8 }
            }
            ToolButton {
                text: "×"
                font.pixelSize: 24
                onClicked: root.hide()
                contentItem: Text { text: parent.text; color: root.muted; font: parent.font; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                background: Rectangle { color: parent.hovered ? root.panelRaised : "transparent"; radius: 8 }
            }
        }
    }

    StackLayout {
        id: pages
        anchors.fill: parent
        anchors.leftMargin: 18
        anchors.rightMargin: 18
        anchors.bottomMargin: 18
        currentIndex: 0

        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Rectangle {
                        Layout.preferredWidth: 184
                        Layout.preferredHeight: 38
                        color: root.panel
                        radius: 10
                        border.color: root.edge
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 3
                            spacing: 3
                            Button {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                text: calendarController.text("today")
                                onClicked: calendarController.setView("day")
                                contentItem: Text { text: parent.text; color: calendarController.view === "day" ? "#211a12" : root.muted; font.pixelSize: 12; font.weight: Font.DemiBold; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                                background: Rectangle { radius: 7; color: calendarController.view === "day" ? root.accent : "transparent" }
                            }
                            Button {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                text: calendarController.text("week")
                                onClicked: calendarController.setView("week")
                                contentItem: Text { text: parent.text; color: calendarController.view === "week" ? "#211a12" : root.muted; font.pixelSize: 12; font.weight: Font.DemiBold; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                                background: Rectangle { radius: 7; color: calendarController.view === "week" ? root.accent : "transparent" }
                            }
                        }
                    }
                    Item { Layout.fillWidth: true }
                    NikuButton { text: calendarController.text("add"); onClicked: calendarController.newActivity() }
                }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                    Column {
                        width: parent.width
                        spacing: 9

                        Text {
                            visible: calendarController.events.length === 0
                            width: parent.width
                            topPadding: 80
                            leftPadding: 25
                            rightPadding: 25
                            text: calendarController.text("empty")
                            color: root.muted
                            font.pixelSize: 14
                            wrapMode: Text.WordWrap
                            horizontalAlignment: Text.AlignHCenter
                        }

                        Repeater {
                            model: calendarController.events
                            delegate: Column {
                                required property var modelData
                                required property int index
                                width: parent.width
                                spacing: 7

                                Text {
                                    visible: calendarController.view === "week"
                                             && (index === 0 || calendarController.events[index - 1].date !== modelData.date)
                                    text: modelData.dateLabel
                                    color: root.accent
                                    font.pixelSize: 12
                                    font.weight: Font.Bold
                                    topPadding: index === 0 ? 2 : 9
                                }

                                Rectangle {
                                    width: parent.width
                                    height: cardContent.implicitHeight + 24
                                    radius: 11
                                    color: modelData.state === "active" ? root.accentSoft : root.panel
                                    border.color: modelData.state === "active" ? root.accent : root.edge

                                    RowLayout {
                                        id: cardContent
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.verticalCenter: parent.verticalCenter
                                        anchors.leftMargin: 13
                                        anchors.rightMargin: 11
                                        spacing: 11

                                        Rectangle {
                                            Layout.preferredWidth: 4
                                            Layout.fillHeight: true
                                            Layout.minimumHeight: 42
                                            radius: 2
                                            color: modelData.state === "occurred" ? "#686272"
                                                  : modelData.state === "active" ? root.accent : "#8f78c9"
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 3
                                            Text {
                                                text: modelData.title
                                                color: modelData.state === "occurred" ? root.muted : root.ink
                                                font.pixelSize: 15
                                                font.weight: Font.DemiBold
                                                elide: Text.ElideRight
                                                Layout.fillWidth: true
                                            }
                                            Text {
                                                text: modelData.startTime + " – " + modelData.endTime
                                                      + (modelData.location ? "  ·  " + modelData.location : "")
                                                color: root.muted
                                                font.pixelSize: 12
                                                elide: Text.ElideRight
                                                Layout.fillWidth: true
                                            }
                                        }
                                        ToolButton {
                                            visible: modelData.links && modelData.links.length > 0
                                            text: "↗"
                                            onClicked: calendarController.openLink(modelData.links[0].url)
                                            contentItem: Text { text: parent.text; color: root.accent; font.pixelSize: 18; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                                            background: Rectangle { color: parent.hovered ? root.panelRaised : "transparent"; radius: 7 }
                                        }
                                        ToolButton {
                                            text: "✎"
                                            onClicked: calendarController.editActivity(modelData.id)
                                            contentItem: Text { text: parent.text; color: root.muted; font.pixelSize: 16; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                                            background: Rectangle { color: parent.hovered ? root.panelRaised : "transparent"; radius: 7 }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    visible: calendarController.notice.length > 0
                    Layout.fillWidth: true
                    Layout.preferredHeight: 32
                    radius: 8
                    color: root.panelRaised
                    Text { anchors.centerIn: parent; width: parent.width - 20; text: calendarController.notice; color: root.muted; font.pixelSize: 11; elide: Text.ElideRight; horizontalAlignment: Text.AlignHCenter }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    NikuButton { text: calendarController.text("manage"); quiet: true; onClicked: pages.currentIndex = 1 }
                    NikuButton { text: calendarController.text("importCsv"); quiet: true; onClicked: calendarController.chooseCsv() }
                    Item { Layout.fillWidth: true }
                    Text { text: calendarController.events.length + " " + calendarController.text(calendarController.events.length === 1 ? "event" : "events"); color: root.muted; font.pixelSize: 11 }
                }
            }
        }

        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 12
                RowLayout {
                    Layout.fillWidth: true
                    NikuButton { text: calendarController.text("back"); quiet: true; onClicked: pages.currentIndex = 0 }
                    Text { text: calendarController.text("activities"); color: root.ink; font.pixelSize: 20; font.weight: Font.Bold; Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter }
                    NikuButton { text: calendarController.text("new"); onClicked: calendarController.newActivity() }
                }
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    Column {
                        width: parent.width
                        spacing: 8
                        Text {
                            visible: calendarController.activities.length === 0
                            width: parent.width
                            topPadding: 80
                            text: calendarController.text("empty")
                            color: root.muted
                            wrapMode: Text.WordWrap
                            horizontalAlignment: Text.AlignHCenter
                        }
                        Repeater {
                            model: calendarController.activities
                            delegate: Rectangle {
                                required property var modelData
                                width: parent.width
                                height: 66
                                radius: 10
                                color: root.panel
                                border.color: root.edge
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 11
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 3
                                        Text { text: modelData.title; color: root.ink; font.pixelSize: 14; font.weight: Font.DemiBold; elide: Text.ElideRight; Layout.fillWidth: true }
                                        Text { text: modelData.startDate + "  ·  " + modelData.startTime + " – " + modelData.endTime + (modelData.recurrence.type !== "none" ? "  ·  " + modelData.recurrence.type : ""); color: root.muted; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
                                    }
                                    NikuButton { text: calendarController.text("edit"); quiet: true; onClicked: calendarController.editActivity(modelData.id) }
                                    ToolButton {
                                        text: "×"
                                        onClicked: calendarController.deleteActivity(modelData.id)
                                        contentItem: Text { text: parent.text; color: root.danger; font.pixelSize: 20; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                                        background: Rectangle { color: parent.hovered ? "#3a252c" : "transparent"; radius: 7 }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        Item {
            function dayList(text) {
                if (!text.trim()) return []
                return text.split(/[,; ]+/).filter(value => value.length > 0).map(value => Number(value))
            }

            ColumnLayout {
                anchors.fill: parent
                spacing: 10
                RowLayout {
                    Layout.fillWidth: true
                    NikuButton { text: calendarController.text("cancel"); quiet: true; onClicked: pages.currentIndex = 0 }
                    Text { text: calendarController.text(editorId.text ? "editActivity" : "newActivity"); color: root.ink; font.pixelSize: 20; font.weight: Font.Bold; Layout.fillWidth: true; horizontalAlignment: Text.AlignRight }
                }
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    ColumnLayout {
                        width: parent.width
                        spacing: 7
                        TextField { id: editorId; visible: false }
                        FieldLabel { text: calendarController.text("title") }
                        NikuField { id: titleField; Layout.fillWidth: true; placeholderText: "Team sync" }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 9
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 5
                                FieldLabel { text: calendarController.text("date") }
                                NikuField { id: dateField; Layout.fillWidth: true; placeholderText: "YYYY-MM-DD" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 5
                                FieldLabel { text: calendarController.text("start") }
                                NikuField { id: startField; Layout.fillWidth: true; placeholderText: "09:00" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 5
                                FieldLabel { text: calendarController.text("end") }
                                NikuField { id: endField; Layout.fillWidth: true; placeholderText: "10:00" }
                            }
                        }
                        FieldLabel { text: calendarController.text("location") }
                        NikuField { id: locationField; Layout.fillWidth: true; placeholderText: calendarController.text("optional") }
                        FieldLabel { text: calendarController.text("notes") }
                        NikuField { id: notesField; Layout.fillWidth: true; placeholderText: calendarController.text("optional") }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 9
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 5
                                FieldLabel { text: calendarController.text("repeat") }
                                ComboBox {
                                    id: recurrenceField
                                    Layout.fillWidth: true
                                    model: ["none", "daily", "weekly", "monthly", "yearly"]
                                }
                            }
                            ColumnLayout {
                                Layout.preferredWidth: 85
                                spacing: 5
                                FieldLabel { text: calendarController.text("every") }
                                NikuField { id: intervalField; Layout.fillWidth: true; inputMethodHints: Qt.ImhDigitsOnly; text: "1" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 5
                                FieldLabel { text: calendarController.text("until") }
                                NikuField { id: untilField; Layout.fillWidth: true; placeholderText: "Optional" }
                            }
                        }
                        FieldLabel { visible: recurrenceField.currentText === "weekly"; text: calendarController.text("weekdays") }
                        NikuField { id: weekdaysField; visible: recurrenceField.currentText === "weekly"; Layout.fillWidth: true; placeholderText: "0, 2, 4" }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 9
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 5
                                FieldLabel { text: calendarController.text("linkLabel") }
                                NikuField { id: linkLabelField; Layout.fillWidth: true; placeholderText: "Meeting" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 5
                                FieldLabel { text: calendarController.text("linkUrl") }
                                NikuField { id: linkUrlField; Layout.fillWidth: true; placeholderText: "https://…" }
                            }
                        }
                    }
                }
                Text { visible: calendarController.notice.length > 0; text: calendarController.notice; color: root.danger; font.pixelSize: 11; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                NikuButton {
                    text: calendarController.text("saveActivity")
                    Layout.fillWidth: true
                    onClicked: calendarController.saveActivity({
                        "id": editorId.text,
                        "title": titleField.text,
                        "startDate": dateField.text,
                        "startTime": startField.text,
                        "endTime": endField.text,
                        "location": locationField.text,
                        "notes": notesField.text,
                        "recurrenceType": recurrenceField.currentText,
                        "interval": intervalField.text,
                        "weekdays": parent.parent.dayList(weekdaysField.text),
                        "until": untilField.text,
                        "linkLabel": linkLabelField.text,
                        "linkUrl": linkUrlField.text
                    })
                }
            }
        }

        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 14
                RowLayout {
                    Layout.fillWidth: true
                    NikuButton { text: calendarController.text("cancel"); quiet: true; onClicked: pages.currentIndex = 0 }
                    Text { text: calendarController.text("importPreview"); color: root.ink; font.pixelSize: 20; font.weight: Font.Bold; Layout.fillWidth: true; horizontalAlignment: Text.AlignRight }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 90
                    radius: 11
                    color: root.panel
                    border.color: root.edge
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        Text { text: calendarController.importPreview.name || ""; color: root.ink; font.pixelSize: 15; font.weight: Font.DemiBold; elide: Text.ElideMiddle; Layout.fillWidth: true }
                        Text { text: (calendarController.importPreview.count || 0) + " " + calendarController.text("validActivities"); color: root.accent; font.pixelSize: 12 }
                        Text { text: (calendarController.importPreview.warnings || []).length + " " + calendarController.text("skippedRows"); color: root.muted; font.pixelSize: 11 }
                    }
                }
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    Column {
                        width: parent.width
                        spacing: 7
                        Repeater {
                            model: calendarController.importPreview.activities || []
                            delegate: Rectangle {
                                required property var modelData
                                width: parent.width
                                height: 52
                                radius: 9
                                color: root.panel
                                Text { anchors.fill: parent; anchors.margins: 11; text: modelData.title + "\n" + modelData.startDate + "  ·  " + modelData.startTime; color: root.ink; font.pixelSize: 12; elide: Text.ElideRight }
                            }
                        }
                    }
                }
                Text { text: calendarController.text("importHelp"); color: root.muted; font.pixelSize: 11; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                RowLayout {
                    Layout.fillWidth: true
                    NikuButton { text: calendarController.text("replaceAll"); quiet: true; Layout.fillWidth: true; onClicked: calendarController.importCsv(true) }
                    NikuButton { text: calendarController.text("mergeImport"); Layout.fillWidth: true; onClicked: calendarController.importCsv(false) }
                }
            }
        }
    }

    Dialog {
        id: settingsDialog
        anchors.centerIn: parent
        width: Math.min(390, root.width - 40)
        modal: true
        title: calendarController.text("settings")
        standardButtons: Dialog.Close
        palette.window: root.panel
        palette.windowText: root.ink
        palette.buttonText: root.ink
        background: Rectangle { color: root.panel; radius: 12; border.color: root.edge }
        contentItem: ColumnLayout {
            spacing: 10
            FieldLabel { text: calendarController.text("calendarName") }
            NikuField { id: calendarNameField; Layout.fillWidth: true; text: calendarController.calendarTitle; onEditingFinished: calendarController.setCalendarTitle(text) }
            FieldLabel { text: calendarController.text("language") }
            ComboBox {
                Layout.fillWidth: true
                model: ["English", "Español"]
                currentIndex: calendarController.language === "es" ? 1 : 0
                onActivated: calendarController.setLanguage(currentIndex === 1 ? "es" : "en")
            }
            CheckBox {
                text: calendarController.text("runAtStartup")
                checked: calendarController.runAtStartup
                enabled: Qt.platform.os === "windows"
                onToggled: calendarController.setRunAtStartup(checked)
                palette.windowText: root.ink
            }
            Text { text: calendarController.text("privacy"); color: root.muted; font.pixelSize: 11; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        }
    }

    Connections {
        target: calendarController
        function onPageRequested(index) {
            pages.currentIndex = index
            if (index === 2) loadEditor()
        }
    }

    function loadEditor() {
        const item = calendarController.editor
        editorId.text = item.id || ""
        titleField.text = item.title || ""
        dateField.text = item.startDate || calendarController.todayIso
        startField.text = item.startTime || "09:00"
        endField.text = item.endTime || "10:00"
        locationField.text = item.location || ""
        notesField.text = item.notes || ""
        linkLabelField.text = item.linkLabel || ""
        linkUrlField.text = item.linkUrl || ""
        intervalField.text = item.interval || "1"
        untilField.text = item.until || ""
        weekdaysField.text = (item.weekdays || []).join(", ")
        recurrenceField.currentIndex = Math.max(0, recurrenceField.model.indexOf(item.recurrenceType || "none"))
    }
}
