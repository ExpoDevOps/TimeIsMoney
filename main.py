import sys
import sqlite3
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QListWidget
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QPixmap, QPainter

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

    def load_employees(self):
        """Load employee names into the dropdown from the database (no wages)."""
        employees = self.get_employees()
        for name, wage in employees:
            self.employee_combo.addItem(name, name)  # Show only name, store name as data

    def add_participant(self):
        """Add selected employee to the participants list (name only)."""
        selected_name = self.employee_combo.currentData()  # Get the name (data)
        if selected_name and selected_name not in [self.participants_list.item(i).text() for i in range(self.participants_list.count())]:
            self.participants_list.addItem(selected_name)  # Add just the name
            # Fetch wage for Easter egg
            self.cursor.execute("SELECT working_wage FROM Employees WHERE name = ?", (selected_name,))
            wage = self.cursor.fetchone()[0]
            print(f"EASTER EGG: {selected_name} joined the money-making party!")

    def showEvent(self, event):
        """Scale the SVG to fit the window after it's shown."""
        super().showEvent(event)
        self.fit_svg_to_window()

    def fit_svg_to_window(self):
        """Scale and center the SVG to fit the view."""
        if self.svg_renderer.isValid():
            svg_size = self.svg_renderer.defaultSize()
            self.view.fitInView(
                QRectF(0, 0, svg_size.width(), svg_size.height()),
                Qt.AspectRatioMode.KeepAspectRatio
            )
            print(f"Viewport size: {self.view.viewport().size()}")
            print(f"Scene rect: {self.scene.sceneRect()}")

    def start_meeting(self):
        """Start the timer when the button is clicked."""
        if not self.timer.isActive():
            import time
            self.start_time = int(time.time() * 1000)
            self.timer.start(10)
            self.start_button.setText("Meeting Started")
            self.start_button.setEnabled(False)
            self.end_button.setEnabled(True)
            self.duration_label.setText("")
            print("EASTER EGG: Meeting initiated! Time to make some money, honey!")

    def end_meeting(self):
        """Stop the timer and display meeting duration."""
        if self.timer.isActive():
            self.timer.stop()
            self.end_button.setEnabled(False)
            self.start_button.setEnabled(True)
            self.start_button.setText("Meeting Start")
            duration_str = self.format_time(self.elapsed_ms)
            self.duration_label.setText(f"Meeting Duration: {duration_str}")
            print(f"EASTER EGG: Meeting over! Time banked: {duration_str}. Cash it in!")

    def update_timer(self):
        """Update the timer label with precise time."""
        import time
        current_time = int(time.time() * 1000)
        self.elapsed_ms = current_time - self.start_time
        time_str = self.format_time(self.elapsed_ms)
        self.timer_label.setText(f"Time Elapsed: {time_str}")
        if self.elapsed_ms % 10000 < 10:
            print("EASTER EGG: Tick-tock! Time’s money, and you’re racking it up!")

    def format_time(self, milliseconds):
        """Convert milliseconds to HH:MM:SS:ms format."""
        hours = milliseconds // (1000 * 60 * 60)
        minutes = (milliseconds // (1000 * 60)) % 60
        seconds = (milliseconds // 1000) % 60
        ms = milliseconds % 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{ms:03d}"

    def get_employees(self):
        """Fetch all employees from the database."""
        self.cursor.execute("SELECT name, working_wage FROM Employees")
        return self.cursor.fetchall()

    def mousePressEvent(self, event):
        """Handle mouse click events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.handle_left_click(event.pos())
        elif event.button() == Qt.MouseButton.RightButton:
            self.handle_right_click(event.pos())

    def handle_left_click(self, pos):
        """Placeholder for left-click functionality."""
        print(f"Left click at {pos}")

    def handle_right_click(self, pos):
        """Placeholder for right-click functionality."""
        print(f"Right click at {pos}")

    def closeEvent(self, event):
        """Close the database connection when the app closes."""
        self.conn.close()
        super().closeEvent(event)

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    window = TimeIsMoney()
    window.show()
    employees = window.get_employees()
    print("Employees in database:", employees)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()