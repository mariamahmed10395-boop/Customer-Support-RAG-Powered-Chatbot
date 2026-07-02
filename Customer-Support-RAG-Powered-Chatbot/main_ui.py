#!/usr/bin/env python3
"""
RAG-Powered Customer Support Chatbot Frontend
=============================================
A modern, dark-themed PySide6 Desktop GUI featuring:
1. Dual-Tab Layout (Knowledge Base Search & Interactive Chatbot).
2. WhatsApp-style messaging viewport with styled dynamic chat bubbles.
3. Multi-threaded background network calling via QThread to prevent GUI freezing.
4. Smooth workflow integration (Send search result context to active chat tab).
"""

import sys
import time
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QComboBox, QLabel, QScrollArea, QFrame,
    QSizePolicy, QTabWidget, QTextBrowser
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QTimer
from PySide6.QtGui import QFont, QIcon, QColor, QTextCursor

# Backend API Configuration
API_BASE = "http://localhost:8000"

# --- Curated QSS Stylesheet (Modern Dark Slate Theme) ---
STYLESHEET = """
QMainWindow {
    background-color: #0f172a; /* Slate 900 */
}

QWidget {
    color: #f1f5f9; /* Slate 100 */
    font-family: "Segoe UI", "Inter", -apple-system, sans-serif;
    font-size: 13px;
}

/* Tab View Customization */
QTabWidget::pane {
    border: 1px solid #1e293b; /* Slate 800 */
    background-color: #0f172a;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #1e293b;
    border: 1px solid #1e293b;
    border-bottom-color: transparent;
    color: #94a3b8; /* Slate 400 */
    padding: 12px 24px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: bold;
    font-size: 13px;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background-color: #0f172a;
    color: #38bdf8; /* Sky 400 Accent */
    border-bottom: 2px solid #0ea5e9; /* Sky 500 */
}

QTabBar::tab:hover:!selected {
    background-color: #334155; /* Slate 700 */
    color: #cbd5e1;
}

/* Input Fields styling */
QLineEdit {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    color: #f8fafc;
    padding: 10px 14px;
    selection-background-color: #0ea5e9;
}

QLineEdit:focus {
    border: 1px solid #38bdf8;
    background-color: #0f172a;
}

/* Primary Button Styling */
QPushButton {
    background-color: #0284c7; /* Sky 600 */
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #0ea5e9; /* Sky 500 */
}

QPushButton:pressed {
    background-color: #0369a1; /* Sky 700 */
}

QPushButton:disabled {
    background-color: #334155;
    color: #64748b;
}

/* Scrollbars */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #0f172a;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #334155;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

# --- Background Network Thread Workers ---

class SearchWorker(QThread):
    """
    Background worker that queries the FastAPI semantic search API.
    Utilizes local mock results fallback if the server is offline.
    """
    results_ready = Signal(dict)
    error = Signal(str)

    def __init__(self, query, category="ALL"):
        super().__init__()
        self.query = query
        self.category = category

    def run(self):
        payload = {
            "query": self.query,
            "category": self.category,
            "top_k": 5
        }
        try:
            # Attempt to hit local production API
            response = requests.post(f"{API_BASE}/api/search", json=payload, timeout=4)
            if response.status_code == 200:
                self.results_ready.emit(response.json())
                return
        except Exception:
            # Fallback to simulation mode if API is unreachable
            pass

        # Simulate network delay (Mock mode)
        time.sleep(1.2)
        
        # Structure mock payload matching API response
        mock_payload = {
            "query": self.query,
            "category_filter": self.category,
            "results": [
                {
                    "instruction": f"How do I request a refund for {self.query or 'my order'}?",
                    "response": "Refunds can be requested via your account dashboard under the active orders page. Once submitted, refunds are processed back to the original payment method within 5-7 business days.",
                    "category": "REFUND",
                    "intent": "request_refund",
                    "similarity": 95.8
                },
                {
                    "instruction": f"What is the shipping protocol for item containing {self.query or 'fragile goods'}?",
                    "response": "Standard shipping takes 3-5 business days. Express shipping is available for next-day delivery. All packages are insured and tracking info will be mailed immediately on dispatch.",
                    "category": "DELIVERY",
                    "intent": "shipping_info",
                    "similarity": 84.2
                },
                {
                    "instruction": f"How do I reset my password if I forgot it?",
                    "response": "Click on 'Forgot Password' on the login screen, enter your registered email account, and follow the reset link instructions sent to your inbox.",
                    "category": "ACCOUNT",
                    "intent": "password_reset",
                    "similarity": 71.5
                }
            ]
        }
        self.results_ready.emit(mock_payload)


class ChatWorker(QThread):
    """
    Background worker that handles the RAG LLM Chat API connection asynchronously.
    Emits a mock answer if backend service is unreachable.
    """
    response_ready = Signal(dict)
    error = Signal(str)

    def __init__(self, message, category="ALL"):
        super().__init__()
        self.message = message
        self.category = category

    def run(self):
        payload = {
            "query": self.message,
            "category": self.category,
            "top_k": 5
        }
        try:
            # Attempt to query the backend API chat route
            response = requests.post(f"{API_BASE}/api/chat", json=payload, timeout=8)
            if response.status_code == 200:
                self.response_ready.emit(response.json())
                return
        except Exception:
            # Fallback to simulated offline behavior
            pass

        # Network latency simulation
        time.sleep(2.0)

        # Mock fallback response
        mock_response = {
            "query": self.message,
            "response": f"I processed your query: '{self.message}' using RAG-grounding templates. (Backend server offline, running simulated QThread response mode).",
            "sources": [
                {
                    "instruction": "Dummy source query document description",
                    "response": "Underlying knowledge base data matched internally",
                    "similarity": 98.4
                }
            ]
        }
        self.response_ready.emit(mock_response)


# --- Custom Widgets ---

class ChatBubble(QWidget):
    """
    Custom Chat Bubble Widget aligning message text either to the Left (Bot)
    or to the Right (User) with modern bubble aesthetics.
    """
    def __init__(self, text, is_user=True):
        super().__init__()
        # Horizontal container layout to offset the bubble left/right
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)

        # Primary bubble frame wrapper
        self.bubble_frame = QFrame()
        self.bubble_frame.setObjectName("BubbleFrame")
        
        # Prevent bubble from filling the entire screen width
        self.bubble_frame.setMaximumWidth(580)
        
        # Internal bubble layout
        frame_layout = QVBoxLayout(self.bubble_frame)
        frame_layout.setContentsMargins(14, 10, 14, 10)
        frame_layout.setSpacing(4)

        # Sender Label
        sender_lbl = QLabel("YOU" if is_user else "SUPPORT BOT")
        sender_lbl.setStyleSheet("font-size: 9px; font-weight: bold; color: rgba(255, 255, 255, 0.4);")
        frame_layout.addWidget(sender_lbl)

        # Actual Message text using selectable text options
        message_lbl = QLabel(text)
        message_lbl.setWordWrap(True)
        message_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        message_lbl.setStyleSheet("font-size: 13px; color: #f8fafc;")
        frame_layout.addWidget(message_lbl)

        if is_user:
            # Aligned to Right: Add elastic stretch on the Left
            layout.addStretch()
            layout.addWidget(self.bubble_frame)
            
            # User Bubble: Teal/Dark Blue modern style
            self.bubble_frame.setStyleSheet("""
                QFrame#BubbleFrame {
                    background-color: #1e3a8a; /* Slate/Blue primary */
                    border: 1px solid #1d4ed8;
                    border-radius: 14px;
                    border-bottom-right-radius: 2px;
                }
            """)
        else:
            # Aligned to Left: Add elastic stretch on the Right
            layout.addWidget(self.bubble_frame)
            layout.addStretch()

            # Bot Bubble: Dark gray/slate style
            self.bubble_frame.setStyleSheet("""
                QFrame#BubbleFrame {
                    background-color: #1e293b; /* Slate 800 */
                    border: 1px solid #334155;
                    border-radius: 14px;
                    border-top-left-radius: 2px;
                }
            """)


class TypingIndicator(QWidget):
    """
    Displays a temporary 'Bot is typing...' widget in the chat window.
    """
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)

        self.bubble_frame = QFrame()
        self.bubble_frame.setObjectName("TypingFrame")
        self.bubble_frame.setMinimumWidth(160)
        self.bubble_frame.setMaximumWidth(200)

        frame_layout = QHBoxLayout(self.bubble_frame)
        frame_layout.setContentsMargins(14, 10, 14, 10)

        self.indicator_lbl = QLabel("Bot is typing...")
        self.indicator_lbl.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 12px;")
        frame_layout.addWidget(self.indicator_lbl)

        layout.addWidget(self.bubble_frame)
        layout.addStretch()

        self.bubble_frame.setStyleSheet("""
            QFrame#TypingFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 14px;
                border-top-left-radius: 2px;
            }
        """)


class ResultCard(QFrame):
    """
    Tab 1: Search Result display card.
    Contains category badge, similarity scoring, instruction title, content,
    and a button to bridge/transfer the query context into the chat tab.
    """
    send_to_chat_signal = Signal(str)

    def __init__(self, result):
        super().__init__()
        self.setObjectName("ResultCard")
        
        # Styles for individual card aesthetics
        self.setStyleSheet("""
            QFrame#ResultCard {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 16px;
            }
            QFrame#ResultCard:hover {
                background-color: #334155;
                border: 1px solid #38bdf8;
            }
            QLabel#CardTitle {
                font-size: 15px;
                font-weight: bold;
                color: #f8fafc;
            }
            QLabel#CardBody {
                font-size: 13px;
                color: #cbd5e1;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header: Category badge & Match Score
        header_layout = QHBoxLayout()
        
        category = result.get("category", "GENERAL").upper()
        cat_badge = QLabel(f" {category} ")
        cat_badge.setStyleSheet("""
            background-color: #0369a1; 
            color: #e0f2fe; 
            border-radius: 4px; 
            font-size: 10px; 
            font-weight: bold;
            padding: 2px;
        """)
        
        score = result.get("similarity", 0.0)
        score_lbl = QLabel(f"Confidence: {score:.1f}%")
        score_lbl.setStyleSheet("color: #4ade80; font-weight: bold; font-size: 11px;")

        header_layout.addWidget(cat_badge)
        header_layout.addStretch()
        header_layout.addWidget(score_lbl)
        layout.addLayout(header_layout)

        # Question/Instruction
        title_text = result.get("instruction", "No Title")
        title_lbl = QLabel(title_text)
        title_lbl.setObjectName("CardTitle")
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)

        # Response Content snippet
        body_text = result.get("response", "No response body content available.")
        body_lbl = QLabel(body_text)
        body_lbl.setObjectName("CardBody")
        body_lbl.setWordWrap(True)
        layout.addWidget(body_lbl)

        # Footer Button to copy text to chat input
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        send_btn = QPushButton("Send to Chat ➜")
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f172a;
                color: #38bdf8;
                border: 1px solid #334155;
                padding: 6px 12px;
                font-size: 11px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0ea5e9;
                color: white;
                border-color: #0ea5e9;
            }
        """)
        
        # Connect button click to emit the title/query
        send_btn.clicked.connect(lambda: self.send_to_chat_signal.emit(title_text))
        footer_layout.addWidget(send_btn)
        layout.addLayout(footer_layout)


# --- Main Window Container ---

class MainWindow(QMainWindow):
    """
    Main PySide6 Application Window.
    Implements a responsive Dual-Tab architecture.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Customer Support RAG Chatbot Client")
        self.resize(1000, 750)
        self.setMinimumSize(700, 500)

        # Reference to active typing indicator
        self.typing_indicator = None

        # Setup Tab Controller
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create Tab Screens
        self.setup_tab_search()
        self.setup_tab_chatbot()

        # Apply Global Styling
        self.setStyleSheet(STYLESHEET)

    # --- TAB 1: Knowledge Base Manual Search ---
    def setup_tab_search(self):
        search_tab = QWidget()
        layout = QVBoxLayout(search_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Page Header
        header_lbl = QLabel("Knowledge Base Semantic Search")
        header_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header_lbl)

        # Query Toolbar Layout
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter terms or question to search the vector index...")
        self.search_input.returnPressed.connect(self.trigger_search)
        toolbar_layout.addWidget(self.search_input)

        # Category selection box
        self.category_combo = QComboBox()
        self.category_combo.addItems(["ALL", "ACCOUNT", "REFUND", "DELIVERY", "ORDER", "CONTACT"])
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 10px;
                color: #f8fafc;
                min-width: 120px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                selection-background-color: #0ea5e9;
                color: #f8fafc;
            }
        """)
        toolbar_layout.addWidget(self.category_combo)

        self.search_btn = QPushButton("Search Vector Store")
        self.search_btn.clicked.connect(self.trigger_search)
        toolbar_layout.addWidget(self.search_btn)
        
        layout.addLayout(toolbar_layout)

        # Scroll viewport for resulting cards
        self.search_scroll = QScrollArea()
        self.search_scroll.setWidgetResizable(True)
        
        self.search_results_widget = QWidget()
        self.search_results_layout = QVBoxLayout(self.search_results_widget)
        self.search_results_layout.setAlignment(Qt.AlignTop)
        self.search_results_layout.setSpacing(12)
        
        self.search_scroll.setWidget(self.search_results_widget)
        layout.addWidget(self.search_scroll)

        # Populate with initial visual guide state
        self.show_search_placeholder("Type a question and click search to view retrieved context cards.")

        self.tabs.addTab(search_tab, "Knowledge Base Search")

    def show_search_placeholder(self, message):
        """Displays clear user guides inside the search layout."""
        self.clear_search_results()
        placeholder = QLabel(message)
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #64748b; font-size: 14px; margin-top: 100px;")
        self.search_results_layout.addWidget(placeholder)

    def clear_search_results(self):
        """Safely removes all result widgets from Tab 1 layout."""
        while self.search_results_layout.count():
            item = self.search_results_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def trigger_search(self):
        query = self.search_input.text().strip()
        if not query:
            self.show_search_placeholder("Please input a valid search query first.")
            return

        # Visual feedback during query execution
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Searching...")
        self.clear_search_results()

        loading_lbl = QLabel("Querying local vector store index...")
        loading_lbl.setAlignment(Qt.AlignCenter)
        loading_lbl.setStyleSheet("color: #38bdf8; font-size: 14px; margin-top: 100px;")
        self.search_results_layout.addWidget(loading_lbl)

        # Launch Async Thread to fetch matches
        category = self.category_combo.currentText()
        self.search_thread = SearchWorker(query, category)
        self.search_thread.results_ready.connect(self.on_search_completed)
        self.search_thread.start()

    def on_search_completed(self, data):
        # Reset UI controls
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search Vector Store")
        self.clear_search_results()

        results = data.get("results", [])
        if not results:
            self.show_search_placeholder("No matching documents found in the database store.")
            return

        # Construct result cards dynamically
        for res in results:
            card = ResultCard(res)
            # Connecting card's button signal directly to slot
            card.send_to_chat_signal.connect(self.handle_transfer_to_chat)
            self.search_results_layout.addWidget(card)

    def handle_transfer_to_chat(self, prompt_text):
        """
        Bridges the Search Tab with Chat Tab.
        Pastes prompt, switches tab focus, and prompts active input.
        """
        self.chat_input.setText(prompt_text)
        self.tabs.setCurrentIndex(1) # Switch tab to Interactive Chatbot
        self.chat_input.setFocus()

    # --- TAB 2: Interactive Chatbot viewport ---
    def setup_tab_chatbot(self):
        chat_tab = QWidget()
        layout = QVBoxLayout(chat_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header Info Row
        header_layout = QHBoxLayout()
        header_lbl = QLabel("Interactive RAG AI Chatbot")
        header_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        header_layout.addWidget(header_lbl)
        
        header_layout.addStretch()
        
        status_dot = QLabel("● Online")
        status_dot.setStyleSheet("color: #10b981; font-weight: bold; font-size: 12px;")
        header_layout.addWidget(status_dot)
        layout.addLayout(header_layout)

        # Scroll viewport showing chat messages
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        
        self.chat_viewport = QWidget()
        self.chat_viewport.setObjectName("ChatViewport")
        self.chat_viewport.setStyleSheet("background-color: #0b1329; border-radius: 8px; border: 1px solid #1e293b;")
        
        self.chat_layout = QVBoxLayout(self.chat_viewport)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(12)
        
        self.chat_scroll.setWidget(self.chat_viewport)
        layout.addWidget(self.chat_scroll)

        # Populate with welcome greeting bubble
        welcome_bubble = ChatBubble("Hello! I am your Customer Support Chatbot. Ask me anything about refund protocols, accounts, order tracking, or standard support policies.", is_user=False)
        self.chat_layout.addWidget(welcome_bubble)

        # Bottom Input Area
        input_container = QHBoxLayout()
        input_container.setSpacing(10)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your support question here and press enter...")
        self.chat_input.returnPressed.connect(self.trigger_chat_send)
        input_container.addWidget(self.chat_input)

        self.send_btn = QPushButton("Send Message")
        self.send_btn.clicked.connect(self.trigger_chat_send)
        input_container.addWidget(self.send_btn)

        layout.addLayout(input_container)
        self.tabs.addTab(chat_tab, "Interactive Chatbot")

    def trigger_chat_send(self):
        message = self.chat_input.text().strip()
        if not message:
            return

        # Append User Message Bubble
        user_bubble = ChatBubble(message, is_user=True)
        self.chat_layout.addWidget(user_bubble)
        self.chat_input.clear()

        # Add Typing Indicator
        self.typing_indicator = TypingIndicator()
        self.chat_layout.addWidget(self.typing_indicator)

        # Disable Controls
        self.chat_input.setEnabled(False)
        self.send_btn.setEnabled(False)

        # Scroll to bottom
        QTimer.singleShot(50, self.scroll_chat_to_bottom)

        # Trigger Async RAG Graph call
        self.chat_thread = ChatWorker(message)
        self.chat_thread.response_ready.connect(self.on_chat_response_completed)
        self.chat_thread.start()

    def on_chat_response_completed(self, data):
        # Remove Typing Indicator
        if self.typing_indicator:
            self.chat_layout.removeWidget(self.typing_indicator)
            self.typing_indicator.deleteLater()
            self.typing_indicator = None

        # Re-enable inputs
        self.chat_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.chat_input.setFocus()

        # Render Bot Response
        bot_response = data.get("response", "No answer generated.")
        bot_bubble = ChatBubble(bot_response, is_user=False)
        self.chat_layout.addWidget(bot_bubble)

        # Handle Source metadata displays if returned
        sources = data.get("sources", [])
        if sources:
            source_lbl = QLabel(f"Source Similarity: {sources[0].get('similarity', 0.0):.1f}% | Ref: {sources[0].get('instruction', 'KB document')}")
            source_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.35); font-size: 10px; margin-left: 24px; margin-top: -6px;")
            self.chat_layout.addWidget(source_lbl)

        # Scroll to bottom
        QTimer.singleShot(50, self.scroll_chat_to_bottom)

    def scroll_chat_to_bottom(self):
        """Smoothly resets viewport coordinates to bottom offset."""
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
#.