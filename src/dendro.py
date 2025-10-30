# Gera dendrograma hierárquico comparando as distribuições de intensidade dos diferentes componentes usando os histogramas.

import numpy as np
from typing import Dict
import plotly.figure_factory as ff
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage


def normalize_histogram(hist: np.ndarray) -> np.ndarray:
    total = np.sum(hist)
    if total == 0:
        return np.zeros_like(hist, dtype=np.float64)
    return hist.astype(np.float64) / total


def create_feature_matrix(histograms: Dict[str, np.ndarray]) -> tuple:
    """
    Args:
        histograms: Dicionário  
    Returns:
        Tupla (feature_matrix, labels)
        - feature_matrix: Array (n_components, 256) com histogramas normalizados
        - labels: Lista de nomes dos componentes
    """
    labels = []
    features = []
    
    for component, hist in histograms.items():
        labels.append(component)
        norm_hist = normalize_histogram(hist)
        features.append(norm_hist)
    
    feature_matrix = np.array(features)
    
    return feature_matrix, labels


def compute_distance_matrix(feature_matrix: np.ndarray, 
                           metric: str = 'euclidean') -> np.ndarray:
    """
    Args:
        feature_matrix: Array (n_samples, n_features)
        metric: Métrica de distância ('euclidean', 'correlation', 'cosine', etc.)
        
    Returns:
        Matriz de distâncias (n_samples, n_samples)
    """
    # Calcula distâncias par-a-par (condensed form)
    distances_condensed = pdist(feature_matrix, metric=metric)
    
    # Converte para square form
    distance_matrix = squareform(distances_condensed)
    
    return distance_matrix


def create_dendrogram_plotly(histograms: Dict[str, np.ndarray],
                            output_path: str = None,
                            metric: str = 'euclidean',
                            linkage_method: str = 'ward') -> None:
    """
    Args:
        histograms: Dicionário 
        output_path: Caminho para salvar a figura (PNG ou HTML)
        metric: Métrica de distância ('euclidean', 'correlation', 'cosine')
        linkage_method: Método de linkage ('ward', 'average', 'complete', 'single')
    """
    print("\n=== Gerando dendrograma (Item IV) ===")
    
    # Cria matriz de features
    feature_matrix, labels = create_feature_matrix(histograms)
    
    print(f"  Componentes: {', '.join(labels)}")
    print(f"  Métrica: {metric}")
    print(f"  Método de linkage: {linkage_method}")
    
    # Cria dendrograma 
    fig = ff.create_dendrogram(
        feature_matrix,
        labels=labels,
        linkagefun=lambda x: linkage(x, method=linkage_method, metric=metric)
    )
    
    # Customiza layout
    fig.update_layout(
        title={
            'text': 'Dendrograma - Similaridade entre Componentes<br><sub>Baseado em histogramas de intensidade GS-IVUS</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis={
            'title': 'Componente',
            'tickfont': {'size': 14}
        },
        yaxis={
            'title': f'Distância ({metric})',
            'tickfont': {'size': 14}
        },
        width=1000,
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    
    if output_path:
        from pathlib import Path
        output_path = Path(output_path)
        
        if output_path.suffix == '.html':
            fig.write_html(str(output_path))
        else:
            
            fig.write_image(str(output_path), width=1000, height=600)
        
        print(f"Salvo: {output_path.name}")
    
    # Mostra figura
    # fig.show() 
    
    print("Dendrograma gerado")
    
    return fig


def print_distance_matrix(histograms: Dict[str, np.ndarray], 
                         metric: str = 'euclidean'):
    feature_matrix, labels = create_feature_matrix(histograms)
    distance_matrix = compute_distance_matrix(feature_matrix, metric=metric)
    
    print(f"\n=== Matriz de Distâncias ({metric}) ===")
    
    # Cabeçalho
    print(f"{'':10s}", end='')
    for label in labels:
        print(f"{label:>10s}", end='')
    print()
    
    # Linhas
    for i, label_i in enumerate(labels):
        print(f"{label_i:10s}", end='')
        for j in range(len(labels)):
            print(f"{distance_matrix[i, j]:10.4f}", end='')
        print()


def find_most_similar_pairs(histograms: Dict[str, np.ndarray],
                           metric: str = 'euclidean',
                           top_n: int = 3):
    feature_matrix, labels = create_feature_matrix(histograms)
    distance_matrix = compute_distance_matrix(feature_matrix, metric=metric)
    
    # Extrai pares e distâncias (triângulo superior, excluindo diagonal)
    pairs = []
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            pairs.append((labels[i], labels[j], distance_matrix[i, j]))
    
    # Ordena por distância (menor = mais similar)
    pairs.sort(key=lambda x: x[2])
    
    print(f"\n=== Top {top_n} Pares Mais Similares ({metric}) ===")
    for rank, (comp1, comp2, dist) in enumerate(pairs[:top_n], 1):
        print(f"  {rank}. {comp1} ↔ {comp2}: distância = {dist:.4f}")
    
    print(f"\n=== Top {top_n} Pares Mais Distintos ({metric}) ===")
    for rank, (comp1, comp2, dist) in enumerate(reversed(pairs[-top_n:]), 1):
        print(f"  {rank}. {comp1} ↔ {comp2}: distância = {dist:.4f}")
