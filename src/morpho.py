# Módulo de operações morfológicas - implementação manual
import numpy as np


def get_se_3x3() -> np.ndarray:
    return np.ones((3, 3), dtype=np.uint8)


def create_structuring_element(shape: str, ksize) -> np.ndarray:

    rows, cols = ksize
    element = np.zeros(ksize, dtype=np.uint8)
    
    center_y, center_x = rows // 2, cols // 2
    
    if shape == 'rect':
        element[:, :] = 1
    elif shape == 'ellipse':
        for i in range(rows):
            for j in range(cols):
                y = (i - center_y) / (center_y + 0.5)
                x = (j - center_x) / (center_x + 0.5)
                if x*x + y*y <= 1.0:
                    element[i, j] = 1
    elif shape == 'cross':
        element[center_y, :] = 1
        element[:, center_x] = 1
    else:
        raise ValueError(f"Shape desconhecida: {shape}")
    
    return element


def erode_manual(image: np.ndarray, kernel: np.ndarray, iterations: int = 1) -> np.ndarray:

    result = image.copy()
    for _ in range(iterations):
        result = _erode_once(result, kernel)
    return result


def _erode_once(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    if len(image.shape) == 3:
        image = image[:, :, 0]
    
    rows, cols = image.shape
    k_rows, k_cols = kernel.shape
    k_center_y, k_center_x = k_rows // 2, k_cols // 2
    
    result = np.zeros_like(image)
    padded = np.pad(image, 
                    ((k_center_y, k_center_y), (k_center_x, k_center_x)),
                    mode='constant', constant_values=0)
    
    for i in range(rows):
        for j in range(cols):
            region = padded[i:i+k_rows, j:j+k_cols]
            matches = True
            for ki in range(k_rows):
                for kj in range(k_cols):
                    if kernel[ki, kj] == 1 and region[ki, kj] < 255:
                        matches = False
                        break
                if not matches:
                    break
            result[i, j] = 255 if matches else 0
    
    return result


def dilate_manual(image: np.ndarray, kernel: np.ndarray, iterations: int = 1) -> np.ndarray:
    result = image.copy()
    for _ in range(iterations):
        result = _dilate_once(result, kernel)
    return result


def _dilate_once(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:

    if len(image.shape) == 3:
        image = image[:, :, 0]
    
    rows, cols = image.shape
    k_rows, k_cols = kernel.shape
    k_center_y, k_center_x = k_rows // 2, k_cols // 2
    
    result = np.zeros_like(image)
    padded = np.pad(image,
                    ((k_center_y, k_center_y), (k_center_x, k_center_x)),
                    mode='constant', constant_values=0)
    
    for i in range(rows):
        for j in range(cols):
            region = padded[i:i+k_rows, j:j+k_cols]
            has_white = False
            for ki in range(k_rows):
                for kj in range(k_cols):
                    if kernel[ki, kj] == 1 and region[ki, kj] == 255:
                        has_white = True
                        break
                if has_white:
                    break
            result[i, j] = 255 if has_white else 0
    
    return result


def opening_manual(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    eroded = erode_manual(image, kernel, iterations=1)
    opened = dilate_manual(eroded, kernel, iterations=1)
    return opened


def closing_manual(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    dilated = dilate_manual(image, kernel, iterations=1)
    closed = erode_manual(dilated, kernel, iterations=1)
    return closed


def morphological_gradient_manual(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    dilated = dilate_manual(image, kernel, iterations=1)
    eroded = erode_manual(image, kernel, iterations=1)
    gradient = np.clip(dilated.astype(int) - eroded.astype(int), 0, 255).astype(np.uint8)
    return gradient


def get_interior_pixels_manual(binary_mask: np.ndarray) -> np.ndarray:
    kernel = get_se_3x3()
    return erode_manual(binary_mask, kernel, iterations=1)


def get_boundary_pixels_manual(binary_mask: np.ndarray) -> np.ndarray:
    kernel = get_se_3x3()
    eroded = erode_manual(binary_mask, kernel, iterations=1)
    boundary = np.clip(binary_mask.astype(int) - eroded.astype(int), 0, 255).astype(np.uint8)
    return boundary


def bitwise_or_manual(img1: np.ndarray, img2: np.ndarray) -> np.ndarray:
    """Operação OR bit a bit."""
    return np.bitwise_or(img1, img2)


def bitwise_and_manual(img1: np.ndarray, img2: np.ndarray) -> np.ndarray:
    """Operação AND bit a bit."""
    return np.bitwise_and(img1, img2)


def check_contact_manual(mask1: np.ndarray, mask2: np.ndarray) -> bool:
    """Verifica se duas máscaras têm contato (vizinhança 8-conectada)."""
    kernel = get_se_3x3()
    mask1_dilated = dilate_manual(mask1, kernel, iterations=1)
    contact = bitwise_and_manual(mask1_dilated, mask2)
    return np.any(contact > 0)


def get_contact_mask_manual(mask1: np.ndarray, mask2: np.ndarray) -> np.ndarray:
    """Retorna a máscara de contato entre duas máscaras."""
    kernel = get_se_3x3()
    mask1_dilated = dilate_manual(mask1, kernel, iterations=1)
    contact = bitwise_and_manual(mask1_dilated, mask2)
    return contact


def get_interior_pixels_from_islands_manual(island_masks: dict) -> np.ndarray:

    if not island_masks:
        return np.zeros((1, 1), dtype=np.uint8)
    
    sample_mask = list(island_masks.values())[0]
    height, width = sample_mask.shape
    interior_union = np.zeros((height, width), dtype=np.uint8)
    
    for label, island_mask in island_masks.items():
        interior = get_interior_pixels_manual(island_mask)
        interior_union = bitwise_or_manual(interior_union, interior)
    
    return interior_union


# ============================================================================
# API compatível com código existente
# ============================================================================


def erode_3x3(binary_mask: np.ndarray) -> np.ndarray:
    """Erosão 3x3."""
    se = get_se_3x3()
    return erode_manual(binary_mask, se, iterations=1)


def dilate_3x3(binary_mask: np.ndarray) -> np.ndarray:
    """Dilatação 3x3."""
    se = get_se_3x3()
    return dilate_manual(binary_mask, se, iterations=1)


def opening_3x3(binary_mask: np.ndarray) -> np.ndarray:
    """Abertura 3x3."""
    se = get_se_3x3()
    return opening_manual(binary_mask, se)


def closing_3x3(binary_mask: np.ndarray) -> np.ndarray:
    """Fechamento 3x3."""
    se = get_se_3x3()
    return closing_manual(binary_mask, se)


def get_interior_pixels(binary_mask: np.ndarray) -> np.ndarray:
    """Extrai pixels interiores."""
    return get_interior_pixels_manual(binary_mask)


def get_interior_pixels_from_islands(island_masks: dict) -> np.ndarray:
    """Extrai pixels interiores de ilhas."""
    return get_interior_pixels_from_islands_manual(island_masks)


def get_boundary_pixels(binary_mask: np.ndarray) -> np.ndarray:
    """Extrai pixels de borda."""
    return get_boundary_pixels_manual(binary_mask)


def check_contact(mask1: np.ndarray, mask2: np.ndarray) -> bool:
    """Verifica contato entre máscaras."""
    return check_contact_manual(mask1, mask2)


def get_contact_mask(mask1: np.ndarray, mask2: np.ndarray) -> np.ndarray:
    """Retorna máscara de contato."""
    return get_contact_mask_manual(mask1, mask2)
