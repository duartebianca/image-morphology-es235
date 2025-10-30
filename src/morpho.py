# Módulo de operações morfológicas.
import numpy as np
import cv2


def get_se_3x3() -> np.ndarray:
    return np.ones((3, 3), dtype=np.uint8)


def erode_3x3(binary_mask: np.ndarray) -> np.ndarray:
    se = get_se_3x3()
    eroded = cv2.erode(binary_mask, se, iterations=1)
    return eroded


def dilate_3x3(binary_mask: np.ndarray) -> np.ndarray:
    se = get_se_3x3()
    dilated = cv2.dilate(binary_mask, se, iterations=1)
    return dilated


def get_interior_pixels(binary_mask: np.ndarray) -> np.ndarray:
    return erode_3x3(binary_mask)


def get_interior_pixels_from_islands(island_masks: dict) -> np.ndarray:
    if not island_masks:
        return np.zeros((1, 1), dtype=np.uint8)
    
    # Pega dimensões da primeira máscara
    sample_mask = list(island_masks.values())[0]
    height, width = sample_mask.shape
    
    # Inicializa máscara de resultado
    interior_union = np.zeros((height, width), dtype=np.uint8)
    
    # Para cada ilha, extrai interior e une
    for label, island_mask in island_masks.items():
        interior = erode_3x3(island_mask)
        interior_union = cv2.bitwise_or(interior_union, interior)
    
    return interior_union


def opening_3x3(binary_mask: np.ndarray) -> np.ndarray:
    se = get_se_3x3()
    opened = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, se)
    return opened


def closing_3x3(binary_mask: np.ndarray) -> np.ndarray:
    se = get_se_3x3()
    closed = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, se)
    return closed


def get_boundary_pixels(binary_mask: np.ndarray) -> np.ndarray:
    eroded = erode_3x3(binary_mask)
    boundary = cv2.subtract(binary_mask, eroded)
    return boundary


def check_contact(mask1: np.ndarray, mask2: np.ndarray) -> bool:
    # Dilata mask1 para incluir vizinhança de 1 pixel
    mask1_dilated = dilate_3x3(mask1)
    
    # Verifica se há overlap entre mask1_dilated e mask2
    contact = cv2.bitwise_and(mask1_dilated, mask2)
    
    return np.any(contact > 0)


def get_contact_mask(mask1: np.ndarray, mask2: np.ndarray) -> np.ndarray:
    mask1_dilated = dilate_3x3(mask1)
    contact = cv2.bitwise_and(mask1_dilated, mask2)
    return contact
