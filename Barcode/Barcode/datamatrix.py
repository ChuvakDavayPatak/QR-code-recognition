# -*- coding: cp1251 -*-
import cv2
from PIL import Image
import pylibdmtx.pylibdmtx as dmtx_module
import numpy as np
import os

image_path = "C:/Users/Михаил/source/repos/Barcode/DATAMATRIX.png"

try:
    if not os.path.exists(image_path):
        print(f"Ошибка: Файл не найден по пути: {image_path}")
        exit()

    pil_image = Image.open(image_path)
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
        
    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    gray_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

    print(f"Тестируем DataMatrix Code на {image_path} (размер: {gray_image.shape})")
    
    decoded_objects = dmtx_module.decode(gray_image)

    if decoded_objects:
        print(f"pylibdmtx нашел {len(decoded_objects)} объектов:")
        for obj in decoded_objects:
            data = obj.data.decode('utf-8', errors='ignore')
            print(f"  Тип: DATA_MATRIX, Данные: {data}, Rect: {obj.rect}")
    else:
        print("pylibdmtx не нашел DataMatrix Code.")

except ImportError:
    print("Ошибка: pylibdmtx не установлен. pip install pylibdmtx")
except Exception as e:
    print(f"Произошла ошибка: {e}")
