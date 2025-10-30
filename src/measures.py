# módulo de medidas
# Implementa o cálculo  área total de cada componente por frame e da área de NC@DC por frame
import numpy as np
from typing import Dict, List
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
import pandas as pd
from labeling import (
    label_connected_components, 
    get_total_area,
    get_island_masks
)
from morpho import dilate_3x3


def measure_areas_per_frame(masks: Dict[str, np.ndarray]) -> Dict[str, int]:
    areas = {}
    
    for component, mask in masks.items():
        areas[component] = get_total_area(mask)
    
    return areas


def compute_nc_at_dc(mask_nc: np.ndarray, mask_dc: np.ndarray) -> int:
    # Se não há NC ou DC, retorna 0
    if not np.any(mask_nc) or not np.any(mask_dc):
        return 0
    
    # Rotula ilhas NC
    num_labels, labels_nc, stats_nc, _ = label_connected_components(mask_nc)
    
    # Dilata máscara NC completa em 1 pixel
    mask_nc_dilated = dilate_3x3(mask_nc)
    
    # Identifica região de contato (overlap entre NC dilatado e DC)
    contact_region = np.logical_and(mask_nc_dilated, mask_dc).astype(np.uint8) * 255
    
    # Encontra quais labels NC tocam a região de contato
    touching_labels = set()
    
    for label in range(1, num_labels):  # Ignora background (0)
        # Máscara da ilha NC específica
        island_mask = (labels_nc == label).astype(np.uint8) * 255
        
        # Dilata a ilha
        island_dilated = dilate_3x3(island_mask)
        
        # Verifica se toca DC
        if np.any(np.logical_and(island_dilated, mask_dc)):
            touching_labels.add(label)
    
    # 5. Soma áreas das ilhas NC que tocam DC
    nc_at_dc_area = 0
    for label in touching_labels:
        area = stats_nc[label, 4]  # Coluna 4 = CC_STAT_AREA
        nc_at_dc_area += area
    
    return nc_at_dc_area


def measure_frame_complete(masks: Dict[str, np.ndarray]) -> Dict[str, int]:
    #  áreas de todos os componentes
    areas = measure_areas_per_frame(masks)
    
    # NC@DC
    areas['NC_AT_DC'] = compute_nc_at_dc(masks['NC'], masks['DC'])
    
    return areas


def process_all_frames(vh_frames: List[np.ndarray], 
                       create_masks_func) -> List[Dict[str, int]]:
    results = []
    
    print("\n=== Processando medidas (Item I e II) ===")
    
    for frame_idx, vh_frame in enumerate(vh_frames):
        # Cria máscaras
        masks = create_masks_func(vh_frame)
        
        # Realiza medidas
        measures = measure_frame_complete(masks)
        
        results.append(measures)
        
        # Feedback
        if (frame_idx + 1) % 10 == 0 or frame_idx == 0:
            print(f"  Frame {frame_idx}: FB={measures['FB']}, "
                  f"NC={measures['NC']}, NC@DC={measures['NC_AT_DC']}")
    
    print(f" Processados {len(results)} frames")
    
    return results


def create_results_dataframe(measures_list: List[Dict[str, int]]):
    
    data = []
    
    for frame_idx, measures in enumerate(measures_list):
        row = {
            'quadro': frame_idx,
            'lumen_area': measures['LUMEN'],
            'media_area': measures['MEDIA'],
            'fb_area': measures['FB'],
            'ff_area': measures['FF'],
            'nc_area': measures['NC'],
            'dc_area': measures['DC'],
            'nc@dc_area': measures['NC_AT_DC']
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    return df


def print_summary_statistics(df):
    print("\n=== Estatísticas Resumidas ===")
    print("\nÁreas médias por componente:")
    
    components = ['lumen_area', 'media_area', 'fb_area', 'ff_area', 
                  'nc_area', 'dc_area', 'nc@dc_area']
    
    for comp in components:
        mean_val = df[comp].mean()
        std_val = df[comp].std()
        max_val = df[comp].max()
        min_val = df[comp].min()
        print(f"  {comp:15s}: {mean_val:8.1f} ± {std_val:6.1f} "
              f"(min={min_val:6.0f}, max={max_val:6.0f})")
