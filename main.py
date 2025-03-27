import sys
import sqlite3
import os
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QPushButton, \
    QLabel, QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QListWidget
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QFont


class TimeIsMoney(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TimeIsMoney")
        self.resize(800, 600)

        # Database connection
        self.db_path = "G:\\expo\\Software\\TimeIsMoney\\TimeIsMoney\\EmployeeData.db"
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # Main widget and horizontal layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Left sidebar (vertical layout for controls)
        self.sidebar = QWidget(self)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar.setMaximumWidth(200)

        # Employee selection dropdown
        self.employee_combo = QComboBox(self)
        self.load_employees()
        self.sidebar_layout.addWidget(self.employee_combo)

        # Add Participant button
        self.add_participant_button = QPushButton("Add Participant", self)
        self.add_participant_button.clicked.connect(self.add_participant)
        self.sidebar_layout.addWidget(self.add_participant_button)

        # Remove Participant button
        self.remove_participant_button = QPushButton("Remove Participant", self)
        self.remove_participant_button.clicked.connect(self.remove_participant)
        self.sidebar_layout.addWidget(self.remove_participant_button)

        # Add All Employees button
        self.add_all_button = QPushButton("Add All Employees", self)
        self.add_all_button.clicked.connect(self.add_all_employees)
        self.sidebar_layout.addWidget(self.add_all_button)

        # Participants list
        self.participants_list = QListWidget(self)
        self.sidebar_layout.addWidget(self.participants_list)

        # Timer display label
        self.timer_label = QLabel("Time Elapsed: 00:00:00:000", self)
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sidebar_layout.addWidget(self.timer_label)

        # Meeting Start button
        self.start_button = QPushButton("Meeting Start", self)
        self.start_button.clicked.connect(self.start_meeting)
        self.sidebar_layout.addWidget(self.start_button)

        # End Meeting button
        self.end_button = QPushButton("End Meeting", self)
        self.end_button.clicked.connect(self.end_meeting)
        self.end_button.setEnabled(False)
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

        # Add stretch to push controls to top
        self.sidebar_layout.addStretch()

        # Add sidebar to main layout
        self.main_layout.addWidget(self.sidebar)

        # Create the graphics view and scene
        self.view = QGraphicsView(self)
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        self.view.setMinimumSize(600, 600)

        # Enable mouse tracking for click events
        self.view.setMouseTracking(True)
        self.view.viewport().installEventFilter(self)

        # Add view to main layout
        self.main_layout.addWidget(self.view)

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
        self.total_hourly_rate = 0.0

    def load_employees(self):
        """Load employee names into the dropdown from the database (no wages shown)."""
        employees = self.get_employees()
        for employee in employees:
            name = employee[0]  # First column: name
            self.employee_combo.addItem(name, name)

    def add_participant(self):
        """Add selected employee to the participants list and update total hourly rate."""
        selected_name = self.employee_combo.currentData()
        if selected_name and selected_name not in [self.participants_list.item(i).text() for i in
                                                   range(self.participants_list.count())]:
            self.participants_list.addItem(selected_name)
            self.cursor.execute("SELECT working_wage FROM Employees WHERE name = ?", (selected_name,))
            wage = self.cursor.fetchone()[0]
            self.total_hourly_rate += wage
            print(f"EASTER EGG: {selected_name} joined the money-making party!")

    def remove_participant(self):
        """Remove the selected participant from the list and adjust the total hourly rate."""
        selected_items = self.participants_list.selectedItems()
        if not selected_items:
            return
        selected_name = selected_items[0].text()
        self.participants_list.takeItem(self.participants_list.row(selected_items[0]))
        self.cursor.execute("SELECT working_wage FROM Employees WHERE name = ?", (selected_name,))
        wage = self.cursor.fetchone()[0]
        self.total_hourly_rate -= wage
        print(f"EASTER EGG: {selected_name} has left the money-making party!")
        if self.timer.isActive():
            cost = self.total_hourly_rate * (self.elapsed_ms / 3600000.0)
            self.cost_label.setText(f"Meeting Cost: ${cost:.2f}")

    def add_all_employees(self):
        """Add all employees from the database to the participants list."""
        employees = self.get_employees()
        current_participants = [self.participants_list.item(i).text() for i in range(self.participants_list.count())]

        for employee in employees:
            name, wage = employee[0], employee[1]  # name and working_wage
            if name not in current_participants:
                self.participants_list.addItem(name)
                self.total_hourly_rate += wage
                print(f"EASTER EGG: {name} joined the company-wide cash bash!")

        if self.timer.isActive():
            cost = self.total_hourly_rate * (self.elapsed_ms / 3600000.0)
            self.cost_label.setText(f"Meeting Cost: ${cost:.2f}")

    def showEvent(self, event):
        super().showEvent(event)
        self.fit_svg_to_window()

    def fit_svg_to_window(self):
        if self.svg_renderer.isValid():
            svg_size = self.svg_renderer.defaultSize()
            self.view.fitInView(QRectF(0, 0, svg_size.width(), svg_size.height()), Qt.AspectRatioMode.KeepAspectRatio)

    def start_meeting(self):
        if not self.timer.isActive():
            import time
            self.start_time = int(time.time() * 1000)
            self.timer.start(10)
            self.start_button.setText("Meeting Started")
            self.start_button.setEnabled(False)
            self.end_button.setEnabled(True)
            self.duration_label.setText("")
            self.cost_label.setText("Meeting Cost: $0.00")
            print("EASTER EGG: Meeting initiated! Time to make some money, honey!")

    def end_meeting(self):
        if self.timer.isActive():
            self.timer.stop()
            self.end_button.setEnabled(False)
            self.start_button.setEnabled(True)
            self.start_button.setText("Meeting Start")
            duration_str = self.format_time(self.elapsed_ms)
            self.duration_label.setText(f"Meeting Duration: {duration_str}")
            cost = self.total_hourly_rate * (self.elapsed_ms / 3600000.0)
            self.cost_label.setText(f"Cost Estimate: ${cost:.2f}")
            print(f"EASTER EGG: Meeting over! Time banked: {duration_str}. Cash it in!")
            self.save_meeting_data(self.participants_list, duration_str, cost)

    def save_meeting_data(self, participants, duration, cost):
        """Save meeting data to a text file in the session logs folder with a timestamped name."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = os.path.join("G:\\expo\\Software\\TimeIsMoney\\TimeIsMoney", "session logs")
        os.makedirs(log_dir, exist_ok=True)
        filename = os.path.join(log_dir, f"meeting_log_{timestamp}.txt")
        participants_list = [self.participants_list.item(i).text() for i in range(self.participants_list.count())]
        with open(filename, "w") as f:
            f.write("Meeting Summary\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Participants: {', '.join(participants_list)}\n")
            f.write(f"Duration: {duration}\n")
            f.write(f"Cost Estimate before Benefits: ${cost:.2f}\n")
        print(f"EASTER EGG: Meeting data saved to {filename}! Cash it in later!")

    def update_timer(self):
        import time
        current_time = int(time.time() * 1000)
        self.elapsed_ms = current_time - self.start_time
        time_str = self.format_time(self.elapsed_ms)
        self.timer_label.setText(f"Time Elapsed: {time_str}")
        cost = self.total_hourly_rate * (self.elapsed_ms / 3600000.0)
        self.cost_label.setText(f"Meeting Cost: ${cost:.2f}")
        if self.elapsed_ms % 10000 < 10:
            print("EASTER EGG: Tick-tock! Time’s money, and you’re racking it up!")

    def format_time(self, milliseconds):
        hours = milliseconds // (1000 * 60 * 60)
        minutes = (milliseconds // (1000 * 60)) % 60
        seconds = (milliseconds // 1000) % 60
        ms = milliseconds % 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{ms:03d}"

    def get_employees(self):
        """Fetch all employees from the database."""
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