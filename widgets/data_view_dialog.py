from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QFileDialog, QMessageBox, QComboBox, QLabel, QWidget, QSplitter
from PySide6.QtCore import Qt
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure

class DataViewDialog(QDialog):
    def __init__(self, parent, buffer_name, data_frames):
        super().__init__(parent)
        self.setWindowTitle(f"Data for {buffer_name}")
        self.resize(700, 400)
        self.buffer_name = buffer_name
        self.data_frames = data_frames
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        splitter = QSplitter()
        # Left: Table
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        if self.data_frames:
            headers = list(self.data_frames[0].keys())
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            self.table.setRowCount(len(self.data_frames))
            for row, entry in enumerate(self.data_frames):
                for col, key in enumerate(headers):
                    self.table.setItem(row, col, QTableWidgetItem(str(entry[key])))
        left_layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save in GUI")
        self.export_btn = QPushButton("Export as Excel")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.export_btn)
        left_layout.addLayout(btn_layout)
        left_widget.setLayout(left_layout)

        # Right: Plot controls and plot area
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        # Controls (top)
        controls_layout = QHBoxLayout()
        self.x_label = QLabel("X axis:")
        self.x_combo = QComboBox()
        self.y_label = QLabel("Y axis:")
        from PySide6.QtWidgets import QListWidget, QListWidgetItem, QLineEdit, QFormLayout, QGroupBox
        self.y_list = QListWidget()
        self.y_list.setMaximumHeight(120)
        # Add scale factor inputs for each Y column
        self.scale_inputs = {}  # key: column name, value: QLineEdit
        self.scale_group = QGroupBox("Y Column Scale Factors")
        self.scale_form = QFormLayout()
        self.scale_group.setLayout(self.scale_form)
        self.plot_btn = QPushButton("Plot")
        controls_layout.addWidget(self.x_label)
        controls_layout.addWidget(self.x_combo)
        controls_layout.addWidget(self.y_label)
        controls_layout.addWidget(self.y_list)
        controls_layout.addWidget(self.scale_group)
        controls_layout.addWidget(self.plot_btn)
        right_layout.addLayout(controls_layout)
        # Plot area (bottom)
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)
        # Add matplotlib navigation toolbar below the plot
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        right_layout.addWidget(self.toolbar)
        right_widget.setLayout(right_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([350, 350])
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # Fill combo boxes
        if self.data_frames:
            df = pd.DataFrame(self.data_frames)
            headers = list(df.columns)
            self.x_combo.addItems(headers)
            for h in headers:
                item = QListWidgetItem(h)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.y_list.addItem(item)
                # Add scale input for each Y column
                scale_input = QLineEdit()
                scale_input.setPlaceholderText("Scale (default 1.0)")
                scale_input.setText("1.0")
                self.scale_inputs[h] = scale_input
                self.scale_form.addRow(h, scale_input)

        self.save_btn.clicked.connect(self.save_in_gui)
        self.export_btn.clicked.connect(self.export_excel)
        self.plot_btn.clicked.connect(self.plot_data)
    def plot_data(self):
        if not self.data_frames:
            QMessageBox.warning(self, "No Data", "No data to plot.")
            return
        df = pd.DataFrame(self.data_frames)
        x_col = self.x_combo.currentText()
        checked_y_items = [self.y_list.item(i).text() for i in range(self.y_list.count()) if self.y_list.item(i).checkState() == Qt.Checked]
        if not x_col or not checked_y_items:
            QMessageBox.warning(self, "Select Columns", "Please select X and at least one Y column.")
            return
        try:
            x = df[x_col]
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            colors = [
                'b', 'g', 'r', 'c', 'm', 'y', 'k',
                '#e377c2', '#8c564b', '#9467bd', '#2ca02c', '#d62728', '#ff7f0e', '#1f77b4'
            ]
            for idx, y_col in enumerate(checked_y_items):
                y = df[y_col]
                # Get scale factor from input, default to 1.0 if invalid
                try:
                    scale = float(self.scale_inputs[y_col].text())
                except Exception:
                    scale = 1.0
                y_scaled = y * scale
                color = colors[idx % len(colors)]
                ax.plot(x, y_scaled, marker='o', label=f"{y_col} (x{scale})" if scale != 1.0 else y_col, color=color)
            ax.set_xlabel(x_col)
            ax.set_ylabel("Y")
            ax.set_title(f"Multiple Y vs {x_col}")
            ax.grid(True)
            ax.legend()
            self.figure.tight_layout()
            self.canvas.draw()
        except Exception as e:
            QMessageBox.warning(self, "Plot Error", f"Failed to plot: {e}")

    def save_in_gui(self):
        # Inform parent to save this data
        if hasattr(self.parent(), 'save_data_buffer'):
            self.parent().save_data_buffer(self.buffer_name, self.data_frames)
            QMessageBox.information(self, "Saved", "Data saved in GUI.")
        else:
            QMessageBox.warning(self, "Error", "Cannot save data in GUI.")

    def export_excel(self):
        if not self.data_frames:
            QMessageBox.warning(self, "No Data", "No data to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export as Excel", f"{self.buffer_name}.xlsx", "Excel Files (*.xlsx)")
        if path:
            df = pd.DataFrame(self.data_frames)
            try:
                df.to_excel(path, index=False)
                QMessageBox.information(self, "Exported", f"Data exported to {path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export: {e}")
