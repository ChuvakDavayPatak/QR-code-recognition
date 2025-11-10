# -*- coding: cp1251 -*-
import cv2
import numpy as np
from PIL import Image
import os
import traceback
import sys

PYZBAR_AVAILABLE = False

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    PYZBAR_AVAILABLE = True
    print("PyZBar доступен для QR-кодов")
except ImportError:
    print("PyZBar не доступен. Установите: pip install pyzbar")

class ImageProcessor:
    """Класс для обработки изображений (только для QR-кодов)"""
    def __init__(self, image_path: str):
        self.original_path = image_path
        self.scale = 1.0
        try:
            print(f"Загрузка изображения: {image_path}")
            pil_image = Image.open(image_path)
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            self.image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            self.original_image = self.image.copy()
            print(f"Изображение загружено. Размер: {self.image.shape}")
        except Exception as e:
            print(f"Ошибка при загрузке изображения: {str(e)}")
            raise ValueError(f"Не удалось загрузить изображение: {str(e)}")
    
    def optimize_size(self):
        """Усиленная оптимизация для мелких QR-кодов"""
        h, w = self.image.shape[:2]
        max_dim = max(h, w)
    
        # Критически маленькие изображения (менее 500px)
        if max_dim < 500:
            self.scale = 1500 / max_dim
            new_w, new_h = int(w * self.scale), int(h * self.scale)
            self.image = cv2.resize(self.image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            print(f"Критическое увеличение до: {new_w}x{new_h} (масштаб: {self.scale:.2f})")
    
        # Маленькие изображения (500-800px)
        elif max_dim < 800:
            self.scale = 1200 / max_dim
            new_w, new_h = int(w * self.scale), int(h * self.scale)
            self.image = cv2.resize(self.image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            print(f"Умеренное увеличение до: {new_w}x{new_h} (масштаб: {self.scale:.2f})")
    
        # Слишком большие изображения
        elif max_dim > 1800:
            self.scale = 1400 / max_dim
            new_w, new_h = int(w * self.scale), int(h * self.scale)
            self.image = cv2.resize(self.image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            print(f"Умеренное уменьшение до: {new_w}x{new_h} (масштаб: {self.scale:.2f})")
    
        # Оптимальный размер
        else:
            self.scale = 1.0
            print(f"Размер без изменений: {w}x{h} (масштаб: {self.scale:.2f})")
    
        print(f"Размер после оптимизации: {self.image.shape[1]}x{self.image.shape[0]}")

    def create_processing_variants(self):
        """Улучшенные варианты обработки для сложных QR-кодов"""
        if len(self.image.shape) == 3:
            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        else:
            gray = self.image
            hsv = None
    
        variants = {
            'original': gray,
            'clahe': self._enhance_clahe(gray),
            'binary_otsu': self._binarize_otsu(gray),
            'binary_adaptive': self._binarize_adaptive(gray),
            'color_enhanced': self._enhance_color(hsv) if hsv is not None else gray
        }
        return variants

    def _enhance_color(self, hsv):
        """Улучшение цветовых QR-кодов"""
        # Увеличиваем насыщенность и яркость
        hsv[:,:,1] = cv2.convertScaleAbs(hsv[:,:,1], alpha=1.3)
        hsv[:,:,2] = cv2.convertScaleAbs(hsv[:,:,2], alpha=1.2)
    
        # Возвращаем к BGR для PyZBar
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    def _enhance_clahe(self, gray):
        """Улучшение контраста через CLAHE"""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(10, 10))
        return clahe.apply(gray)
    
    def _binarize_otsu(self, gray):
        """Бинаризация с Otsu"""
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    
    def _binarize_adaptive(self, gray):
        """Улучшенная адаптивная бинаризация"""
        # Маленькие блоки для мелких QR-кодов
        small_blocks = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
    
        # Большие блоки для крупных QR-кодов
        large_blocks = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 21, 3
        )
    
        # Комбинируем результаты
        combined = cv2.bitwise_and(small_blocks, large_blocks)
        return combined
    
    def get_original_image(self):
        return self.original_image

class FastQRDecoder:
    """Декодер для QR-кодов с мульти-проверкой"""
    def __init__(self):
        if not PYZBAR_AVAILABLE:
            raise RuntimeError("PyZBar не установлен. Для работы с QR-кодами требуется: pip install pyzbar")
        self.supported_formats = ["QRCODE"]
    
    def decode(self, variants):
        """Мульти-сканирование через все варианты обработки + поиск в мелких фрагментах"""
        all_results = []
        print(f"=== МУЛЬТИ-СКАНИРОВАНИЕ ===")
    
        # 1. Основное сканирование всех вариантов
        for variant_name, image in variants.items():
            print(f"Проверка варианта: {variant_name}")
            try:
                decoded = pyzbar_decode(image)
                print(f"  Найдено {len(decoded)} объектов в варианте '{variant_name}'")
            
                for obj in decoded:
                    if obj.type != 'QRCODE':
                        continue
                
                    data_str = obj.data.decode('utf-8', errors='ignore') if isinstance(obj.data, bytes) else str(obj.data)
                    print(f"    [QR] {data_str[:30]}... (Размер: {obj.rect.width}x{obj.rect.height})")
                    all_results.append((variant_name, obj))
                
            except Exception as e:
                print(f"  Ошибка при сканировании варианта '{variant_name}': {e}")

        print("=== ДОПОЛНИТЕЛЬНЫЙ ПОИСК В МЕЛКИХ ФРАГМЕНТАХ ===")
        small_results = []
    
        for variant_name, image in variants.items():
            # Обрабатываем только основные варианты для ускорения
            if variant_name not in ['original', 'clahe', 'color_enhanced']:
                continue
        
            h, w = image.shape[:2]
            fragment_size = min(h, w) // 3  # Делим на 9 частей (3x3)
        
            # Сканируем сетку 3x3
            for i in range(3):
                for j in range(3):
                    x_start = max(0, j * fragment_size - fragment_size // 4)
                    y_start = max(0, i * fragment_size - fragment_size // 4)
                    x_end = min(w, x_start + fragment_size + fragment_size // 2)
                    y_end = min(h, y_start + fragment_size + fragment_size // 2)
                
                    fragment = image[y_start:y_end, x_start:x_end]
                
                    try:
                        decoded = pyzbar_decode(fragment)
                        for obj in decoded:
                            if obj.type != 'QRCODE':
                                continue
                        
                            # Корректируем координаты относительно исходного изображения
                            obj.rect.left += x_start
                            obj.rect.top += y_start
                            small_results.append((variant_name, obj))
                    except Exception as e:
                        continue
    
        # Добавляем результаты поиска в фрагментах
        all_results.extend(small_results)
        print(f"Найдено в мелких фрагментах: {len(small_results)}")

        # 3. Усиленная фильтрация дубликатов
        unique_results = []
    
        for variant, obj in all_results:
            is_duplicate = False
        
            for _, existing_obj in unique_results:
                # Используем улучшенную проверку пересечения
                if self._is_overlapping(obj.rect, existing_obj.rect, threshold=0.5):
                    is_duplicate = True
                    break
        
            if not is_duplicate:
                unique_results.append((variant, obj))
    
        print(f"Уникальных QR-кодов после усиленной фильтрации: {len(unique_results)}")
        return unique_results

    def _is_overlapping(self, rect1, rect2, threshold=0.5):
        """Улучшенная проверка пересечения с учетом размера"""
        x1, y1, w1, h1 = rect1.left, rect1.top, rect1.width, rect1.height
        x2, y2, w2, h2 = rect2.left, rect2.top, rect2.width, rect2.height
    
        # Если один код явно больше другого - снижаем порог
        size_ratio = max(w1*h1, w2*h2) / min(w1*h1, w2*h2)
        adjusted_threshold = threshold * (1.0 if size_ratio < 2.0 else 0.7)
    
        inter_x1 = max(x1, x2)
        inter_y1 = max(y1, y2)
        inter_x2 = min(x1 + w1, x2 + w2)
        inter_y2 = min(y1 + h1, y2 + h2)
    
        inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
        area1 = w1 * h1
        area2 = w2 * h2
    
        # Проверяем пересечение относительно меньшей области
        if area1 < area2:
            overlap = inter_area / area1
        else:
            overlap = inter_area / area2
    
        return overlap > adjusted_threshold

class BarcodeRecognizer:
    """Основной класс для распознавания (только QR-коды)"""
    def __init__(self, image_path: str):
        self.image_path = image_path

    def recognize(self) -> dict:
        """Распознавание QR-кодов с мульти-проверкой"""
        try:
            print(f"Обработка QR-кода: {os.path.basename(self.image_path)}")
            
            # Загрузка и обработка изображения
            processor = ImageProcessor(self.image_path)
            processor.optimize_size()
            variants = processor.create_processing_variants()
            
            # Мульти-сканирование
            decoder = FastQRDecoder()
            detected = decoder.decode(variants)
            
            # Коррекция масштаба и форматирование результатов
            results = []
            scale_factor = 1.0 / processor.scale
            
            for variant, obj in detected:
                rect = obj.rect
                scaled_rect = type('Rect', (), {
                    'left': int(rect.left * scale_factor),
                    'top': int(rect.top * scale_factor),
                    'width': int(rect.width * scale_factor),
                    'height': int(rect.height * scale_factor)
                })
                
                data_str = obj.data.decode('utf-8', errors='ignore') if isinstance(obj.data, bytes) else str(obj.data)
                results.append({
                    'data': data_str,
                    'type': 'QRCODE',
                    'rect': scaled_rect,
                    'polygon': [(int(x * scale_factor), int(y * scale_factor)) for x, y in obj.polygon],
                    'variant_used': variant
                })
            
            return {
            'success': len(results) > 0,
            'results': results,
            'image': processor.get_original_image(),
            'processed_variants': variants if 'variants' in locals() else {},
            'scale_factor': processor.scale if 'processor' in locals() else 1.0,
            'supported_formats': ['QRCODE']
        }
        except Exception as e:
            error_msg = f"{str(e)}"
            print(f"Ошибка: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'results': [],
                'processed_variants': {},
                'supported_formats': ['QRCODE']
            }