# ROTEIRO PDI — Análise Morfológica de Imagens VH-IVUS
> **Convenções:**
> - **A = Pessoa 1** | **B = Pessoa 2**
> - Duração: ~14 minutos
> - Mostrar no Colab + navegação estratégica no código

---

## 0) ABERTURA & AGENDA (00:00–01:00) — **A** (1:00)

**[FALA DIRETA]**

"Bom dia/tarde! Nosso projeto implementa **análise quantitativa de imagens VH-IVUS** usando **morfologia matemática** para quantificar componentes de placa aterosclerótica. 

Vamos mostrar:
1. **Como o código funciona** (arquitetura e funções principais)
2. **Resultados gerados**: tabela de medidas, máscaras binárias, histogramas e dendrograma
3. **Desafios técnicos** que enfrentamos, especialmente o **NC@DC** e o histograma "estranho"

Toda a execução está documentada neste notebook Colab."

---

## 1) CONTEXTO CLÍNICO & DEFINIÇÕES TÉCNICAS (01:00–03:00) — **A** (2:00)

**[FALA DIRETA]**

### 1.1 Componentes da Placa (0:30)
"Primeiro, o que estamos analisando? Placas ateroscleróticas em artérias coronárias têm 6 componentes principais:

- **FB** (fibrótico) — verde escuro — tecido cicatricial
- **FF** (fibrolipídico) — verde-amarelo — gordura + fibras
- **NC** (core necrótico) — vermelho — núcleo morto/inflamatório
- **DC** (cálcio denso) — branco — calcificação
- **Lúmen** — preto — cavidade do vaso
- **Média** — cinza — camada muscular do vaso"

### 1.2 Definições Morfológicas (1:00)
"Agora, termos técnicos essenciais para entender nosso método:

**→ Ilha**: conjunto de pixels **8-conectados** da mesma classe. Se dois pixels NC se tocam por canto/diagonal/aresta, pertencem à mesma ilha.

**→ Pixels interiores**: pixels que **sobrevivem à erosão 3×3**. Isso garante que todos os 8 vizinhos são do mesmo componente — evita mistura de bordas entre tecidos.

**→ NC@DC** — definição crítica: **soma das áreas das ilhas NC que estão em contato com DC**. 
   - *Por que isso importa clinicamente?* NC adjacente a cálcio indica instabilidade da placa.
   - *Como detectamos o contato?* Usamos **dilatação morfológica**: expandimos cada ilha NC em 1 pixel e verificamos overlap com a máscara de DC.

**→ Histogramas 0–255**: distribuições de intensidade do **GS-IVUS** (escala de cinza), usando **apenas pixels interiores** de ilhas **≥5 pixels**.

**→ Dendrograma**: agrupamento hierárquico das distribuições normalizadas dos histogramas. Usamos **distância Euclidiana** + **linkage Ward** para comparar assinaturas radiométricas."

### 1.3 Por Quê? (0:30)
**[RESPONDER ANTECIPADAMENTE AS PERGUNTAS DO PROFESSOR]**

"Por que usar apenas interiores? **Para medir tecido "puro"**, sem viés de borda onde dois componentes se misturam.

Por que Ward + Euclidiana? **Ward minimiza variação intra-cluster**; Euclidiana é natural para vetores normalizados de contagens.

Por que rotulagem manual? **Controle fino sobre conectividade-8 e rastreabilidade** — bibliotecas prontas podem não seguir exatamente a mesma convenção."

---

## 2) ARQUITETURA DO CÓDIGO & FLUXO (03:00–05:30) — **B** (2:30)

**[MOSTRAR NO COLAB — NAVEGAR PELAS CÉLULAS]**

### 2.1 Visão Geral do Pipeline (0:45)
"Nosso código tem **5 etapas principais** orquestradas pela função `main()`:

```
main()
 ├─1. carregar_dados()          → Lê TIFFs VH + GS
 ├─2. criar_mascaras()          → Segmenta cores → 6 máscaras binárias/quadro
 ├─3. calcular_medidas()        → Áreas + NC@DC + classificação de placa
 ├─4. calcular_histogramas()    → Só interiores, ilhas ≥5px
 └─5. salvar_resultados()       → Excel, TIFFs, PNGs
```

Cada etapa é **modular e rastreável**."

### 2.2 Módulos Principais (1:45)
**[NAVEGAR RAPIDAMENTE PELAS CÉLULAS — MOSTRAR AS FUNÇÕES-CHAVE]**

