# Coleta intensidades GS-IVUS dos pixels interiores de ilhas >=5px e computa histogramas de 256 bins (0-255).
import numpy as np
from typing import Dict, List
import sys
from pathlib import Path
from labeling import label_connected_components
from morpho import dilate_3x3
import matplotlib.pyplot as plt
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from labeling import (
    filter_islands_by_size,
    get_island_masks
)
from morpho import get_interior_pixels_from_islands


def collect_interior_intensities(mask: np.ndarray, 
                                 gs_frame: np.ndarray,
                                 min_island_size: int = 5) -> np.ndarray:
    # Filtra ilhas pequenas
    mask_filtered = filter_islands_by_size(mask, min_area=min_island_size)
    
    if not np.any(mask_filtered):
        return np.array([], dtype=np.uint8)
    
    # Obtém máscaras individuais das ilhas
    island_masks = get_island_masks(mask_filtered, min_area=min_island_size)
    
    # Extrai pixels interiores de cada ilha e une
    interior_mask = get_interior_pixels_from_islands(island_masks)
    
    # Coleta intensidades dos pixels interiores
    intensities = gs_frame[interior_mask > 0]
    
    return intensities


def compute_histogram_256(intensities: np.ndarray) -> np.ndarray:
    if len(intensities) == 0:
        return np.zeros(256, dtype=np.int64)
    hist, _ = np.histogram(intensities, bins=256, range=(0, 256))
    
    return hist


def collect_all_frames_intensities(masks_all_frames: List[Dict[str, np.ndarray]],
                                   gs_frames: List[np.ndarray],
                                   component: str,
                                   min_island_size: int = 5) -> np.ndarray:
    all_intensities = []
    
    for frame_idx, (masks, gs_frame) in enumerate(zip(masks_all_frames, gs_frames)):
        mask = masks[component]
        intensities = collect_interior_intensities(mask, gs_frame, min_island_size)
        all_intensities.append(intensities)
    
    # Concatena todos os frames
    if all_intensities:
        return np.concatenate(all_intensities)
    else:
        return np.array([], dtype=np.uint8)


def compute_nc_at_dc_mask(mask_nc: np.ndarray, mask_dc: np.ndarray) -> np.ndarray:
    
    if not np.any(mask_nc) or not np.any(mask_dc):
        return np.zeros_like(mask_nc)
    
    # Rotula ilhas NC
    num_labels, labels_nc, stats_nc, _ = label_connected_components(mask_nc)
    
    # Identifica ilhas NC que tocam DC
    touching_labels = set()
    
    for label in range(1, num_labels):
        island_mask = (labels_nc == label).astype(np.uint8) * 255
        island_dilated = dilate_3x3(island_mask)
        
        if np.any(np.logical_and(island_dilated, mask_dc)):
            touching_labels.add(label)
    
    # Cria máscara NC@DC
    nc_at_dc_mask = np.zeros_like(mask_nc)
    for label in touching_labels:
        nc_at_dc_mask[labels_nc == label] = 255
    
    return nc_at_dc_mask


def process_histograms_all_components(masks_all_frames: List[Dict[str, np.ndarray]],
                                     gs_frames: List[np.ndarray]) -> Dict[str, np.ndarray]:
    """
    Processa histogramas para todos os componentes (Item III).
    
    Componentes: FB, FF, NC, DC, LUMEN, MEDIA, NC@DC
    
    Args:
        masks_all_frames: Lista de dicionários de máscaras
        gs_frames: Lista de frames GS-IVUS
        
    Returns:
        Dicionário {componente: histogram_256}
        onde histogram_256 é array de 256 elementos com contagens
    """
    components = ['FB', 'FF', 'NC', 'DC', 'LUMEN', 'MEDIA']
    histograms = {}
    
    print("\n=== Computando histogramas (Item III) ===")
    
    # Componentes regulares
    for component in components:
        print(f"  Processando {component}...")
        intensities = collect_all_frames_intensities(
            masks_all_frames, gs_frames, component, min_island_size=5
        )
        hist = compute_histogram_256(intensities)
        histograms[component] = hist
        print(f"    Total de pixels interiores: {len(intensities)}")
    
    # NC@DC especial
    print("  Processando NC@DC...")
    nc_at_dc_intensities = []
    
    for frame_idx, (masks, gs_frame) in enumerate(zip(masks_all_frames, gs_frames)):
        # Cria máscara NC@DC
        nc_at_dc_mask = compute_nc_at_dc_mask(masks['NC'], masks['DC'])
        
        # Coleta intensidades
        intensities = collect_interior_intensities(nc_at_dc_mask, gs_frame, min_island_size=5)
        nc_at_dc_intensities.append(intensities)
    
    nc_at_dc_all = np.concatenate(nc_at_dc_intensities) if nc_at_dc_intensities else np.array([])
    histograms['NC@DC'] = compute_histogram_256(nc_at_dc_all)
    print(f"    Total de pixels interiores: {len(nc_at_dc_all)}")
    
    print("✓ Histogramas computados")
    
    return histograms


def create_histogram_dataframe(histograms: Dict[str, np.ndarray]):
    """
    Cria DataFrame pandas com histogramas.
    
    Args:
        histograms: Dicionário {componente: histogram_256}
        
    Returns:
        DataFrame com colunas:
        [componente, total_pixels, h0, h1, ..., h255]
    """
    import pandas as pd
    
    data = []
    
    for component, hist in histograms.items():
        row = {
            'componente': component.lower(),
            'total_pixels': int(np.sum(hist))
        }
        
        # Adiciona bins h0 a h255
        for bin_idx in range(256):
            row[f'h{bin_idx}'] = int(hist[bin_idx])
        
        data.append(row)
    
    df = pd.DataFrame(data)
    
    return df


def plot_histograms(histograms: Dict[str, np.ndarray], output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n=== Gerando gráficos de histogramas ===")
    
    # Cores para cada componente
    colors = {
        'FB': 'green',
        'FF': 'yellowgreen',
        'NC': 'red',
        'DC': 'lightgray',
        'LUMEN': 'black',
        'MEDIA': 'gray',
        'NC@DC': 'darkred'
    }
    
    for component, hist in histograms.items():
        plt.figure(figsize=(10, 6))
        
        bins = np.arange(256)
        plt.bar(bins, hist, width=1.0, color=colors.get(component, 'blue'), 
                alpha=0.7, edgecolor='none')
        
        plt.xlabel('Intensidade (0-255)', fontsize=12)
        plt.ylabel('Frequência', fontsize=12)
        plt.title(f'Histograma - {component}', fontsize=14, fontweight='bold')
        plt.grid(axis='y', alpha=0.3)
        plt.xlim(0, 255)
        
        # Salva
        output_path = output_dir / f'hist_{component.lower()}.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"{output_path.name}")
    
    print("Gráficos salvos")
