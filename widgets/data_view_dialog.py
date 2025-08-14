from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QHBoxLayout, QFileDialog, QMessageBox, 
                             QComboBox, QLabel, QWidget, QSplitter, QListWidget, 
                             QListWidgetItem, QLineEdit, QFormLayout, QGroupBox,
                             QScrollArea, QCheckBox, QSpinBox, QDoubleSpinBox)
from PySide6.QtCore import Qt
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure

class DataViewDialog(QDialog):
    def __init__(self, parent, buffer_name, data_frames):
        super().__init__(parent)
        self.setWindowTitle(f"Data for {buffer_name}")
        self.resize(1000, 600)  # Increased width for better layout
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
        
        # Controls (top) - More compact layout
        controls_widget = QWidget()
        controls_widget.setMaximumHeight(200)  # Limit height of controls
        controls_layout = QVBoxLayout()
        
        # First row: X-axis selection
        x_layout = QHBoxLayout()
        self.x_label = QLabel("X axis:")
        self.x_combo = QComboBox()
        self.x_combo.setMinimumWidth(120)
        x_layout.addWidget(self.x_label)
        x_layout.addWidget(self.x_combo)
        x_layout.addStretch()  # Push everything to the left
        controls_layout.addLayout(x_layout)
        
        # Second row: Y-axis selection and controls
        y_controls_layout = QHBoxLayout()
        
        # Y column selection (left side)
        y_selection_widget = QWidget()
        y_selection_layout = QVBoxLayout()
        y_selection_layout.setContentsMargins(0, 0, 0, 0)
        
        self.y_label = QLabel("Y columns:")
        y_selection_layout.addWidget(self.y_label)
        
        # Scrollable area for Y column checkboxes
        scroll_area = QScrollArea()
        scroll_area.setMaximumHeight(100)
        scroll_area.setMinimumWidth(150)
        scroll_area.setWidgetResizable(True)
        
        self.y_checkboxes_widget = QWidget()
        self.y_checkboxes_layout = QVBoxLayout()
        self.y_checkboxes_layout.setContentsMargins(5, 5, 5, 5)
        self.y_checkboxes_widget.setLayout(self.y_checkboxes_layout)
        scroll_area.setWidget(self.y_checkboxes_widget)
        
        y_selection_layout.addWidget(scroll_area)
        y_selection_widget.setLayout(y_selection_layout)
        y_controls_layout.addWidget(y_selection_widget)
        
        # Scale factors (right side) - More compact
        scale_widget = QWidget()
        scale_layout = QVBoxLayout()
        scale_layout.setContentsMargins(0, 0, 0, 0)
        
        scale_label = QLabel("Scale factors:")
        scale_layout.addWidget(scale_label)
        
        # Scrollable area for scale inputs
        scale_scroll = QScrollArea()
        scale_scroll.setMaximumHeight(100)
        scale_scroll.setMinimumWidth(200)
        scale_scroll.setWidgetResizable(True)
        
        self.scale_inputs_widget = QWidget()
        self.scale_inputs_layout = QFormLayout()
        self.scale_inputs_layout.setContentsMargins(5, 5, 5, 5)
        self.scale_inputs_widget.setLayout(self.scale_inputs_layout)
        scale_scroll.setWidget(self.scale_inputs_widget)
        
        scale_layout.addWidget(scale_scroll)
        scale_widget.setLayout(scale_layout)
        y_controls_layout.addWidget(scale_widget)
        
        # Plot button
        plot_layout = QVBoxLayout()
        plot_layout.addStretch()
        self.plot_btn = QPushButton("Plot")
        self.plot_btn.setMaximumWidth(80)
        self.plot_btn.setMaximumHeight(40)
        plot_layout.addWidget(self.plot_btn)
        plot_layout.addStretch()
        y_controls_layout.addLayout(plot_layout)
        
        controls_layout.addLayout(y_controls_layout)
        controls_widget.setLayout(controls_layout)
        right_layout.addWidget(controls_widget)
        
        # Plot area (bottom) - Now gets more space
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)
        
        # Add matplotlib navigation toolbar below the plot
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        right_layout.addWidget(self.toolbar)
        right_widget.setLayout(right_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 600])  # Give more space to the right side
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # Initialize controls with data
        self.y_checkboxes = {}
        self.scale_inputs = {}
        
        if self.data_frames:
            df = pd.DataFrame(self.data_frames)
            headers = list(df.columns)
            self.x_combo.addItems(headers)
            
            for h in headers:
                # Create checkbox for Y column selection
                checkbox = QCheckBox(h)
                self.y_checkboxes[h] = checkbox
                self.y_checkboxes_layout.addWidget(checkbox)
                
                # Create scale input with more compact widget
                scale_input = QDoubleSpinBox()
                scale_input.setRange(0.001, 1000.0)
                scale_input.setValue(1.0)
                scale_input.setDecimals(3)
                scale_input.setSingleStep(0.1)
                scale_input.setMaximumWidth(80)
                self.scale_inputs[h] = scale_input
                self.scale_inputs_layout.addRow(f"{h}:", scale_input)

        self.save_btn.clicked.connect(self.save_in_gui)
        self.export_btn.clicked.connect(self.export_excel)
        self.plot_btn.clicked.connect(self.plot_data)

    def plot_data(self):
        if not self.data_frames:
            QMessageBox.warning(self, "No Data", "No data to plot.")
            return
            
        df = pd.DataFrame(self.data_frames)
        x_col = self.x_combo.currentText()
        
        # Get checked Y columns
        checked_y_cols = [col for col, checkbox in self.y_checkboxes.items() 
                         if checkbox.isChecked()]
        
        if not x_col or not checked_y_cols:
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
            
            for idx, y_col in enumerate(checked_y_cols):
                y = df[y_col]
                # Get scale factor from spinbox
                scale = self.scale_inputs[y_col].value()
                y_scaled = y * scale
                color = colors[idx % len(colors)]
                label = f"{y_col} (×{scale})" if scale != 1.0 else y_col
                ax.plot(x, y_scaled, marker='o', label=label, color=color, linewidth=2, markersize=4)
                
            ax.set_xlabel(x_col)
            ax.set_ylabel("Y")
            ax.set_title(f"Multiple Y vs {x_col}")
            ax.grid(True, alpha=0.3)
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
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