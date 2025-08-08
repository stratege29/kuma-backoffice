#!/usr/bin/env python3
"""
🖼️  Kuma Image Manager - Desktop Application
GUI version of the image management tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os
import json
import subprocess
from datetime import datetime
import sys

# Import the core functionality
from kuma_image_manager import KumaImageManager, CONFIG
from country_data_manager import CountryDataManager, COUNTRY_CONFIG

class KumaDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🖼️ Kuma Image Manager")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize core managers
        self.manager = KumaImageManager()
        self.country_manager = CountryDataManager()
        
        # Queue for thread communication
        self.message_queue = queue.Queue()
        
        # Variables
        self.source_directory = tk.StringVar()
        self.audio_directory = tk.StringVar()
        self.country_data_file = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar()
        
        # Setup UI
        self.setup_ui()
        
        # Start message processing
        self.process_messages()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = tk.Label(main_frame, text="🖼️🎵🌍 Kuma Media & Data Manager", 
                              font=("Arial", 16, "bold"), bg='#f0f0f0')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Image directory selection
        ttk.Label(main_frame, text="Images Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        dir_frame.columnconfigure(0, weight=1)
        
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.source_directory, width=50)
        self.dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(dir_frame, text="Browse", command=self.browse_directory).grid(row=0, column=1)
        
        # Audio directory selection
        ttk.Label(main_frame, text="Audio Directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        audio_dir_frame = ttk.Frame(main_frame)
        audio_dir_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        audio_dir_frame.columnconfigure(0, weight=1)
        
        self.audio_dir_entry = ttk.Entry(audio_dir_frame, textvariable=self.audio_directory, width=50)
        self.audio_dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(audio_dir_frame, text="Browse", command=self.browse_audio_directory).grid(row=0, column=1)
        
        # Country data file selection
        ttk.Label(main_frame, text="Country Data File:").grid(row=3, column=0, sticky=tk.W, pady=5)
        
        country_file_frame = ttk.Frame(main_frame)
        country_file_frame.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        country_file_frame.columnconfigure(0, weight=1)
        
        self.country_file_entry = ttk.Entry(country_file_frame, textvariable=self.country_data_file, width=50)
        self.country_file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(country_file_frame, text="Browse", command=self.browse_country_data_file).grid(row=0, column=1)
        
        # Action buttons frame
        button_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
        button_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        # Image action buttons
        ttk.Label(button_frame, text="Images:", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        self.optimize_btn = ttk.Button(button_frame, text="🔧 Optimize Images", 
                                      command=self.optimize_images)
        self.optimize_btn.grid(row=1, column=0, padx=5, pady=2, sticky=(tk.W, tk.E))
        
        self.upload_btn = ttk.Button(button_frame, text="☁️ Upload to Firebase", 
                                    command=self.upload_images)
        self.upload_btn.grid(row=1, column=1, padx=5, pady=2, sticky=(tk.W, tk.E))
        
        self.update_btn = ttk.Button(button_frame, text="🔄 Update Firestore", 
                                    command=self.update_firestore)
        self.update_btn.grid(row=2, column=0, padx=5, pady=2, sticky=(tk.W, tk.E))
        
        self.verify_btn = ttk.Button(button_frame, text="✅ Verify Images", 
                                    command=self.verify_images)
        self.verify_btn.grid(row=2, column=1, padx=5, pady=2, sticky=(tk.W, tk.E))
        
        # Audio action buttons
        ttk.Separator(button_frame, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        ttk.Label(button_frame, text="Audio:", font=("Arial", 10, "bold")).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        self.optimize_audio_btn = ttk.Button(button_frame, text="🎵 Optimize Audio", 
                                           command=self.optimize_audio)
        self.optimize_audio_btn.grid(row=5, column=0, padx=5, pady=2, sticky=(tk.W, tk.E))
        
        self.upload_audio_btn = ttk.Button(button_frame, text="☁️ Upload Audio", 
                                         command=self.upload_audio)
        self.upload_audio_btn.grid(row=5, column=1, padx=5, pady=2, sticky=(tk.W, tk.E))
        
        self.update_audio_btn = ttk.Button(button_frame, text="🔄 Update Audio URLs", 
                                         command=self.update_audio_urls)
        self.update_audio_btn.grid(row=6, column=0, padx=5, pady=2, sticky=(tk.W, tk.E))
        
        # Country data action buttons
        ttk.Separator(button_frame, orient='horizontal').grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        ttk.Label(button_frame, text="Country Data:", font=("Arial", 10, "bold")).grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        self.load_country_btn = ttk.Button(button_frame, text="🌍 Load Country Data", 
                                         command=self.load_country_data)
        self.load_country_btn.grid(row=9, column=0, padx=5, pady=2, sticky=(tk.W, tk.E))
        
        self.upload_country_btn = ttk.Button(button_frame, text="☁️ Upload to Firestore", 
                                           command=self.upload_country_data)
        self.upload_country_btn.grid(row=9, column=1, padx=5, pady=2, sticky=(tk.W, tk.E))
        
        self.validate_country_btn = ttk.Button(button_frame, text="✅ Validate Data", 
                                             command=self.validate_country_data)
        self.validate_country_btn.grid(row=10, column=0, padx=5, pady=2, sticky=(tk.W, tk.E))
        
        self.country_report_btn = ttk.Button(button_frame, text="📊 View Report", 
                                           command=self.view_country_report)
        self.country_report_btn.grid(row=10, column=1, padx=5, pady=2, sticky=(tk.W, tk.E))
        
        # Complete workflow buttons (prominent)
        ttk.Separator(button_frame, orient='horizontal').grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.workflow_btn = tk.Button(button_frame, text="🚀 Complete Image Workflow", 
                                     command=self.complete_workflow,
                                     bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                                     relief="raised", bd=2)
        self.workflow_btn.grid(row=12, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        self.audio_workflow_btn = tk.Button(button_frame, text="🎵 Complete Audio Workflow", 
                                          command=self.complete_audio_workflow,
                                          bg="#FF9800", fg="white", font=("Arial", 10, "bold"),
                                          relief="raised", bd=2)
        self.audio_workflow_btn.grid(row=12, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Country data workflow button
        self.country_workflow_btn = tk.Button(button_frame, text="🌍 Complete Country Data Workflow", 
                                            command=self.complete_country_workflow,
                                            bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                                            relief="raised", bd=2)
        self.country_workflow_btn.grid(row=13, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Map Editor section
        ttk.Separator(button_frame, orient='horizontal').grid(row=14, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        ttk.Label(button_frame, text="Map Editor:", font=("Arial", 10, "bold")).grid(row=15, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        self.map_editor_btn = ttk.Button(button_frame, text="🗺️ Open Country Position Editor", 
                                       command=self.open_map_editor)
        self.map_editor_btn.grid(row=16, column=0, columnspan=2, padx=5, pady=2, sticky=(tk.W, tk.E))
        
        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_text)
        self.status_label.grid(row=0, column=1)
        
        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="Output Log", padding="5")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(bottom_frame, text="🔧 Settings", command=self.show_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="📁 Open Output Folder", command=self.open_output_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="📄 View Reports", command=self.view_reports).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="❌ Exit", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
        
        # Configure row weights for resizing
        main_frame.rowconfigure(5, weight=1)
        
        # Pre-fill country data file if it exists
        default_country_file = "/Users/arnaudkossea/development/kumacodex/scripts/complete_african_countries_data.json"
        if os.path.exists(default_country_file):
            self.country_data_file.set(default_country_file)
            self.log(f"📁 Auto-detected country data file: {os.path.basename(default_country_file)}")
    
    def browse_directory(self):
        """Open directory selection dialog"""
        directory = filedialog.askdirectory()
        if directory:
            self.source_directory.set(directory)
            self.log(f"📁 Selected images directory: {directory}")
    
    def browse_audio_directory(self):
        """Open audio directory selection dialog"""
        directory = filedialog.askdirectory()
        if directory:
            self.audio_directory.set(directory)
            self.log(f"🎵 Selected audio directory: {directory}")
    
    def log(self, message):
        """Add message to log output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Thread-safe logging
        if threading.current_thread() != threading.main_thread():
            self.message_queue.put(('log', formatted_message))
        else:
            self.log_text.insert(tk.END, formatted_message)
            self.log_text.see(tk.END)
            self.root.update_idletasks()
    
    def update_status(self, status, progress=None):
        """Update status and progress"""
        if threading.current_thread() != threading.main_thread():
            self.message_queue.put(('status', status, progress))
        else:
            self.status_text.set(status)
            if progress is not None:
                self.progress_var.set(progress)
            self.root.update_idletasks()
    
    def process_messages(self):
        """Process messages from worker threads"""
        try:
            while True:
                msg = self.message_queue.get_nowait()
                if msg[0] == 'log':
                    self.log_text.insert(tk.END, msg[1])
                    self.log_text.see(tk.END)
                elif msg[0] == 'status':
                    self.status_text.set(msg[1])
                    if len(msg) > 2 and msg[2] is not None:
                        self.progress_var.set(msg[2])
                elif msg[0] == 'enable_buttons':
                    self.enable_buttons(msg[1])
                elif msg[0] == 'show_success':
                    messagebox.showinfo("Success", msg[1])
                elif msg[0] == 'show_error':
                    messagebox.showerror("Error", msg[1])
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_messages)
    
    def enable_buttons(self, enabled=True):
        """Enable or disable action buttons"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.optimize_btn.config(state=state)
        self.upload_btn.config(state=state)
        self.update_btn.config(state=state)
        self.verify_btn.config(state=state)
        self.workflow_btn.config(state=state)
        self.optimize_audio_btn.config(state=state)
        self.upload_audio_btn.config(state=state)
        self.update_audio_btn.config(state=state)
        self.audio_workflow_btn.config(state=state)
        self.map_editor_btn.config(state=state)
        # Country data buttons
        self.load_country_btn.config(state=state)
        self.upload_country_btn.config(state=state)
        self.validate_country_btn.config(state=state)
        self.country_report_btn.config(state=state)
        self.country_workflow_btn.config(state=state)
    
    def run_in_thread(self, target, *args, **kwargs):
        """Run a function in a separate thread"""
        def wrapper():
            try:
                self.message_queue.put(('enable_buttons', False))
                result = target(*args, **kwargs)
                if result:
                    self.message_queue.put(('show_success', "Operation completed successfully!"))
                else:
                    self.message_queue.put(('show_error', "Operation failed. Check the log for details."))
            except Exception as e:
                self.message_queue.put(('show_error', f"Error: {str(e)}"))
                self.message_queue.put(('log', f"❌ Error: {str(e)}"))
            finally:
                self.message_queue.put(('enable_buttons', True))
                self.message_queue.put(('status', "Ready", 0))
        
        thread = threading.Thread(target=wrapper)
        thread.daemon = True
        thread.start()
    
    def optimize_images(self):
        """Optimize images in selected directory"""
        if not self.source_directory.get():
            messagebox.showerror("Error", "Please select a source directory first")
            return
        
        def optimize_worker():
            self.message_queue.put(('log', "🔧 Starting image optimization..."))
            self.message_queue.put(('status', "Optimizing images...", 10))
            
            # Patch the manager's print functions to use our logging
            original_print = print
            def log_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                self.message_queue.put(('log', message))
            
            # Temporarily replace print
            import builtins
            builtins.print = log_print
            
            try:
                result = self.manager.optimize_images(self.source_directory.get())
                self.message_queue.put(('status', "Optimization complete", 100))
                return result
            finally:
                builtins.print = original_print
        
        self.run_in_thread(optimize_worker)
    
    def upload_images(self):
        """Upload images to Firebase Storage"""
        def upload_worker():
            self.message_queue.put(('log', "☁️ Starting Firebase upload..."))
            self.message_queue.put(('status', "Uploading to Firebase...", 30))
            
            # Patch print for logging
            original_print = print
            def log_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                self.message_queue.put(('log', message))
            
            import builtins
            builtins.print = log_print
            
            try:
                result = self.manager.upload_to_firebase()
                self.message_queue.put(('status', "Upload complete", 100))
                return bool(result)
            finally:
                builtins.print = original_print
        
        self.run_in_thread(upload_worker)
    
    def update_firestore(self):
        """Update Firestore URLs"""
        def update_worker():
            self.message_queue.put(('log', "🔄 Updating Firestore URLs..."))
            self.message_queue.put(('status', "Updating Firestore...", 60))
            
            original_print = print
            def log_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                self.message_queue.put(('log', message))
            
            import builtins
            builtins.print = log_print
            
            try:
                result = self.manager.update_firestore_urls()
                self.message_queue.put(('status', "Firestore update complete", 100))
                return result
            finally:
                builtins.print = original_print
        
        self.run_in_thread(update_worker)
    
    def verify_images(self):
        """Verify uploaded images"""
        def verify_worker():
            self.message_queue.put(('log', "✅ Verifying image URLs..."))
            self.message_queue.put(('status', "Verifying images...", 80))
            
            original_print = print
            def log_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                self.message_queue.put(('log', message))
            
            import builtins
            builtins.print = log_print
            
            try:
                result = self.manager.verify_images()
                self.message_queue.put(('status', "Verification complete", 100))
                return result
            finally:
                builtins.print = original_print
        
        self.run_in_thread(verify_worker)
    
    def complete_workflow(self):
        """Execute complete workflow"""
        if not self.source_directory.get():
            messagebox.showerror("Error", "Please select a source directory first")
            return
        
        # Confirm action
        if not messagebox.askyesno("Confirm", 
                                  "This will optimize, upload, and update all images. Continue?"):
            return
        
        def workflow_worker():
            self.message_queue.put(('log', "🚀 Starting complete workflow..."))
            self.message_queue.put(('status', "Running complete workflow...", 0))
            
            original_print = print
            def log_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                self.message_queue.put(('log', message))
            
            import builtins
            builtins.print = log_print
            
            try:
                result = self.manager.complete_workflow(self.source_directory.get())
                self.message_queue.put(('status', "Workflow complete!", 100))
                return result
            finally:
                builtins.print = original_print
        
        self.run_in_thread(workflow_worker)
    
    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x400")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Settings content
        frame = ttk.Frame(settings_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Firebase settings
        firebase_frame = ttk.LabelFrame(frame, text="Firebase Configuration", padding="10")
        firebase_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(firebase_frame, text=f"Project ID: {CONFIG['firebase']['project_id']}").pack(anchor=tk.W)
        ttk.Label(firebase_frame, text=f"Bucket: {CONFIG['firebase']['bucket']}").pack(anchor=tk.W)
        
        # Optimization settings
        opt_frame = ttk.LabelFrame(frame, text="Optimization Settings", padding="10")
        opt_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(opt_frame, text=f"Standard Size: {CONFIG['optimization']['standard_size']}").pack(anchor=tk.W)
        ttk.Label(opt_frame, text=f"Retina Size: {CONFIG['optimization']['retina_size']}").pack(anchor=tk.W)
        ttk.Label(opt_frame, text=f"JPEG Quality: {CONFIG['optimization']['jpeg_quality']}%").pack(anchor=tk.W)
        ttk.Label(opt_frame, text=f"WebP Quality: {CONFIG['optimization']['webp_quality']}%").pack(anchor=tk.W)
        
        # Directories
        dir_frame = ttk.LabelFrame(frame, text="Directories", padding="10")
        dir_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(dir_frame, text=f"Output: {CONFIG['directories']['output']}").pack(anchor=tk.W)
        
        ttk.Button(frame, text="Close", command=settings_window.destroy).pack(pady=10)
    
    def open_output_folder(self):
        """Open output folder in finder/explorer"""
        output_dir = CONFIG['directories']['output']
        if os.path.exists(output_dir):
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", output_dir])
            elif sys.platform == "win32":  # Windows
                subprocess.run(["explorer", output_dir])
            else:  # Linux
                subprocess.run(["xdg-open", output_dir])
        else:
            messagebox.showwarning("Warning", f"Output directory does not exist: {output_dir}")
    
    def view_reports(self):
        """Show reports dialog"""
        reports_window = tk.Toplevel(self.root)
        reports_window.title("Reports")
        reports_window.geometry("600x400")
        reports_window.transient(self.root)
        
        frame = ttk.Frame(reports_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Report files
        report_files = [
            "optimization_report.json",
            "upload_report.json",
            "firestore_update_report.json",
            "image_verification_report.json"
        ]
        
        for report_file in report_files:
            full_path = os.path.join(CONFIG['directories']['output'], report_file)
            if os.path.exists(full_path):
                ttk.Button(frame, text=f"📄 {report_file}", 
                          command=lambda f=full_path: self.open_report(f)).pack(pady=2, fill=tk.X)
        
        ttk.Button(frame, text="Close", command=reports_window.destroy).pack(pady=10)
    
    def open_report(self, file_path):
        """Open report file"""
        if sys.platform == "darwin":  # macOS
            subprocess.run(["open", file_path])
        elif sys.platform == "win32":  # Windows
            subprocess.run(["notepad", file_path])
        else:  # Linux
            subprocess.run(["xdg-open", file_path])
    
    def optimize_audio(self):
        """Optimize audio files"""
        if not self.audio_directory.get():
            messagebox.showerror("Error", "Please select an audio directory first")
            return
        
        def optimize_worker():
            self.message_queue.put(('log', "🎵 Starting audio optimization..."))
            self.message_queue.put(('status', "Optimizing audio files...", 10))
            
            # Patch the manager's print functions to use our logging
            original_print = print
            def log_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                self.message_queue.put(('log', message))
            
            # Temporarily replace print
            import builtins
            builtins.print = log_print
            
            try:
                result = self.manager.optimize_audio_files(self.audio_directory.get())
                self.message_queue.put(('status', "Audio optimization complete", 100))
                return result
            finally:
                builtins.print = original_print
        
        self.run_in_thread(optimize_worker)
    
    def upload_audio(self):
        """Upload audio files to Firebase Storage"""
        def upload_worker():
            self.message_queue.put(('log', "☁️ Starting audio upload..."))
            self.message_queue.put(('status', "Uploading audio to Firebase...", 30))
            
            # Patch print for logging
            original_print = print
            def log_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                self.message_queue.put(('log', message))
            
            import builtins
            builtins.print = log_print
            
            try:
                result = self.manager.upload_audio_to_firebase()
                self.message_queue.put(('status', "Audio upload complete", 100))
                return bool(result)
            finally:
                builtins.print = original_print
        
        self.run_in_thread(upload_worker)
    
    def update_audio_urls(self):
        """Update Firestore with audio URLs"""
        def update_worker():
            self.message_queue.put(('log', "🔄 Updating audio URLs in Firestore..."))
            self.message_queue.put(('status', "Updating audio URLs...", 60))
            
            original_print = print
            def log_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                self.message_queue.put(('log', message))
            
            import builtins
            builtins.print = log_print
            
            try:
                result = self.manager.update_firestore_audio_urls()
                self.message_queue.put(('status', "Audio URLs update complete", 100))
                return result
            finally:
                builtins.print = original_print
        
        self.run_in_thread(update_worker)
    
    def complete_audio_workflow(self):
        """Execute complete audio workflow"""
        if not self.audio_directory.get():
            messagebox.showerror("Error", "Please select an audio directory first")
            return
        
        # Confirm action
        if not messagebox.askyesno("Confirm", 
                                  "This will optimize, upload, and update all audio files. Continue?"):
            return
        
        def workflow_worker():
            self.message_queue.put(('log', "🎵 Starting complete audio workflow..."))
            self.message_queue.put(('status', "Running complete audio workflow...", 0))
            
            original_print = print
            def log_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                self.message_queue.put(('log', message))
            
            import builtins
            builtins.print = log_print
            
            try:
                # Step 1: Optimize audio
                self.message_queue.put(('status', "Optimizing audio files...", 25))
                if not self.manager.optimize_audio_files(self.audio_directory.get()):
                    self.message_queue.put(('log', "❌ Audio optimization failed"))
                    return False
                
                # Step 2: Upload to Firebase
                self.message_queue.put(('status', "Uploading to Firebase...", 50))
                uploaded_files = self.manager.upload_audio_to_firebase()
                if not uploaded_files:
                    self.message_queue.put(('log', "❌ Audio upload failed"))
                    return False
                
                # Step 3: Update Firestore
                self.message_queue.put(('status', "Updating Firestore...", 75))
                if not self.manager.update_firestore_audio_urls(uploaded_files):
                    self.message_queue.put(('log', "❌ Firestore update failed"))
                    return False
                
                self.message_queue.put(('status', "Audio workflow complete!", 100))
                return True
            finally:
                builtins.print = original_print
        
        self.run_in_thread(workflow_worker)
    
    # Country Data Management Methods
    def browse_country_data_file(self):
        """Browse for country data JSON file"""
        file_path = filedialog.askopenfilename(
            title="Select Country Data JSON File",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ],
            initialdir=os.path.dirname(self.country_data_file.get()) if self.country_data_file.get() else None
        )
        
        if file_path:
            self.country_data_file.set(file_path)
            self.log(f"📁 Selected country data file: {os.path.basename(file_path)}")
    
    def load_country_data(self):
        """Load and validate country data"""
        if not self.country_data_file.get():
            messagebox.showerror("Error", "Please select a country data file first")
            return
        
        def load_worker():
            self.message_queue.put(('log', "📁 Loading country data..."))
            self.message_queue.put(('status', "Loading country data...", 0))
            
            original_print = print
            def log_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                self.message_queue.put(('log', message))
            
            import builtins
            builtins.print = log_print
            
            try:
                success = self.country_manager.load_country_data_from_json(self.country_data_file.get())
                if success:
                    self.message_queue.put(('status', "Country data loaded successfully", 100))
                else:
                    self.message_queue.put(('status', "Failed to load country data", 0))
                return success
            finally:
                builtins.print = original_print
        
        self.run_in_thread(load_worker)
    
    def validate_country_data(self):
        """Validate loaded country data"""
        if not self.country_manager.countries_data:
            messagebox.showerror("Error", "Please load country data first")
            return
        
        def validate_worker():
            self.message_queue.put(('log', "🔍 Validating country data..."))
            self.message_queue.put(('status', "Validating country data...", 0))
            
            original_print = print
            def log_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                self.message_queue.put(('log', message))
            
            import builtins
            builtins.print = log_print
            
            try:
                is_valid = self.country_manager.validate_country_data()
                if is_valid:
                    self.message_queue.put(('status', "Country data validation passed", 100))
                else:
                    self.message_queue.put(('status', "Country data validation failed", 0))
                return is_valid
            finally:
                builtins.print = original_print
        
        self.run_in_thread(validate_worker)
    
    def upload_country_data(self):
        """Upload country data to Firestore"""
        if not self.country_manager.countries_data:
            messagebox.showerror("Error", "Please load country data first")
            return
        
        # Confirm action
        if not messagebox.askyesno("Confirm Upload", 
                                  f"This will upload {len(self.country_manager.countries_data)} countries to Firestore. Continue?"):
            return
        
        def upload_worker():
            self.message_queue.put(('log', "🚀 Uploading country data to Firestore..."))
            self.message_queue.put(('status', "Uploading to Firestore...", 0))
            
            original_print = print
            def log_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                self.message_queue.put(('log', message))
            
            import builtins
            builtins.print = log_print
            
            try:
                # Initialize Firebase first
                if not self.country_manager.initialize_firebase():
                    self.message_queue.put(('status', "Firebase initialization failed", 0))
                    return False
                
                success = self.country_manager.upload_to_firestore()
                if success:
                    self.message_queue.put(('status', "Country data uploaded successfully", 100))
                else:
                    self.message_queue.put(('status', "Country data upload failed", 0))
                return success
            finally:
                builtins.print = original_print
        
        self.run_in_thread(upload_worker)
    
    def view_country_report(self):
        """View the upload report"""
        if not self.country_manager.upload_report.get('total_countries', 0):
            messagebox.showwarning("No Report", "No upload report available. Please upload country data first.")
            return
        
        report = self.country_manager.upload_report
        
        # Create report window
        report_window = tk.Toplevel(self.root)
        report_window.title("📊 Country Data Upload Report")
        report_window.geometry("600x500")
        report_window.transient(self.root)
        
        # Add text widget with scrollbar
        text_frame = ttk.Frame(report_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Generate report content
        report_content = f"""📊 COUNTRY DATA UPLOAD REPORT
