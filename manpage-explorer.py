#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# ManPage Explorer
#
# A PyQt6-powered GUI for browsing, viewing, and searching Unix man pages.
# Features include:
#   - Section-organized man page tree with expandable categories
#   - Formatted man page display with live highlight search
#   - Navigation of multiple matches (next/prev + match counter)
#   - Keyboard shortcuts (Ctrl+F to jump to highlight search)
#   - Lightweight design, no external dependencies beyond PyQt6
#
# Designed and developed by Sean Lum, 2025.
# Refactored and cleaned up in collaboration with ChatGPT.
# -----------------------------------------------------------------------------

import sys
import os
import subprocess
import re

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QTextEdit,
    QLineEdit, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel
)
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor, QKeySequence, QShortcut
from PyQt6.QtCore import Qt


class ManPageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ManPage Explorer")

        self.search_matches = []
        self.current_match_index = -1

        self.init_ui()
        self.populate_tree(expand_all=False)

    def init_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Top search bar
        self.top_search = QLineEdit()
        self.top_search.setPlaceholderText("Search man page...")
        top_search_button = QPushButton("Search")
        self.top_search.textChanged.connect(self.filter_tree)
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addWidget(self.top_search)
        top_bar_layout.addWidget(top_search_button)
        top_search_bar = QWidget()
        top_search_bar.setLayout(top_bar_layout)
        top_search_bar.setMaximumHeight(40)
        layout.addWidget(top_search_bar)

        # Splitter: left = tree, right = man content + search
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Manual Sections")
        self.tree.itemClicked.connect(self.display_man)
        splitter.addWidget(self.tree)

        # Right pane: vertical layout of man text + search controls
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        right_splitter.addWidget(self.text_area)

        # Bottom search bar for highlight matches
        self.man_search_text = QLineEdit()
        self.man_search_text.setPlaceholderText("Search man page...")
        self.man_search_text.returnPressed.connect(self.highlight_matches)

        self.man_search_button = QPushButton("Search...")
        self.man_search_button.clicked.connect(self.highlight_matches)

        self.man_search_prev = QPushButton("◀ Prev")
        self.man_search_next = QPushButton("Next ▶")
        self.man_search_prev.clicked.connect(lambda: self.focus_match(self.current_match_index - 1))
        self.man_search_next.clicked.connect(lambda: self.focus_match(self.current_match_index + 1))

        self.match_label = QLabel("")

        search_bar_layout = QHBoxLayout()
        search_bar_layout.setContentsMargins(0, 0, 0, 0)
        search_bar_layout.addWidget(self.man_search_text)
        search_bar_layout.addWidget(self.man_search_button)
        search_bar_layout.addWidget(self.man_search_prev)
        search_bar_layout.addWidget(self.man_search_next)
        search_bar_layout.addWidget(self.match_label)

        search_bar_widget = QWidget()
        search_bar_widget.setLayout(search_bar_layout)
        search_bar_widget.setMaximumHeight(40)

        right_splitter.addWidget(search_bar_widget)
        right_splitter.setStretchFactor(0, 10)
        right_splitter.setStretchFactor(1, 1)

        splitter.addWidget(right_splitter)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)

        # Shortcut to focus highlight search bar
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.man_search_text.setFocus)

    def filter_tree(self, query):
        query = query.strip().lower()

        root = self.tree.topLevelItem(0)
        for i in range(root.childCount()):
            section_item = root.child(i)
            visible = False
            for j in range(section_item.childCount()):
                entry_item = section_item.child(j)
                entry_text = entry_item.text(0).lower()
                match = query in entry_text
                entry_item.setHidden(not match)
                visible = visible or match
            section_item.setHidden(not visible)

    def populate_tree(self, expand_all=False):
        self.tree.clear()
        root = QTreeWidgetItem(["Man Pages"])
        self.tree.addTopLevelItem(root)

        section_map = {}
        seen = set()
        manpaths = subprocess.run(["manpath"], stdout=subprocess.PIPE, text=True).stdout.strip().split(":")

        for path in manpaths:
            if not os.path.exists(path):
                continue
            for entry in sorted(os.listdir(path)):
                if entry.startswith("man") and os.path.isdir(os.path.join(path, entry)):
                    section = entry[3:]
                    full_path = os.path.join(path, entry)
                    try:
                        for file in sorted(os.listdir(full_path)):
                            if '.' not in file:
                                continue
                            name = file.split(".")[0]
                            if (name, section) in seen:
                                continue
                            seen.add((name, section))
                            section_map.setdefault(section, []).append(f"{name}.{section}")
                    except FileNotFoundError:
                        continue

        def section_sort_key(key):
            try:
                return (int(re.match(r'\d+', key).group()), key)
            except:
                return (999, key)

        for section in sorted(section_map.keys(), key=section_sort_key):
            section_node = QTreeWidgetItem([f"Section {section}"])
            root.addChild(section_node)

            for entry in sorted(section_map[section]):
                child = QTreeWidgetItem([entry])
                section_node.addChild(child)

            if expand_all:
                self.tree.expandItem(section_node)

        self.tree.expandItem(root)
    def display_man(self, item):
        man_entry = item.text(0)
        if "." not in man_entry:
            return
        name, section = man_entry.rsplit(".", 1)
        try:
            command = f"man {section} {name} | col -bx"
            output = subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True).stdout
            self.text_area.setPlainText(output)
        except Exception as e:
            self.text_area.setPlainText(f"Error loading man page: {e}")

    def highlight_matches(self):
        query = self.man_search_text.text().strip()
        if not query:
            return

        # Clear formatting
        self.text_area.moveCursor(QTextCursor.MoveOperation.Start)
        cursor = self.text_area.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(QTextCharFormat())

        # Highlight format
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("yellow"))

        self.search_matches.clear()
        self.current_match_index = -1

        cursor = self.text_area.textCursor()
        cursor.setPosition(0)
        doc = self.text_area.document()

        while True:
            cursor = doc.find(query, cursor)
            if cursor.isNull():
                break
            self.search_matches.append(QTextCursor(cursor))
            cursor.mergeCharFormat(highlight_format)

        if self.search_matches:
            self.focus_match(0)

    def focus_match(self, index):
        if not self.search_matches:
            return
        index = index % len(self.search_matches)
        cursor = self.search_matches[index]
        self.text_area.setTextCursor(cursor)
        self.current_match_index = index
        self.match_label.setText(f"{index + 1} of {len(self.search_matches)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ManPageViewer()
    viewer.resize(1200, 700)
    viewer.show()
    sys.exit(app.exec())