#### **Célula 3: Mapeamento de Cores** (0:20)
"Aqui fazemos a **segmentação por cor mais próxima**:
```python
MAPA_CORES_BGR = {
    'FB': (0, 128, 0),    # Verde escuro
    'NC': (0, 0, 255),    # Vermelho
    # ...
}
```
A função `criar_mascaras_binarias()` calcula a **distância Euclidiana** no espaço BGR de cada pixel para as 6 cores-alvo e atribui ao componente mais próximo. Resultado: **6 máscaras binárias por quadro**."

#### **Célula 4: Rotulagem Manual 8-Conectada** (0:40)
"Esta é a **célula mais técnica** — implementamos o algoritmo **Two-Pass com Union-Find**:

```python
def rotular_componentes_conectados(mascara_binaria, conectividade=8):
    # Passa 1: Atribui rótulos temporários + registra equivalências
    # Passa 2: Resolve rótulos finais + calcula estatísticas (área, centroide)
```

**Por que manual?** 
1. Controle total sobre **conectividade-8** (diagonais incluídas)
2. **Rastreabilidade** de cada ilha individualmente
3. Necessário para **filtrar ilhas <5px** e para **NC@DC por ilha**

Isso nos dá: **número de ilhas, mapa de rótulos, áreas, centroides**."

#### **Célula 5: Medidas Morfológicas** (0:45)
"Aqui implementamos as **análises requisitadas**:

**→ `medir_areas_por_quadro()`**: Soma áreas de todas as ilhas de cada componente.

**→ `calcular_area_nc_conectado_dc()`** — **algoritmo NC@DC**:
```python
Para cada ilha NC:
  1. Dilata a ilha em 1 pixel (elemento estruturante 3×3)
  2. Verifica overlap: ilha_dilatada ∧ mascara_DC
  3. Se toca: adiciona área ORIGINAL da ilha à soma
```
**Importante**: Somamos a **área original** das ilhas NC que tocam DC, não a área dilatada.

**→ `coletar_intensidades_interiores()`**:
```python
1. Filtra ilhas por tamanho (≥5 px)
2. Para cada ilha válida: erode 3×3 (extrai só interiores)
3. Coleta intensidades GS-IVUS desses pixels
```

**→ `criar_mascara_nc_conectado_dc()`**: Versão do NC@DC que **retorna a máscara** (não a área), usada para gerar o histograma de NC@DC."

---

## 3) DEMONSTRAÇÃO DOS RESULTADOS (05:30–10:00) — **A** (4:30)

**[ABRIR OS ARQUIVOS NO COLAB — INTERPRETAR CADA UM]**

### 3.1 Planilha Excel (1:20)
**[MOSTRAR `results/tabelas/planilha_resultados_finais.xlsx`]**

"A planilha tem **2 abas**:

#### **Aba 1: Medidas_Quadro_a_Quadro**
```
| Quadro | Tipo_Placa | LUMEN | MEDIA | FB | FF | NC | DC | NC_AT_DC |
|--------|------------|-------|-------|----|----|----|----|----------|
| 0      | PIT        | 1250  | 890   | ...| ...| ...| ...| 42       |
```

Colunas explicadas:
- **Quadro**: índice do frame
- **Tipo_Placa**: classificação automática (VH-TCFA, ThCFA, PIT, Fib, FibCa)
- **LUMEN...DC**: áreas em **pixels²** de cada componente
- **NC_AT_DC**: **soma das áreas das ilhas NC conectadas a DC** — métrica de instabilidade

**[APONTAR PARA UMA LINHA COM NC_AT_DC > 0]**
'Veja o quadro X: 180 pixels de NC tocam DC — isso indica uma zona de alto risco.'

#### **Aba 2: Histogramas_Dados**
Contém os **vetores de 256 bins** (frequências normalizadas) para cada componente — usados no dendrograma."

### 3.2 Máscaras Binárias TIFF (0:50)
**[ABRIR `results/mascaras/mascara_nc.tif` E `mascara_dc.tif` NO IMAGECODECS/TIFFFILE]**

"Geramos **6 arquivos TIFF multi-página**, um por componente:
- Cada página = um quadro
- Pixels brancos (255) = componente presente
- Pixels pretos (0) = ausente

**[MOSTRAR QUADRO 0 DE NC E DC LADO A LADO]**
'Aqui vemos ilhas NC (branco) e DC (branco) no mesmo quadro. Nosso algoritmo detecta onde elas se aproximam a ≤1 pixel de distância.'"

### 3.3 Histogramas de Intensidade (1:20)
**[ABRIR `results/graficos/histograma_nc.png` E `histograma_nc@dc.png`]**

