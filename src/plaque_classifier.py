# Este módulo implementa a classificação automática de placas baseada nas áreas dos componentes 
import numpy as np
from typing import Dict, List


def classify_plaque(areas: Dict[str, float]) -> str:
    """
    Classifica o tipo de placa aterosclerótica baseado nas áreas dos componentes.
    Critérios de classificação:
    1. VH-TCFA: NC >= 10% da placa + NC confluente (em contato com DC ou superfície)
    2. ThCFA: NC >= 10% da placa + NC não confluente (coberto por capa fibrosa)
    3. FIB: Predominância de tecido fibrótico (FB > 50%)
    4. FibCa: Tecido fibrótico com calcificação significativa (FB alto + DC > 10%)
    5. PIT: Espessamento intimal com predominância de FF ou sem NC significativo
    """
    # Área total da placa (exclui lúmen e média - componentes não-placa)
    plaque_area = (areas['fb_area'] + areas['ff_area'] + 
                   areas['nc_area'] + areas['dc_area'])
    
    # Se não há placa detectável, retorna UNKNOWN
    if plaque_area == 0:
        return 'UNKNOWN'
    
    # Calcula porcentagens dos componentes em relação à área da placa
    nc_percent = (areas['nc_area'] / plaque_area) * 100
    fb_percent = (areas['fb_area'] / plaque_area) * 100
    dc_percent = (areas['dc_area'] / plaque_area) * 100
    ff_percent = (areas['ff_area'] / plaque_area) * 100
    
    # Presença significativa de NC (>=10%) 
    if nc_percent >= 10:
        # Verifica se NC está confluente (exposto/conectado)
        # NC@DC indica NC em contato com cálcio ou outras estruturas
        # Se NC@DC representa >50% do NC total, consideramos confluente
        nc_confluent_ratio = 0
        if areas['nc_area'] > 0:
            nc_confluent_ratio = areas['nc@dc_area'] / areas['nc_area']
        
        if nc_confluent_ratio > 0.5:
            # NC confluente/exposto = Alto risco de ruptura
            return 'VH-TCFA'
        else:
            # NC não confluente (coberto por capa fibrosa espessa)
            return 'ThCFA'
    
    # Predominância de tecido fibrótico (FB > 50%) 
    if fb_percent > 50:
        # Verifica se há calcificação significativa associada
        if dc_percent > 10:
            # Placa fibrocalcífica (FB + DC)
            return 'FibCa'
        else:
            # Placa fibrótica pura (estável)
            return 'FIB'
    
    # Espessamento Intimal Patológico (PIT) 
    # Predominância de FF ou pouco NC sem predominância de FB
    if ff_percent > 30 or (nc_percent < 5 and fb_percent < 50):
        return 'PIT'
    
    # Se há cálcio significativo mas não caiu no critério FB, classifica como FibCa
    if dc_percent > 10:
        return 'FibCa'
    
    # Caso padrão: Fibrótica (placa estável com composição mista)
    return 'FIB'


def classify_all_frames(frame_areas: List[Dict[str, float]]) -> List[str]:
    classifications = []
    
    for i, areas in enumerate(frame_areas):
        plaque_type = classify_plaque(areas)
        classifications.append(plaque_type)
    
    return classifications


def get_classification_summary(classifications: List[str]) -> Dict[str, int]:
    unique, counts = np.unique(classifications, return_counts=True)
    summary = dict(zip(unique, counts))
    
    return summary


def print_classification_report(classifications: List[str]) -> None:
    print("\n=== Relatório de Classificação de Placas ===")
    
    summary = get_classification_summary(classifications)
    total = len(classifications)
    
    print(f"\nTotal de quadros analisados: {total}")
    print("\nDistribuição de tipos de placa:")
    
    # Ordena por frequência 
    sorted_types = sorted(summary.items(), key=lambda x: x[1], reverse=True)
    
    for plaque_type, count in sorted_types:
        percentage = (count / total) * 100
        print(f"  {plaque_type:10s}: {count:3d} quadros ({percentage:5.1f}%)")
    
    # Análise de risco
    print("\n--- Análise de Risco ---")
    high_risk = summary.get('VH-TCFA', 0)
    moderate_risk = summary.get('ThCFA', 0)
    low_risk = summary.get('FIB', 0) + summary.get('FibCa', 0) + summary.get('PIT', 0)
    
    print(f"  Alto risco (VH-TCFA)      : {high_risk:3d} quadros ({high_risk/total*100:5.1f}%)")
    print(f"  Risco moderado (ThCFA)    : {moderate_risk:3d} quadros ({moderate_risk/total*100:5.1f}%)")
    print(f"  Baixo risco (FIB/FibCa/PIT): {low_risk:3d} quadros ({low_risk/total*100:5.1f}%)")
    
    print("\n" + "="*50)


def get_plaque_description(plaque_type: str) -> str:
    descriptions = {
        'VH-TCFA': 'Thin-Cap Fibroatheroma - Alto risco de ruptura (NC confluente)',
        'ThCFA': 'Thick-Cap Fibroatheroma - Risco moderado (NC não confluente)',
        'FIB': 'Placa Fibrótica - Placa estável com predominância de tecido fibroso',
        'FibCa': 'Placa Fibrocalcífica - Placa estável com fibrose e calcificação',
        'PIT': 'Pathological Intimal Thickening - Espessamento intimal patológico',
        'UNKNOWN': 'Classificação indeterminada - Área de placa insuficiente'
    }
    
    return descriptions.get(plaque_type, 'Tipo de placa desconhecido')
