import cv2
from PIL import Image
from pyzbar.pyzbar import decode as pyzbar_decode
import numpy as np
import os

image_path = "C:/Users/Михаил/source/repos/Barcode/HelloAztec.png" # Убедитесь, что путь правильный
# или лучше: image_path = "hello_aztec_test.png" # Положите его в ту же папку, что и скрипт

try:
    if not os.path.exists(image_path):
        print(f"Ошибка: Файл не найден по пути: {image_path}")
        exit()

    pil_image = Image.open(image_path)
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
        
    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    gray_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

    print(f"Тестируем Aztec Code на {image_path} (размер: {gray_image.shape})")
    
    decoded_objects = pyzbar_decode(gray_image)

    if decoded_objects:
        print(f"PyZBar нашел {len(decoded_objects)} объектов:")
        for obj in decoded_objects:
            data = obj.data.decode('utf-8', errors='ignore')
            print(f"  Тип: {obj.type}, Данные: {data}, Rect: {obj.rect}")
    else:
        print("PyZBar не нашел Aztec Code.")

except ImportError:
    print("Ошибка: pyzbar не установлен. pip install pyzbar")
except Exception as e:
    print(f"Произошла ошибка: {e}")
