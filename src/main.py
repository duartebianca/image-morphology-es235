import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).parent))

# módulos do projeto
from io_module import load_vh_and_gs_stacks, save_tiff_stack
from color_map import create_binary_masks_optimized, COMPONENTS
from measures import measure_frame_complete, create_results_dataframe, print_summary_statistics
from hist import process_histograms_all_components, create_histogram_dataframe, plot_histograms
from dendro import create_dendrogram_plotly, print_distance_matrix, find_most_similar_pairs


class VHIVUSPipeline:
    
    def __init__(self, vh_path: str, gs_path: str, output_dir: str = "data/out"):
        self.vh_path = Path(vh_path)
        self.gs_path = Path(gs_path)
        self.output_dir = Path(output_dir)
        
        # Cria diretórios de saída
        self.tables_dir = self.output_dir / "tables"
        self.masks_dir = self.output_dir / "masks"
        self.plots_dir = self.output_dir / "plots"
        
        for dir_path in [self.tables_dir, self.masks_dir, self.plots_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Dados carregados
        self.vh_frames = None
        self.gs_frames = None
        self.masks_all_frames = None
        
        # Resultados
        self.df_measures = None
        self.df_histograms = None
        self.histograms = None
    
    def load_data(self):
        print("\n" + "="*60)
        print("PIPELINE VH-IVUS - MORFOLOGIA MATEMÁTICA")
        print("="*60)
        
        self.vh_frames, self.gs_frames = load_vh_and_gs_stacks(
            str(self.vh_path), 
            str(self.gs_path)
        )
        
        print(f"\n✓ Dados carregados: {len(self.vh_frames)} frames")
    
    def create_masks(self):
        print("\n=== Criando máscaras binárias ===")
        
        self.masks_all_frames = []
        
        for frame_idx, vh_frame in enumerate(self.vh_frames):
            masks = create_binary_masks_optimized(vh_frame)
            self.masks_all_frames.append(masks)
            
            if (frame_idx + 1) % 20 == 0:
                print(f"  Frame {frame_idx + 1}/{len(self.vh_frames)}")
        
        print(f"Máscaras criadas para {len(self.masks_all_frames)} frames")
    
    def compute_measures(self):
        print("\n=== Calculando medidas (Item I e II) ===")
        
        measures_list = []
        
        for frame_idx, masks in enumerate(self.masks_all_frames):
            measures = measure_frame_complete(masks)
            measures['quadro'] = frame_idx
            measures_list.append(measures)
            
            if (frame_idx + 1) % 20 == 0 or frame_idx == 0:
                print(f"  Frame {frame_idx}: FB={measures['FB']:5d}, "
                      f"NC={measures['NC']:5d}, NC@DC={measures['NC_AT_DC']:5d}")
        
        # Cria DataFrame
        self.df_measures = self._create_measures_dataframe(measures_list)
        
        print(f" Medidas calculadas para {len(measures_list)} frames")
        
        # Estatísticas resumidas
        print_summary_statistics(self.df_measures)
    
    def _create_measures_dataframe(self, measures_list):
        data = []
        
        for measures in measures_list:
            row = {
                'quadro': measures['quadro'],
                'plaque_type': '',  
                'lumen_area': measures['LUMEN'],
                'media_area': measures['MEDIA'],
                'fb_area': measures['FB'],
                'ff_area': measures['FF'],
                'nc_area': measures['NC'],
                'dc_area': measures['DC'],
                'nc@dc_area': measures['NC_AT_DC']
            }
            data.append(row)
        
        return pd.DataFrame(data)
    
    def compute_histograms(self):
        self.histograms = process_histograms_all_components(
            self.masks_all_frames,
            self.gs_frames
        )
        
        self.df_histograms = create_histogram_dataframe(self.histograms)
        
        print(f"Histogramas computados para {len(self.histograms)} componentes")
    
    def generate_plots(self):
        plot_histograms(self.histograms, str(self.plots_dir))
        dendro_path = self.plots_dir / "dendrogram.png"
        create_dendrogram_plotly(
            self.histograms,
            output_path=str(dendro_path),
            metric='euclidean',
            linkage_method='ward'
        )
        
        # Análise de similaridade
        print_distance_matrix(self.histograms, metric='euclidean')
        find_most_similar_pairs(self.histograms, metric='euclidean', top_n=3)
    
    def save_mask_tiffs(self):
        print("\n=== Salvando máscaras TIFF ===")
        
        for component in COMPONENTS:
            # Coleta máscaras do componente de todos os frames
            component_masks = [masks[component] for masks in self.masks_all_frames]
            
            # Salva como stack TIFF multi-página
            output_path = self.masks_dir / f"{component.lower()}.tif"
            save_tiff_stack(component_masks, str(output_path))
        
        print(f"{len(COMPONENTS)} arquivos TIFF salvos em {self.masks_dir}")
    
    def save_results(self):
        print("\n=== Salvando resultados ===")
        
        excel_path = self.tables_dir / "results.xlsx"
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Aba "quadros" (Item I e II)
            self.df_measures.to_excel(writer, sheet_name='itens_i_ii', index=False)
            
            # Aba "histograms" (Item III)
            self.df_histograms.to_excel(writer, sheet_name='histograms', index=False)
        
        print(f"✓ Resultados salvos: {excel_path}")
        print(f"  - Aba 'itens_i_ii': {len(self.df_measures)} frames")
        print(f"  - Aba 'histograms': {len(self.df_histograms)} componentes")
    
    def run(self):
        try:
            # Carrega dados
            self.load_data()
            
            # Cria máscaras binárias
            self.create_masks()
            
            # Calcula medidas (Item I e II)
            self.compute_measures()
            
            # Calcula histogramas (Item III)
            self.compute_histograms()

            # Gera gráficos (Item III e IV)
            self.generate_plots()

            # Salva máscaras TIFF
            self.save_mask_tiffs()

            # Salva resultados
            self.save_results()
            
            print("\n" + "="*60)
            print("CONCLUÍDO COM SUCESSO!")
            print("="*60)
            print(f"\nEntregáveis gerados em: {self.output_dir}")
            print(f"  - Tabelas: {self.tables_dir}")
            print(f"  - Máscaras: {self.masks_dir}")
            print(f"  - Gráficos: {self.plots_dir}")
            
        except Exception as e:
            print(f"\n❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
            raise


def main():
    vh_path = "../data/raw_tiff/grupo5_VH.tif"
    gs_path = "../data/raw_tiff/grupo5_GS.tif"
    
    # Verifica se arquivos existem
    if not Path(vh_path).exists():
        print(f"❌ Arquivo não encontrado: {vh_path}")
        print("\nPor favor, coloque os arquivos TIFF em data/raw_tiff/")
        print("  - grupo5_VH.tif (VH-IVUS colorido)")
        print("  - grupo5_GS.tif (GS-IVUS escala de cinza)")
        return
    
    if not Path(gs_path).exists():
        print(f"❌ Arquivo não encontrado: {gs_path}")
        return
    
    pipeline = VHIVUSPipeline(vh_path, gs_path)
    pipeline.run()


if __name__ == "__main__":
    main()
