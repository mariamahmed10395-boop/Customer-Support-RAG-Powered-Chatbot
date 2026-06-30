import sys
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QComboBox, QLabel, QScrollArea, QFrame,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QIcon, QColor, QPalette

API_BASE = "http://localhost:8000"

# --- QSS Stylesheet ---
STYLESHEET = """
QMainWindow {
    background-color: #0a0a0f;
}
QWidget {
    color: #f0f0f5;
    font-family: "Segoe UI", "Inter", sans-serif;
}
QFrame#Header {
    background-color: transparent;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
QLabel#AppTitle {
    font-size: 24px;
    font-weight: bold;
    color: #818cf8;
}
QLabel#AppSubtitle {
    font-size: 12px;
    color: #6b7280;
    text-transform: uppercase;
    font-weight: bold;
}
QFrame#StatPill {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
}
QLabel#StatValue {
    font-size: 16px;
    font-weight: bold;
    color: #818cf8;
}
QLabel#StatLabel {
    font-size: 10px;
    color: #6b7280;
    text-transform: uppercase;
}
QLineEdit#SearchBar {
    background-color: rgba(18, 18, 30, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 10px 15px;
    font-size: 14px;
    color: #f0f0f5;
}
QLineEdit#SearchBar:focus {
    border: 1px solid #6366f1;
}
QPushButton#SearchButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #8b5cf6);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#SearchButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #818cf8, stop:1 #a78bfa);
}
QPushButton#SearchButton:pressed {
    background: #4f46e5;
}
QComboBox {
    background-color: rgba(18, 18, 30, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 5px 10px;
    color: #f0f0f5;
    font-size: 13px;
    min-width: 120px;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #12121a;
    border: 1px solid rgba(255, 255, 255, 0.1);
    selection-background-color: rgba(99, 102, 241, 0.3);
    color: #f0f0f5;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.1);
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.2);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
QFrame#ResultCard {
    background-color: rgba(18, 18, 30, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
}
QFrame#ResultCard:hover {
    background-color: rgba(25, 25, 42, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
QLabel#ResultCategory {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: bold;
    text-transform: uppercase;
}
QLabel#ResultIntent {
    background-color: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 10px;
    color: #818cf8;
}
QLabel#ResultScoreHigh {
    font-size: 18px;
    font-weight: bold;
    color: #34d399;
}
QLabel#ResultScoreMedium {
    font-size: 18px;
    font-weight: bold;
    color: #fbbf24;
}
QLabel#ResultScoreLow {
    font-size: 18px;
    font-weight: bold;
    color: #f87171;
}
QLabel#ResultQuestion {
    font-size: 15px;
    font-weight: bold;
    color: #f0f0f5;
}
QLabel#ResultAnswer {
    font-size: 13px;
    color: #9ca3af;
}
"""

# --- Category Colors ---
CATEGORY_COLORS = {
    'ORDER': '#6366f1',
    'ACCOUNT': '#8b5cf6',
    'REFUND': '#34d399',
    'PAYMENT': '#fbbf24',
    'DELIVERY': '#f97316',
    'SHIPPING': '#06b6d4',
    'CONTACT': '#ec4899',
    'INVOICE': '#14b8a6',
    'FEEDBACK': '#a78bfa',
    'SUBSCRIPTION': '#f472b6',
    'CANCEL': '#f87171',
}

def format_number(num):
    if num >= 1000:
        return f"{num/1000:.1f}k"
    return str(num)

# --- Workers ---

class InitWorker(QThread):
    stats_ready = Signal(dict)
    categories_ready = Signal(list)
    error = Signal(str)

    def run(self):
        try:
            # Fetch stats
            res_stats = requests.get(f"{API_BASE}/api/stats", timeout=5)
            if res_stats.status_code == 200:
                self.stats_ready.emit(res_stats.json())
            
            # Fetch categories
            res_cats = requests.get(f"{API_BASE}/api/categories", timeout=5)
            if res_cats.status_code == 200:
                self.categories_ready.emit(res_cats.json())
        except Exception as e:
            self.error.emit(str(e))


class SearchWorker(QThread):
    results_ready = Signal(dict)
    error = Signal(str)

    def __init__(self, query, category):
        super().__init__()
        self.query = query
        self.category = category

    def run(self):
        try:
            payload = {
                "query": self.query,
                "category": self.category,
                "top_k": 10
            }
            res = requests.post(f"{API_BASE}/api/search", json=payload, timeout=10)
            if res.status_code == 200:
                self.results_ready.emit(res.json())
            else:
                self.error.emit(f"Server error: {res.status_code}")
        except Exception as e:
            self.error.emit(str(e))

# --- Custom Widgets ---

