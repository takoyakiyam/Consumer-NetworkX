import pandas as pd 
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtWidgets, QtGui, QtCore
import sys

# Load the dataset
data = pd.read_csv('shopping_behavior_updated.csv')

class AgeNet(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Customer Age Group Network Viewer")
        self.setGeometry(100, 100, 1000, 1000) 
        self.showFullScreen()

        # Set font for the application
        font = QtGui.QFont("Helvetica", 12)
        self.setFont(font)

        # Layout setup
        layout = QtWidgets.QVBoxLayout()

        # Filters layout
        filter_layout = QtWidgets.QGridLayout()

        # Product Category ComboBox
        self.category_label = QtWidgets.QLabel("Select Product Category:")
        self.category_label.setFont(QtGui.QFont("Helvetica", 14))
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItems(["All"] + sorted(data['Category'].unique()))
        self.category_combo.currentTextChanged.connect(self.update_product_names)
        self.category_combo.setFont(QtGui.QFont("Helvetica", 12))

        # Product Name ComboBox
        self.product_label = QtWidgets.QLabel("Select Product Name:")
        self.product_label.setFont(QtGui.QFont("Helvetica", 14))
        self.product_combo = QtWidgets.QComboBox()
        self.update_product_names()  # Initialize with all items
        self.product_combo.setFont(QtGui.QFont("Helvetica", 12))

        # Gender ComboBox
        self.gender_label = QtWidgets.QLabel("Select Gender:")
        self.gender_label.setFont(QtGui.QFont("Helvetica", 14))
        self.gender_combo = QtWidgets.QComboBox()
        self.gender_combo.addItems(["All", "Male", "Female"])
        self.gender_combo.setFont(QtGui.QFont("Helvetica", 12))

        # Payment Method ComboBox
        self.payment_label = QtWidgets.QLabel("Select Payment Method:")
        self.payment_label.setFont(QtGui.QFont("Helvetica", 14))
        self.payment_combo = QtWidgets.QComboBox()
        self.payment_combo.addItems(["All"] + sorted(data['Payment Method'].unique()))
        self.payment_combo.setFont(QtGui.QFont("Helvetica", 12))

        # Season ComboBox
        self.season_label = QtWidgets.QLabel("Select Season:")
        self.season_label.setFont(QtGui.QFont("Helvetica", 14))
        self.season_combo = QtWidgets.QComboBox()
        self.season_combo.addItems(["All"] + sorted(data['Season'].unique()))
        self.season_combo.setFont(QtGui.QFont("Helvetica", 12))

        # Button to generate network
        self.plot_button = QtWidgets.QPushButton("Generate Network")
        self.plot_button.setFont(QtGui.QFont("Helvetica", 14))
        self.plot_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.plot_button.clicked.connect(self.generate_network)

        # Add widgets to the filter layout
        filter_layout.addWidget(self.category_label, 0, 0)
        filter_layout.addWidget(self.category_combo, 0, 1)
        filter_layout.addWidget(self.product_label, 1, 0)
        filter_layout.addWidget(self.product_combo, 1, 1)
        filter_layout.addWidget(self.gender_label, 2, 0)
        filter_layout.addWidget(self.gender_combo, 2, 1)
        filter_layout.addWidget(self.payment_label, 3, 0)
        filter_layout.addWidget(self.payment_combo, 3, 1)
        filter_layout.addWidget(self.season_label, 4, 0)
        filter_layout.addWidget(self.season_combo, 4, 1)
        filter_layout.addWidget(self.plot_button, 5, 0, 1, 2)

        layout.addLayout(filter_layout)

        # Graph display area
        self.graph_canvas = FigureCanvas(plt.figure(figsize=(8, 6)))
        layout.addWidget(self.graph_canvas)

        # Summary statistics display
        self.stats_label = QtWidgets.QLabel("Graph Summary Statistics:")
        self.stats_label.setFont(QtGui.QFont("Helvetica", 14))  # Title font size remains the same
        self.stats_text = QtWidgets.QTextEdit()
        self.stats_text.setFont(QtGui.QFont("Helvetica", 16))  # Increased font size here
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #f0f0f0;
                border-radius: 5px;
                padding: 10px;
                font-size: 16px;  # Updated this to 16 for larger text
            }
        """)
        layout.addWidget(self.stats_label)
        layout.addWidget(self.stats_text)

        self.setLayout(layout)

    def update_product_names(self):
        """ Update product names based on selected category. """
        selected_category = self.category_combo.currentText()
        if selected_category == "All":
            products = sorted(data['Item Purchased'].unique())
        else:
            products = sorted(data[data['Category'] == selected_category]['Item Purchased'].unique())
        
        self.product_combo.clear()
        self.product_combo.addItems(products)

    def generate_network(self):
        """ Generate and display the network graph based on selected filters. """
        selected_product = self.product_combo.currentText()
        selected_category = self.category_combo.currentText()
        selected_gender = self.gender_combo.currentText()
        selected_payment = self.payment_combo.currentText()
        selected_season = self.season_combo.currentText()

        # Filter dataset based on selections
        filtered_data = data
        if selected_category != "All":
            filtered_data = filtered_data[filtered_data['Category'] == selected_category]
        if selected_gender != "All":
            filtered_data = filtered_data[filtered_data['Gender'] == selected_gender]
        if selected_payment != "All":
            filtered_data = filtered_data[filtered_data['Payment Method'] == selected_payment]
        if selected_season != "All":
            filtered_data = filtered_data[filtered_data['Season'] == selected_season]
        filtered_data = filtered_data[filtered_data['Item Purchased'] == selected_product]

        if filtered_data.empty:
            QtWidgets.QMessageBox.warning(self, "No Data", "No data available for the selected filters.")
        else:
            self.plot_product_age_network(filtered_data, selected_product, selected_category, selected_gender, selected_payment, selected_season)

    def plot_product_age_network(self, product_data, product_name, category, gender, payment, season):
        """ Create and display the network graph for age groups of a specific product. """
        # Clear previous graph
        self.graph_canvas.figure.clf()

        # Define age bins
        bins = [18, 25, 35, 45, 55, 65, 70]
        labels = ['18-24', '25-34', '35-44', '45-54', '55-64', '65-70']
        product_data['Age Group'] = pd.cut(product_data['Age'], bins=bins, labels=labels, right=False)

        # Count the number of purchases per age group
        age_group_counts = product_data['Age Group'].value_counts()

        # Create a NetworkX graph
        G = nx.Graph()
        G.add_node(product_name, color='lightblue', size=3000)

        # Add nodes and edges for each age group
        edge_weights = {}
        for age_group, count in age_group_counts.items():
            if count > 0:  # Exclude edges with weight 0
                G.add_node(age_group, color='orange', size=count * 200)
                G.add_edge(product_name, age_group, weight=count)
                edge_weights[age_group] = count

        # Check if edges were correctly assigned
        print(G.edges(data=True))  # Debugging line to check the edge data

        # Warn if there are no valid edges
        if not edge_weights:
            QtWidgets.QMessageBox.warning(self, "No Data", "No valid connections for the selected filters.")
            return

        # Define node colors and sizes
        node_colors = [nx.get_node_attributes(G, 'color')[node] for node in G.nodes()]
        node_sizes = [nx.get_node_attributes(G, 'size')[node] for node in G.nodes()]

        # Generate dynamic title
        title = f"Network for {product_name}"
        if category != "All":
            title += f" in {category} Category"
        if gender != "All":
            title += f" for {gender}s"
        if payment != "All":
            title += f" using {payment} Payment Method"
        if season != "All":
            title += f" in {season} Season"

        # Set the title on the plot
        ax = self.graph_canvas.figure.add_subplot(111)
        ax.set_title(title, fontsize=16, fontweight='bold')

        # Plot the network
        pos = nx.spring_layout(G)
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes)
        nx.draw_networkx_labels(G, pos, font_size=12)
        nx.draw_networkx_edges(G, pos, width=2, alpha=0.5, edge_color='gray')

        # Draw edge labels
        edge_labels = {(product_name, age_group): G[product_name][age_group]['weight'] for age_group in edge_weights.keys()}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='green', font_size=10, ax=ax)

        # Apply tight layout to prevent clipping
        self.graph_canvas.figure.tight_layout(pad=3.0)

        # Update summary statistics
        self.update_summary_statistics(G, edge_weights)

        # Draw the graph
        self.graph_canvas.draw()

    def update_summary_statistics(self, G, edge_weights):
        """ Update the summary statistics text box with graph details. """
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()

        # Determine age group with the most and least purchases based on edge weights
        most_purchases = max(edge_weights, key=edge_weights.get)
        least_purchases = min(edge_weights, key=edge_weights.get)

        stats = f"Total Nodes: {num_nodes}\n"
        stats += f"Total Edges: {num_edges}\n\n"
        stats += f"Age Group with Most Purchases: {most_purchases} ({edge_weights[most_purchases]} purchases)\n"
        stats += f"Age Group with Least Purchases: {least_purchases} ({edge_weights[least_purchases]} purchases)\n\n"

        self.stats_text.setText(stats)


# Run the application
app = QtWidgets.QApplication(sys.argv)
window = AgeNet()
window.show()
sys.exit(app.exec_())