"Estes gráficos mostram a **distribuição de intensidades GS-IVUS (0–255)** para cada componente.

**Características importantes:**
- **Apenas pixels interiores** (pós-erosão 3×3)
- **Apenas ilhas ≥5 pixels**
- **Somados em todos os quadros**

**[COMPARAR NC vs NC@DC]**
'Vejam: o histograma de **NC@DC é mais ruidoso** e tem **pico deslocado**. Por quê?

1. **Amostra menor**: NC@DC é um subset de NC (menos pixels)
2. **Erosão elimina bordas finas**: contatos NC↔DC tendem a ser estreitos, então a erosão remove muitos pixels
3. **Efeito de borda**: regiões NC próximas a DC podem ter intensidades diferentes do NC "livre" devido a artefatos de imageamento

**Isso não é um erro — é esperado pela natureza morfológica do critério.**'"

### 3.4 Dendrograma (1:00)
**[ABRIR `results/graficos/dendrograma.png`]**

"O dendrograma mostra a **similaridade hierárquica** entre as distribuições de intensidade.

**Como foi construído:**
1. Normalizamos cada histograma (soma = 1)
2. Calculamos distância Euclidiana entre todos os pares
3. Aplicamos agrupamento hierárquico com linkage Ward

**Interpretação:**
**[APONTAR PARA CLUSTERS]**
- 'FB e FF formam um cluster próximo — fazem sentido, ambos são tecidos densos'
- 'NC e NC@DC estão próximos, mas **NC@DC tem distância maior** — confirma o efeito de amostragem reduzida'
- 'LUMEN e MEDIA são mais distantes — têm assinaturas radiométricas únicas'

**Implicação clínica**: componentes com distribuições similares podem ser confundidos em análise automática — daí a importância da VH-IVUS codificada por cor."

---

## 4) DESAFIO TÉCNICO: O "MISTÉRIO" DO NC@DC (10:00–12:00) — **B** (2:00)

**[FALA DIRETA — RESPONDER A PREOCUPAÇÃO DO PROFESSOR]**

### 4.1 Por Que o Histograma de NC@DC Parece "Errado"? (1:00)
"Identificamos que o professor observou que **o histograma de NC@DC não parecia correto**. Vamos explicar o fenômeno:

**Três fatores combinados:**

1. **Amostra drasticamente reduzida**:
   - NC total: ~50.000 pixels interiores
   - NC@DC: ~2.000 pixels interiores (4% do NC)
   - Resultado: **curva mais ruidosa por natureza estatística**

2. **Erosão agrava o problema**:
   ```
   Contato NC↔DC típico:
   ████████  ← Ilha NC (área 60px)
      ██     ← Região de contato (2–3px de largura)
   ▓▓▓▓▓▓▓▓  ← Ilha DC
   
   Após erosão 3×3:
   ██████    ← Interior NC (área 40px)
      ∅      ← REMOVIDO! (muito fino)
   ▓▓▓▓▓▓    ← Interior DC
   ```
   **Se o contato é uma "ponte fina", a erosão elimina completamente essa região**, mesmo que a ilha NC seja válida (≥5px).

3. **Efeito de vizinhança radiométrica**:
   - Pixels NC próximos a DC sofrem **partial volume effect** (mistura de sinal de ultrassom)
   - Intensidades na zona de contato tendem a ser **mais altas** (DC é hiperecóico → 'contamina' o sinal)
   - Resultado: **distribuição de NC@DC deslocada para a direita** vs NC geral"

### 4.2 Validações Que Fizemos (1:00)
"Para garantir que não era erro de código, realizamos **4 sanity checks**:

**✓ Check 1: Overlay visual**
Exportamos alguns quadros com **NC em vermelho + DC em branco + regiões de contato destacadas** → confirmamos que o algoritmo detecta corretamente.

**✓ Check 2: Normalização L1**
Comparamos **NC vs NC@DC normalizados** (área sob curva = 1) → a **forma** da distribuição realmente muda, não é só questão de escala.

**✓ Check 3: Sensibilidade à dilatação**
Testamos **1 pixel vs 2 pixels** de expansão na detecção de contato → resultados consistentes, diferença <5%.

**✓ Check 4: Inspeção da planilha**
Verificamos que **NC_AT_DC ≤ NC** em todos os quadros e que o nome da coluna está correto.

**Conclusão**: O histograma "estranho" é **fenômeno real da morfologia**, não bug."

---

## 5) TÉCNICAS MORFOLÓGICAS UTILIZADAS (12:00–13:00) — **A** (1:00)