class StatPill(QFrame):
    def __init__(self, label_text, value_text):
        super().__init__()
        self.setObjectName("StatPill")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(15, 10, 15, 10)
        
        self.value_label = QLabel(value_text)
        self.value_label.setObjectName("StatValue")
        self.value_label.setAlignment(Qt.AlignCenter)
        
        self.title_label = QLabel(label_text)
        self.title_label.setObjectName("StatLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)
        
    def set_value(self, value):
        self.value_label.setText(value)


class ResultCard(QFrame):
    def __init__(self, result):
        super().__init__()
        self.setObjectName("ResultCard")
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header Row: Category, Intent, Score
        header_layout = QHBoxLayout()
        
        cat_label = QLabel(result['category'])
        cat_label.setObjectName("ResultCategory")
        
        color = CATEGORY_COLORS.get(result['category'], '#6b7280')
        cat_label.setStyleSheet(f"color: {color};")
        
        intent_label = QLabel(result['intent'])
        intent_label.setObjectName("ResultIntent")
        
        header_layout.addWidget(cat_label)
        header_layout.addWidget(intent_label)
        header_layout.addStretch()
        
        score_val = result['similarity']
        score_label = QLabel(f"{int(score_val)}%")
        if score_val >= 70:
            score_label.setObjectName("ResultScoreHigh")
        elif score_val >= 40:
            score_label.setObjectName("ResultScoreMedium")
        else:
            score_label.setObjectName("ResultScoreLow")
        
        header_layout.addWidget(score_label)
        
        # Question
        q_label = QLabel(result['instruction'])
        q_label.setObjectName("ResultQuestion")
        q_label.setWordWrap(True)
        
        # Answer
        a_label = QLabel(result['response'])
        a_label.setObjectName("ResultAnswer")
        a_label.setWordWrap(True)
        
        layout.addLayout(header_layout)
        layout.addWidget(q_label)
        layout.addWidget(a_label)

# --- Main Window ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Customer Support RAG")
        self.resize(900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)
        
        self.setup_header()
        self.setup_search_area()
        self.setup_results_area()
        
        # Start init worker
        self.init_worker = InitWorker()
        self.init_worker.stats_ready.connect(self.on_stats_ready)
        self.init_worker.categories_ready.connect(self.on_categories_ready)
        self.init_worker.error.connect(self.on_init_error)
        self.init_worker.start()

    def setup_header(self):
        header_frame = QFrame()
        header_frame.setObjectName("Header")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        # Title
        title_layout = QVBoxLayout()
        app_title = QLabel("Customer Support RAG")
        app_title.setObjectName("AppTitle")
        app_subtitle = QLabel("Semantic Search Engine")
        app_subtitle.setObjectName("AppSubtitle")
        title_layout.addWidget(app_title)
        title_layout.addWidget(app_subtitle)
        
        # Stats
        self.stat_entries = StatPill("ENTRIES", "0")
        self.stat_categories = StatPill("CATEGORIES", "0")
        self.stat_intents = StatPill("INTENTS", "0")
        
        stats_layout = QHBoxLayout()
        stats_layout.addWidget(self.stat_entries)
        stats_layout.addWidget(self.stat_categories)
        stats_layout.addWidget(self.stat_intents)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addLayout(stats_layout)
        
        self.main_layout.addWidget(header_frame)

    def setup_search_area(self):
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchBar")
        self.search_input.setPlaceholderText("Ask a customer support question...")
        self.search_input.returnPressed.connect(self.perform_search)
        
        self.category_dropdown = QComboBox()
        self.category_dropdown.addItem("ALL")
        
        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("SearchButton")
        self.search_btn.clicked.connect(self.perform_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.category_dropdown)
        search_layout.addWidget(self.search_btn)
        
        self.main_layout.addLayout(search_layout)
        
        # Info bar
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        self.main_layout.addWidget(self.info_label)

    def setup_results_area(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignTop)
        self.results_layout.setSpacing(15)
        
        self.scroll_area.setWidget(self.results_container)
        self.main_layout.addWidget(self.scroll_area)
        
        self.show_empty_state("Type a question to search through the knowledge base.")

    def clear_results(self):
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def show_empty_state(self, message):
        self.clear_results()
        empty_label = QLabel(message)
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet("color: #6b7280; font-size: 16px; margin-top: 50px;")
        self.results_layout.addWidget(empty_label)

    def on_stats_ready(self, stats):
        self.stat_entries.set_value(format_number(stats.get('total_entries', 0)))
        self.stat_categories.set_value(format_number(stats.get('num_categories', 0)))
        self.stat_intents.set_value(format_number(stats.get('num_intents', 0)))

    def on_categories_ready(self, categories):
        self.category_dropdown.clear()
        self.category_dropdown.addItem("ALL")
        for cat in categories:
            self.category_dropdown.addItem(cat['name'])

    def on_init_error(self, err):
        self.info_label.setText(f"Failed to connect to backend: {err}")

    def perform_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
            
        category = self.category_dropdown.currentText()
        
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Searching...")
        self.clear_results()
        
        loading_label = QLabel("Loading results...")
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setStyleSheet("color: #818cf8; font-size: 14px; margin-top: 20px;")
        self.results_layout.addWidget(loading_label)
        
        self.search_worker = SearchWorker(query, category)
        self.search_worker.results_ready.connect(self.on_search_results)
        self.search_worker.error.connect(self.on_search_error)
        self.search_worker.start()

    def on_search_results(self, data):
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")
        self.clear_results()
        
        results = data.get('results', [])
        num_results = data.get('num_results', 0)
        time_ms = data.get('search_time_ms', 0)
        
        self.info_label.setText(f"Found {num_results} results in {time_ms}ms")
        
        if not results:
            self.show_empty_state("No results found. Try a different query.")
            return
            
        for res in results:
            card = ResultCard(res)
            self.results_layout.addWidget(card)

    def on_search_error(self, err):
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")
        self.clear_results()
        self.show_empty_state(f"Search failed: {err}")


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
