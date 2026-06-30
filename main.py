import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

# 纸张尺寸定义 (300 DPI 下的像素分辨率)
PAGE_SIZES = {
    "A3": (3508, 4960),
    "A4": (2480, 3508)
}

class ImageGridApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片多宫格拼接工具")
        self.root.geometry("900x700")

        self.image_paths = []
        self.generated_pages = []  # 存储生成的 PIL Image 对象
        self.current_preview_idx = 0

        self.create_widgets()

    def create_widgets(self):
        # ---- 左侧控制面板 ----
        control_frame = ttk.LabelFrame(self.root, text="设置参数", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # 纸张大小
        ttk.Label(control_frame, text="纸张大小:").pack(anchor=tk.W, pady=2)
        self.size_var = tk.StringVar(value="A4")
        ttk.Combobox(control_frame, textvariable=self.size_var, values=list(PAGE_SIZES.keys()), state="readonly").pack(fill=tk.X, pady=5)

        # 纸张方向
        ttk.Label(control_frame, text="纸张方向:").pack(anchor=tk.W, pady=2)
        self.orient_var = tk.StringVar(value="竖向")
        ttk.Combobox(control_frame, textvariable=self.orient_var, values=["竖向", "横向"], state="readonly").pack(fill=tk.X, pady=5)

        # 宫格样式
        ttk.Label(control_frame, text="宫格布局:").pack(anchor=tk.W, pady=2)
        self.grid_var = tk.StringVar(value="4宫格 (上下各2张)")
        ttk.Combobox(control_frame, textvariable=self.grid_var, values=["4宫格 (上下各2张)", "6宫格 (上下各3张)"], state="readonly").pack(fill=tk.X, pady=5)

        # 按钮区
        ttk.Button(control_frame, text="选择多张图片", command=self.load_images).pack(fill=tk.X, pady=15)
        ttk.Button(control_frame, text="生成拼接预览", command=self.generate_grid).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="导出全部JPG", command=self.save_images).pack(fill=tk.X, pady=15)

        # 分页预览控制
        self.page_label = ttk.Label(control_frame, text="页码: 0 / 0")
        self.page_label.pack(pady=10)
        
        btn_prev = ttk.Button(control_frame, text="上一页", command=self.prev_page)
        btn_prev.pack(fill=tk.X, pady=2)
        btn_next = ttk.Button(control_frame, text="下一页", command=self.next_page)
        btn_next.pack(fill=tk.X, pady=2)

        # ---- 右侧预览面板 ----
        preview_frame = ttk.LabelFrame(self.root, text="实时预览 (等比缩放)", padding=10)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(preview_frame, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self.on_resize)

    def load_images(self):
        files = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.webp")]
        )
        if files:
            self.image_paths = list(files)
            messagebox.showinfo("成功", f"已成功加载 {len(self.image_paths)} 张图片！")

    def generate_grid(self):
        if not self.image_paths:
            messagebox.showwarning("警告", "请先选择图片！")
            return

        # 1. 确定画布尺寸
        base_w, base_h = PAGE_SIZES[self.size_var.get()]
        if self.orient_var.get() == "横向":
            canvas_w, canvas_h = base_h, base_w
        else:
            canvas_w, canvas_h = base_w, base_h

        # 2. 确定行列数
        grid_style = self.grid_var.get()
        if "4宫格" in grid_style:
            cols, rows = 2, 2
        else:
            cols, rows = 3, 2

        images_per_page = cols * rows
        self.generated_pages = []

        # 计算单张图片的格子大小
        cell_w = canvas_w // cols
        cell_h = canvas_h // rows

        # 3. 分页拼图
        for i in range(0, len(self.image_paths), images_per_page):
            page_img = Image.new("RGB", (canvas_w, canvas_h), "white")
            page_paths = self.image_paths[i:i+images_per_page]

            for idx, img_path in enumerate(page_paths):
                try:
                    with Image.open(img_path) as img:
                        # 计算当前格子位置
                        r = idx // cols
                        c = idx % cols
                        x_offset = c * cell_w
                        y_offset = r * cell_h

                        # 保持比例缩放并居中填满/适应格子
                        img_ratio = img.width / img.height
                        cell_ratio = cell_w / cell_h

                        if img_ratio > cell_ratio:
                            # 图片更宽，以格子宽度为准
                            new_w = cell_w
                            new_h = int(cell_w / img_ratio)
                        else:
                            # 图片更高，以格子高度为准
                            new_h = cell_h
                            new_w = int(cell_h * img_ratio)

                        resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        
                        # 居中放置
                        final_x = x_offset + (cell_w - new_w) // 2
                        final_y = y_offset + (cell_h - new_h) // 2
                        
                        page_img.paste(resized_img, (final_x, final_y))
                except Exception as e:
                    print(f"处理图片出错 {img_path}: {e}")

            self.generated_pages.append(page_img)

        self.current_preview_idx = 0
        self.update_preview()

    def update_preview(self):
        if not self.generated_pages:
            return

        total_pages = len(self.generated_pages)
        self.page_label.config(text=f"页码: {self.current_preview_idx + 1} / {total_pages}")

        # 获取画布当前大小
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w < 10 or canvas_h < 10:
            return

        # 等比缩放 PIL Image 以适应 Tkinter Canvas
        current_img = self.generated_pages[self.current_preview_idx]
        img_ratio = current_img.width / current_img.height
        canvas_ratio = canvas_w / canvas_h

        if img_ratio > canvas_ratio:
            view_w = canvas_w
            view_h = int(canvas_w / img_ratio)
        else:
            view_h = canvas_h
            view_w = int(canvas_h * img_ratio)

        # 缩放用于预览
        preview_img = current_img.resize((view_w, view_h), Image.Resampling.BILINEAR)
        self.tk_img = ImageTk.PhotoImage(preview_img)

        # 居中绘制
        self.canvas.delete("all")
        self.canvas.create_image(canvas_w // 2, canvas_h // 2, image=self.tk_img, anchor=tk.CENTER)

    def on_resize(self, event):
        # 窗口大小改变时自动刷新预览
        if self.generated_pages:
            self.update_preview()

    def prev_page(self):
        if self.current_preview_idx > 0:
            self.current_preview_idx -= 1
            self.update_preview()

    def next_page(self):
        if self.current_preview_idx < len(self.generated_pages) - 1:
            self.current_preview_idx += 1
            self.update_preview()

    def save_images(self):
        if not self.generated_pages:
            messagebox.showwarning("警告", "没有可导出的拼图，请先生成预览！")
            return

        out_dir = filedialog.askdirectory(title="选择保存目录")
        if not out_dir:
            return

        try:
            for idx, page_img in enumerate(self.generated_pages):
                save_path = os.path.join(out_dir, f"output_page_{idx + 1}.jpg")
                page_img.save(save_path, "JPEG", quality=95)
            
            messagebox.showinfo("成功", f"所有图片已成功导出至：\n{out_dir}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGridApp(root)
    root.mainloop()
