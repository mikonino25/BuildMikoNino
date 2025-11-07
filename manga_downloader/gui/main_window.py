#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Window - Giao diện chính của ứng dụng
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import threading
import time
import queue
from pathlib import Path
from PIL import Image, ImageTk
import io
import requests

class MainWindow:
    def __init__(self, root, config_manager, lua_loader, download_manager):
        self.root = root
        self.config = config_manager
        self.lua_loader = lua_loader
        self.download_manager = download_manager
        
        self.setup_window()
        self.create_toolbar()
        self.create_url_section()
        self.create_tabs()
        self.create_status_bar()
        
        # Bắt đầu download manager
        self.download_manager.start_downloads()
        
        # Dictionary để lưu task và tree item mapping
        self.task_items = {}  # {task: tree_item_id}
        
        # Queue để batch insert vào treeview
        self.treeview_insert_queue = queue.Queue()
        self.treeview_insert_thread = None
        self.start_treeview_insert_worker()
        
        # Progress update thread
        self.update_thread = None
        self.update_running = True
        self.start_progress_updater()
        
        # Set callback cho download manager
        self.download_manager.progress_callback = self.on_task_progress_update
        
        # Kiểm tra và thông báo nếu không có modules
        self._check_modules_loaded()
        
        # Hiển thị popup giới thiệu khi mở ứng dụng
        self.root.after(500, self.show_welcome_popup)
        
    def setup_window(self):
        """Thiết lập cửa sổ chính với theme đẹp"""
        self.root.title("MikoNino - Manga Downloader")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        # Modern color scheme - Màu nhẹ nhàng như icon (đỏ/cam nhẹ)
        # Icon có màu đỏ mắt anime, nên dùng tông màu ấm, nhẹ nhàng
        self.colors = {
            'bg_primary': '#2B2B2B',      # Nền chính
            'bg_secondary': '#323232',    # Tab chọn / Secondary background
            'bg_tertiary': '#252526',     # Header/Toolbar (xám đen mịn)
            'bg_tab_selected': '#323232', # Tab được chọn
            'accent': '#FF6B9D',          # Icon màu hồng đào nhẹ (như mắt anime)
            'accent_alt': '#FF8A95',      # Icon màu hồng nhạt (alternative)
            'accent_hover': '#FF9DB0',    # Accent hover (hồng nhạt hơn)
            'accent_soft': '#FFB3C1',     # Accent mềm mại
            'progress_blue': '#4FC3F7',   # Progress bar xanh cyan nhẹ
            'progress_yellow': '#FFD54F', # Progress bar vàng nhẹ
            'success': '#81C784',         # Green success nhẹ
            'warning': '#FFB74D',         # Orange warning nhẹ
            'error': '#E57373',            # Red error nhẹ
            'text_primary': '#E8E8E8',     # Text chính (sáng hơn một chút)
            'text_secondary': '#B0B0B0',   # Text phụ
            'border': '#3d3d3d',           # Border color
        }
        
        # Set background color cho root
        self.root.config(bg=self.colors['bg_primary'])
        
        # Configure ttk styles
        self.setup_styles()
        
        # Set icon cho window và taskbar - đảm bảo hiển thị đúng
        try:
            import sys
            from pathlib import Path
            
            # Xác định thư mục gốc
            if getattr(sys, 'frozen', False):
                # Chạy từ EXE (PyInstaller)
                base_dir = Path(sys.executable).parent
                # Thử _MEIPASS (temp folder của PyInstaller)
                if hasattr(sys, '_MEIPASS'):
                    meipass_dir = Path(sys._MEIPASS)
                else:
                    meipass_dir = None
            else:
                # Chạy từ source
                base_dir = Path(__file__).parent.parent.parent
                meipass_dir = None
            
            # Tìm icon trong nhiều vị trí (ưu tiên theo thứ tự)
            icon_paths = []
            
            # 1. Cùng thư mục với EXE (khi chạy từ EXE)
            if getattr(sys, 'frozen', False):
                icon_paths.append(base_dir / "assets" / "Red-Eye-Anime.ico")
                icon_paths.append(base_dir / "Red-Eye-Anime.ico")
            
            # 2. Trong _MEIPASS (temp folder của PyInstaller)
            if meipass_dir:
                icon_paths.append(meipass_dir / "assets" / "Red-Eye-Anime.ico")
                icon_paths.append(meipass_dir / "Red-Eye-Anime.ico")
            
            # 3. Từ source code
            icon_paths.append(Path(__file__).parent.parent.parent / "assets" / "Red-Eye-Anime.ico")
            
            # 4. Thư mục hiện tại
            icon_paths.append(Path.cwd() / "assets" / "Red-Eye-Anime.ico")
            icon_paths.append(Path.cwd() / "Red-Eye-Anime.ico")
            
            # Thử load icon với nhiều cách
            icon_loaded = False
            for icon_path in icon_paths:
                if icon_path.exists():
                    try:
                        # Cách 1: iconbitmap (cho window)
                        self.root.iconbitmap(str(icon_path))
                        
                        # Cách 2: iconphoto (cho taskbar - tốt hơn)
                        try:
                            from PIL import Image
                            img = Image.open(str(icon_path))
                            # Tạo PhotoImage từ icon
                            photo = ImageTk.PhotoImage(img)
                            self.root.iconphoto(True, photo)
                            # Giữ reference để không bị garbage collect
                            self.root._icon_photo = photo
                        except:
                            pass
                        
                        print(f"✓ Đã load icon: {icon_path}")
                        icon_loaded = True
                        break
                    except Exception as e:
                        print(f"⚠ Không thể load icon từ {icon_path}: {e}")
                        continue
            
            # Nếu không tìm thấy file, thử load từ EXE
            if not icon_loaded and getattr(sys, 'frozen', False):
                try:
                    exe_path = Path(sys.executable)
                    if exe_path.exists():
                        # Thử load icon từ EXE
                        self.root.iconbitmap(str(exe_path))
                        print(f"✓ Sử dụng icon từ EXE: {exe_path}")
                except Exception as e:
                    print(f"⚠ Không thể load icon từ EXE: {e}")
                    
        except Exception as e:
            print(f"⚠ Lỗi khi load icon: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_styles(self):
        """Thiết lập styles cho ttk widgets"""
        style = ttk.Style()
        
        # Try to use a modern theme
        try:
            style.theme_use('clam')
        except:
            style.theme_use('default')
        
        # Configure styles
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 16, 'bold'),
                       foreground=self.colors['text_primary'])
        
        style.configure('Heading.TLabel',
                       font=('Segoe UI', 11, 'bold'),
                       foreground=self.colors['accent'])
        
        style.configure('Primary.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=8)
        
        style.configure('Accent.TButton',
                       font=('Segoe UI', 10),
                       padding=6)
        
        style.configure('Toolbar.TButton',
                       font=('Segoe UI', 9),
                       padding=5)
        
        # Treeview style
        style.configure('Custom.Treeview',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       fieldbackground=self.colors['bg_primary'],
                       borderwidth=0,
                       font=('Segoe UI', 9))
        
        style.configure('Custom.Treeview.Heading',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=1,
                       relief=tk.FLAT)
        
        style.map('Custom.Treeview',
                 background=[('selected', self.colors['accent'])],
                 foreground=[('selected', self.colors['text_primary'])])
        
        # Notebook style
        style.configure('Custom.TNotebook',
                       background=self.colors['bg_primary'],
                       borderwidth=0)
        
        style.configure('Custom.TNotebook.Tab',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_secondary'],
                       padding=[20, 10],
                       font=('Segoe UI', 10))
        
        style.map('Custom.TNotebook.Tab',
                 background=[('selected', self.colors['bg_tab_selected'])],
                 foreground=[('selected', self.colors['accent'])],
                 expand=[('selected', [1, 1, 1, 0])])
        
        # Progressbar style
        style.configure('Custom.Horizontal.TProgressbar',
                       background=self.colors['progress_blue'],
                       troughcolor=self.colors['bg_secondary'],
                       borderwidth=0,
                       lightcolor=self.colors['progress_blue'],
                       darkcolor=self.colors['progress_blue'])
        
        # Frame style
        style.configure('Card.TFrame',
                       background=self.colors['bg_secondary'],
                       relief=tk.FLAT,
                       borderwidth=1)
        
        style.configure('Section.TLabelFrame',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=1,
                       relief=tk.FLAT)
        
        style.configure('Section.TLabelFrame.Label',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['accent'],
                       font=('Segoe UI', 10, 'bold'))
            
    def create_toolbar(self):
        """Tạo toolbar với design đẹp - Header/Toolbar màu #252526"""
        toolbar_frame = tk.Frame(self.root, bg=self.colors['bg_tertiary'], height=50)
        toolbar_frame.pack(fill=tk.X, padx=0, pady=0)
        toolbar_frame.pack_propagate(False)
        
        # Container cho buttons
        button_container = tk.Frame(toolbar_frame, bg=self.colors['bg_tertiary'])
        button_container.pack(side=tk.LEFT, padx=15, pady=8)
        
        # Primary action buttons với màu nhẹ nhàng như icon
        start_btn = tk.Button(button_container, 
                             text="▶ Start All", 
                             command=self.start_all_downloads,
                             bg=self.colors['accent'],
                             fg=self.colors['text_primary'],
                             font=('Segoe UI', 9, 'bold'),
                             relief=tk.FLAT,
                             padx=15,
                             pady=6,
                             cursor='hand2',
                             activebackground=self.colors['accent_hover'],
                             activeforeground=self.colors['text_primary'])
        start_btn.pack(side=tk.LEFT, padx=3)
        
        stop_btn = tk.Button(button_container,
                            text="⏹ Stop",
                            command=self.stop_all_downloads,
                            bg=self.colors['error'],
                            fg=self.colors['text_primary'],
                            font=('Segoe UI', 9),
                            relief=tk.FLAT,
                            padx=12,
                            pady=6,
                            cursor='hand2',
                            activebackground='#e53935',
                            activeforeground=self.colors['text_primary'])
        stop_btn.pack(side=tk.LEFT, padx=3)
        
        pause_btn = tk.Button(button_container,
                             text="⏸ Pause",
                             command=self.pause_all_downloads,
                             bg=self.colors['warning'],
                             fg=self.colors['text_primary'],
                             font=('Segoe UI', 9),
                             relief=tk.FLAT,
                             padx=12,
                             pady=6,
                             cursor='hand2',
                             activebackground='#fb8c00',
                             activeforeground=self.colors['text_primary'])
        pause_btn.pack(side=tk.LEFT, padx=3)
        
        # Separator
        separator = tk.Frame(toolbar_frame, bg=self.colors['border'], width=1)
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=8)
        
        # Secondary buttons
        secondary_container = tk.Frame(toolbar_frame, bg=self.colors['bg_tertiary'])
        secondary_container.pack(side=tk.LEFT, padx=5, pady=8)
        
        # Icons tham khảo FontAwesome (Unicode alternatives)
        buttons = [
            ("📂 Folder", self.open_download_folder),      # folder-open
            ("📄 Load TXT", self.load_from_txt_file),      # file-text
            ("🔄 Refresh", self.refresh_list),             # sync-alt
            ("⚙ Settings", self.show_settings),           # cog
        ]
        
        for text, command in buttons:
            btn = tk.Button(secondary_container,
                          text=text,
                          command=command,
                          bg=self.colors['bg_tertiary'],
                          fg=self.colors['text_secondary'],
                          font=('Segoe UI', 9),
                          relief=tk.FLAT,
                          padx=12,
                          pady=6,
                          cursor='hand2',
                          activebackground=self.colors['bg_secondary'],
                          activeforeground=self.colors['accent'])
            btn.pack(side=tk.LEFT, padx=2)
        
    def create_url_section(self):
        """Tạo phần nhập URL với design đẹp"""
        url_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        url_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Title với icon màu nhẹ nhàng
        title_label = tk.Label(url_frame,
                              text="➕ Add Manga From URL",
                              bg=self.colors['bg_primary'],
                              fg=self.colors['accent'],
                              font=('Segoe UI', 11, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 8))
        
        # Input container với border
        input_container = tk.Frame(url_frame, 
                                   bg=self.colors['bg_secondary'],
                                   relief=tk.FLAT,
                                   borderwidth=1,
                                   highlightbackground=self.colors['border'],
                                   highlightthickness=1)
        input_container.pack(fill=tk.X, pady=5)
        
        # Entry với modern style
        self.url_entry = tk.Entry(input_container,
                                 font=('Segoe UI', 10),
                                 bg=self.colors['bg_secondary'],
                                 fg=self.colors['text_primary'],
                                 insertbackground=self.colors['accent'],
                                 relief=tk.FLAT,
                                 borderwidth=0,
                                 highlightthickness=0)
        self.url_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=10)
        self.url_entry.insert(0, "Enter manga URL here...")
        self.url_entry.config(fg=self.colors['text_secondary'])
        self.url_entry.bind('<FocusIn>', self.clear_url_placeholder)
        self.url_entry.bind('<FocusOut>', self.restore_url_placeholder)
        self.url_entry.bind('<Return>', lambda e: self.add_manga_from_url())
        
        # Add button với accent color
        add_btn = tk.Button(input_container,
                          text="Add",
                          command=self.add_manga_from_url,
                          bg=self.colors['accent'],
                          fg=self.colors['text_primary'],
                          font=('Segoe UI', 10, 'bold'),
                          relief=tk.FLAT,
                          padx=20,
                          pady=10,
                          cursor='hand2',
                          activebackground=self.colors['accent_hover'],
                          activeforeground=self.colors['text_primary'])
        add_btn.pack(side=tk.RIGHT, padx=2, pady=2)
        
    def clear_url_placeholder(self, event):
        """Xóa placeholder khi click vào"""
        if self.url_entry.get() == "Enter manga URL here...":
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(fg=self.colors['text_primary'])
    
    def restore_url_placeholder(self, event):
        """Khôi phục placeholder nếu rỗng"""
        if not self.url_entry.get().strip():
            self.url_entry.insert(0, "Enter manga URL here...")
            self.url_entry.config(fg=self.colors['text_secondary'])
            
    def create_tabs(self):
        """Tạo tabbed interface với style đẹp"""
        # Container với background
        tab_container = tk.Frame(self.root, bg=self.colors['bg_primary'])
        tab_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        self.notebook = ttk.Notebook(tab_container, style='Custom.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Downloads tab
        self.downloads_frame = tk.Frame(self.notebook, bg=self.colors['bg_secondary'])
        self.notebook.add(self.downloads_frame, text="📥 Downloads")
        self.create_downloads_tab()
        
        # Settings tab
        self.settings_frame = tk.Frame(self.notebook, bg=self.colors['bg_secondary'])
        self.notebook.add(self.settings_frame, text="⚙ Settings")
        self.create_settings_tab()
        
        
    def create_downloads_tab(self):
        """Tạo tab Downloads với design đẹp"""
        # Container với padding - nền chính
        container = tk.Frame(self.downloads_frame, bg=self.colors['bg_primary'])
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview để hiển thị danh sách download
        columns = ("Cover", "Manga Title", "Chapters", "Pages", "Status", "Progress", "File Size")
        self.download_tree = ttk.Treeview(container, columns=columns, show="headings", height=20, style='Custom.Treeview')
        
        # Lưu ảnh bìa đã load (để tránh load lại)
        self.cover_images = {}  # {item_id: PhotoImage}
        
        # Định nghĩa các cột với icon đẹp hơn (FontAwesome style)
        self.download_tree.heading("Cover", text="🖼 Cover")
        self.download_tree.heading("Manga Title", text="📚 Manga Title")
        self.download_tree.heading("Chapters", text="📑 Chapters")
        self.download_tree.heading("Pages", text="📄 Pages")
        self.download_tree.heading("Status", text="⚡ Status")
        self.download_tree.heading("Progress", text="📊 Progress")
        self.download_tree.heading("File Size", text="💾 File Size")
        
        # Đặt độ rộng cột
        self.download_tree.column("Cover", width=90, anchor=tk.CENTER)
        self.download_tree.column("Manga Title", width=350)
        self.download_tree.column("Chapters", width=90, anchor=tk.CENTER)
        self.download_tree.column("Pages", width=100, anchor=tk.CENTER)
        self.download_tree.column("Status", width=150, anchor=tk.CENTER)
        self.download_tree.column("Progress", width=120, anchor=tk.CENTER)
        self.download_tree.column("File Size", width=110, anchor=tk.CENTER)
        
        # Tag colors cho status với màu nhẹ nhàng
        self.download_tree.tag_configure("Queued", foreground=self.colors['text_secondary'])
        self.download_tree.tag_configure("Processing", foreground=self.colors['accent'])
        self.download_tree.tag_configure("Getting Info", foreground=self.colors['accent_soft'])
        self.download_tree.tag_configure("Downloading", foreground=self.colors['progress_blue'])
        self.download_tree.tag_configure("Retrying", foreground=self.colors['progress_yellow'])
        self.download_tree.tag_configure("Completed", foreground=self.colors['success'])
        self.download_tree.tag_configure("Error", foreground=self.colors['error'])
        self.download_tree.tag_configure("Paused", foreground=self.colors['progress_yellow'])
        
        # Scrollbar với style
        scrollbar_frame = tk.Frame(container, bg=self.colors['bg_primary'])
        scrollbar_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar = ttk.Scrollbar(scrollbar_frame, orient=tk.VERTICAL, command=self.download_tree.yview)
        self.download_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        tree_frame = tk.Frame(container, bg=self.colors['bg_primary'])
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.download_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Context menu
        self.download_tree.bind("<Button-3>", self.show_context_menu)
        
        # Double click để xem chi tiết/error
        self.download_tree.bind("<Double-1>", self.show_task_details)
        
        # Hover để hiển thị ảnh bìa phóng to
        self.download_tree.bind("<Motion>", self._on_treeview_hover)
        self.cover_tooltip = None  # Tooltip window cho ảnh phóng to
        
    def create_settings_tab(self):
        """Tạo tab Settings với design đẹp"""
        # Main container - nền chính
        main_container = tk.Frame(self.settings_frame, bg=self.colors['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title với icon màu nhẹ nhàng
        title_label = tk.Label(main_container,
                              text="⚙️ Application Settings",
                              bg=self.colors['bg_primary'],
                              fg=self.colors['accent'],
                              font=('Segoe UI', 16, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Settings card - tab chọn màu
        settings_card = tk.Frame(main_container,
                                bg=self.colors['bg_tab_selected'],
                                relief=tk.FLAT,
                                borderwidth=1,
                                highlightbackground=self.colors['border'],
                                highlightthickness=1)
        settings_card.pack(fill=tk.X, pady=10)
        
        # Inner padding
        inner_frame = tk.Frame(settings_card, bg=self.colors['bg_tab_selected'])
        inner_frame.pack(fill=tk.BOTH, padx=20, pady=20)
        
        # Download directory section với icon màu nhẹ nhàng
        dir_label = tk.Label(inner_frame,
                            text="📂 Download Directory:",
                            bg=self.colors['bg_tab_selected'],
                            fg=self.colors['text_primary'],
                            font=('Segoe UI', 10, 'bold'))
        dir_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        dir_input_frame = tk.Frame(inner_frame, bg=self.colors['bg_tab_selected'])
        dir_input_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 15))
        
        self.download_dir_var = tk.StringVar(value=str(self.config.get_download_directory()))
        dir_entry = tk.Entry(dir_input_frame,
                           textvariable=self.download_dir_var,
                           font=('Segoe UI', 10),
                           bg=self.colors['bg_primary'],
                           fg=self.colors['text_primary'],
                           insertbackground=self.colors['accent'],
                           relief=tk.FLAT,
                           borderwidth=0,
                           highlightthickness=1,
                           highlightbackground=self.colors['border'],
                           highlightcolor=self.colors['accent'])
        dir_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=8)
        
        browse_btn = tk.Button(dir_input_frame,
                              text="Browse",
                              command=self.browse_download_folder,
                              bg=self.colors['accent'],
                              fg=self.colors['text_primary'],
                              font=('Segoe UI', 9, 'bold'),
                              relief=tk.FLAT,
                              padx=20,
                              pady=8,
                              cursor='hand2',
                              activebackground=self.colors['accent_hover'],
                              activeforeground=self.colors['text_primary'])
        browse_btn.pack(side=tk.RIGHT)
        
        # Max concurrent downloads section với icon màu nhẹ nhàng
        max_label = tk.Label(inner_frame,
                            text="⚡ Max Concurrent Downloads:",
                            bg=self.colors['bg_tab_selected'],
                            fg=self.colors['text_primary'],
                            font=('Segoe UI', 10, 'bold'))
        max_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 8))
        
        max_input_frame = tk.Frame(inner_frame, bg=self.colors['bg_tab_selected'])
        max_input_frame.grid(row=3, column=0, sticky=tk.W, pady=(0, 20))
        
        self.max_downloads_var = tk.StringVar(value=self.config.get('Queuing & Error Handling', 'DownloadsMax', '10'))
        max_spinbox = tk.Spinbox(max_input_frame,
                                from_=1,
                                to=20,
                                textvariable=self.max_downloads_var,
                                font=('Segoe UI', 10),
                                bg=self.colors['bg_primary'],
                                fg=self.colors['text_primary'],
                                insertbackground=self.colors['accent'],
                                relief=tk.FLAT,
                                borderwidth=0,
                                highlightthickness=1,
                                highlightbackground=self.colors['border'],
                                highlightcolor=self.colors['accent'],
                                width=10)
        max_spinbox.pack(side=tk.LEFT, padx=(0, 10), pady=8)
        
        max_hint = tk.Label(max_input_frame,
                           text="(1-20 downloads simultaneously)",
                           bg=self.colors['bg_tab_selected'],
                           fg=self.colors['text_secondary'],
                           font=('Segoe UI', 9))
        max_hint.pack(side=tk.LEFT, pady=8)
        
        # Save button với icon
        save_btn = tk.Button(inner_frame,
                           text="💾 Save Settings",
                           command=self.save_settings,
                           bg=self.colors['success'],
                           fg=self.colors['text_primary'],
                           font=('Segoe UI', 11, 'bold'),
                           relief=tk.FLAT,
                           padx=30,
                           pady=12,
                           cursor='hand2',
                           activebackground='#45a049',
                           activeforeground=self.colors['text_primary'])
        save_btn.grid(row=4, column=0, columnspan=3, pady=(10, 0))
        
    def create_status_bar(self):
        """Tạo status bar với design đẹp - Header/Toolbar màu"""
        # Status bar container - Header/Toolbar màu
        status_container = tk.Frame(self.root, bg=self.colors['bg_tertiary'], height=30)
        status_container.pack(side=tk.BOTTOM, fill=tk.X)
        status_container.pack_propagate(False)
        
        # Status text
        self.status_bar = tk.Label(status_container,
                                   text="Ready",
                                   bg=self.colors['bg_tertiary'],
                                   fg=self.colors['text_secondary'],
                                   font=('Segoe UI', 9),
                                   anchor=tk.W,
                                   padx=15)
        self.status_bar.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Daily downloads counter với màu nhẹ nhàng
        self.daily_downloads_label = tk.Label(status_container,
                                             text="Daily downloads: 25 remaining",
                                             bg=self.colors['bg_tertiary'],
                                             fg=self.colors['accent'],
                                             font=('Segoe UI', 9, 'bold'),
                                             padx=15)
        self.daily_downloads_label.pack(side=tk.RIGHT)
        
    def add_manga_from_url(self):
        """Thêm manga từ URL"""
        url = self.url_entry.get().strip()
        
        if not url or url == "Enter manga URL here...":
            messagebox.showwarning("Warning", "Vui lòng nhập URL hợp lệ")
            return
            
        # Kiểm tra module phù hợp
        module = self.lua_loader.find_module_for_url(url)
        if not module:
            # Kiểm tra xem có modules nào không
            total_modules = len(self.lua_loader.get_all_modules())
            if total_modules == 0:
                error_msg = (
                    "Không tìm thấy modules!\n\n"
                    f"Thư mục modules: {self.lua_loader.modules_dir}\n"
                    f"Vui lòng đảm bảo thư mục 'modules/lua/' tồn tại và chứa các file .lua"
                )
                messagebox.showerror("Lỗi", error_msg)
                return
            else:
                result = messagebox.askyesno(
                    "Warning", 
                    f"Không tìm thấy module phù hợp cho URL này.\n"
                    f"Đã load {total_modules} modules nhưng không có module nào hỗ trợ domain này.\n\n"
                    f"URL: {url}\n\n"
                    "Bạn có muốn thử tải không?"
                )
                if not result:
                    return
                
        # Thêm vào download queue
        task = self.download_manager.add_download(url)
        
        # Thêm vào treeview (tạm thời với URL, sẽ update sau khi có info)
        item_id = self.download_tree.insert("", tk.END, values=(
            "",  # Cover image (sẽ load sau)
            url[:50],  # Tạm thời hiển thị URL
            task.chapters,
            task.pages,
            task.status,
            f"{task.progress}%",
            self.format_file_size(task.file_size)
        ), tags=(task.status,))
        
        # Lưu mapping task -> item_id
        self.task_items[task] = item_id
        
        # Lấy thông tin và ảnh bìa ngay lập tức (trong thread riêng) - KHÔNG tải ảnh
        self._fetch_manga_info_only(task, url)
        
        # Xóa URL entry
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, "Manga URL")
        
        self.status_bar.config(text=f"Đang lấy thông tin: {url[:50]}...")
        
    def add_from_url(self):
        """Menu: Add from URL"""
        self.add_manga_from_url()
        
    def start_all_downloads(self):
        """Bắt đầu tất cả downloads - chỉ tải ảnh khi bấm Start"""
        # Đảm bảo download manager đã start
        if not self.download_manager.running:
            self.download_manager.start_downloads()
            print("✓ Đã khởi động download threads")
        
        # Đếm số tasks đang queued hoặc có thông tin nhưng chưa tải
        tasks_to_download = []
        for task in self.task_items.keys():
            with task.lock:
                if task.status in ["Queued", "Getting Info"] or (task.status not in ["Downloading", "Completed", "Error"] and task.pages > 0):
                    # Đảm bảo task có thông tin trước khi tải
                    if not task.title or task.pages == 0:
                        # Chưa có thông tin, bỏ qua
                        continue
                    tasks_to_download.append(task)
        
        if tasks_to_download:
            # Update status và thêm vào queue để bắt đầu download
            for task in tasks_to_download:
                with task.lock:
                    # Chỉ thêm vào queue nếu có thông tin đầy đủ
                    if task.title and task.pages > 0:
                        task.status = "Queued"
                        # Thêm vào queue nếu chưa có
                        try:
                            # Kiểm tra xem task đã trong queue chưa
                            queue_list = list(self.download_manager.download_queue.queue)
                            if task not in queue_list:
                                self.download_manager.download_queue.put(task)
                                print(f"✓ Đã thêm task vào queue: {task.title[:50]}")
                        except:
                            # Nếu lỗi, thêm trực tiếp
                            self.download_manager.download_queue.put(task)
            
            self.status_bar.config(text=f"Đã bắt đầu tải {len(tasks_to_download)} manga...")
            print(f"✓ Bắt đầu tải {len(tasks_to_download)} manga")
        else:
            self.status_bar.config(text="Không có tasks nào để download (cần có thông tin trước)")
        
    def stop_all_downloads(self):
        """Dừng tất cả downloads"""
        self.download_manager.stop_downloads()
        self.status_bar.config(text="Đã dừng tất cả downloads")
        
    def pause_all_downloads(self):
        """Tạm dừng tất cả downloads"""
        self.status_bar.config(text="Đã tạm dừng tất cả downloads")
        
    def remove_selected(self):
        """Xóa các item đã chọn"""
        selected = self.download_tree.selection()
        for item in selected:
            self.download_tree.delete(item)
        self.status_bar.config(text=f"Đã xóa {len(selected)} item(s)")
        
    def refresh_list(self):
        """Làm mới danh sách"""
        self.status_bar.config(text="Đã làm mới danh sách")
        
    def show_settings(self):
        """Hiển thị settings tab"""
        self.notebook.select(1)
        
    def save_settings(self):
        """Lưu settings"""
        download_dir = Path(self.download_dir_var.get())
        if download_dir.exists() or download_dir.parent.exists():
            self.config.set_download_directory(download_dir)
            
        self.config.set('Queuing & Error Handling', 'DownloadsMax', self.max_downloads_var.get())
        
        messagebox.showinfo("Success", "Đã lưu cài đặt")
        
    def browse_download_folder(self):
        """Chọn thư mục download"""
        folder = filedialog.askdirectory(initialdir=str(self.config.get_download_directory()))
        if folder:
            self.download_dir_var.set(folder)
            
    def open_download_folder(self):
        """Mở thư mục download"""
        download_dir = self.config.get_download_directory()
        if download_dir.exists():
            os.startfile(str(download_dir))
        else:
            messagebox.showwarning("Warning", "Thư mục download không tồn tại")
            
    def show_welcome_popup(self):
        """Hiển thị popup giới thiệu đẹp khi mở ứng dụng"""
        popup = tk.Toplevel(self.root)
        popup.title("Welcome to MikoNino")
        popup.geometry("600x700")
        popup.resizable(False, False)
        popup.configure(bg=self.colors['bg_primary'])
        
        # Center window
        popup.transient(self.root)
        popup.grab_set()
        
        # Đảm bảo popup hiển thị ở giữa màn hình
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (600 // 2)
        y = (popup.winfo_screenheight() // 2) - (700 // 2)
        popup.geometry(f"600x700+{x}+{y}")
        
        # Header với gradient effect
        header_frame = tk.Frame(popup, bg=self.colors['accent'], height=120)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Icon và title
        title_container = tk.Frame(header_frame, bg=self.colors['accent'])
        title_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Load và hiển thị icon thực tế
        icon_label = None
        try:
            import sys
            from pathlib import Path
            
            # Tìm icon trong nhiều vị trí
            icon_paths = []
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys.executable).parent
                icon_paths.append(base_dir / "assets" / "Red-Eye-Anime.ico")
                icon_paths.append(base_dir / "Red-Eye-Anime.ico")
                if hasattr(sys, '_MEIPASS'):
                    meipass_dir = Path(sys._MEIPASS)
                    icon_paths.append(meipass_dir / "assets" / "Red-Eye-Anime.ico")
                    icon_paths.append(meipass_dir / "Red-Eye-Anime.ico")
            else:
                base_dir = Path(__file__).parent.parent.parent
                icon_paths.append(base_dir / "assets" / "Red-Eye-Anime.ico")
            icon_paths.append(Path.cwd() / "assets" / "Red-Eye-Anime.ico")
            icon_paths.append(Path.cwd() / "Red-Eye-Anime.ico")
            
            icon_loaded = False
            for icon_path in icon_paths:
                if icon_path.exists():
                    try:
                        # Load icon và resize
                        img = Image.open(str(icon_path))
                        # Resize về 64x64 hoặc 80x80 để hiển thị đẹp
                        img = img.resize((80, 80), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        icon_label = tk.Label(title_container,
                                             image=photo,
                                             bg=self.colors['accent'])
                        icon_label.image = photo  # Giữ reference
                        icon_label.pack(pady=10)
                        icon_loaded = True
                        break
                    except Exception as e:
                        print(f"⚠ Không thể load icon từ {icon_path}: {e}")
                        continue
            
            # Fallback nếu không load được icon
            if not icon_loaded:
                icon_label = tk.Label(title_container,
                                     text="📚",
                                     bg=self.colors['accent'],
                                     font=('Segoe UI', 48),
                                     pady=10)
                icon_label.pack()
        except Exception as e:
            print(f"⚠ Lỗi khi load icon: {e}")
            # Fallback
            icon_label = tk.Label(title_container,
                                 text="📚",
                                 bg=self.colors['accent'],
                                 font=('Segoe UI', 48),
                                 pady=10)
            icon_label.pack()
        
        title_label = tk.Label(title_container,
                              text="MikoNino",
                              bg=self.colors['accent'],
                              fg=self.colors['text_primary'],
                              font=('Segoe UI', 28, 'bold'))
        title_label.pack()
        
        subtitle_label = tk.Label(title_container,
                                 text="Manga Downloader - Professional Edition",
                                 bg=self.colors['accent'],
                                 fg=self.colors['text_primary'],
                                 font=('Segoe UI', 11))
        subtitle_label.pack(pady=(5, 0))
        
        # Main content
        content_frame = tk.Frame(popup, bg=self.colors['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Version info
        version_frame = tk.Frame(content_frame, bg=self.colors['bg_secondary'], relief=tk.FLAT)
        version_frame.pack(fill=tk.X, pady=(0, 15))
        
        version_inner = tk.Frame(version_frame, bg=self.colors['bg_secondary'])
        version_inner.pack(fill=tk.BOTH, padx=20, pady=15)
        
        version_label = tk.Label(version_inner,
                                text="Version 1.0.0",
                                bg=self.colors['bg_secondary'],
                                fg=self.colors['accent'],
                                font=('Segoe UI', 12, 'bold'))
        version_label.pack(anchor=tk.W)
        
        # Features list
        features_frame = tk.Frame(content_frame, bg=self.colors['bg_primary'])
        features_frame.pack(fill=tk.BOTH, expand=True)
        
        features_title = tk.Label(features_frame,
                                  text="✨ Key Features",
                                  bg=self.colors['bg_primary'],
                                  fg=self.colors['accent'],
                                  font=('Segoe UI', 14, 'bold'))
        features_title.pack(anchor=tk.W, pady=(0, 10))
        
        features = [
            "🎨 Beautiful dark theme UI with soft colors",
            "📥 Download manga from multiple websites",
            "📚 Support 300+ Lua modules",
            "⚡ Real-time download progress",
            "🖼️ Cover image preview with hover zoom",
            "📄 Load links from TXT files (up to 100MB)",
            "🔄 Automatic manga info fetching",
            "💾 External modules for easy updates"
        ]
        
        for feature in features:
            feature_label = tk.Label(features_frame,
                                    text=f"  {feature}",
                                    bg=self.colors['bg_primary'],
                                    fg=self.colors['text_primary'],
                                    font=('Segoe UI', 10),
                                    anchor=tk.W,
                                    justify=tk.LEFT)
            feature_label.pack(anchor=tk.W, pady=3)
        
        # Footer với button
        footer_frame = tk.Frame(popup, bg=self.colors['bg_tertiary'], height=80)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)
        
        footer_inner = tk.Frame(footer_frame, bg=self.colors['bg_tertiary'])
        footer_inner.pack(fill=tk.BOTH, expand=True)
        
        # Close button
        close_btn = tk.Button(footer_inner,
                             text="🚀 Get Started",
                             command=popup.destroy,
                             bg=self.colors['accent'],
                             fg=self.colors['text_primary'],
                             font=('Segoe UI', 11, 'bold'),
                             relief=tk.FLAT,
                             padx=30,
                             pady=10,
                             cursor='hand2',
                             activebackground=self.colors['accent_hover'],
                             activeforeground=self.colors['text_primary'])
        close_btn.pack(pady=15)
        
        # Copyright
        copyright_label = tk.Label(footer_inner,
                                  text="© 2024 MikoNino - Free Version",
                                  bg=self.colors['bg_tertiary'],
                                  fg=self.colors['text_secondary'],
                                  font=('Segoe UI', 8))
        copyright_label.pack(pady=(0, 10))
        
        # Focus vào popup
        popup.focus_set()
    
    def _refresh_modules(self):
        """Refresh modules (reload)"""
        # Reload modules
        self.lua_loader.modules = {}
        self.lua_loader.load_modules()
        
        total_modules = len(self.lua_loader.get_all_modules())
        messagebox.showinfo(
            "Modules Refreshed",
            f"Đã refresh modules!\n\n"
            f"Loaded: {total_modules} modules\n"
            f"Directory: {self.lua_loader.modules_dir}"
        )
    
    def _fetch_manga_info_only(self, task, url):
        """Chỉ lấy thông tin manga và ảnh bìa, KHÔNG tải ảnh pages"""
        def fetch_thread():
            try:
                # Tìm module
                module = self.lua_loader.find_module_for_url(url)
                if not module:
                    self.root.after_idle(
                        lambda: self._update_task_error(task, "Không tìm thấy module phù hợp")
                    )
                    return
                
                # Lấy thông tin từ download manager
                self.root.after_idle(
                    lambda: self.status_bar.config(text=f"Đang lấy thông tin: {url[:50]}...")
                )
                
                info = self.download_manager._get_manga_info(url, module)
                if info:
                    with task.lock:
                        task.title = info.get('title', task.title)
                        task.chapters = info.get('chapters', 0)
                        task.pages = info.get('pages', 0)
                        task.total_pages = info.get('pages', 0)
                    
                    print(f"✓ Đã lấy thông tin: {task.title}, {task.pages} pages")
                    
                    # Lấy ảnh bìa
                    cover_url = self._extract_cover_image_url(url, module)
                    if cover_url:
                        task.cover_image_url = cover_url
                        # Download ảnh bìa
                        self._download_cover_image(task, cover_url)
                        print(f"✓ Đã tải ảnh bìa")
                
                # Update UI
                if task in self.task_items:
                    item_id = self.task_items[task]
                    self.root.after_idle(self._update_item_with_cover, task, item_id)
                    self.root.after_idle(
                        lambda: self.status_bar.config(text=f"Đã thêm: {task.title[:50]}...")
                    )
                    
            except Exception as e:
                print(f"Lỗi khi lấy thông tin manga: {e}")
                import traceback
                traceback.print_exc()
                self.root.after_idle(
                    lambda: self._update_task_error(task, f"Lỗi: {str(e)[:50]}")
                )
        
        thread = threading.Thread(target=fetch_thread, daemon=True)
        thread.start()
    
    def _update_task_error(self, task, error_msg):
        """Update task với lỗi"""
        with task.lock:
            task.status = "Error"
            task.error = error_msg
        
        if task in self.task_items:
            item_id = self.task_items[task]
            self.root.after_idle(self._update_single_item, task, item_id)
    
    def _extract_cover_image_url(self, url, module):
        """Trích xuất URL ảnh bìa từ HTML"""
        try:
            response = self.download_manager.session.get(url, timeout=15)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content[:200000], 'html.parser')  # Đọc 200KB đầu
            
            # Tìm ảnh bìa - các pattern thường gặp
            cover_selectors = [
                'img.cover',
                'img[class*="cover"]',
                'img[class*="thumbnail"]',
                'img[class*="thumb"]',
                '.cover img',
                '.thumbnail img',
                '.thumb img',
                'meta[property="og:image"]',
                'meta[name="twitter:image"]',
            ]
            
            for selector in cover_selectors:
                if selector.startswith('meta'):
                    meta = soup.select_one(selector)
                    if meta and meta.get('content'):
                        img_url = meta.get('content')
                        if img_url.startswith('http'):
                            return img_url
                else:
                    img = soup.select_one(selector)
                    if img:
                        img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                        if img_url:
                            # Convert relative URL to absolute
                            if img_url.startswith('//'):
                                img_url = 'https:' + img_url
                            elif img_url.startswith('/'):
                                from urllib.parse import urljoin
                                img_url = urljoin(url, img_url)
                            elif not img_url.startswith('http'):
                                from urllib.parse import urljoin
                                img_url = urljoin(url, img_url)
                            
                            if img_url.startswith('http'):
                                return img_url
            
            # Fallback: tìm bất kỳ ảnh lớn nào
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src and ('cover' in src.lower() or 'thumb' in src.lower() or 'poster' in src.lower()):
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        from urllib.parse import urljoin
                        src = urljoin(url, src)
                    if src.startswith('http'):
                        return src
                        
        except Exception as e:
            print(f"Lỗi khi extract cover image: {e}")
        
        return None
    
    def _download_cover_image(self, task, cover_url):
        """Download ảnh bìa"""
        try:
            response = self.download_manager.session.get(cover_url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Giới hạn kích thước ảnh (max 2MB)
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > 2 * 1024 * 1024:  # 2MB
                    break
            
            task.cover_image_data = content
            
        except Exception as e:
            print(f"Lỗi khi download cover image: {e}")
    
    def _update_item_with_cover(self, task, item_id):
        """Update item trong treeview với ảnh bìa"""
        try:
            if item_id not in self.download_tree.get_children():
                return
            
            # Thread-safe read
            with task.lock:
                status = task.status
                progress = task.progress
                error = task.error
                title = task.title
                pages = task.pages
                current_page = task.current_page
                total_pages = task.total_pages
                chapters = task.chapters
                file_size = task.file_size
                cover_data = task.cover_image_data
            
            # Hiển thị error nếu có
            status_display = status
            if error:
                status_display = f"{status}: {error[:40]}"
            
            # Hiển thị pages đang tải
            pages_display = pages
            if total_pages > 0:
                if current_page > 0:
                    pages_display = f"{current_page}/{total_pages}"
                else:
                    pages_display = f"0/{total_pages}"
            
            # Load và hiển thị ảnh bìa
            cover_display = "📷" if cover_data else ""
            if cover_data and item_id not in self.cover_images:
                try:
                    # Resize ảnh về thumbnail (60x60)
                    img = Image.open(io.BytesIO(cover_data))
                    img.thumbnail((60, 60), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    # Lưu để tránh garbage collection
                    self.cover_images[item_id] = photo
                except Exception as e:
                    print(f"Lỗi khi load ảnh bìa: {e}")
            
            # Update values
            self.download_tree.item(item_id, values=(
                cover_display,
                title or task.url[:50],
                chapters,
                pages_display,
                status_display,
                f"{progress}%",
                self.format_file_size(file_size)
            ), tags=(status,))
            
            # Set image vào cột Cover (nếu có)
            if item_id in self.cover_images:
                # Tạm thời dùng text, sẽ cải thiện sau
                pass
                    
        except Exception as e:
            print(f"Lỗi update item với cover: {e}")
    
    def _on_treeview_hover(self, event):
        """Xử lý hover trên treeview để hiển thị ảnh bìa phóng to"""
        try:
            item = self.download_tree.identify_row(event.y)
            if not item:
                # Ẩn tooltip nếu không hover vào item nào
                if self.cover_tooltip:
                    self.cover_tooltip.destroy()
                    self.cover_tooltip = None
                return
            
            # Kiểm tra xem có hover vào cột Cover không
            column = self.download_tree.identify_column(event.x)
            if column != '#1':  # Cột Cover là cột đầu tiên
                if self.cover_tooltip:
                    self.cover_tooltip.destroy()
                    self.cover_tooltip = None
                return
            
            # Tìm task tương ứng
            task = None
            for t, item_id in self.task_items.items():
                if item_id == item:
                    task = t
                    break
            
            if not task or not task.cover_image_data:
                return
            
            # Hiển thị tooltip với ảnh phóng to
            if not self.cover_tooltip:
                self.cover_tooltip = tk.Toplevel(self.root)
                self.cover_tooltip.overrideredirect(True)
                self.cover_tooltip.attributes('-topmost', True)
            
            # Load và resize ảnh
            try:
                img = Image.open(io.BytesIO(task.cover_image_data))
                # Resize về kích thước lớn hơn (300x300)
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # Update tooltip
                if hasattr(self.cover_tooltip, 'label'):
                    self.cover_tooltip.label.config(image=photo)
                    self.cover_tooltip.label.image = photo
                else:
                    label = tk.Label(self.cover_tooltip, image=photo)
                    label.image = photo  # Keep reference
                    label.pack()
                    self.cover_tooltip.label = label
                
                # Đặt vị trí tooltip
                x = event.x_root + 20
                y = event.y_root + 20
                self.cover_tooltip.geometry(f"+{x}+{y}")
                
            except Exception as e:
                print(f"Lỗi khi hiển thị tooltip ảnh: {e}")
                
        except Exception:
            pass
        
    def show_context_menu(self, event):
        """Hiển thị context menu"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Start", command=self.start_selected)
        menu.add_command(label="Pause", command=self.pause_selected)
        menu.add_command(label="Remove", command=self.remove_selected)
        menu.add_separator()
        menu.add_command(label="Open Folder", command=self.open_selected_folder)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
            
    def start_selected(self):
        """Bắt đầu item đã chọn"""
        pass
        
    def pause_selected(self):
        """Tạm dừng item đã chọn"""
        pass
        
    def open_selected_folder(self):
        """Mở thư mục của item đã chọn"""
        pass
    
    def show_task_details(self, event):
        """Hiển thị chi tiết task khi double click"""
        item = self.download_tree.selection()[0] if self.download_tree.selection() else None
        if not item:
            return
        
        # Tìm task tương ứng
        task = None
        for t, item_id in self.task_items.items():
            if item_id == item:
                task = t
                break
        
        if not task:
            return
        
        # Hiển thị dialog với thông tin chi tiết
        dialog = tk.Toplevel(self.root)
        dialog.title("Task Details")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        
        # Tạo text widget để hiển thị thông tin
        text_widget = tk.Text(dialog, wrap=tk.WORD, font=("Consolas", 9))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Thông tin task
        info = f"""URL: {task.url}

Status: {task.status}
Progress: {task.progress}%
Chapters: {task.chapters}
Pages: {task.current_page}/{task.total_pages} (Total: {task.pages})
File Size: {self.format_file_size(task.file_size)}

Title: {task.title or 'N/A'}

"""
        
        if task.error:
            info += f"ERROR:\n{task.error}\n\n"
        
        if task.retry_count > 0:
            info += f"Retry Count: {task.retry_count}/{task.max_retries}\n"
        
        text_widget.insert("1.0", info)
        text_widget.config(state=tk.DISABLED)
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=5)
        
    def format_file_size(self, size):
        """Định dạng kích thước file"""
        if size == 0:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
        
    def load_from_txt_file(self):
        """Load URLs từ file TXT"""
        file_path = filedialog.askopenfilename(
            title="Chọn file TXT chứa URLs",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        # Kiểm tra kích thước file
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        if file_size > 100:
            result = messagebox.askyesno(
                "Cảnh báo",
                f"File có kích thước {file_size:.2f} MB (lớn hơn 100MB).\n"
                "Quá trình load có thể mất thời gian.\n"
                "Bạn có muốn tiếp tục?"
            )
            if not result:
                return
        
        # Load trong thread riêng để không block UI
        thread = threading.Thread(
            target=self._load_txt_file_thread,
            args=(file_path,),
            daemon=True
        )
        thread.start()
        
        # Hiển thị progress dialog
        self.show_loading_dialog(file_path)
        
    def _load_txt_file_thread(self, file_path):
        """Thread để load file TXT (không block UI)"""
        try:
            urls = []
            total_lines = 0
            valid_urls = 0
            last_update = 0
            
            # Đếm tổng số dòng trước (nhanh hơn với buffering)
            print("Đang đếm tổng số dòng...")
            with open(file_path, 'r', encoding='utf-8', errors='ignore', buffering=8192*16) as f:
                for _ in f:
                    total_lines += 1
            
            print(f"Tổng số dòng: {total_lines}")
            
            # Đọc từng dòng (không load hết vào memory)
            with open(file_path, 'r', encoding='utf-8', errors='ignore', buffering=8192*16) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Bỏ qua dòng trống và comment
                    if not line or line.startswith('#'):
                        continue
                    
                    # Kiểm tra URL hợp lệ
                    if line.startswith('http://') or line.startswith('https://'):
                        urls.append(line)
                        valid_urls += 1
                        
                        # Update progress mỗi 1000 URLs (giảm tần suất)
                        if valid_urls - last_update >= 1000:
                            self.root.after_idle(self._update_loading_progress, 
                                                line_num, total_lines, valid_urls)
                            last_update = valid_urls
                            
                            # Cho UI thở một chút
                            time.sleep(0.01)
            
            # Update lần cuối
            self.root.after_idle(self._update_loading_progress, 
                               total_lines, total_lines, valid_urls)
            
            print(f"Đã đọc xong: {valid_urls} URLs")
            
            # Thêm tất cả URLs vào queue (trong thread riêng để không block)
            # Không dùng after_idle vì sẽ block UI, dùng thread trực tiếp
            self._add_urls_from_txt_batch(urls, valid_urls)
            
        except Exception as e:
            import traceback
            error_msg = f"Không thể đọc file:\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            self.root.after_idle(lambda: messagebox.showerror("Lỗi", error_msg))
        finally:
            self.root.after_idle(self._close_loading_dialog)
            
    def _update_loading_progress(self, current, total, valid):
        """Update progress khi load file"""
        if hasattr(self, 'loading_label') and self.loading_label.winfo_exists():
            try:
                percent = (current / total * 100) if total > 0 else 0
                self.loading_label.config(
                    text=f"Đang đọc: {current:,}/{total:,} dòng, {valid:,} URLs hợp lệ... ({percent:.1f}%)"
                )
                # Update progress bar nếu có
                if hasattr(self, 'loading_progress_determinate'):
                    self.loading_progress_determinate['value'] = percent
            except:
                pass  # Ignore errors khi window đã đóng
            
    def _add_urls_from_txt_batch(self, urls, count):
        """Thêm URLs từ TXT vào download queue (batch processing để tránh đơ UI)"""
        print(f"Bắt đầu thêm {len(urls)} URLs...")
        
        # Chạy trong thread riêng để không block UI
        def add_urls_thread():
            try:
                added = 0
                skipped = 0
                
                # Lấy danh sách URLs hiện có để check duplicate nhanh hơn
                existing_urls = set()
                for task in list(self.task_items.keys()):  # Copy để tránh modification during iteration
                    existing_urls.add(task.url)
                
                print(f"Đã có {len(existing_urls)} URLs trong queue")
                
                # Batch size để thêm vào queue
                BATCH_SIZE = 1000  # Có thể lớn hơn vì chỉ thêm vào queue
                
                # Thêm URLs vào download queue (nhanh)
                new_tasks = []
                for i, url in enumerate(urls):
                    # Kiểm tra URL đã tồn tại chưa
                    if url in existing_urls:
                        skipped += 1
                        continue
                    
                    task = self.download_manager.add_download(url)
                    new_tasks.append((task, url))
                    existing_urls.add(url)
                    added += 1
                    
                    # Thêm vào treeview insert queue (không block)
                    if len(new_tasks) >= BATCH_SIZE:
                        self.treeview_insert_queue.put(new_tasks.copy())
                        new_tasks = []
                        
                        # Update status bar
                        self.root.after_idle(
                            self.status_bar.config,
                            {"text": f"Đang thêm: {added:,}/{len(urls):,} URLs..."}
                        )
                
                # Thêm batch cuối cùng
                if new_tasks:
                    self.treeview_insert_queue.put(new_tasks)
                
                # Thêm marker để biết đã xong
                self.treeview_insert_queue.put(None)  # None = done marker
                
                # Update status bar cuối cùng
                self.root.after_idle(
                    self.status_bar.config,
                    {"text": f"Đã thêm {added:,} URLs, bỏ qua {skipped:,} URLs trùng lặp"}
                )
                
                print(f"Hoàn thành: {added} added, {skipped} skipped")
                
                if added > 0 and added <= 100:
                    self.root.after_idle(
                        lambda: messagebox.showinfo(
                            "Thành công",
                            f"Đã thêm {added:,} URLs vào queue!\n"
                            f"Bỏ qua {skipped:,} URLs trùng lặp."
                        )
                    )
            except Exception as e:
                import traceback
                error_msg = f"Lỗi khi thêm URLs: {str(e)}\n\n{traceback.format_exc()}"
                print(error_msg)
                self.root.after_idle(
                    lambda: messagebox.showerror("Lỗi", error_msg)
                )
        
        # Chạy trong thread riêng
        thread = threading.Thread(target=add_urls_thread, daemon=True)
        thread.start()
                
    def start_treeview_insert_worker(self):
        """Bắt đầu worker thread để insert vào treeview với rate limiting"""
        def insert_worker():
            while True:
                try:
                    # Lấy batch từ queue
                    batch = self.treeview_insert_queue.get(timeout=1)
                    
                    # None = done marker
                    if batch is None:
                        continue
                    
                    # Insert batch vào treeview
                    self.root.after_idle(self._insert_tasks_to_treeview, batch)
                    
                    # Rate limiting: delay nhỏ giữa các batch
                    time.sleep(0.02)  # 20ms delay = ~50 batches/giây
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Lỗi trong treeview insert worker: {e}")
        
        self.treeview_insert_thread = threading.Thread(target=insert_worker, daemon=True)
        self.treeview_insert_thread.start()
    
    def _insert_tasks_to_treeview(self, tasks):
        """Insert nhiều tasks vào treeview cùng lúc (tối ưu)"""
        try:
            # Insert tất cả items
            for task, url in tasks:
                item_id = self.download_tree.insert("", tk.END, values=(
                    "",  # Cover image (sẽ load sau)
                    url[:50],  # Tạm thời hiển thị URL
                    task.chapters,
                    task.pages,
                    task.status,
                    f"{task.progress}%",
                    self.format_file_size(task.file_size)
                ), tags=(task.status,))
                self.task_items[task] = item_id
                
                # Lấy thông tin và ảnh bìa async
                self._fetch_manga_info_async(task, url)
            
            # Chỉ update UI một lần sau khi insert xong batch
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"Lỗi khi insert tasks: {e}")
            
    def show_loading_dialog(self, file_path):
        """Hiển thị dialog khi đang load file"""
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("Đang load file...")
        self.loading_window.geometry("500x150")
        self.loading_window.transient(self.root)
        self.loading_window.grab_set()
        
        # Không cho phép đóng khi đang load
        self.loading_window.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Center window
        self.loading_window.update_idletasks()
        x = (self.loading_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.loading_window.winfo_screenheight() // 2) - (150 // 2)
        self.loading_window.geometry(f"500x150+{x}+{y}")
        
        ttk.Label(
            self.loading_window,
            text=f"Đang đọc file:\n{os.path.basename(file_path)}",
            font=("Arial", 10, "bold")
        ).pack(pady=5)
        
        self.loading_label = ttk.Label(
            self.loading_window,
            text="Đang xử lý...",
            font=("Arial", 9)
        )
        self.loading_label.pack(pady=5)
        
        # Progress bar (determinate mode) với màu xanh cyan
        self.loading_progress_determinate = ttk.Progressbar(
            self.loading_window,
            mode='determinate',
            length=450,
            maximum=100,
            style='Custom.Horizontal.TProgressbar'
        )
        self.loading_progress_determinate.pack(pady=5)
        
        # Indeterminate progress bar (backup) với màu xanh cyan
        self.loading_progress = ttk.Progressbar(
            self.loading_window,
            mode='indeterminate',
            length=450,
            style='Custom.Horizontal.TProgressbar'
        )
        self.loading_progress.pack(pady=5)
        self.loading_progress.start()
        
        # Force update
        self.loading_window.update()
        
    def _close_loading_dialog(self):
        """Đóng loading dialog"""
        if hasattr(self, 'loading_window'):
            if self.loading_progress:
                self.loading_progress.stop()
            self.loading_window.destroy()
            
    def add_multiple_urls(self):
        """Thêm nhiều URLs từ text input"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Thêm nhiều URLs")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        
        ttk.Label(dialog, text="Nhập URLs (mỗi URL một dòng):").pack(pady=5)
        
        text_widget = tk.Text(dialog, wrap=tk.WORD, height=15)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        def add_urls():
            content = text_widget.get("1.0", tk.END)
            urls = [line.strip() for line in content.split('\n') if line.strip()]
            urls = [url for url in urls if url.startswith('http://') or url.startswith('https://')]
            
            if urls:
                dialog.destroy()
                # Dùng batch processing
                self._add_urls_from_txt_batch(urls, len(urls))
            else:
                messagebox.showwarning("Cảnh báo", "Không có URL hợp lệ!")
        
        ttk.Button(dialog, text="Thêm", command=add_urls).pack(pady=5)
        
    def start_progress_updater(self):
        """Bắt đầu thread update progress"""
        # Dừng thread cũ nếu có
        if self.update_thread and self.update_thread.is_alive():
            self.update_running = False
            time.sleep(0.1)
        
        self.update_running = True
        
        def update_loop():
            while self.update_running:
                try:
                    # Đếm số lượng theo status
                    status_count = {
                        "Queued": 0,
                        "Processing": 0,
                        "Downloading": 0,
                        "Completed": 0,
                        "Error": 0,
                        "Paused": 0
                    }
                    
                    # Update tất cả items đang active (Processing, Downloading)
                    items_to_update = []
                    for task, item_id in list(self.task_items.items()):
                        # Đếm status
                        if task.status in status_count:
                            status_count[task.status] += 1
                        elif "Retrying" in task.status:
                            status_count["Processing"] += 1
                        elif "Getting Info" in task.status:
                            status_count["Processing"] += 1
                        
                        if task.status in ["Processing", "Downloading", "Getting Info", "Retrying"]:
                            items_to_update.append((task, item_id))
                    
                    # Update active items ngay lập tức
                    for task, item_id in items_to_update:
                        if item_id in self.download_tree.get_children():
                            try:
                                self.root.after_idle(self._update_single_item, task, item_id)
                            except:
                                pass
                    
                    # Update các items khác ít thường xuyên hơn
                    all_items = list(self.task_items.items())
                    if len(all_items) > len(items_to_update):
                        # Chỉ update 50 items không active mỗi lần
                        inactive_items = [(t, i) for t, i in all_items if t.status not in ["Processing", "Downloading", "Getting Info", "Retrying"]]
                        for task, item_id in inactive_items[:50]:
                            if item_id in self.download_tree.get_children():
                                try:
                                    self.root.after_idle(self._update_single_item, task, item_id)
                                except:
                                    pass
                    
                    # Update status bar
                    active = status_count["Processing"] + status_count["Downloading"]
                    total = len(self.task_items)
                    status_text = f"Total: {total} | Queued: {status_count['Queued']} | Active: {active} | Completed: {status_count['Completed']} | Errors: {status_count['Error']}"
                    self.root.after_idle(self.status_bar.config, {"text": status_text})
                                
                    time.sleep(0.5)  # Update mỗi 0.5 giây cho active items
                    
                except Exception as e:
                    print(f"Lỗi update progress: {e}")
                    time.sleep(1)
                
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        
    def _update_single_item(self, task, item_id):
        """Update một item trong treeview"""
        try:
            if item_id not in self.download_tree.get_children():
                return
                
            # Thread-safe read
            with task.lock:
                status = task.status
                progress = task.progress
                error = task.error
                title = task.title
                pages = task.pages
                current_page = task.current_page
                total_pages = task.total_pages
                chapters = task.chapters
                file_size = task.file_size
            
            # Hiển thị error nếu có
            status_display = status
            if error:
                status_display = f"{status}: {error[:40]}"
            
            # Hiển thị pages đang tải
            pages_display = pages
            if total_pages > 0:
                if current_page > 0:
                    pages_display = f"{current_page}/{total_pages}"
                else:
                    pages_display = f"0/{total_pages}"
            
            # Load ảnh bìa nếu có
            cover_display = ""
            if task.cover_image_data and item_id not in self.cover_images:
                try:
                    img = Image.open(io.BytesIO(task.cover_image_data))
                    img.thumbnail((60, 60), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.cover_images[item_id] = photo
                    cover_display = "📷"
                except:
                    pass
            
            # Update values
            self.download_tree.item(item_id, values=(
                cover_display,
                title or task.url[:50],
                chapters,
                pages_display,
                status_display,
                f"{progress}%",
                self.format_file_size(file_size)
            ), tags=(status,))
                    
        except Exception as e:
            print(f"Lỗi update item: {e}")
    
    def on_task_progress_update(self, task):
        """Callback được gọi khi task progress thay đổi"""
        # Update UI ngay lập tức
        if task in self.task_items:
            item_id = self.task_items[task]
            self.root.after_idle(self._update_single_item, task, item_id)
    
    def _check_modules_loaded(self):
        """Kiểm tra xem modules đã được load chưa"""
        total_modules = len(self.lua_loader.get_all_modules())
        if total_modules == 0:
            # Hiển thị warning sau khi UI đã load xong
            self.root.after(1000, self._show_modules_warning)
        else:
            # Update status bar với số lượng modules
            self.status_bar.config(
                text=f"Ready | {total_modules} modules loaded"
            )
    
    def _show_modules_warning(self):
        """Hiển thị cảnh báo nếu không có modules"""
        modules_dir = self.lua_loader.modules_dir
        if modules_dir and modules_dir.exists():
            return  # Đã có modules
        
        result = messagebox.askyesno(
            "Cảnh báo",
            f"Không tìm thấy modules!\n\n"
            f"Thư mục tìm kiếm: {modules_dir or 'N/A'}\n\n"
            f"Vui lòng đảm bảo thư mục 'modules/lua/' tồn tại và chứa các file .lua\n\n"
            f"Bạn có muốn mở thư mục để kiểm tra không?"
        )
        
        if result:
            # Mở thư mục
            import subprocess
            try:
                if modules_dir and modules_dir.parent.exists():
                    subprocess.Popen(f'explorer "{modules_dir.parent}"')
                else:
                    subprocess.Popen(f'explorer "{Path.cwd()}"')
            except:
                pass

