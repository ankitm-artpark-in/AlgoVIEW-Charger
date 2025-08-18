from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QHBoxLayout, QFileDialog, QMessageBox, 
                             QComboBox, QLabel, QWidget, QSplitter, QListWidget, 
                             QListWidgetItem, QLineEdit, QFormLayout, QGroupBox,
                             QScrollArea, QCheckBox, QSpinBox, QDoubleSpinBox)
from PySide6.QtCore import Qt
import pandas as pd
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure

class DataViewDialog(QDialog):
    def __init__(self, parent, buffer_name, data_frames):
        super().__init__(parent)
        self.setWindowTitle(f"Data for {buffer_name}")
        self.resize(1000, 600)  # Increased width for better layout
        self.buffer_name = buffer_name
        self.data_frames = data_frames
        
        # Initialize hover-related attributes
        self.hover_annotation = None
        self.plotted_lines = {}  # Store line objects with their data
        self.df = None  # Store the DataFrame for hover data access
        
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
        self.figure = Figure(figsize=(16, 12))
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
            self.df = pd.DataFrame(self.data_frames)
            headers = list(self.df.columns)
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
            
        self.df = pd.DataFrame(self.data_frames)
        x_col = self.x_combo.currentText()
        
        # Get checked Y columns
        checked_y_cols = [col for col, checkbox in self.y_checkboxes.items() 
                         if checkbox.isChecked()]
        
        if not x_col or not checked_y_cols:
            QMessageBox.warning(self, "Select Columns", "Please select X and at least one Y column.")
            return
            
        try:
            x = self.df[x_col]
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            colors = [
                'b', 'g', 'r', 'c', 'm', 'y', 'k',
                '#e377c2', '#8c564b', '#9467bd', '#2ca02c', '#d62728', '#ff7f0e', '#1f77b4'
            ]
            
            # Clear previous plot data
            self.plotted_lines.clear()
            
            for idx, y_col in enumerate(checked_y_cols):
                y = self.df[y_col]
                # Get scale factor from spinbox
                scale = self.scale_inputs[y_col].value()
                y_scaled = y * scale
                color = colors[idx % len(colors)]
                label = f"{y_col}" if scale != 1.0 else y_col
                
                # Plot the line and store reference with data
                line, = ax.plot(x, y_scaled, marker='o', label=label, color=color, 
                              linewidth=2, markersize=4)
                
                # Store line data for hover functionality
                self.plotted_lines[line] = {
                    'x_col': x_col,
                    'y_col': y_col,
                    'x_data': x.values,
                    'y_data': y.values,
                    'y_scaled': y_scaled.values,
                    'scale': scale,
                    'color': color
                }
                
            ax.set_xlabel(x_col)
            ax.set_ylabel("Y")
            ax.set_title(f"Multiple Y vs {x_col}")
            ax.grid(True, alpha=0.3)
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            self.figure.tight_layout()
            
            # Connect hover event
            self.canvas.mpl_connect('motion_notify_event', self.on_hover)
            self.canvas.draw()
            
        except Exception as e:
            QMessageBox.warning(self, "Plot Error", f"Failed to plot: {e}")

    def on_hover(self, event):
        """Handle mouse hover events on the plot"""
        if event.inaxes is None:
            return
            
        # Remove previous annotation if it exists
        if self.hover_annotation:
            self.hover_annotation.remove()
            self.hover_annotation = None
            
        # Find the closest data point across all plotted lines
        closest_point = None
        min_distance = float('inf')
        closest_line_info = None
        
        for line, line_data in self.plotted_lines.items():
            # Get the line's data
            x_data = line_data['x_data']
            y_data = line_data['y_scaled']
            
            # Convert data coordinates to display coordinates
            try:
                # Transform data points to display coordinates
                points = np.column_stack([x_data, y_data])
                transformed_points = event.inaxes.transData.transform(points)
                
                # Calculate distances from mouse position to all points
                mouse_pos = np.array([event.x, event.y])
                distances = np.sqrt(np.sum((transformed_points - mouse_pos)**2, axis=1))
                
                # Find the closest point on this line
                min_idx = np.argmin(distances)
                min_dist = distances[min_idx]
                
                # Check if this is the globally closest point
                if min_dist < min_distance and min_dist < 20:  # 20 pixel threshold
                    min_distance = min_dist
                    closest_point = {
                        'idx': min_idx,
                        'x': x_data[min_idx],
                        'y': y_data[min_idx],
                        'original_y': line_data['y_data'][min_idx]
                    }
                    closest_line_info = line_data
                    
            except Exception:
                continue
                
        # If we found a close point, show tooltip
        if closest_point and closest_line_info:
            self.show_hover_tooltip(event, closest_point, closest_line_info)
            self.canvas.draw_idle()
    
    def show_hover_tooltip(self, event, point, line_info):
        """Show tooltip with point information"""
        ax = event.inaxes
        
        # Create tooltip text with all relevant information
        x_val = point['x']
        y_val = point['original_y']  # Original unscaled value
        y_scaled = point['y']  # Scaled value for display
        
        # Get all data for this point index
        row_data = self.df.iloc[point['idx']]
        
        # Create comprehensive tooltip
        tooltip_lines = [
            f"{line_info['x_col']}: {x_val}",
            f"{line_info['y_col']}: {y_val}"
        ]
        
        if line_info['scale'] != 1.0:
            tooltip_lines.append(f"Scaled: {y_scaled:.3f}")
            
        # Add other relevant columns from the same row
        important_cols = ['rel_time', 'charge_voltage', 'charge_current', 'error_flags',
                         'set_c_rate1', 'set_c_rate2', 'max_volta_temp', 'avg_volta_temp']
        
        for col in important_cols:
            if col in row_data and col not in [line_info['x_col'], line_info['y_col']]:
                value = row_data[col]
                if pd.notna(value) and str(value) != '--':
                    tooltip_lines.append(f"{col}: {value}")
        
        tooltip_text = '\n'.join(tooltip_lines)
        
        # Create annotation
        self.hover_annotation = ax.annotate(
            tooltip_text,
            xy=(x_val, y_scaled),
            xytext=(10, 10),
            textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.9, edgecolor='black'),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='black'),
            fontsize=9,
            ha='left',
            va='bottom',
            zorder=1000  # Ensure tooltip appears on top
        )

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