import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from PIL import Image, ImageTk, ImageEnhance, ImageOps, ImageFilter
import os
import sys

# --- 资源路径函数 ---
def resource_path(relative_path):
    """ 获取资源绝对路径，适配开发环境和打包后的 exe 环境 """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 会将资源解压到 sys._MEIPASS
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# --- Character Sets ---
# 1. Simple: Good for very small icons or high contrast
CHARS_SIMPLE = ['.', ':', '*', '#', '@']

# 2. Standard: Balanced for most images
CHARS_STANDARD = [' ', '.', ':', '-', '=', '+', '*', '#', '%', '@']

# 3. High Detail: 70 characters for maximum detail (Standard ramp)
CHARS_HIGH = list("$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. ")


class AsciiArtGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("ASCII Art Generator Pro")
        self.root.geometry("1000x750")

        # Styles
        self.font_ui = ("Segoe UI", 9)
        self.font_art = ("Consolas", 9)  # Monospaced font is strictly required

        self.original_image = None

        # --- Layout ---
        # 1. Top Control Panel
        control_frame = tk.LabelFrame(root, text="Settings", padx=10, pady=10, font=self.font_ui)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Row 1: Load & Dimensions
        row1 = tk.Frame(control_frame)
        row1.pack(fill=tk.X, pady=2)

        self.btn_load = tk.Button(row1, text="Load Image", command=self.load_image, bg="#e0e0e0", font=self.font_ui)
        self.btn_load.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(row1, text="Width (chars):", font=self.font_ui).pack(side=tk.LEFT)
        self.entry_width = tk.Entry(row1, width=6, font=self.font_ui)
        self.entry_width.pack(side=tk.LEFT, padx=5)

        tk.Label(row1, text="Height (lines):", font=self.font_ui).pack(side=tk.LEFT)
        self.entry_height = tk.Entry(row1, width=6, font=self.font_ui)
        self.entry_height.pack(side=tk.LEFT, padx=5)

        self.lock_aspect = tk.BooleanVar(value=True)
        self.chk_aspect = tk.Checkbutton(row1, text="Lock Aspect Ratio (Fix Stretch)", variable=self.lock_aspect,
                                         command=self.update_height_suggestion, font=self.font_ui)
        self.chk_aspect.pack(side=tk.LEFT, padx=10)

        # Row 2: Detail & Mode
        row2 = tk.Frame(control_frame)
        row2.pack(fill=tk.X, pady=5)

        tk.Label(row2, text="Detail Mode:", font=self.font_ui).pack(side=tk.LEFT)
        self.combo_mode = ttk.Combobox(row2,
                                       values=["High Detail (70 chars)", "Standard (10 chars)", "Simple (5 chars)"],
                                       state="readonly", width=20)
        self.combo_mode.current(1)  # Default to Standard
        self.combo_mode.pack(side=tk.LEFT, padx=5)

        tk.Label(row2, text="Contrast Boost:", font=self.font_ui).pack(side=tk.LEFT, padx=(15, 0))
        self.scale_contrast = tk.Scale(row2, from_=1.0, to=3.0, resolution=0.1, orient=tk.HORIZONTAL, length=100)
        self.scale_contrast.set(1.5)  # Default 1.5x
        self.scale_contrast.pack(side=tk.LEFT, padx=5)

        self.btn_convert = tk.Button(row2, text="GENERATE", command=self.generate_ascii, bg="#4CAF50", fg="white",
                                     font=("Segoe UI", 9, "bold"), width=15)
        self.btn_convert.pack(side=tk.LEFT, padx=20)

        # 2. Main Display Area
        paned = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashwidth=4, bg="#d9d9d9")
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left: Preview
        self.preview_frame = tk.Frame(paned, bg="#f0f0f0", width=300)
        self.preview_label = tk.Label(self.preview_frame, text="Image Preview", bg="#f0f0f0", font=self.font_ui)
        self.preview_label.pack(expand=True)
        paned.add(self.preview_frame, minsize=200)

        # Right: Text Output
        self.text_area = scrolledtext.ScrolledText(paned, font=self.font_art, undo=False,
                                                   wrap=tk.NONE)  # No wrap to keep lines straight
        paned.add(self.text_area, minsize=400)

        # 3. Bottom Bar
        bottom_frame = tk.Frame(root, pady=5)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10)

        self.btn_copy = tk.Button(bottom_frame, text="Copy to Clipboard", command=self.copy_to_clipboard, bg="#2196F3",
                                  fg="white", font=self.font_ui)
        self.btn_copy.pack(side=tk.RIGHT)

        self.status_label = tk.Label(bottom_frame, text="Ready", anchor=tk.W, font=self.font_ui, fg="#666")
        self.status_label.pack(side=tk.LEFT)

        default_path = resource_path("default.jpg")

        self.original_image = None

        # 为了复用逻辑，建议把加载图片的核心逻辑独立出来，或者在这里直接写
        if os.path.exists(default_path):
            try:
                self.load_image_from_path(default_path)
            except Exception as e:
                print(f"Error loading default image: {e}")


        # 建议拆分一个加载指定路径图片的函数

    def load_image_from_path(self, path):
            self.original_image = Image.open(path)

            # 显示预览
            display_img = self.original_image.copy()
            display_img.thumbnail((300, 300))
            self.photo = ImageTk.PhotoImage(display_img)
            # 注意：这里需要确保 self.preview_label 已经创建了
            if hasattr(self, 'preview_label'):
                self.preview_label.config(image=self.photo, text="")

            # 设置默认宽度
            if hasattr(self, 'entry_width') and not self.entry_width.get():
                self.entry_width.insert(0, "120")

            self.update_height_suggestion()
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"Loaded: {os.path.basename(path)}")

        # 原来的 load_image 修改一下，调用上面的函数
    def load_image(self):
            file_path = filedialog.askopenfilename(
                title="Select Image",
                filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All Files", "*.*")]
            )
            if file_path:
                self.load_image_from_path(file_path)

    def update_height_suggestion(self):
        if not self.original_image or not self.lock_aspect.get():
            return

        try:
            w = int(self.entry_width.get())
            img_w, img_h = self.original_image.size
            ratio = img_h / img_w
            # Aspect Ratio Correction Factor (0.55 is standard for most fonts)
            h = int(w * ratio * 0.55)
            h = max(1, h)

            self.entry_height.delete(0, tk.END)
            self.entry_height.insert(0, str(h))
        except ValueError:
            pass

    def get_char_set(self):
        mode = self.combo_mode.get()
        if "High" in mode:
            # Need to reverse this list because user wants dark=@, light=.
            # The standard string "$@..." usually goes from Dark to Light.
            # So we keep it as is if 0=dark, 255=white.
            # Let's verify mapping logic later.
            return CHARS_HIGH
        elif "Standard" in mode:
            return CHARS_STANDARD
        else:
            return CHARS_SIMPLE

    def generate_ascii(self):
        if not self.original_image:
            messagebox.showwarning("Warning", "Please load an image first.")
            return

        try:
            target_w = int(self.entry_width.get())
            target_h = int(self.entry_height.get())
        except ValueError:
            messagebox.showerror("Error", "Width and Height must be integers.")
            return

        self.status_label.config(text="Processing...")
        self.root.update()

        # 1. Resize Image (using LANCZOS for quality)
        img = self.original_image.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # 2. Convert to Grayscale
        img = img.convert("L")

        # 3. Enhance Quality
        # Auto-Contrast: Maximizes the difference between dark and light pixels
        img = ImageOps.autocontrast(img)

        # Manual Contrast Boost
        contrast_val = self.scale_contrast.get()
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast_val)

        # Sharpen: Helps define edges at low resolution
        img = img.filter(ImageFilter.SHARPEN)

        # 4. Map Pixels to Characters
        chars = self.get_char_set()
        pixels = img.getdata()
        ascii_str = ""

        num_chars = len(chars)
        range_width = 255 / num_chars

        for i, pixel_val in enumerate(pixels):
            # Mapping logic:
            # If CHARS list is ['dark', ..., 'light']: index = pixel_val // range_width
            # If CHARS list is ['light', ..., 'dark']: index = (255 - pixel_val) // range_width

            # Check the definition of our lists:
            # CHARS_HIGH starts with '$' (Dark) -> ends with ' ' (Light)
            # CHARS_SIMPLE starts with '.' (Light) -> ends with '@' (Dark)

            mode = self.combo_mode.get()

            if "High" in mode:
                # High list is Dark -> Light ($ ... space)
                # Pixel 0 (black) should be index 0 ($)
                # Pixel 255 (white) should be last index (space)
                index = int(pixel_val / 255 * (num_chars - 1))
            else:
                # Simple/Standard lists are Light -> Dark (. ... @)
                # Pixel 0 (black) should be last index (@)
                # Pixel 255 (white) should be first index (.)
                index = int((255 - pixel_val) / 255 * (num_chars - 1))

            # Safety clamp
            index = max(0, min(index, num_chars - 1))

            ascii_str += chars[index]

            if (i + 1) % target_w == 0:
                ascii_str += "\n"

        # 5. Output
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, ascii_str)
        self.status_label.config(text=f"Done! {target_w}x{target_h} chars.")

    def copy_to_clipboard(self):
        content = self.text_area.get(1.0, tk.END)
        if not content.strip():
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.status_label.config(text="Copied to clipboard!")


if __name__ == "__main__":
    root = tk.Tk()
    app = AsciiArtGenerator(root)
    root.mainloop()