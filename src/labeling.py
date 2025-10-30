# Implementa rotulagem 8-conectada de ilhas manualmente usando algoritmo Two-Pass.
# Fornece estatísticas de área, centroide e outros atributos das regiões.
import numpy as np
from typing import Tuple, List, Dict


class UnionFind:
    """
    Estrutura Union-Find (Disjoint Set Union) para gerenciar equivalências de rótulos.
    Usada no algoritmo Two-Pass para unir componentes conectados.
    """
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x: int) -> int:
        """Encontra a raiz do conjunto que contém x (com compressão de caminho)."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x: int, y: int):
        """Une os conjuntos que contêm x e y (com união por rank)."""
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x != root_y:
            # União por rank para manter a árvore balanceada
            if self.rank[root_x] < self.rank[root_y]:
                self.parent[root_x] = root_y
            elif self.rank[root_x] > self.rank[root_y]:
                self.parent[root_y] = root_x
            else:
                self.parent[root_y] = root_x
                self.rank[root_x] += 1


def label_connected_components(binary_mask: np.ndarray, 
                               connectivity: int = 8) -> Tuple[int, np.ndarray, np.ndarray, np.ndarray]:
    """
    Implementação manual do algoritmo Two-Pass para rotulação de componentes conectados.
    
    Algoritmo:
    1. Primeira passagem: atribui rótulos temporários e registra equivalências
    2. Segunda passagem: substitui rótulos temporários pelos rótulos finais
    3. Calcula estatísticas (área, bounding box, centroides)
    
    Args:
        binary_mask: Máscara binária (0 ou 255) em uint8
        connectivity: 4 ou 8 (conectividade dos vizinhos)
        
    Returns:
        num_labels: Número total de componentes (incluindo background)
        labels: Array com rótulos de cada pixel (0 = background)
        stats: Array Nx5 com [left, top, width, height, area] para cada componente
        centroids: Array Nx2 com [cx, cy] para cada componente
    """
    # Garante que a máscara é binária (0 ou 255)
    binary_mask = (binary_mask > 0).astype(np.uint8) * 255
    
    height, width = binary_mask.shape
    labels = np.zeros((height, width), dtype=np.int32)
    
    # Define os offsets de vizinhos baseado na conectividade
    if connectivity == 8:
        # 8-conectividade: verifica vizinhos acima e à esquerda (diagonal incluída)
        neighbor_offsets = [
            (-1, -1),  # noroeste
            (-1,  0),  # norte
            (-1,  1),  # nordeste
            ( 0, -1),  # oeste
        ]
    else:  # connectivity == 4
        # 4-conectividade: verifica apenas vizinhos vertical e horizontal
        neighbor_offsets = [
            (-1,  0),  # norte
            ( 0, -1),  # oeste
        ]
    
    # Primeira passagem: atribui rótulos temporários
    next_label = 1
    uf = UnionFind(height * width)  # Pior caso: cada pixel é um rótulo
    
    for y in range(height):
        for x in range(width):
            # Ignora pixels de background
            if binary_mask[y, x] == 0:
                continue
            
            # Verifica rótulos dos vizinhos já processados
            neighbor_labels = []
            for dy, dx in neighbor_offsets:
                ny, nx = y + dy, x + dx
                # Verifica se está dentro dos limites e não é background
                if 0 <= ny < height and 0 <= nx < width and labels[ny, nx] > 0:
                    neighbor_labels.append(labels[ny, nx])
            
            if not neighbor_labels:
                # Nenhum vizinho rotulado: cria novo rótulo
                labels[y, x] = next_label
                next_label += 1
            else:
                # Usa o menor rótulo dos vizinhos
                min_label = min(neighbor_labels)
                labels[y, x] = min_label
                
                # Registra equivalências entre todos os rótulos vizinhos
                for label in neighbor_labels:
                    if label != min_label:
                        uf.union(min_label, label)
    
    # Mapeamento de rótulos temporários para rótulos finais
    label_mapping = {}
    final_label = 1
    
    for temp_label in range(1, next_label):
        root = uf.find(temp_label)
        if root not in label_mapping:
            label_mapping[root] = final_label
            final_label += 1
    
    # Segunda passagem: substitui rótulos temporários pelos finais
    for y in range(height):
        for x in range(width):
            if labels[y, x] > 0:
                root = uf.find(labels[y, x])
                labels[y, x] = label_mapping[root]
    
    num_labels = final_label  # Inclui o background (label 0)
    
    # Calcula estatísticas de cada componente
    stats, centroids = _calculate_statistics(labels, num_labels)
    
    return num_labels, labels, stats, centroids


def _calculate_statistics(labels: np.ndarray, num_labels: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calcula estatísticas para cada componente rotulado.
    
    Args:
        labels: Array com rótulos de cada pixel
        num_labels: Número total de componentes (incluindo background)
        
    Returns:
        stats: Array Nx5 com [left, top, width, height, area] para cada componente
        centroids: Array Nx2 com [cx, cy] para cada componente
    """
    height, width = labels.shape
    
    # Inicializa arrays de estatísticas
    stats = np.zeros((num_labels, 5), dtype=np.int32)
    centroids = np.zeros((num_labels, 2), dtype=np.float64)
    
    # Para cada componente, inicializa bounding box com valores extremos
    min_x = np.full(num_labels, width, dtype=np.int32)
    min_y = np.full(num_labels, height, dtype=np.int32)
    max_x = np.full(num_labels, -1, dtype=np.int32)
    max_y = np.full(num_labels, -1, dtype=np.int32)
    
    # Acumuladores para centroides
    sum_x = np.zeros(num_labels, dtype=np.float64)
    sum_y = np.zeros(num_labels, dtype=np.float64)
    areas = np.zeros(num_labels, dtype=np.int32)
    
    # Percorre todos os pixels para calcular estatísticas
    for y in range(height):
        for x in range(width):
            label = labels[y, x]
            
            # Atualiza área
            areas[label] += 1
            
            # Atualiza bounding box
            if min_x[label] > x:
                min_x[label] = x
            if max_x[label] < x:
                max_x[label] = x
            if min_y[label] > y:
                min_y[label] = y
            if max_y[label] < y:
                max_y[label] = y
            
            # Acumula coordenadas para centroide
            sum_x[label] += x
            sum_y[label] += y
    
    # Preenche o array de estatísticas
    for label in range(num_labels):
        if areas[label] > 0:
            # Stats formato: [left, top, width, height, area]
            stats[label, 0] = min_x[label]  # left
            stats[label, 1] = min_y[label]  # top
            stats[label, 2] = max_x[label] - min_x[label] + 1  # width
            stats[label, 3] = max_y[label] - min_y[label] + 1  # height
            stats[label, 4] = areas[label]  # area
            
            # Centroide: média das coordenadas
            centroids[label, 0] = sum_x[label] / areas[label]  # cx
            centroids[label, 1] = sum_y[label] / areas[label]  # cy
        else:
            # Background ou componente vazio
            stats[label, :] = 0
            centroids[label, :] = 0.0
    
    return stats, centroids


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
    # Formato stats: [left, top, width, height, area]
    areas = []
    for label in range(1, num_labels):
        area = stats[label, 4]  # Área está na coluna 4
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
    # Formato stats: [left, top, width, height, area]
    for label in range(1, num_labels):
        area = stats[label, 4]  # Área está na coluna 4
        if area >= min_area:
            # Mantém a ilha
            filtered_mask[labels == label] = 255
    
    return filtered_mask


def get_island_masks(binary_mask: np.ndarray, 
                     min_area: int = 0) -> Dict[int, np.ndarray]:
    num_labels, labels, stats, centroids = label_connected_components(binary_mask)
    
    island_masks = {}
    
    # Formato stats: [left, top, width, height, area]
    for label in range(1, num_labels):
        area = stats[label, 4]  # Área está na coluna 4
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
    # Formato stats: [left, top, width, height, area]
    island_areas = [stats[label, 4]  # Área está na coluna 4
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