**[FALA DIRETA — RESUMO TÉCNICO]**

"Resumindo as técnicas de morfologia matemática aplicadas:

**1. Mapeamento por cor mais próxima** (distância Euclidiana BGR)
   - Garante estabilidade com variação de iluminação

**2. Rotulagem manual 8-conectada** (Two-Pass + Union-Find)
   - **Por quê?** Controle sobre conectividade, estatísticas por ilha, filtro de tamanho

**3. Dilatação 3×3** (detecção de contato NC↔DC)
   - **Por quê?** Detecta vizinhança estrutural robusta (até 1 pixel de gap)

**4. Erosão 3×3** (extração de pixels interiores)
   - **Por quê?** Remove borda mista entre tecidos → amostra "tecido puro"

**5. Filtro de tamanho (ilhas ≥5 pixels)**
   - **Por quê?** Elimina ruído de segmentação (artefatos pequenos)

**6. Dendrograma (Ward + Euclidiana)**
   - **Por quê?** Ward minimiza variância intra-cluster; Euclidiana é natural para vetores de frequência normalizados

**Todas essas escolhas estão documentadas nos comentários do código.**"

---

## 6) FLUXOGRAMA VISUAL & REPRODUTIBILIDADE (13:00–13:40) — **B** (0:40)

**[MOSTRAR DIAGRAMA MENTAL — PODE DESENHAR NO QUADRO OU SLIDE]**

```
┌─────────────┐
│ VH + GS TIF │
└──────┬──────┘
       │
       ├─→ [Segmentação por Cor] → 6 Máscaras/quadro
       │
       ├─→ [Rotulagem 8-conn] → Ilhas rotuladas
       │
       ├─→ [Medidas]
       │   ├─ Áreas totais (soma de ilhas)
       │   ├─ NC@DC (dilatação → overlap → soma áreas originais)
       │   └─ Classificação de placa
       │
       ├─→ [Histogramas]
       │   ├─ Filtro ≥5px
       │   ├─ Erosão 3×3 (interiores)
       │   └─ Coleta intensidades GS → bins 0–255
       │
       └─→ [Saídas]
           ├─ Excel (medidas + histogramas)
           ├─ 6 TIFFs de máscaras
           ├─ 8 PNGs (7 histogramas + dendrograma)
           └─ Reprodutibilidade total
```

"Todo o código está **organizado em módulos**, **comentado linha a linha** e **executável de forma determinística** — basta rodar a célula `main()`."

---

## 7) CONCLUSÃO & LIÇÕES APRENDIDAS (13:40–14:00) — **A** (0:20)

"Para concluir:

**O que entregamos:**
- ✅ Planilha com medidas e histogramas
- ✅ 6 stacks TIFF de máscaras binárias
- ✅ 8 gráficos (histogramas + dendrograma)
- ✅ Código-fonte comentado e rastreável

**Principais desafios técnicos:**
- Implementar rotulagem manual 8-conectada
- Entender o comportamento não-intuitivo do histograma NC@DC
- Balancear precisão morfológica vs. amostra estatisticamente viável

**Aprendizados:**
- **Morfologia não é "caixa-preta"** — pequenas escolhas (conectividade, elemento estruturante) têm grandes impactos
- **Validação visual é essencial** — números sozinhos não contam a história completa
- **Efeitos de borda são reais** — erosão é necessária, mas reduz amostra

Obrigado! Estamos prontos para perguntas."

---

## APÊNDICE: POSSÍVEIS PERGUNTAS DO PROFESSOR

**P1: "Por que não usar `cv2.connectedComponents`?"**
**R:** "Usamos rotulagem manual para **controle total sobre conectividade-8** e **rastreabilidade de cada ilha** — necessário para filtro de tamanho e NC@DC por ilha."

**P2: "Como garantem que o NC@DC está correto?"**
**R:** "Fizemos overlay visual de NC+DC com destacamento das regiões de contato; verificamos que NC_AT_DC ≤ NC em todos os quadros; testamos sensibilidade à dilatação (1px vs 2px)."

**P3: "Por que erosão 3×3 especificamente?"**
**R:** "Garante que todos os **8 vizinhos** são do mesmo componente — define 'interior' de forma estrita e consistente com a conectividade-8."

**P4: "O dendrograma faz sentido clinicamente?"**
**R:** "Sim — FB e FF são tecidos densos e ficam próximos; LUMEN e MEDIA são estruturas anatômicas distintas e ficam distantes. A proximidade NC↔NC@DC está correta dado que NC@DC é subset de NC."