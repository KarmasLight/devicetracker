import tkinter as tk
from tkinter import ttk, messagebox, font, filedialog
import sqlite3
from datetime import datetime
import pytz
import pandas as pd
import os
import pandas as pd
from tkinter.ttk import Style
import sys
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('headset_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Modern color scheme with all text in black
COLORS = {
    'primary': '#4a6da7',
    'primary_dark': '#3a5a8c',  # Darker shade of primary
    'secondary': '#f8f9fa',
    'secondary_dark': '#e2e6ea',  # Darker shade of secondary
    'success': '#28a745',
    'success_dark': '#218838',    # Darker shade of success
    'danger': '#dc3545',
    'danger_dark': '#c82333',     # Darker shade of danger
    'warning': '#ffc107',
    'warning_dark': '#e0a800',    # Darker shade of warning
    'dark': '#000000',          # Pure black for all text
    'light': '#f8f9fa',
    'text': '#000000',           # Pure black for all text
    'bg': '#f0f2f5'
}

# Font settings
FONTS = {
    'title': ('Segoe UI', 18, 'bold'),
    'heading': ('Segoe UI', 14, 'bold'),
    'bold': ('Segoe UI', 12, 'bold'),
    'normal': ('Segoe UI', 12),
    'small': ('Segoe UI', 10)
}

class BarcodeTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("🎧 Headset Tracker")
        self.root.geometry("1000x700")
        self.root.configure(bg=COLORS['bg'])
        
        # Set application icon and style
        self.setup_styles()
        
    def format_phone_e164(self, phone):
        """Convert phone number to E.164 format (+[country code][number])"""
        if not phone:
            return ""
            
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, str(phone)))
        
        # If empty after cleaning, return empty
        if not digits:
            return ""
            
        # If already in E.164 format (starts with +), return as is
        if str(phone).startswith('+'):
            return phone
            
        # Handle US/Canada numbers (add +1)
        if len(digits) == 10:  # US/Canada without country code
            return f"+1{digits}"
        elif len(digits) == 11 and digits[0] == '1':  # US/Canada with country code
            return f"+{digits}"
            
        # For other numbers, assume they're in international format without +
        return f"+{digits}"
        
    def format_phone_display(self, phone):
        """Format phone number for display in +XX-XXX-XXX-XXXX format"""
        if not phone:
            return ""
            
        # Remove all non-digit characters except leading +
        digits = ''.join(c for c in str(phone) if c == '+' or c.isdigit())
        
        # If empty or doesn't start with +, return as is (invalid format)
        if not digits or not digits.startswith('+'):
            return phone
            
        # Extract country code and number
        country_code = digits[:3]  # Includes the + and 2-digit country code
        number = digits[3:]
        
        # Format as +XX-XXX-XXX-XXXX (or shorter if number is shorter)
        formatted = country_code
        
        # Add remaining digits in groups of 3, separated by hyphens
        while number:
            chunk_length = min(3, len(number))
            formatted += f"-{number[:chunk_length]}"
            number = number[chunk_length:]
            
        return formatted
        
    def setup_styles(self):
        """Configure ttk styles for a modern look"""
        style = ttk.Style()
        
        # Configure the main window background
        self.root.configure(bg=COLORS['bg'])
        
        # Configure tab style
        style.configure('TNotebook', 
                     background=COLORS['bg'],
                     borderwidth=0)
        
        # Base tab style
        style.configure('TNotebook.Tab',
                     font=('Segoe UI', 12, 'bold'),
                     padding=[15, 5],
                     background=COLORS['light'],
                     foreground='black',
                     borderwidth=2,  # Thicker border
                     relief='flat',   # Start with flat relief
                     lightcolor=COLORS['primary'],  # Border color
                     darkcolor=COLORS['primary'],   # Border color
                     bordercolor=COLORS['primary']) # Border color
        
        # Style for selected tab - more prominent border
        style.map('TNotebook.Tab',
                background=[('selected', COLORS['light']),
                          ('!selected', COLORS['light'])],
                foreground=[('selected', 'black'),
                          ('!selected', 'black')],
                relief=[('selected', 'solid'),      # Solid border for selected
                      ('!selected', 'flat')],       # No border for unselected
                borderwidth=[('selected', 3),       # Thicker border for selected
                           ('!selected', 0)])       # No border for unselected
        
        # Configure button styles
        style.configure('TButton', 
                      font=FONTS['normal'],
                      padding=6)
        
        # Primary button (Check Out)
        style.configure('Primary.TButton',
                      background=COLORS['primary'],
                      foreground='black',  # Black text
                      font=FONTS['bold'],
                      padding=10)
        style.map('Primary.TButton',
                 background=[('active', COLORS['primary_dark'])],
                 foreground=[('active', 'black'), ('!active', 'black')])
        
        # Secondary button (Check In)
        style.configure('Secondary.TButton',
                      background=COLORS['secondary'],
                      foreground='black',  # Black text
                      font=FONTS['bold'],
                      padding=10)
        style.map('Secondary.TButton',
                 background=[('active', COLORS['secondary_dark'])],
                 foreground=[('active', 'black'), ('!active', 'black')],
                 bordercolor=[('active', '#1e7e34'), 
                             ('!disabled', '#1e7e34')],
                 lightcolor=[('active', '#34ce57'), 
                            ('!disabled', '#34ce57')],
                 darkcolor=[('active', '#1e7e34'), 
                           ('!disabled', '#1e7e34')])
        
        style.map('Danger.TButton',
                foreground=[('active', 'black'), ('!disabled', 'black')],
                background=[('active', '#ff6b6b'),  # Lighter red background
                          ('!disabled', '#ff6b6b')],
                bordercolor=[('active', '#dc3545'), 
                            ('!disabled', '#dc3545')],
                lightcolor=[('active', '#ff6b6b'), 
                           ('!disabled', '#ff6b6b')],
                darkcolor=[('active', '#dc3545'), 
                          ('!disabled', '#dc3545')])
        
        # Configure entry style
        style.configure('TEntry', 
                       padding=5,
                       relief='flat',
                       fieldbackground='white')
        
        # Configure frame styles
        style.configure('Card.TFrame',
                      background='white',
                      relief='raised',
                      borderwidth=1)
                      
        # Status bar style
        style.configure('StatusBar.TFrame',
                      background=COLORS['light'],
                      relief='flat',
                      borderwidth=0)
                      
        # Status counts style
        style.configure('StatusCounts.TLabel',
                      font=FONTS['bold'],
                      foreground=COLORS['primary'],
                      background=COLORS['light'])
        
        # Database setup
        self.db_path = "headset_tracking.db"
        self.setup_database()
        
        # UI Setup
        self.setup_ui()
    
    def setup_database(self):
        """Initialize the SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create devices table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            attendee_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            check_out_time TEXT NOT NULL,
            check_in_time TEXT,
            notes TEXT
        )
        ''')
        
        # Check if we need to add the email and phone columns
        cursor.execute("PRAGMA table_info(devices)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add email column if it doesn't exist
        if 'email' not in columns:
            cursor.execute('ALTER TABLE devices ADD COLUMN email TEXT')
        
        # Add phone column if it doesn't exist
        if 'phone' not in columns:
            cursor.execute('ALTER TABLE devices ADD COLUMN phone TEXT')
        
        conn.commit()
        conn.close()
    
    def setup_ui(self):
        """Set up the main user interface"""
        # Main container
        main_container = ttk.Frame(self.root, padding=(20, 10))
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header with three sections: title (left), status (center), counts (right)
        header = ttk.Frame(main_container)
        header.pack(fill=tk.X, pady=(0, 20))
        
        # Left section - Title
        title_frame = ttk.Frame(header)
        title_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(title_frame, 
                text="🎧 Headset Tracker", 
                font=FONTS['title'],
                foreground=COLORS['primary']
        ).pack()
        
        # Right section - Device counts
        count_frame = ttk.Frame(header, style='StatusBar.TFrame')
        count_frame.pack(side=tk.RIGHT)
        
        self.status_counts = ttk.Label(
            count_frame,
            text="Checked Out: 0 | Checked In: 0 | Total: 0",
            font=('Segoe UI', 10, 'bold'),
            foreground=COLORS['primary'],
            background=COLORS['light'],
            padding=(12, 6),
            relief='solid',
            borderwidth=1
        )
        self.status_counts.pack()
        
        # Create a frame for the tab control and status message
        tab_container = ttk.Frame(main_container)
        tab_container.pack(fill=tk.X, pady=(0, 15))
        
        # Create the tab control with padding
        self.tab_control = ttk.Notebook(tab_container, style='TNotebook')
        self.tab_control.pack(side=tk.LEFT, expand=0)
        
        # Status message next to tabs
        self.status_indicator = ttk.Label(
            tab_container,
            text="",
            font=('Segoe UI', 18, 'bold'),  
            foreground='red',
            padding=(15, 5)
        )
        self.status_indicator.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Create tabs with consistent padding
        tab_padding = (25, 10)
        self.check_out_tab = ttk.Frame(self.tab_control, padding=15)
        self.check_in_tab = ttk.Frame(self.tab_control, padding=15)
        
        # Add tabs with icons and text
        self.tab_control.add(self.check_out_tab, text='  🔹 CHECK OUT  ')
        self.tab_control.add(self.check_in_tab, text='  ✅ CHECK IN  ')
        
        # Configure tab positions and padding
        self.tab_control.enable_traversal()  # Enable keyboard navigation
        
        # Set initial tab selection
        self.tab_control.select(self.check_out_tab)
        
        # Setup check out tab
        self.setup_check_out_ui()
        # Setup check in tab
        self.setup_check_in_ui()
        
        # Card for device list (goes below tabs)
        card = ttk.Frame(main_container, style='Card.TFrame', padding=15)
        card.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Set up the device list in the main container
        self.setup_device_list(card)
    
    def setup_check_out_ui(self):
        """Set up the check out tab UI"""
        # Main frame for check out tab
        main_frame = ttk.Frame(self.check_out_tab)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form frame
        form_frame = ttk.LabelFrame(main_frame, text="Check Out Device", padding=15)
        form_frame.pack(fill=tk.X, pady=10)
        
        # Barcode Entry
        barcode_frame = ttk.Frame(form_frame)
        barcode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(barcode_frame, 
                 text="🔢 Scan Barcode:",
                 font=FONTS['heading']
                 ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.check_out_barcode = ttk.Entry(barcode_frame, 
                                       width=30,
                                       font=('Segoe UI', 14),
                                       justify='center')
        self.check_out_barcode.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.check_out_barcode.focus()
        
        # Auto-focus on barcode entry and handle scanner input
        def handle_barcode_input(event=None):
            barcode = self.check_out_barcode.get().strip()
            # If barcode contains a newline (scanner typically sends Enter key)
            if '\n' in barcode or '\r' in barcode:
                barcode = barcode.strip('\n\r')
                self.check_out_barcode.delete(0, tk.END)
                self.check_out_barcode.insert(0, barcode)
                # Auto-tab to name field after scan
                self.name_entry.focus()
        
        # Bind both key release and focus events
        self.check_out_barcode.bind('<KeyRelease>', handle_barcode_input)
        self.check_out_barcode.bind('<FocusIn>', lambda e: self.check_out_barcode.selection_range(0, tk.END))
        
        # Auto-focus on barcode field when window is focused
        self.root.after(100, lambda: self.check_out_barcode.focus_force())
        
        # Attendee Name Entry
        name_frame = ttk.Frame(form_frame)
        name_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(name_frame, 
                 text="👤 Attendee Name:",
                 font=FONTS['heading']
                 ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.name_entry = ttk.Entry(name_frame, 
                                  width=30,
                                  font=('Segoe UI', 14))
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Auto-focus on name entry
        def focus_name_entry(event=None):
            self.name_entry.focus()
        
        self.root.bind('<Control-n>', focus_name_entry)
        
        # Email Entry (required)
        email_frame = ttk.Frame(form_frame)
        email_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(email_frame, 
                 text="📧 Email *:",
                 font=FONTS['heading']
                 ).pack(side=tk.LEFT, padx=(0, 10))
                 
        # Add a small note that email is required
        ttk.Label(email_frame,
                 text="(required)",
                 font=('Segoe UI', 8),
                 foreground='red'
                 ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.email_entry = ttk.Entry(email_frame, 
                                   width=30,
                                   font=('Segoe UI', 14))
        self.email_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Auto-focus on email entry
        def focus_email_entry(event=None):
            self.email_entry.focus()
        
        self.root.bind('<Control-e>', focus_email_entry)
        
        # Phone Entry
        phone_frame = ttk.Frame(form_frame)
        phone_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(phone_frame, 
                 text="📞 Phone:",
                 font=FONTS['heading']
                 ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.phone_entry = ttk.Entry(phone_frame, 
                                   width=30,
                                   font=('Segoe UI', 14))
        self.phone_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Auto-focus on phone entry
        def focus_phone_entry(event=None):
            self.phone_entry.focus()
        
        self.root.bind('<Control-p>', focus_phone_entry)
        
        # Check Out Button
        check_out_btn = ttk.Button(form_frame, 
                                 text="🔹 CHECK OUT", 
                                 command=self.check_out_device,
                                 style='Primary.TButton')
        check_out_btn.pack(pady=(15, 5), fill=tk.X)
    
    def setup_check_in_ui(self):
        """Set up the check in tab UI"""
        # Main frame for check in tab
        main_frame = ttk.Frame(self.check_in_tab)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Form frame
        form_frame = ttk.LabelFrame(main_frame, text="Check In Device", padding=15)
        form_frame.pack(fill=tk.X, pady=10)
        
        # Barcode Entry
        barcode_frame = ttk.Frame(form_frame)
        barcode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(barcode_frame, 
                 text="🔢 Scan Barcode:",
                 font=FONTS['heading']
                 ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.check_in_barcode = ttk.Entry(barcode_frame, 
                                       width=30,
                                       font=('Segoe UI', 14),
                                       justify='center')
        self.check_in_barcode.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.check_in_barcode.focus()
        
        # Handle barcode scanner input for check-in
        def handle_check_in_scan(event=None):
            barcode = self.check_in_barcode.get().strip()
            # If barcode contains a newline (scanner typically sends Enter key)
            if '\n' in barcode or '\r' in barcode:
                barcode = barcode.strip('\n\r')
                self.check_in_barcode.delete(0, tk.END)
                self.check_in_barcode.insert(0, barcode)
                self.check_in_device()
        
        # Bind both key release and focus events
        self.check_in_barcode.bind('<KeyRelease>', handle_check_in_scan)
        self.check_in_barcode.bind('<FocusIn>', lambda e: self.check_in_barcode.selection_range(0, tk.END))
        
        # Auto-focus on check-in barcode field when tab is selected
        def on_tab_changed(event):
            tab = event.widget.tab('current')['text'].strip()
            if 'CHECK IN' in tab:
                self.root.after(100, lambda: self.check_in_barcode.focus_force())
            elif 'CHECK OUT' in tab:
                self.root.after(100, lambda: self.check_out_barcode.focus_force())
        
        # Bind tab change event
        self.tab_control.bind('<<NotebookTabChanged>>', on_tab_changed)
        
        # Initial focus
        self.root.after(100, lambda: self.check_out_barcode.focus_force())
        
        # Check In Button
        check_in_btn = ttk.Button(form_frame, 
                                text="✅ CHECK IN", 
                                command=self.check_in_device,
                                style='Secondary.TButton')
        check_in_btn.pack(pady=(15, 5), fill=tk.X)
    
    def setup_device_list(self, parent):
        """Set up the device list view"""
        # Create container for the treeview and scrollbars
        tree_container = ttk.Frame(parent)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)
        
        # Create Treeview with custom style
        style = ttk.Style()
        style.configure('Treeview', 
                      rowheight=30,
                      font=FONTS['normal'],
                      fieldbackground='white',
                      foreground='black')  # Ensure text is black
        
        # Create Treeview with custom style
        self.tree = ttk.Treeview(tree_container, 
                               columns=('ID', 'Barcode', 'Attendee', 'Email', 'Phone', 'Status', 'Check Out Time', 'Check In Time'),
                               show='headings',
                               selectmode='browse')
        
        # Define columns with better formatting
        columns = {
            'ID': {'text': 'ID', 'width': 50, 'anchor': 'center'},
            'Barcode': {'text': 'Barcode', 'width': 150, 'anchor': 'center'},
            'Attendee': {'text': 'Attendee', 'width': 150, 'anchor': 'w'},
            'Email': {'text': 'Email', 'width': 200, 'anchor': 'w'},
            'Phone': {'text': 'Phone', 'width': 150, 'anchor': 'center'},
            'Status': {'text': 'Status', 'width': 100, 'anchor': 'center'},
            'Check Out Time': {'text': 'Checked Out', 'width': 160, 'anchor': 'center'},
            'Check In Time': {'text': 'Checked In', 'width': 160, 'anchor': 'center'}
        }
        
        for col, config in columns.items():
            self.tree.heading(col, text=config['text'])
            self.tree.column(col, width=config['width'], anchor=config['anchor'])
        
        # Configure tags for row coloring
        self.tree.tag_configure('checked_out', background='#fff3cd')
        self.tree.tag_configure('checked_in', background='#d4edda')
        
        # Add scrollbars
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        # Add double-click to select and focus barcode
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        
        # Add search box
        search_frame = ttk.Frame(tree_container)
        search_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(5, 0))
        
        ttk.Label(search_frame, text="🔍 Search:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_changed)
        
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Add export button
        export_btn = ttk.Button(search_frame, 
                             text="📊 Export to Excel", 
                             command=self.export_to_excel,
                             style='Primary.TButton')
        export_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Configure grid weights
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)
        
        # Load initial data
        self.refresh_device_list()
    
    def show_status(self, message, status_type='info'):
        """Show status message with appropriate styling
        
        Args:
            message (str): The message to display
            status_type (str): Type of message ('info', 'success', 'error', 'warning')
        """
        if not hasattr(self, 'status_indicator'):
            return  # Status indicator not initialized yet
            
        # Map status types to colors and icons
        status_config = {
            'info': {'color': COLORS['primary'], 'icon': 'ℹ️'},
            'success': {'color': '#28a745', 'icon': '✅'},  # Green
            'error': {'color': '#dc3545', 'icon': '❌'},    # Red
            'warning': {'color': '#ffc107', 'icon': '⚠️'}   # Yellow
        }
        
        # Get the config for this status type, default to info
        config = status_config.get(status_type, status_config['info'])
        
        # Update the status indicator with larger font
        self.status_indicator.config(
            text=f"{config['icon']} {message}" if message else "",
            foreground=config['color'],
            font=('Segoe UI', 18, 'bold')  
        )
        
        # Clear the status after 5 seconds if there's a message
        if hasattr(self, '_status_timeout'):
            self.root.after_cancel(self._status_timeout)
            
        if message:
            self._status_timeout = self.root.after(5000, lambda: self.show_status(""))
    
    def export_to_excel(self):
        """Export the current device list view to an Excel file"""
        try:
            # Get the current search term
            search_term = self.search_var.get().lower()
            
            # Get data from database
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT 
                    barcode,
                    attendee_name,
                    email,
                    phone,
                    check_out_time,
                    check_in_time,
                    notes
                FROM devices
            """
            params = []
            
            # Add search filter if there's a search term
            if search_term:
                query += """
                    WHERE 
                        barcode LIKE ? OR
                        attendee_name LIKE ? OR
                        email LIKE ? OR
                        phone LIKE ? OR
                        notes LIKE ?
                """
                search_pattern = f'%{search_term}%'
                params = [search_pattern] * 5
            
            # Add ORDER BY to sort by check_out_time (newest first)
            query += " ORDER BY datetime(check_out_time) DESC"
            
            # Fetch data
            df = pd.read_sql_query(query, conn, params=params)
            
            if df.empty:
                self.show_status("No data to export", 'warning')
                return
                
            # Ask user for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Save Excel File As"
            )
            
            if not file_path:  # User cancelled
                return
                
            # Export to Excel
            df.to_excel(file_path, index=False, engine='openpyxl')
            self.show_status(f"Exported to {file_path}", 'success')
            
        except Exception as e:
            error_msg = f"Error exporting to Excel: {str(e)}"
            logger.error(error_msg)
            self.show_status(error_msg, 'error')
            
    def on_search_changed(self, *args):
        """Handle search box text changes"""
        search_term = self.search_var.get().lower()
        self.refresh_device_list(search_term)
        
    def on_tree_double_click(self, event):
        """Handle double-click on device list"""
        # Get the selected item
        item = self.tree.selection()[0]
        values = self.tree.item(item, 'values')
        
        # Extract device information
        barcode = values[1]  # Barcode is the second column (index 1)
        
        # Populate the check-out form
        self.tab_control.select(self.check_out_tab)  # Switch to check-out tab
        self.check_out_barcode.delete(0, tk.END)
        self.check_out_barcode.insert(0, barcode)
        
        # Focus the name entry for quick typing
        self.name_entry.focus_set()
    
    def refresh_device_list(self, search_term=''):
        """Refresh the device list from the database"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Fetch data from database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = '''
            SELECT id, barcode, attendee_name, email, phone, check_out_time, check_in_time 
            FROM devices 
            WHERE barcode LIKE ? 
               OR attendee_name LIKE ?
               OR email LIKE ?
               OR phone LIKE ?
            ORDER BY check_out_time DESC
        '''
        search_pattern = f'%{search_term}%'
        cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern))
        
        # Counters for status
        checked_out = 0
        checked_in = 0
        
        for row in cursor.fetchall():
            barcode = row['barcode']
            name = row['attendee_name']
            email = row['email'] or ''
            phone = self.format_phone_display(row['phone']) if row['phone'] else ''
            out_time = row['check_out_time']
            in_time = row['check_in_time']
            
            # Format timestamps
            if out_time:
                out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y %I:%M %p')
            if in_time:
                in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y %I:%M %p')
            
            status = "Returned" if in_time else "Checked Out"
            
            # Update counters
            if in_time:
                checked_in += 1
            else:
                checked_out += 1
            
            # Insert with appropriate tag
            self.tree.insert('', 'end', 
                          values=(row['id'], barcode, name, email, phone, status, out_time, in_time if in_time else 'N/A'),
                          tags=('checked_in' if in_time else 'checked_out'))
        
        # Update status bar
        self.update_status_bar(checked_out, checked_in)
        
    def update_status_bar(self, checked_out, checked_in):
        """Update the status bar with current counts"""
        total = checked_out + checked_in
        # Clear text display with labels
        status_text = f"Checked Out: {checked_out} | Checked In: {checked_in} | Total: {total}"
        if hasattr(self, 'status_counts'):
            self.status_counts.config(text=status_text)
        return checked_out, checked_in, total
        
    def get_current_time(self):
        """Get current time in local timezone"""
        try:
            return datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def is_valid_email(self, email):
        """Validate email format and check if it's provided"""
        if not email:
            return False
            
        # Basic email validation regex
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
            
    def check_out_device(self):
        """Check out a device"""
        try:
            # Use check_out_barcode instead of barcode_entry
            barcode = self.check_out_barcode.get().strip()
            name = self.name_entry.get().strip()
            email = self.email_entry.get().strip()
            phone = self.format_phone_e164(self.phone_entry.get().strip())
            
            logger.info(f"Attempting to check out device. Barcode: {barcode}, Name: {name}")
            
            if not barcode or not name:
                error_msg = "Both barcode and attendee name are required"
                logger.warning(error_msg)
                self.show_status("❌ " + error_msg, 'error')
                return
                
            # Check if name contains at least first and last name (at least 2 words)
            name_parts = name.strip().split()
            if len(name_parts) < 2:
                error_msg = "Please provide both first and last name"
                logger.warning(error_msg)
                self.show_status("❌ " + error_msg, 'error')
                self.name_entry.focus()
                self.name_entry.select_range(0, tk.END)
                return
                
            # Get email and phone
            email = self.email_entry.get().strip()
            phone = self.phone_entry.get().strip()
            
            # Validate email (required field)
            if not email:
                error_msg = "Email is required"
                logger.warning("Email not provided")
                self.show_status("❌ " + error_msg, 'error')
                self.email_entry.focus()
                return
                
            if not self.is_valid_email(email):
                error_msg = "Please enter a valid email address (e.g., user@example.com)"
                logger.warning(f"Invalid email format: {email}")
                self.show_status("❌ " + error_msg, 'error')
                self.email_entry.focus()
                self.email_entry.select_range(0, tk.END)
                return
                
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check if the device is already checked out
            cursor.execute('''
                SELECT id, check_in_time 
                FROM devices 
                WHERE barcode = ?
                ORDER BY check_out_time DESC
                LIMIT 1
            ''', (barcode,))
            result = cursor.fetchone()
            
            if result and result['check_in_time'] is None:
                self.show_status("❌ This device is already checked out", 'error')
                conn.close()
                return
                
            if result:
                # Update existing record
                cursor.execute('''
                    UPDATE devices 
                    SET attendee_name = ?, 
                        email = ?, 
                        phone = ?, 
                        check_out_time = ?,
                        check_in_time = NULL
                    WHERE barcode = ?
                ''', (name, email, phone, self.get_current_time(), barcode))
                self.show_status(f"✅ Updated check-out for {barcode}", 'success')
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO devices (barcode, attendee_name, email, phone, check_out_time)
                    VALUES (?, ?, ?, ?, ?)
                ''', (barcode, name, email, phone, self.get_current_time()))
                self.show_status(f"✅ Checked out {barcode} to {name}", 'success')
            
            conn.commit()
            self.refresh_device_list()
            
            # Clear the form
            self.check_out_barcode.delete(0, tk.END)
            self.name_entry.delete(0, tk.END)
            self.email_entry.delete(0, tk.END)
            self.phone_entry.delete(0, tk.END)
            self.check_out_barcode.focus()
            
        except sqlite3.Error as e:
            self.show_status(f"❌ Database error: {str(e)}", 'error')
            logger.error(f"Database error during check-out: {str(e)}", exc_info=True)
        except Exception as e:
            error_msg = f"Unexpected error during check-out: {str(e)}"
            self.show_status(f"❌ {error_msg}", 'error')
            logger.error(error_msg, exc_info=True)
        finally:
            if 'conn' in locals():
                conn.close()
    
    def check_in_device(self):
        """Check in a device"""
        barcode = self.check_in_barcode.get().strip()
        
        if not barcode:
            self.show_status("❌ Please scan a barcode", 'error')
            self.check_in_barcode.focus()
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check if the device is already checked in
            cursor.execute('''
                SELECT id, check_in_time, attendee_name
                FROM devices 
                WHERE barcode = ?
                ORDER BY check_out_time DESC
                LIMIT 1
            ''', (barcode,))
            result = cursor.fetchone()
            
            if not result:
                self.show_status(f"❌ No record found for barcode {barcode}", 'error')
                return
                
            if result['check_in_time'] is not None:
                self.show_status(f"ℹ️ Device {barcode} is already checked in", 'info')
                return
            
            # Update the record
            cursor.execute('''
                UPDATE devices 
                SET check_in_time = ?
                WHERE id = ?
            ''', (self.get_current_time(), result['id']))
            
            conn.commit()
            self.refresh_device_list()
            
            # Clear the barcode field and refocus
            self.check_in_barcode.delete(0, tk.END)
            self.check_in_barcode.focus()
            
            self.show_status(f"✅ Checked in device {barcode} from {result['attendee_name']}", 'success')
            
        except sqlite3.Error as e:
            self.show_status(f"❌ Database error: {str(e)}", 'error')
            logger.error(f"Database error during check-in: {str(e)}", exc_info=True)
        except Exception as e:
            error_msg = f"Unexpected error during check-in: {str(e)}"
            self.show_status(f"❌ {error_msg}", 'error')
            logger.error(error_msg, exc_info=True)
        finally:
            if 'conn' in locals():
                conn.close()

def main():
    root = tk.Tk()
    app = BarcodeTracker(root)
    root.mainloop()

if __name__ == "__main__":
    main()
