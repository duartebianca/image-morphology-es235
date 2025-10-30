# módulo para leitura de stacks TIFF multi-página.
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, List
import tifffile


def load_tiff_stack(filepath: str) -> Tuple[List[np.ndarray], int]:
    """
    Returns:
        Tupla contendo:
        - Lista de arrays numpy (um por frame)
        - Número total de frames
        
    Raises:
        FileNotFoundError: Se o arquivo não existir
        ValueError: Se não conseguir ler o arquivo ou estiver vazio
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
    
    # Lê todas as páginas do TIFF
    ret, images = cv2.imreadmulti(str(filepath), flags=cv2.IMREAD_UNCHANGED)
    
    if not ret or len(images) == 0:
        raise ValueError(f"Erro ao ler o arquivo TIFF ou arquivo vazio: {filepath}")
    
    print(f"Carregado {filepath.name}: {len(images)} frames")
    print(f" Dimensões do primeiro frame: {images[0].shape}")
    
    return images, len(images)


def load_vh_and_gs_stacks(vh_path: str, gs_path: str) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """
    Carrega VH-IVUS e GS-IVUS valida que ambos têm o mesmo número de frames e dimensões compatíveis.
    """
    print("\n=== Carregando stacks TIFF ===")
    
    # Carrega VH-IVUS 
    vh_frames, vh_count = load_tiff_stack(vh_path)
    
    # Carrega GS-IVUS 
    gs_frames, gs_count = load_tiff_stack(gs_path)
    
    # Valida compatibilidade
    if vh_count != gs_count:
        raise ValueError(
            f"Número de frames não coincide: VH={vh_count}, GS={gs_count}"
        )
    
    # Valida dimensões espaciais
    vh_shape = vh_frames[0].shape[:2]  # (altura, largura)
    gs_shape = gs_frames[0].shape[:2]
    
    if vh_shape != gs_shape:
        raise ValueError(
            f"Dimensões não coincidem: VH={vh_shape}, GS={gs_shape}"
        )
    
    # Converte VH para BGR se necessário
    vh_frames_bgr = []
    for i, frame in enumerate(vh_frames):
        if len(frame.shape) == 2:  # Imagem com paleta
            # Converte para BGR
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            vh_frames_bgr.append(frame_bgr)
        elif frame.shape[2] == 3:
            vh_frames_bgr.append(frame)
        else:
            raise ValueError(f"Frame VH {i} tem formato inesperado: {frame.shape}")
    
    # Garante que GS está em escala de cinza
    gs_frames_gray = []
    for i, frame in enumerate(gs_frames):
        if len(frame.shape) == 3:
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gs_frames_gray.append(frame_gray)
        else:
            gs_frames_gray.append(frame)
    
    print(f"\n Validação concluída:")
    print(f"  {vh_count} frames alinhados")
    print(f"  Dimensões: {vh_shape[0]}×{vh_shape[1]} pixels")
    print(f"  VH-IVUS: BGR colorido")
    print(f"  GS-IVUS: Escala de cinza 8-bit")
    
    return vh_frames_bgr, gs_frames_gray


def save_tiff_stack(frames: List[np.ndarray], output_path: str) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Garante que todos os frames são uint8
    frames_uint8 = [frame.astype(np.uint8) for frame in frames]
    tifffile.imwrite(str(output_path), np.array(frames_uint8), compression='lzw')
    
    print(f" Salvo: {output_path.name} ({len(frames)} frames)")
