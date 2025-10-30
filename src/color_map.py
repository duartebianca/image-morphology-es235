#Módulo de mapeamento de cores VH-IVUS para classes de componentes.
# Mapeia as cores da imagem VH-IVUS para rótulos de classe:

import numpy as np
import cv2
from typing import Dict, Tuple

# Definição das classes de componentes
COMPONENTS = ['FB', 'FF', 'NC', 'DC', 'LUMEN', 'MEDIA']

# Mapeamento de cores BGR
COLOR_MAP_BGR = {
    'FB': (0, 128, 0),        # Verde escuro (Fibrotic)
    'FF': (0, 255, 128),      # Verde-amarelado (Fibro-Fatty)
    'NC': (0, 0, 255),        # Vermelho (Necrotic Core)
    'DC': (255, 255, 255),    # Branco (Dense Calcium)
    'LUMEN': (0, 0, 0),       # Preto (Lumen)
    'MEDIA': (128, 128, 128)  # Cinza (Media)
}

# Tolerâncias para match de cor
COLOR_TOLERANCE = 30

# distancia euclidiana entre duas cores BGR
def color_distance(color1: Tuple[int, int, int], 
                   color2: Tuple[int, int, int]) -> float:
    """
    Args:
        color1: Tupla BGR (B, G, R)
        color2: Tupla BGR (B, G, R)
    """
    return np.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2)))


def classify_pixel_by_color(pixel_bgr: Tuple[int, int, int]) -> str:
    min_distance = float('inf')
    best_match = 'UNKNOWN'
    
    for component, color_ref in COLOR_MAP_BGR.items():
        dist = color_distance(pixel_bgr, color_ref)
        if dist < min_distance:
            min_distance = dist
            best_match = component
    
    # Retorna apenas se dentro da tolerância
    if min_distance <= COLOR_TOLERANCE:
        return best_match
    else:
        return 'UNKNOWN'


def create_binary_masks(vh_frame: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Este método usa nearest color matching com distância Euclidiana no espaço BGR.
    Args:
        vh_frame: Frame VH-IVUS em formato BGR (H×W×3)
    Returns:
        Dicionário com máscaras binárias uint8 para cada componente
    """
    height, width = vh_frame.shape[:2]
    
    # Inicializa máscaras vazias
    masks = {comp: np.zeros((height, width), dtype=np.uint8) 
             for comp in COMPONENTS}
    
    for component, target_color in COLOR_MAP_BGR.items():
        # Calcula distância de cada pixel para a cor alvo
        diff = vh_frame.astype(np.float32) - np.array(target_color, dtype=np.float32)
        distances = np.sqrt(np.sum(diff ** 2, axis=2))
        
        # Pixels dentro da tolerância pertencem ao componente
        masks[component][distances <= COLOR_TOLERANCE] = 255
    
    return masks


def create_binary_masks_optimized(vh_frame: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Args:
        vh_frame: Frame VH-IVUS em formato BGR (H×W×3)
        
    Returns:
        Dicionário com máscaras binárias uint8 para cada componente
    """
    height, width = vh_frame.shape[:2]
    
    # Inicializa máscaras vazias
    masks = {comp: np.zeros((height, width), dtype=np.uint8) 
             for comp in COMPONENTS}
    
    # Cria array de distâncias para cada componente
    distances = np.zeros((height, width, len(COMPONENTS)), dtype=np.float32)
    
    for i, (component, target_color) in enumerate(COLOR_MAP_BGR.items()):
        diff = vh_frame.astype(np.float32) - np.array(target_color, dtype=np.float32)
        distances[:, :, i] = np.sqrt(np.sum(diff ** 2, axis=2))
    
    # Para cada pixel, encontra o componente mais próximo
    closest_component = np.argmin(distances, axis=2)
    
    # Preenche as máscaras
    for i, component in enumerate(COMPONENTS):
        masks[component][closest_component == i] = 255
    
    return masks


def visualize_masks(masks: Dict[str, np.ndarray], 
                    output_path: str = None) -> np.ndarray:
    """
    Args:
        masks: Dicionário de máscaras binárias
        output_path: Caminho para salvar a visualização
        
    Returns:
        Imagem BGR colorida com as máscaras
    """
    height, width = list(masks.values())[0].shape
    vis = np.zeros((height, width, 3), dtype=np.uint8)
    
    for component, mask in masks.items():
        color = COLOR_MAP_BGR[component]
        vis[mask > 0] = color
    
    if output_path:
        cv2.imwrite(output_path, vis)
    
    return vis


def print_mask_statistics(masks: Dict[str, np.ndarray], frame_idx: int = None):
    """
    Args:
        masks: Dicionário de máscaras binárias
        frame_idx: Índice do frame
    """
    if frame_idx is not None:
        print(f"\nEstatísticas do Frame {frame_idx}:")
    else:
        print("\nEstatísticas das Máscaras:")
    
    total_pixels = list(masks.values())[0].size
    
    for component in COMPONENTS:
        mask = masks[component]
        count = np.count_nonzero(mask)
        percentage = (count / total_pixels) * 100
        print(f"  {component:6s}: {count:6d} pixels ({percentage:5.2f}%)")
