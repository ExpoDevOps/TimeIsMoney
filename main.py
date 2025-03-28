import sys
import sqlite3
import os
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QPushButton, \
    QLabel, QVBoxLayout, QHBoxLayout, QWidget, QListWidget, QMessageBox, QMenu, QLineEdit, QListWidgetItem, QTextEdit
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QFont, QAction
import xml.etree.ElementTree as ET


class TimeIsMoney(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TimeIsMoney")
        self.resize(800, 600)

        # Database connection
        self.db_path = "G:\\expo\\Software\\TimeIsMoney\\TimeIsMoney\\EmployeeData.db"
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # Main widget and vertical layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Top layout for sidebar, SVG, and Reset button
        self.top_layout = QHBoxLayout()

        # Left sidebar (vertical layout for controls)
        self.sidebar = QWidget(self)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar.setMaximumWidth(200)

        # Search box for employees
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("Search Employees...")
        self.search_box.textChanged.connect(self.update_search_results)
        self.sidebar_layout.addWidget(self.search_box)

        # Search results list
        self.search_results = QListWidget(self)
        self.search_results.itemClicked.connect(self.add_participant_from_search)
        self.search_results.setMaximumHeight(100)
        self.sidebar_layout.addWidget(self.search_results)

        # Add Participant button (Red)
        self.add_participant_button = QPushButton("Add Participant", self)
        self.add_participant_button.clicked.connect(self.show_participant_menu)
        self.add_participant_button.setStyleSheet("background-color: red; color: white;")
        self.sidebar_layout.addWidget(self.add_participant_button)

        # Remove Participant button (Green)
        self.remove_participant_button = QPushButton("Remove Participant", self)
        self.remove_participant_button.clicked.connect(self.remove_participant)
        self.remove_participant_button.setStyleSheet("background-color: green; color: white;")
        self.sidebar_layout.addWidget(self.remove_participant_button)

        # Add All Employees button (Purple)
        self.add_all_button = QPushButton("Add All Employees", self)
        self.add_all_button.clicked.connect(self.add_all_employees)
        self.add_all_button.setStyleSheet("background-color: purple; color: white;")
        self.sidebar_layout.addWidget(self.add_all_button)

        # Participants list
        self.participants_list = QListWidget(self)
        self.sidebar_layout.addWidget(self.participants_list)

        # Timer display label
        self.timer_label = QLabel("Time Elapsed: 00:00:00:000", self)
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sidebar_layout.addWidget(self.timer_label)

        # Meeting Start button (Blue when active, Grey when inactive)
        self.start_button = QPushButton("Meeting Start", self)
        self.start_button.clicked.connect(self.start_meeting)
        self.start_button.setStyleSheet("background-color: blue; color: white;")
        self.sidebar_layout.addWidget(self.start_button)

        # End Meeting button (Grey initially, Blue when active)
        self.end_button = QPushButton("End Meeting", self)
        self.end_button.clicked.connect(self.end_meeting)
        self.end_button.setEnabled(False)
        self.end_button.setStyleSheet("background-color: grey; color: white;")
        self.sidebar_layout.addWidget(self.end_button)

        # Meeting duration label
        self.duration_label = QLabel("", self)
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sidebar_layout.addWidget(self.duration_label)

        # Meeting cost label
        self.cost_label = QLabel("Meeting Cost: $0.00", self)
        self.cost_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cost_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.sidebar_layout.addWidget(self.cost_label)

        # Submit Note button (Yellow, below cost label)
        self.submit_note_button = QPushButton("Submit Note", self)
        self.submit_note_button.clicked.connect(self.submit_note)
        self.submit_note_button.setStyleSheet("background-color: yellow; color: black; font-weight: bold;")
        self.sidebar_layout.addWidget(self.submit_note_button)

        # Add stretch to push controls to top
        self.sidebar_layout.addStretch()

        # Add sidebar to top layout
        self.top_layout.addWidget(self.sidebar)

        # Create the graphics view and scene
        self.view = QGraphicsView(self)
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        self.view.setMinimumSize(600, 400)
        self.view.setMaximumHeight(400)

        # Enable mouse tracking for click events
        self.view.setMouseTracking(True)
        self.view.viewport().installEventFilter(self)

        # Add view to top layout
        self.top_layout.addWidget(self.view)

        # Reset button (top right in top_layout)
        self.reset_button = QPushButton("Reset Meeting", self)
        self.reset_button.clicked.connect(self.reset_meeting)
        self.reset_button.setStyleSheet("background-color: orange; color: black;")
        self.top_layout.addWidget(self.reset_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        # Add top layout to main layout
        self.main_layout.addLayout(self.top_layout)

        # Notes section
        self.notes_widget = QWidget(self)
        self.notes_layout = QHBoxLayout(self.notes_widget)

        self.notes_input = QTextEdit(self)
        self.notes_input.setPlaceholderText("Enter meeting notes here...")
        self.notes_input.setMaximumHeight(100)
        self.notes_layout.addWidget(self.notes_input)

        self.main_layout.addWidget(self.notes_widget)

        # Load the SVG
        self.svg_renderer = QSvgRenderer("G:\\expo\\Software\\TimeIsMoney\\TimeIsMoney\\icons\\table.svg")
        if not self.svg_renderer.isValid():
            print("Error: Could not load SVG file. Check the file path.")
            return

        # Render SVG to pixmap
        svg_size = self.svg_renderer.defaultSize()
        pixmap = QPixmap(svg_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        self.svg_renderer.render(painter)
        painter.end()

        # Add pixmap to scene
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)

        # Set scene rect
        self.scene.setSceneRect(QRectF(0, 0, svg_size.width(), svg_size.height()))

        # Timer setup
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.start_time = None
        self.elapsed_ms = 0
        self.total_hourly_rate = 0.0  # Current hourly rate for active participants
        self.incurred_cost = 0.0  # Accumulated cost from past participation
        self.participant_events = []
        self.meeting_start_str = ""
        self.meeting_notes = []
        self.participant_times = {}  # Tracks join times for cost calculation

        # Store employee data for menu and search
        self.employee_data = self.get_employees()

    def show_participant_menu(self):
        menu = QMenu(self)
        departments = {
            "OFFICE": QMenu("Office", self),
            "DRIVER": QMenu("Driver", self),
            "TABLETOP": QMenu("Tabletop", self),
            "PARTY_RENTAL": QMenu("Party Rental", self),
            "DISPATCH": QMenu("Dispatch", self),
            "WAREHOUSE": QMenu("Warehouse", self),
            "EXECUTIVE": QMenu("Executive", self),
            "SALES": QMenu("Sales", self),
            "CREATIVE": QMenu("Creative", self),
            "AUDIO_VISUAL": QMenu("Audio Visual", self),
            "TRADE_SHOW": QMenu("Trade Show", self)
        }

        for employee in self.employee_data:
            name, _, department, _, _, _ = employee
            if department in departments:
                action = QAction(name, self)
                action.triggered.connect(lambda checked, n=name: self.add_participant_from_menu(n))
                departments[department].addAction(action)

        for dept, submenu in departments.items():
            if not submenu.isEmpty():
                menu.addMenu(submenu)

        menu.exec(self.add_participant_button.mapToGlobal(self.add_participant_button.rect().bottomLeft()))

    def add_participant_from_menu(self, name):
        if name not in [self.participants_list.item(i).text() for i in range(self.participants_list.count())]:
            self.participants_list.addItem(name)
            self.cursor.execute("SELECT working_wage FROM Employees WHERE name = ?", (name,))
            wage = self.cursor.fetchone()[0]
            self.total_hourly_rate += wage
            print(f"EASTER EGG: {name} joined the money-making party via menu!")
            if self.timer.isActive():
                event_time = datetime.fromtimestamp((self.start_time + self.elapsed_ms) / 1000).strftime(
                    '%I:%M%p').lower()
                minutes_elapsed = self.elapsed_ms // (1000 * 60)
                self.participant_events.append(
                    f"{name} joined @ {event_time}; {minutes_elapsed} minutes after the meeting start ({self.meeting_start_str})"
                )
                self.participant_times[name] = self.elapsed_ms  # Record join time

    def update_search_results(self, text):
        self.search_results.clear()
        if text:
            matches = [emp[0] for emp in self.employee_data if text.lower() in emp[0].lower()]
            for name in matches:
                self.search_results.addItem(name)
        else:
            self.search_results.clear()

    def add_participant_from_search(self, item):
        name = item.text()
        if name not in [self.participants_list.item(i).text() for i in range(self.participants_list.count())]:
            self.participants_list.addItem(name)
            self.cursor.execute("SELECT working_wage FROM Employees WHERE name = ?", (name,))
            wage = self.cursor.fetchone()[0]
            self.total_hourly_rate += wage
            print(f"EASTER EGG: {name} joined the money-making party via search!")
            if self.timer.isActive():
                event_time = datetime.fromtimestamp((self.start_time + self.elapsed_ms) / 1000).strftime(
                    '%I:%M%p').lower()
                minutes_elapsed = self.elapsed_ms // (1000 * 60)
                self.participant_events.append(
                    f"{name} joined @ {event_time}; {minutes_elapsed} minutes after the meeting start ({self.meeting_start_str})"
                )
                self.participant_times[name] = self.elapsed_ms  # Record join time

    def remove_participant(self):
        selected_items = self.participants_list.selectedItems()
        if not selected_items:
            print("DEBUG: No participant selected for removal.")
            return
        selected_name = selected_items[0].text()
        self.participants_list.takeItem(self.participants_list.row(selected_items[0]))

        self.cursor.execute("SELECT working_wage FROM Employees WHERE name = ?", (selected_name,))
        wage = self.cursor.fetchone()[0]
        print(f"DEBUG: Removing {selected_name} with hourly wage ${wage}")

        # Calculate cost incurred by this participant before removal
        if self.timer.isActive() and selected_name in self.participant_times:
            time_in_meeting_ms = self.elapsed_ms - self.participant_times[selected_name]
            cost_incurred = wage * (time_in_meeting_ms / 3600000.0)  # Convert ms to hours
            self.incurred_cost += cost_incurred
            print(
                f"DEBUG: {selected_name} was in meeting for {time_in_meeting_ms}ms, incurred cost: ${cost_incurred:.2f}")
            del self.participant_times[selected_name]  # Remove from tracking

        # Reduce total_hourly_rate for future cost calculation
        self.total_hourly_rate -= wage
        print(
            f"DEBUG: New total hourly rate: ${self.total_hourly_rate}, Incurred cost so far: ${self.incurred_cost:.2f}")

        print(f"EASTER EGG: {selected_name} has left the money-making party!")
        if self.timer.isActive():
            event_time = datetime.fromtimestamp((self.start_time + self.elapsed_ms) / 1000).strftime('%I:%M%p').lower()
            minutes_elapsed = self.elapsed_ms // (1000 * 60)
            self.participant_events.append(
                f"{selected_name} left @ {event_time}; {minutes_elapsed} minutes after the meeting start ({self.meeting_start_str})"
            )
            total_cost = self.incurred_cost + (self.total_hourly_rate * (self.elapsed_ms / 3600000.0))
            self.cost_label.setText(f"Meeting Cost: ${total_cost:.2f}")
            print(f"DEBUG: Updated total cost after removal: ${total_cost:.2f}")

    def add_all_employees(self):
        employees = self.get_employees()
        current_participants = [self.participants_list.item(i).text() for i in range(self.participants_list.count())]

        for employee in employees:
            name, wage = employee[0], employee[1]
            if name not in current_participants:
                self.participants_list.addItem(name)
                self.total_hourly_rate += wage
                print(f"EASTER EGG: {name} joined the company-wide cash bash!")
                if self.timer.isActive():
                    event_time = datetime.fromtimestamp((self.start_time + self.elapsed_ms) / 1000).strftime(
                        '%I:%M%p').lower()
                    minutes_elapsed = self.elapsed_ms // (1000 * 60)
                    self.participant_events.append(
                        f"{name} joined @ {event_time}; {minutes_elapsed} minutes after the meeting start ({self.meeting_start_str})"
                    )
                    self.participant_times[name] = self.elapsed_ms  # Record join time

        if self.timer.isActive():
            total_cost = self.incurred_cost + (self.total_hourly_rate * (self.elapsed_ms / 3600000.0))
            self.cost_label.setText(f"Meeting Cost: ${total_cost:.2f}")

    def submit_note(self):
        note_text = self.notes_input.toPlainText().strip()
        if note_text:
            timestamp = datetime.now().strftime('%I:%M%p').lower()
            self.meeting_notes.append(f"{timestamp}: {note_text}")
            self.notes_input.clear()
            print(f"EASTER EGG: Note added at {timestamp}—keeping the minutes spicy!")

    def showEvent(self, event):
        super().showEvent(event)
        self.fit_svg_to_window()

    def fit_svg_to_window(self):
        if self.svg_renderer.isValid():
            svg_size = self.svg_renderer.defaultSize()
            self.view.fitInView(QRectF(0, 0, svg_size.width(), svg_size.height()), Qt.AspectRatioMode.KeepAspectRatio)

    def start_meeting(self):
        if self.participants_list.count() == 0:
            QMessageBox.warning(self, "No Participants", "MEETINGS ARE FOR PEOPLE")
            return

        if not self.timer.isActive():
            import time
            self.start_time = int(time.time() * 1000)
            self.meeting_start_str = datetime.fromtimestamp(self.start_time / 1000).strftime('%I:%M%p').lower()
            self.timer.start(10)
            self.start_button.setText("Meeting Started")
            self.start_button.setEnabled(False)
            self.start_button.setStyleSheet("background-color: grey; color: white;")
            self.end_button.setEnabled(True)
            self.end_button.setStyleSheet("background-color: blue; color: white;")
            self.duration_label.setText("")
            self.cost_label.setText("Meeting Cost: $0.00")
            self.participant_events = []
            self.meeting_notes = []
            self.incurred_cost = 0.0
            self.participant_times = {}
            print("EASTER EGG: Meeting initiated! Time to make some money, honey!")

    def end_meeting(self):
        if self.timer.isActive():
            self.timer.stop()
            self.end_button.setEnabled(False)
            self.end_button.setStyleSheet("background-color: grey; color: white;")
            self.start_button.setEnabled(True)
            self.start_button.setStyleSheet("background-color: blue; color: white;")
            self.start_button.setText("Meeting Start")
            duration_str = self.format_time(self.elapsed_ms)
            self.duration_label.setText(f"Meeting Duration: {duration_str}")
            total_cost = self.incurred_cost + (self.total_hourly_rate * (self.elapsed_ms / 3600000.0))
            self.cost_label.setText(f"Meeting Cost: ${total_cost:.2f}")
            print(f"EASTER EGG: Meeting over! Time banked: {duration_str}. Cash it in!")
            self.save_meeting_data(self.participants_list, duration_str, total_cost)

    def save_meeting_data(self, participants, duration, cost):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = os.path.join("G:\\expo\\Software\\TimeIsMoney\\TimeIsMoney", "session logs")
        html_dir = os.path.join(log_dir, "HTML")
        xml_dir = os.path.join(log_dir, "XML")
        os.makedirs(html_dir, exist_ok=True)
        os.makedirs(xml_dir, exist_ok=True)

        # HTML Export
        html_filename = os.path.join(html_dir, f"meeting_log_{timestamp}.html")
        participants_list = [self.participants_list.item(i).text() for i in range(self.participants_list.count())]

        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Meeting Log</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1, h2 { color: #333; }
                .summary { margin-bottom: 20px; }
                .event, .note { margin: 5px 0; }
                .swatch { display: inline-block; width: 15px; height: 15px; margin-right: 10px; vertical-align: middle; }
                .join { background-color: red; }
                .leave { background-color: green; }
                .note { color: blue; }
            </style>
        </head>
        <body>
            <h1>Meeting Summary</h1>
            <div class="summary">
        """
        html_content += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>"
        html_content += f"Participants (at end): {', '.join(participants_list)}<br>"
        html_content += f"Duration: {duration}<br>"
        html_content += f"Total Cost: ${cost:.2f}<br>"
        html_content += "</div><h2>Participant Events</h2>"

        if self.participant_events:
            for event in self.participant_events:
                if "joined" in event:
                    swatch_class = "join"
                elif "left" in event:
                    swatch_class = "leave"
                else:
                    swatch_class = ""
                html_content += f'<div class="event"><span class="swatch {swatch_class}"></span>{event}</div>'
        else:
            html_content += '<div class="event">No participant changes during the meeting.</div>'

        html_content += "<h2>Meeting Notes</h2>"
        if self.meeting_notes:
            for note in self.meeting_notes:
                html_content += f'<div class="note">{note}</div>'
        else:
            html_content += '<div class="note">No notes recorded during the meeting.</div>'

        html_content += """
        </body>
        </html>
        """

        with open(html_filename, "w") as f:
            f.write(html_content)

        # XML Export
        xml_filename = os.path.join(xml_dir, f"meeting_log_{timestamp}.xml")
        root = ET.Element("MeetingLog")

        summary = ET.SubElement(root, "Summary")
        ET.SubElement(summary, "Date").text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ET.SubElement(summary, "Participants").text = ','.join(participants_list)
        ET.SubElement(summary, "Duration").text = duration
        ET.SubElement(summary, "TotalCost").text = f"{cost:.2f}"

        events = ET.SubElement(root, "ParticipantEvents")
        if self.participant_events:
            for event in self.participant_events:
                event_elem = ET.SubElement(events, "Event")
                if "joined" in event:
                    event_elem.set("type", "join")
                elif "left" in event:
                    event_elem.set("type", "leave")
                event_elem.text = event
        else:
            ET.SubElement(events, "Event").text = "No participant changes during the meeting."

        notes = ET.SubElement(root, "MeetingNotes")
        if self.meeting_notes:
            for note in self.meeting_notes:
                timestamp, note_text = note.split(": ", 1)
                note_elem = ET.SubElement(notes, "Note")
                note_elem.set("timestamp", timestamp)
                note_elem.text = note_text
        else:
            ET.SubElement(notes, "Note").text = "No notes recorded during the meeting."

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(xml_filename, encoding="utf-8", xml_declaration=True)

        print(
            f"EASTER EGG: Meeting data saved to {html_filename} (HTML) and {xml_filename} (XML)! Blue notes and metadata galore!")

    def reset_meeting(self):
        if self.timer.isActive():
            self.timer.stop()
        self.participants_list.clear()
        self.total_hourly_rate = 0.0
        self.incurred_cost = 0.0
        self.elapsed_ms = 0
        self.participant_events = []
        self.meeting_notes = []
        self.participant_times = {}
        self.notes_input.clear()
        self.timer_label.setText("Time Elapsed: 00:00:00:000")
        self.duration_label.setText("")
        self.cost_label.setText("Meeting Cost: $0.00")
        self.start_button.setText("Meeting Start")
        self.start_button.setEnabled(True)
        self.start_button.setStyleSheet("background-color: blue; color: white;")
        self.end_button.setEnabled(False)
        self.end_button.setStyleSheet("background-color: grey; color: white;")
        print("EASTER EGG: Resetting the money clock—cha-ching!")

    def update_timer(self):
        import time
        current_time = int(time.time() * 1000)
        self.elapsed_ms = current_time - self.start_time
        time_str = self.format_time(self.elapsed_ms)
        self.timer_label.setText(f"Time Elapsed: {time_str}")
        total_cost = self.incurred_cost + (self.total_hourly_rate * (self.elapsed_ms / 3600000.0))
        self.cost_label.setText(f"Meeting Cost: ${total_cost:.2f}")
        if self.elapsed_ms % 10000 < 10:
            print("EASTER EGG: Tick-tock! Time’s money, and you’re racking it up!")

    def format_time(self, milliseconds):
        hours = milliseconds // (1000 * 60 * 60)
        minutes = (milliseconds // (1000 * 60)) % 60
        seconds = (milliseconds // 1000) % 60
        ms = milliseconds % 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{ms:03d}"

    def get_employees(self):
        self.cursor.execute(
            "SELECT name, working_wage, department, cost_center, worksite_assignment, has_benefits FROM Employees")
        return self.cursor.fetchall()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.handle_left_click(event.pos())
        elif event.button() == Qt.MouseButton.RightButton:
            self.handle_right_click(event.pos())

    def handle_left_click(self, pos):
        print(f"Left click at {pos}")

    def handle_right_click(self, pos):
        print(f"Right click at {pos}")

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    window = TimeIsMoney()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()