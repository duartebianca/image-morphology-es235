# Análise Morfológica de Imagens VH-IVUS | ES235 - Processamento de Imagem

## 📋 Sobre o Projeto

Este projeto implementa análise quantitativa de imagens **VH-IVUS** usando técnicas de **morfologia matemática**, com o objetivo é quantificar componentes de placa aterosclerótica e extrair características morfológicas para análise clínica e foi realizado para a disciplina de Processamento de Imagem da UFPE, em 2025.2. 

### Componentes Analisados
- **FB** - Fibrótico (verde escuro)
- **FF** - Fibrolipídico (verde-amarelado)
- **NC** - Core Necrótico (vermelho)
- **DC** - Cálcio Denso (branco)
- **Lúmen** - Cavidade (preto)
- **Média** - Camada média (cinza)

---

## 👥 Autores

- Bianca Duarte Santos (bds@cin.ufpe.br)
- Juliana Serafim ()
- Luiz Fernando ()

---

## 🚀 Como rodar

### 1️⃣ Criar venv e ativar (não é obrigatório, mas recomendamos!)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2️⃣ Instalar Dependências
```powershell
pip install -r requirements.txt
```

### 3️⃣ Executar
```powershell
cd src
python main.py 
```
Obs: se não funcionar com python, testa com python3.

### 4️⃣ Resultados
Todos os entregáveis serão gerados em `data/out/`:
```
data/out/
├── tables/results.xlsx       # Planilha com áreas e histogramas (utilizamos a planilha fornecida pelo professor no PDF de explicação)
├── masks/                    # 6 arquivos TIFF de máscaras binárias
└── plots/                    # 8 gráficos PNG
```

---

## 🎯 Funcionalidades Implementadas

### Item I - Áreas por Quadro
Quantificação da área (em pixels²) de cada componente em cada frame:
- Contagem de pixels de FB, FF, NC, DC, Lúmen e Média
- Soma de todas as ilhas 8-conectadas
- Resultados na aba "itens_i_ii" da planilha

### Item II - NC@DC (Necrótico em Contato com Cálcio)
Quantificação de NC adjacente a DC usando:
- Rotulagem 8-conectada de ilhas NC
- Dilatação morfológica (elemento estruturante 3×3)
- Verificação de overlap com máscara DC
- Algoritmo robusto para detecção de vizinhança

### Item III - Histogramas de Intensidade
Distribuição de intensidades GS-IVUS (0-255) para cada componente:
- Apenas pixels interiore*: Erosão 3×3 (8-conectividade completa)
- Apenas ilhas válidas: >= 5 pixels
- 256 bins de intensidade
- 7 componentes: FB, FF, NC, DC, Lúmen, Média + NC@DC

### Item IV - Dendrograma de Similaridade
Análise hierárquica baseada em histogramas:
- Distância Euclidiana entre distribuições normalizadas
- Linkage hierárquico (Ward)
- Visualização interativa com Plotly
- Identificação de componentes similares

---

## 📦 Estrutura do Projeto

```
image-morphology-es235/
├── src/                     
│   ├── io_module.py          # Leitura/escrita TIFF multi-página
│   ├── color_map.py          # Mapeamento BGR 
│   ├── labeling.py           # Rotulagem 8-conectada
│   ├── morpho.py             # Erosão, dilatação, etc.
│   ├── measures.py           # Cálculo de áreas
│   ├── hist.py               # Histogramas 
│   ├── dendro.py             # Dendrograma 
│   ├── main.py               
│   └── adjust_colors.py      # Ajuste de mapeamento de cores
│
├── data/
│   ├── raw_tiff/             # TIFs do grupo 5
│   └── out/                  # Resultados gerados
│       ├── tables/           #   - results.xlsx
│       ├── masks/            #   - 6 TIFFs de máscaras
│       └── plots/            #   - 8 gráficos PNG
│
├── requirements.txt         
└── README.md              
```
---

## 🔬 Metodologia Científica

### Mapeamento de Cores VH-IVUS

| Componente | Cor BGR | Descrição |
|------------|---------|-----------|
| FB | (0, 128, 0) | Verde escuro - Tecido fibrótico |
| FF | (0, 255, 128) | Verde-amarelado - Fibrolipídico |
| NC | (0, 0, 255) | Vermelho - Core necrótico |
| DC | (255, 255, 255) | Branco - Cálcio denso |
| LUMEN | (0, 0, 0) | Preto - Cavidade do vaso |
| MEDIA | (128, 128, 128) | Cinza - Camada média |

### Algoritmo NC@DC 

```python
Para cada frame:
  1. Rotular ilhas NC (8-conectividade)
  2. Para cada ilha NC:
     a. Dilatar ilha em 1 pixel (SE 3×3)
     b. Verificar overlap com máscara DC
     c. Se toca DC: adicionar área da ilha
  3. NC@DC = soma das áreas das ilhas NC adjacentes a DC
```

### Algoritmo de Histogramas 

```python
Para cada componente:
  1. Filtrar ilhas por tamanho (>=5 pixels)
  2. Para cada ilha válida:
     a. Erodir 3×3 (extrair apenas pixels interiores)
     b. Coletar intensidades GS-IVUS correspondentes
  3. Computar histograma de 256 bins (0-255)
  4. Agregar todos os frames
```

### Conectividade 8-Vizinhos

Todas as operações de rotulagem e morfologia utilizam **8-conectividade**.



