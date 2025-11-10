# -*- coding: cp1251 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import cv2
from BarcodeProcessor import BarcodeRecognizer, PYZBAR_AVAILABLE

class BarcodeScannerApp:
    """Графический интерфейс"""

    def __init__(self, root):
        self.root = root
        self.root.title("Сканер QR-кодов")
        self.root.geometry("1000x800")

        # Переменные
        self.current_image = None
        self.photo_image = None
        self.current_result = None

        self.setup_ui()
        self.check_dependencies()

        # Цвета для QR-кодов (BGR для OpenCV)
        self.qr_colors_bgr = [
            (0, 255, 0),    # Зелёный
            (0, 0, 255),    # Красный
            (255, 0, 0),    # Синий
            (0, 255, 255),  # Жёлтый
            (255, 0, 255),  # Фиолетовый
            (255, 255, 0),  # Бирюзовый
            (128, 0, 128),  # Пурпурный
            (0, 165, 255),  # Оранжевый
            (0, 128, 0),    # Тёмно-зелёный
            (128, 128, 128),# Серый
            (0, 255, 127),  # Весенний зелёный
            (255, 0, 127),  # Розовый (насыщенный)
            (127, 0, 255),  # Аметист
            (0, 127, 255),  # Оранжево-жёлтый
            (255, 127, 0),  # Оранжево-красный
            (127, 255, 0),  # Лаймовый
            (0, 0, 128),    # Тёмно-синий
            (128, 0, 0),    # Тёмно-красный
            (0, 128, 128),  # Бирюзово-зелёный
            (128, 128, 0),  # Оливковый
            (192, 192, 192),# Серебряный
            (0, 69, 255),   # Шоколадный
            (255, 20, 147), # Глубокий розовый
            (255, 228, 196),# Бисквитный
            (205, 133, 63), # Перу
            (255, 99, 71),  # Томатный
            (238, 130, 238),# Фиолетовый (светлый)
            (210, 105, 30), # Шоколад
            (0, 206, 209),  # Тёмная бирюза
            (255, 192, 203) # Розовый
        ]

        # Цвета в HEX для Tkinter
        self.qr_colors_hex = [
            "#00FF00", "#FF0000", "#0000FF", "#FFFF00",
            "#FF00FF", "#00FFFF", "#800080", "#FFA500",
            "#008000", "#808080", "#7FFF00", "#7F00FF",
            "#FF007F", "#FF7F00", "#007FFF", "#00FF7F",
            "#800000", "#000080", "#008080", "#808000",
            "#C0C0C0", "#FF4500", "#9370DB", "#DC143C",
            "#DAA520", "#B22222", "#DDA0DD", "#8B4513",
            "#20B2AA", "#FFC0CB"
        ]

    def check_dependencies(self):
        """Проверка PyZBar"""
        if not PYZBAR_AVAILABLE:
            messagebox.showerror(
                "Ошибка", 
                "PyZBar не установлен!\n"
                "Для установки выполните:\n"
                "pip install pyzbar"
            )
            self.root.destroy()  # Завершает работу, т.к. без PyZBar ничего не работает

    def setup_ui(self):
        """Интерфейс"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        title_label = ttk.Label(main_frame, text="Сканер QR-кодов", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))

        ttk.Button(button_frame, text="Выбрать изображение", command=self.load_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Сканировать QR-код", command=self.scan_barcode).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Показать оригинал", command=self.show_original_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Показать обработанное", command=self.show_processed_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Информация", command=self.show_system_info).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Очистить", command=self.clear_all).pack(side=tk.LEFT, padx=5)

        # Изображение
        self.image_frame = ttk.LabelFrame(main_frame, text="Изображение", padding="5")
        self.image_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.image_label = ttk.Label(self.image_frame, text="Изображение не загружено", justify=tk.CENTER)
        self.image_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        self.image_info_var = tk.StringVar(value="")
        ttk.Label(self.image_frame, textvariable=self.image_info_var).pack(pady=5)

        # Результаты
        result_frame = ttk.LabelFrame(main_frame, text="Результаты сканирования", padding="5")
        result_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        columns = ("№", "Тип", "Данные")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=20)
        for col, width in zip(columns, [50, 100, 450]):
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=width)
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_tree.bind("<Double-1>", self.on_item_double_click)

        # Указание поддерживаемого формата
        ttk.Label(main_frame, text="Поддерживаемый формат: QR Code", 
                 font=('Arial', 10, 'bold'), foreground="green").grid(row=3, column=0, columnspan=2, pady=5)

        self.status_var = tk.StringVar(value="Готов к работе")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN).grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

    def load_image(self):
        """Загрузка изображения"""
        file_path = filedialog.askopenfilename(title="Выберите изображение",
                                               filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.gif"),
                                                          ("Все файлы", "*.*")])
        if not file_path:
            return

        try:
            self.current_image_path = file_path
            image = Image.open(file_path)
            width, height = image.size
            file_size = os.path.getsize(file_path) / 1024
            self.image_info_var.set(f"Размер: {width}x{height} | Файл: {file_size:.1f} КБ")

            display_image = self.resize_image_for_display(image)
            self.photo_image = ImageTk.PhotoImage(display_image)
            self.image_label.configure(image=self.photo_image)
            self.status_var.set(f"Загружено: {os.path.basename(file_path)}")

            for item in self.result_tree.get_children():
                self.result_tree.delete(item)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {str(e)}")

    def resize_image_for_display(self, image, max_size=(450, 550)):
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        return image

    def scan_barcode(self):
        if not hasattr(self, 'current_image_path'):
            messagebox.showwarning("Предупреждение", "Сначала выберите изображение")
            return

        try:
            self.status_var.set("Сканирование...")
            self.root.update()
            recognizer = BarcodeRecognizer(self.current_image_path)
            result = recognizer.recognize()
            self.current_result = result

            # Очистка таблицы
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)

            if result['success']:
                # Настройка цветовых тегов для Treeview
                for i in range(len(self.qr_colors_hex)):
                    self.result_tree.tag_configure(f"color_{i}", foreground=self.qr_colors_hex[i])
            
                # Добавление результатов с цветами
                for i, res in enumerate(result['results']):
                    color_index = i % len(self.qr_colors_bgr)
                    res['color_bgr'] = self.qr_colors_bgr[color_index]  # Для отрисовки рамок
                    res['color_hex'] = self.qr_colors_hex[color_index]  # Для текста в таблице
                
                    self.result_tree.insert(
                        "", "end", 
                        values=(i+1, res['type'], res['data']), 
                        tags=(f"color_{color_index}",)
                    )
            
                self.status_var.set(f"УСПЕХ: Найдено {len(result['results'])} QR-кодов")
                self.show_annotated_image(result)
                if len(result['results']) > 0:
                    # Сортируем по позиции (сверху-вниз, слева-направо)
                    result['results'].sort(key=lambda x: (x['rect'].top, x['rect'].left))
    
                    # Проверка на явные дубликаты по данным
                    unique_data = []
                    final_results = []
                    for res in result['results']:
                        if res['data'] not in unique_data:
                            unique_data.append(res['data'])
                            final_results.append(res)
    
                    result['results'] = final_results
            else:
                self.status_var.set("QR-коды не обнаружены")
                messagebox.showinfo("Результат", "QR-коды не обнаружены")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сканировании: {str(e)}")
            self.status_var.set("Ошибка при сканировании")

    def show_annotated_image(self, result):
        try:
            image = result['image'].copy()
        
            for res in result['results']:
                rect = res['rect']
                if rect and hasattr(rect, 'width') and rect.width > 0 and rect.height > 0:
                    # Получаем цвет из результата
                    color = res.get('color_bgr', (0, 255, 0))
                
                    # Рисуем рамку
                    cv2.rectangle(
                        image, 
                        (rect.left, rect.top), 
                        (rect.left + rect.width, rect.top + rect.height), 
                        color, 
                        3
                    )
                
                    # Подготовка текста с фоном
                    text = "QRCODE"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.6
                    thickness = 2
                
                    # Размеры текста
                    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
                
                    # Позиция текста (над рамкой)
                    text_x = max(rect.left, 5)
                    text_y = max(rect.top - 10, 20)
                
                    # Рисуем белый фон для текста
                    cv2.rectangle(
                        image,
                        (text_x - 3, text_y - text_height - 5),
                        (text_x + text_width + 3, text_y + 3),
                        (255, 255, 255),  # Белый фон
                        -1
                    )
                
                    # Рисуем цветной текст
                    cv2.putText(
                        image, 
                        text, 
                        (text_x, text_y),
                        font,
                        font_scale,
                        color,
                        thickness,
                        cv2.LINE_AA
                    )
        
            # Конвертация для отображения в Tkinter
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            display_image = self.resize_image_for_display(pil_image)
            self.photo_image = ImageTk.PhotoImage(display_image)
            self.image_label.configure(image=self.photo_image)
            self.status_var.set("QR-коды выделены цветом")
        
        except Exception as e:
            print(f"Ошибка при отображении изображения: {e}")
            self.status_var.set("Ошибка при отображении результатов")

    def show_original_image(self):
        if hasattr(self, 'current_image_path'):
            try:
                image = Image.open(self.current_image_path)
                display_image = self.resize_image_for_display(image)
                self.photo_image = ImageTk.PhotoImage(display_image)
                self.image_label.configure(image=self.photo_image)
                self.status_var.set("Показано оригинальное изображение")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def show_processed_image(self):
        if not self.current_result:
            messagebox.showinfo("Информация", "Сначала выполните сканирование")
            return
    
        # Используем clahe-вариант как основной для отображения
        if 'processed_variants' in self.current_result and 'clahe' in self.current_result['processed_variants']:
            processed = self.current_result['processed_variants']['clahe']
        
            # Если изображение серое, преобразуем в RGB для отображения
            if len(processed.shape) == 2:
                processed_rgb = cv2.cvtColor(processed, cv2.COLOR_GRAY2RGB)
            else:
                processed_rgb = processed
            
            pil_image = Image.fromarray(processed_rgb)
            display_image = self.resize_image_for_display(pil_image)
            self.photo_image = ImageTk.PhotoImage(display_image)
            self.image_label.configure(image=self.photo_image)
            self.status_var.set("Показано обработанное изображение (CLAHE)")
        else:
            messagebox.showinfo("Информация", "Обработанное изображение недоступно")

    def show_system_info(self):
        import sys
        info = f"""
        Версия Python: {sys.version}
        Поддерживаемые библиотеки:
        - OpenCV: {cv2.__version__}
        - pyzbar: {'Доступен' if PYZBAR_AVAILABLE else 'Не доступен'}

        Рекомендации:
        1. Используйте четкие изображения
        2. Поддерживаются форматы: QR Code
        """
        messagebox.showinfo("Информация о системе", info)

    def on_item_double_click(self, event):
        selection = self.result_tree.selection()
        if not selection:
            return
        item = selection[0]
        values = self.result_tree.item(item, 'values')
        if values:
            data_window = tk.Toplevel(self.root)
            data_window.title("Данные штрих-кода")
            data_window.geometry("600x400")

            text_frame = ttk.Frame(data_window, padding="10")
            text_frame.pack(fill=tk.BOTH, expand=True)

            text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Arial', 10))
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Временно устанавливаем состояние NORMAL для вставки текста
            text_widget.config(state=tk.NORMAL)
            text_widget.insert(tk.END, values[2])
            # Возвращаем состояние DISABLED, но теперь текст можно выделить и скопировать
            # Заметьте, что для копирования через Ctrl+C/Cmd+C или контекстное меню,
            # текст должен быть в состоянии NORMAL или "нормально" выделен.
            # Однако, Tkinter позволяет выделять и копировать текст из DISABLED,
            # если он был вставлен и затем состояние изменено.
            text_widget.config(state=tk.DISABLED)

            # Для более полного контроля и возможности копирования через контекстное меню
            # или горячие клавиши, обычно оставляют состояние NORMAL
            # и устанавливают атрибут readonly или биндят события.
            # Однако, самый простой способ разрешить копирование без редактирования:
            # - Оставить state=tk.NORMAL
            # - Сделать виджет "read-only" через биндинг
            
            # Вместо DISABLED можно сделать так, чтобы текст был только для чтения:
            text_widget.bind("<Key>", lambda e: "break") # Отключаем ввод с клавиатуры
            text_widget.bind("<Button-1>", lambda e: text_widget.focus_set()) # Позволяем фокусироваться для выделения
            text_widget.bind("<ButtonRelease-1>", lambda e: None) # Позволяем выделять
            text_widget.bind("<Button-2>", lambda e: None) # Средняя кнопка мыши (прокрутка)
            text_widget.bind("<Button-3>", self.show_copy_context_menu) # Правая кнопка мыши для меню

            # Добавляем кнопку "Копировать все"
            copy_button = ttk.Button(text_frame, text="Копировать все", command=lambda: self.copy_to_clipboard(text_widget))
            copy_button.pack(pady=5)

    def copy_to_clipboard(self, text_widget):
        """Копирует весь текст из виджета в буфер обмена."""
        text_content = text_widget.get("1.0", tk.END).strip()
        if text_content:
            self.root.clipboard_clear()
            self.root.clipboard_append(text_content)
            messagebox.showinfo("Копирование", "Текст скопирован в буфер обмена!")
        else:
            messagebox.showwarning("Копирование", "Нет текста для копирования.")

    def show_copy_context_menu(self, event):
        """Отображает контекстное меню "Копировать"."""
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Копировать", command=lambda: self.copy_selected_text(event.widget))
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def copy_selected_text(self, text_widget):
        """Копирует выделенный текст из виджета в буфер обмена."""
        try:
            selected_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
            else:
                messagebox.showwarning("Копирование", "Текст не выделен.")
        except tk.TclError: # Если ничего не выделено, tk.SEL_FIRST вызовет ошибку
            messagebox.showwarning("Копирование", "Текст не выделен.")

    def clear_all(self):
        self.image_label.configure(image='', text="Изображение не загружено")
        self.image_info_var.set("")
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        self.status_var.set("Готов к работе")
        if hasattr(self, 'current_image_path'):
            del self.current_image_path
        self.current_result = None


def main():
    root = tk.Tk()
    app = BarcodeScannerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()