═══════════════════════════════════════

📅 Timestamp: {report['timestamp']}
🌍 Total Countries: {report['total_countries']}
✅ Successful Uploads: {report['successful_uploads']}
❌ Failed Uploads: {report['failed_uploads']}

"""
        
        if report['uploaded_countries']:
            report_content += "✅ SUCCESSFULLY UPLOADED COUNTRIES:\n"
            report_content += "─" * 40 + "\n"
            for country in report['uploaded_countries']:
                report_content += f"  • {country['name']} ({country['code']})\n"
            report_content += "\n"
        
        if report['failed_countries']:
            report_content += "❌ FAILED UPLOADS:\n"
            report_content += "─" * 40 + "\n"
            for country in report['failed_countries']:
                report_content += f"  • {country['name']} ({country['code']}): {country['error']}\n"
            report_content += "\n"
        
        if report['errors']:
            report_content += "🚨 ERRORS:\n"
            report_content += "─" * 40 + "\n"
            for error in report['errors']:
                report_content += f"  • {error}\n"
        
        text_widget.insert(tk.END, report_content)
        text_widget.config(state=tk.DISABLED)
        
        # Add buttons
        button_frame = ttk.Frame(report_window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Save Report", 
                  command=lambda: self.save_country_report(report_content)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", 
                  command=report_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Center the window
        report_window.update_idletasks()
        x = (report_window.winfo_screenwidth() // 2) - (report_window.winfo_width() // 2)
        y = (report_window.winfo_screenheight() // 2) - (report_window.winfo_height() // 2)
        report_window.geometry(f"+{x}+{y}")
        
        self.log("📊 Country upload report displayed")
    
    def save_country_report(self, content):
        """Save the country report to file"""
        file_path = filedialog.asksaveasfilename(
            title="Save Country Report",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Report saved to {os.path.basename(file_path)}")
                self.log(f"📄 Country report saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save report: {str(e)}")
                self.log(f"❌ Error saving report: {str(e)}")
    
    def complete_country_workflow(self):
        """Execute complete country data workflow"""
        if not self.country_data_file.get():
            messagebox.showerror("Error", "Please select a country data file first")
            return
        
        # Confirm action
        if not messagebox.askyesno("Confirm Workflow", 
                                  "This will load, validate, and upload all country data. Continue?"):
            return
        
        def workflow_worker():
            self.message_queue.put(('log', "🌍 Starting complete country data workflow..."))
            self.message_queue.put(('status', "Running complete country workflow...", 0))
            
            original_print = print
            def log_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                self.message_queue.put(('log', message))
            
            import builtins
            builtins.print = log_print
            
            try:
                success = self.country_manager.complete_workflow(self.country_data_file.get())
                if success:
                    self.message_queue.put(('status', "Country workflow completed successfully!", 100))
                else:
                    self.message_queue.put(('status', "Country workflow completed with errors", 0))
                return success
            finally:
                builtins.print = original_print
        
        self.run_in_thread(workflow_worker)
    
    def open_map_editor(self):
        """Open the country position editor"""
        try:
            editor = CountryPositionEditor(self.root, self.log)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open map editor: {str(e)}")
            self.log(f"❌ Error opening map editor: {str(e)}")


class CountryPositionEditor:
    """Country position editor for the Africa map"""
    
    def __init__(self, parent, log_callback):
        self.parent = parent
        self.log = log_callback
        self.positions = {}
        self.selected_country = None
        self.canvas_width = 900
        self.canvas_height = 1000
        self.map_scale = 0.8  # Scale the map to fit better
        self.country_points = {}  # Store canvas items for countries
        
        # Load current positions
        self.load_positions()
        
        # Create editor window
        self.window = tk.Toplevel(parent)
        self.window.title("🗺️ Country Position Editor")
        self.window.geometry("1300x1000")
        self.window.transient(parent)
        
        self.setup_ui()
        
        # Make sure window is visible
        self.window.lift()
        self.window.focus_force()
    
    def load_positions(self):
        """Load current country positions from the Dart file"""
        # Use the positions file from kumacodex project
        positions_file = "/Users/arnaudkossea/development/kumacodex/lib/constants/country_positions.dart"
        
        self.log(f"📁 Looking for positions file: {positions_file}")
        
        if not os.path.exists(positions_file):
            self.log(f"❌ Positions file not found: {positions_file}")
            self.use_fallback_positions()
            return
            
        try:
            with open(positions_file, 'r') as f:
                content = f.read()
                
            # Parse the positions from the Dart file
            import re
            pattern = r"'([A-Z]{2})':\s*CountryPosition\(([0-9.]+),\s*([0-9.]+)\)"
            matches = re.findall(pattern, content)
            
            for country_code, x, y in matches:
                self.positions[country_code] = {
                    'x': float(x),
                    'y': float(y)
                }
                
            self.log(f"📍 Loaded {len(self.positions)} country positions")
            
        except Exception as e:
            self.log(f"⚠️ Could not parse positions from Dart file: {e}")
            self.use_fallback_positions()
    
    def use_fallback_positions(self):
        """Use fallback positions when file loading fails"""
        self.log("🔄 Using fallback positions for testing")
        # Default positions for testing
        self.positions = {
            'NG': {'x': 0.389, 'y': 0.409},
            'ZA': {'x': 0.495, 'y': 0.873},
            'EG': {'x': 0.662, 'y': 0.261},
            'KE': {'x': 0.742, 'y': 0.568},
        }
    
    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="🗺️ Country Position Editor", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        # Close button
        ttk.Button(title_frame, text="❌ Close", 
                  command=self.window.destroy).pack(side=tk.RIGHT)
        
        # Main content
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Controls
        control_frame = ttk.LabelFrame(content_frame, text="Controls", padding="10")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Country count and selection
        count_label = ttk.Label(control_frame, text=f"Countries loaded: {len(self.positions)}", 
                               font=("Arial", 9), foreground="blue")
        count_label.pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Label(control_frame, text="Selected Country:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.country_var = tk.StringVar()
        self.country_combo = ttk.Combobox(control_frame, textvariable=self.country_var,
                                         values=sorted(self.positions.keys()),
                                         state="readonly", width=15)
        self.country_combo.pack(pady=5, fill=tk.X)
        self.country_combo.bind('<<ComboboxSelected>>', self.on_country_selected)
        
        # Position inputs
        ttk.Label(control_frame, text="Position:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 0))
        
        # X coordinate
        x_frame = ttk.Frame(control_frame)
        x_frame.pack(fill=tk.X, pady=2)
        ttk.Label(x_frame, text="X:").pack(side=tk.LEFT)
        self.x_var = tk.StringVar()
        self.x_entry = ttk.Entry(x_frame, textvariable=self.x_var, width=10)
        self.x_entry.pack(side=tk.RIGHT)
        self.x_var.trace_add('write', self.on_position_changed)
        
        # Y coordinate
        y_frame = ttk.Frame(control_frame)
        y_frame.pack(fill=tk.X, pady=2)
        ttk.Label(y_frame, text="Y:").pack(side=tk.LEFT)
        self.y_var = tk.StringVar()
        self.y_entry = ttk.Entry(y_frame, textvariable=self.y_var, width=10)
        self.y_entry.pack(side=tk.RIGHT)
        self.y_var.trace_add('write', self.on_position_changed)
        
        # Instructions
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        instructions = tk.Text(control_frame, height=8, width=25, wrap=tk.WORD)
        instructions.pack(fill=tk.BOTH, expand=True, pady=5)
        instructions.insert(tk.END, 
            "Instructions:\n\n"
            "• Click on a country point to select it\n"
            "• Drag points to move countries\n"
            "• Use X/Y inputs for precise positioning\n"
            "• Values are between 0.0 and 1.0\n"
            "• Click 'Copy Dart Code' when done\n\n"
            "Red point = Selected country\n"
            "Orange points = Other countries"
        )
        instructions.config(state=tk.DISABLED)
        
        # Action buttons
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="📋 Copy Dart Code", 
                  command=self.copy_dart_code).pack(fill=tk.X, pady=2)
        
        ttk.Button(control_frame, text="🔄 Reset All", 
                  command=self.reset_positions).pack(fill=tk.X, pady=2)
        
        # Right panel - Map canvas
        canvas_frame = ttk.LabelFrame(content_frame, text="Africa Map", padding="5")
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Canvas with scrollbars
        canvas_container = ttk.Frame(canvas_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas
        self.canvas = tk.Canvas(canvas_container, 
                               width=self.canvas_width, 
                               height=self.canvas_height,
                               bg='lightblue',
                               scrollregion=(0, 0, self.canvas_width, self.canvas_height))
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Load and display map
        self.load_map_image()
        self.draw_country_points()
        
        # Bind canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        self.dragging = False
        self.drag_item = None
    
    def load_map_image(self):
        """Load the Africa map image"""
        try:
            from PIL import Image, ImageTk
        except ImportError:
            self.log("❌ PIL/Pillow not installed. Run: pip install Pillow")
            messagebox.showerror("Missing Dependency", 
                               "PIL/Pillow is required to display the map image.\n\n"
                               "Please install it with:\n"
                               "pip install Pillow\n\n"
                               "Using placeholder map for now.")
            self.draw_placeholder_map()
            return
            
        try:
            # Use the map from kumacodex project
            map_path = "/Users/arnaudkossea/development/kumacodex/assets/images/maps/africa_base.png"
            
            # Fallback to old location if needed
            if not os.path.exists(map_path):
                map_path = "/Users/arnaudkossea/development/kumacodex/assets/africa_base.png"
            
            self.log(f"📁 Looking for map image: {map_path}")
            
            if not os.path.exists(map_path):
                self.log("⚠️ Map image not found, using placeholder")
                self.draw_placeholder_map()
                return
            
            # Load and resize image
            image = Image.open(map_path)
            # Scale the image to fit our canvas
            new_width = int(self.canvas_width * self.map_scale)
            new_height = int(self.canvas_height * self.map_scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            self.map_image = ImageTk.PhotoImage(image)
            
            # Center the image on canvas
            x_offset = (self.canvas_width - new_width) // 2
            y_offset = (self.canvas_height - new_height) // 2
            
            self.canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.map_image)
            
            # Store offset for coordinate calculation
            self.map_offset_x = x_offset
            self.map_offset_y = y_offset
            self.map_width = new_width
            self.map_height = new_height
            
            self.log("🗺️ Map image loaded successfully")
            
        except Exception as e:
            self.log(f"⚠️ Could not load map image: {e}")
            self.draw_placeholder_map()
    
    def draw_placeholder_map(self):
        """Draw a placeholder map if image can't be loaded"""
        # Draw a simple Africa shape placeholder
        x_offset = self.canvas_width // 4
        y_offset = self.canvas_height // 6
        width = self.canvas_width // 2
        height = int(self.canvas_height * 0.7)
        
        self.canvas.create_rectangle(x_offset, y_offset, x_offset + width, y_offset + height,
                                   fill='lightgreen', outline='darkgreen', width=2)
        self.canvas.create_text(self.canvas_width // 2, self.canvas_height // 2,
                              text="AFRICA\n(Placeholder Map)", font=("Arial", 20, "bold"))
        
        # Store dimensions for coordinate calculation
        self.map_offset_x = x_offset
        self.map_offset_y = y_offset
        self.map_width = width
        self.map_height = height
    
    def draw_country_points(self):
        """Draw country position points on the map"""
        self.log(f"📍 Drawing {len(self.positions)} country points")
        for country_code, pos in self.positions.items():
            self.draw_country_point(country_code, pos['x'], pos['y'])
        self.log(f"✅ Finished drawing country points")
    
    def draw_country_point(self, country_code, rel_x, rel_y):
        """Draw a single country point"""
        # Convert relative coordinates to canvas coordinates
        canvas_x = self.map_offset_x + (rel_x * self.map_width)
        canvas_y = self.map_offset_y + (rel_y * self.map_height)
        
        # Debug log for first few countries
        if len(self.country_points) < 5:
            self.log(f"🎯 Drawing {country_code} at canvas({canvas_x:.1f}, {canvas_y:.1f}) from rel({rel_x:.3f}, {rel_y:.3f})")
        
        # Determine color
        color = 'red' if country_code == self.selected_country else 'orange'
        
        # Remove ALL existing elements for this country (both circle and text)
        self.canvas.delete(country_code)
        
        # Create new point (larger and more visible)
        point = self.canvas.create_oval(canvas_x - 10, canvas_y - 10, canvas_x + 10, canvas_y + 10,
                                      fill=color, outline='darkred' if color == 'red' else 'darkorange',
                                      width=3, tags=(country_code, 'country_point'))
        
        # Add country code text
        text = self.canvas.create_text(canvas_x, canvas_y, text=country_code, 
                                     font=("Arial", 7, "bold"), fill='white', 
                                     tags=(country_code, 'country_text'))
        
        # Store both elements for the country
        self.country_points[country_code] = {'circle': point, 'text': text, 'x': canvas_x, 'y': canvas_y}
    
    def on_country_selected(self, event=None):
        """Handle country selection from combobox"""
        country = self.country_var.get()
        if country in self.positions:
            self.select_country(country)
    
    def select_country(self, country_code):
        """Select a country and update UI"""
        old_selected = self.selected_country
        self.selected_country = country_code
        
        # Update position inputs
        pos = self.positions[country_code]
        self.x_var.set(f"{pos['x']:.3f}")
        self.y_var.set(f"{pos['y']:.3f}")
        
        # Update combobox
        self.country_var.set(country_code)
        
        # Update colors of affected points
        if old_selected and old_selected in self.country_points:
            # Change old selected point back to orange
            old_data = self.country_points[old_selected]
            self.canvas.itemconfig(old_data['circle'], fill='orange', outline='darkorange')
        
        if country_code in self.country_points:
            # Change new selected point to red
            new_data = self.country_points[country_code]
            self.canvas.itemconfig(new_data['circle'], fill='red', outline='darkred')
        
        self.log(f"📍 Selected country: {country_code}")
    
    def on_position_changed(self, *args):
        """Handle manual position input changes"""
        if not self.selected_country:
            return
        
        try:
            x = float(self.x_var.get())
            y = float(self.y_var.get())
            
            # Clamp values
            x = max(0.0, min(1.0, x))
            y = max(0.0, min(1.0, y))
            
            # Calculate new canvas coordinates
            canvas_x = self.map_offset_x + (x * self.map_width)
            canvas_y = self.map_offset_y + (y * self.map_height)
            
            # Update position data
            self.positions[self.selected_country]['x'] = x
            self.positions[self.selected_country]['y'] = y
            
            # Move existing elements
            if self.selected_country in self.country_points:
                country_data = self.country_points[self.selected_country]
                
                # Move the circle
                self.canvas.coords(country_data['circle'], 
                                 canvas_x - 10, canvas_y - 10, 
                                 canvas_x + 10, canvas_y + 10)
                
                # Move the text
                self.canvas.coords(country_data['text'], canvas_x, canvas_y)
                
                # Update stored coordinates
                country_data['x'] = canvas_x
                country_data['y'] = canvas_y
            
        except ValueError:
            pass  # Invalid input, ignore
    
    def on_canvas_click(self, event):
        """Handle canvas click events"""
        # Get clicked item
        item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item)
        
        # Check if clicked on a country point
        for tag in tags:
            if tag in self.positions:
                self.select_country(tag)
                self.dragging = True
                self.drag_item = tag
                break
    
    def on_canvas_drag(self, event):
        """Handle canvas drag events"""
        if self.dragging and self.drag_item:
            # Convert canvas coordinates to relative coordinates
            rel_x = (event.x - self.map_offset_x) / self.map_width
            rel_y = (event.y - self.map_offset_y) / self.map_height
            
            # Clamp coordinates
            rel_x = max(0.0, min(1.0, rel_x))
            rel_y = max(0.0, min(1.0, rel_y))
            
            # Calculate new canvas coordinates
            canvas_x = self.map_offset_x + (rel_x * self.map_width)
            canvas_y = self.map_offset_y + (rel_y * self.map_height)
            
            # Move existing elements instead of redrawing
            if self.drag_item in self.country_points:
                country_data = self.country_points[self.drag_item]
                
                # Move the circle
                self.canvas.coords(country_data['circle'], 
                                 canvas_x - 10, canvas_y - 10, 
                                 canvas_x + 10, canvas_y + 10)
                
                # Move the text
                self.canvas.coords(country_data['text'], canvas_x, canvas_y)
                
                # Update stored coordinates
                country_data['x'] = canvas_x
                country_data['y'] = canvas_y
            
            # Update position data
            self.positions[self.drag_item]['x'] = rel_x
            self.positions[self.drag_item]['y'] = rel_y
            
            # Update input fields if this is the selected country
            if self.drag_item == self.selected_country:
                self.x_var.set(f"{rel_x:.3f}")
                self.y_var.set(f"{rel_y:.3f}")
    
    def on_canvas_release(self, event):
        """Handle canvas mouse release"""
        self.dragging = False
        self.drag_item = None
    
    def copy_dart_code(self):
        """Generate and copy Dart code to clipboard"""
        try:
            dart_code = self.generate_dart_code()
            
            # Copy to clipboard
            self.window.clipboard_clear()
            self.window.clipboard_append(dart_code)
            
            # Show success message
            messagebox.showinfo("Success", 
                              "Dart code copied to clipboard!\n\n"
                              "You can now paste it into:\n"
                              "lib/constants/country_positions.dart")
            
            self.log("📋 Dart code copied to clipboard")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy code: {str(e)}")
            self.log(f"❌ Error copying code: {e}")
    
    def generate_dart_code(self):
        """Generate the Dart code for country positions"""
        code = "const Map<String, CountryPosition> COUNTRY_POSITIONS = {\n"
        
        # Group by regions for better organization
        regions = {
            'North Africa': ['DZ', 'EG', 'LY', 'MA', 'TN'],
            'West Africa': ['BJ', 'BF', 'CV', 'CI', 'GM', 'GH', 'GN', 'GW', 'LR', 'ML', 'MR', 'NE', 'NG', 'SN', 'SL', 'TG'],
            'East Africa': ['BI', 'KM', 'DJ', 'ER', 'ET', 'KE', 'MG', 'MW', 'MU', 'MZ', 'RW', 'SC', 'SO', 'SS', 'SD', 'TZ', 'UG', 'ZM', 'ZW'],
            'Central Africa': ['AO', 'CM', 'CF', 'TD', 'CG', 'CD', 'GQ', 'GA', 'ST'],
            'Southern Africa': ['BW', 'LS', 'NA', 'ZA', 'SZ'],
        }
        
        # Country names for comments
        country_names = {
            'DZ': 'Algeria', 'EG': 'Egypt', 'LY': 'Libya', 'MA': 'Morocco', 'TN': 'Tunisia',
            'BJ': 'Benin', 'BF': 'Burkina Faso', 'CV': 'Cape Verde', 'CI': 'Côte d\'Ivoire',
            'GM': 'Gambia', 'GH': 'Ghana', 'GN': 'Guinea', 'GW': 'Guinea-Bissau',
            'LR': 'Liberia', 'ML': 'Mali', 'MR': 'Mauritania', 'NE': 'Niger',
            'NG': 'Nigeria', 'SN': 'Senegal', 'SL': 'Sierra Leone', 'TG': 'Togo',
            'BI': 'Burundi', 'KM': 'Comoros', 'DJ': 'Djibouti', 'ER': 'Eritrea',
            'ET': 'Ethiopia', 'KE': 'Kenya', 'MG': 'Madagascar', 'MW': 'Malawi',
            'MU': 'Mauritius', 'MZ': 'Mozambique', 'RW': 'Rwanda', 'SC': 'Seychelles',
            'SO': 'Somalia', 'SS': 'South Sudan', 'SD': 'Sudan', 'TZ': 'Tanzania',
            'UG': 'Uganda', 'ZM': 'Zambia', 'ZW': 'Zimbabwe',
            'AO': 'Angola', 'CM': 'Cameroon', 'CF': 'Central African Republic',
            'TD': 'Chad', 'CG': 'Congo', 'CD': 'Democratic Republic of the Congo',
            'GQ': 'Equatorial Guinea', 'GA': 'Gabon', 'ST': 'São Tomé and Príncipe',
            'BW': 'Botswana', 'LS': 'Lesotho', 'NA': 'Namibia', 'ZA': 'South Africa',
            'SZ': 'Eswatini'
        }
        
        for region_name, countries in regions.items():
            code += f"  // {region_name}\n"
            for country_code in countries:
                if country_code in self.positions:
                    pos = self.positions[country_code]
                    country_name = country_names.get(country_code, country_code)
                    code += f"  '{country_code}': CountryPosition({pos['x']:.3f}, {pos['y']:.3f}), // {country_name}\n"
            code += "\n"
        
        code += "};"
        return code
    
    def reset_positions(self):
        """Reset all positions to original values"""
        if messagebox.askyesno("Confirm Reset", 
                              "This will reset all positions to their original values. Continue?"):
            self.load_positions()
            self.canvas.delete("all")
            self.load_map_image()
            self.draw_country_points()
            self.log("🔄 Positions reset to original values")


def main():
    """Main application entry point"""
    root = tk.Tk()
    app = KumaDesktopApp(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()