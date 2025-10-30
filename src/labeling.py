# Implementa rotulagem 8-conectada de ilhas usando cv2.connectedComponentsWithStats.
# Fornece estatísticas de área, centroide e outros atributos das regiões.
import numpy as np
import cv2
from typing import Tuple, List, Dict


def label_connected_components(binary_mask: np.ndarray, 
                               connectivity: int = 8) -> Tuple[int, np.ndarray, np.ndarray, np.ndarray]:
    # Garante que a máscara é binária (0 ou 255)
    binary_mask = (binary_mask > 0).astype(np.uint8) * 255
    
    # Aplica connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binary_mask, connectivity=connectivity, ltype=cv2.CV_32S
    )
    
    return num_labels, labels, stats, centroids


def get_island_areas(binary_mask: np.ndarray, 
                     min_area: int = 0) -> List[int]:
    """
    Args:
        binary_mask: Máscara binária uint8
        min_area: Área mínima para incluir a ilha (default: 0 = todas)
        
    Returns:
        Lista de áreas em pixels² (número de pixels por ilha)
    """
    num_labels, labels, stats, centroids = label_connected_components(binary_mask)
    
    # Extrai áreas (coluna 4 do stats), excluindo background 
    areas = []
    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        if area >= min_area:
            areas.append(area)
    
    return areas


def get_total_area(binary_mask: np.ndarray) -> int:
    return np.count_nonzero(binary_mask)


def filter_islands_by_size(binary_mask: np.ndarray, 
                           min_area: int = 5) -> np.ndarray:
    num_labels, labels, stats, centroids = label_connected_components(binary_mask)
    
    # Cria máscara de saída
    filtered_mask = np.zeros_like(binary_mask)
    
    # Para cada ilha (excluindo background)
    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        if area >= min_area:
            # Mantém a ilha
            filtered_mask[labels == label] = 255
    
    return filtered_mask


def get_island_masks(binary_mask: np.ndarray, 
                     min_area: int = 0) -> Dict[int, np.ndarray]:
    num_labels, labels, stats, centroids = label_connected_components(binary_mask)
    
    island_masks = {}
    
    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        if area >= min_area:
            # Cria máscara individual da ilha
            island_mask = np.zeros_like(binary_mask)
            island_mask[labels == label] = 255
            island_masks[label] = island_mask
    
    return island_masks


def get_component_statistics(binary_mask: np.ndarray) -> Dict:
    """
    Returns:
        Dicionário com:
        - total_area: Área total em pixels²
        - num_islands: Número de ilhas
        - island_areas: Lista de áreas individuais
        - largest_island: Área da maior ilha
        - smallest_island: Área da menor ilha
        - mean_island_area: Área média das ilhas
    """
    num_labels, labels, stats, centroids = label_connected_components(binary_mask)
    
    # Extrai áreas das ilhas (excluindo background)
    island_areas = [stats[label, cv2.CC_STAT_AREA] 
                    for label in range(1, num_labels)]
    
    num_islands = len(island_areas)
    
    if num_islands == 0:
        return {
            'total_area': 0,
            'num_islands': 0,
            'island_areas': [],
            'largest_island': 0,
            'smallest_island': 0,
            'mean_island_area': 0
        }
    
    return {
        'total_area': sum(island_areas),
        'num_islands': num_islands,
        'island_areas': island_areas,
        'largest_island': max(island_areas),
        'smallest_island': min(island_areas),
        'mean_island_area': np.mean(island_areas)
    }


def print_component_statistics(binary_mask: np.ndarray, 
                               component_name: str = "Componente"):
    """
    Imprime estatísticas do componente (útil para debug).
    
    Args:
        binary_mask: Máscara binária uint8
        component_name: Nome do componente para exibição
    """
    stats = get_component_statistics(binary_mask)
    
    print(f"\n{component_name}:")
    print(f"  Área total: {stats['total_area']} pixels²")
    print(f"  Número de ilhas: {stats['num_islands']}")
    
    if stats['num_islands'] > 0:
        print(f"  Maior ilha: {stats['largest_island']} pixels²")
        print(f"  Menor ilha: {stats['smallest_island']} pixels²")
        print(f"  Área média: {stats['mean_island_area']:.1f} pixels²")
