# Processamento Digital de Imagens (PDI) 🖼️

Este repositório contém os trabalhos e experimentos desenvolvidos para a disciplina de **Processamento Digital de Imagens (PDI)**, referente ao 6º Semestre da faculdade.

## 🚀 Sobre o Projeto

O objetivo deste projeto é explorar na prática conceitos fundamentais de Processamento Digital de Imagens através da manipulação e análise de imagens utilizando **Python**. Os experimentos documentados incluem:

- **Carregamento e Conversão**: Leitura de imagens (`.png`, `.jpeg`) e conversão para escala de cinza utilizando o método de média ponderada.
- **Caracterização Estatística**: Análise do contraste e distribuição de intensidade das imagens através do cálculo de média, desvio padrão e percentis (p1, p99).
- **Simulação de Ruído**: Aplicação de ruído sintético e controlado (`sigma = 10`) nas imagens originais, permitindo avaliar o comportamento de técnicas de filtragem e restauração de imagem em etapas posteriores.

## 🛠️ Tecnologias Utilizadas

O desenvolvimento foi feito inteiramente em um ambiente Jupyter Notebook (`Codigo.ipynb`) empregando as seguintes bibliotecas da stack científica do Python:

- **[Python](https://www.python.org/)**
- **[OpenCV (cv2)](https://opencv.org/)** - Utilizada primariamente para I/O das imagens.
- **[NumPy](https://numpy.org/)** - Essencial para manipulações matriciais e operações diretas nos pixels das imagens.
- **[Scikit-Image](https://scikit-image.org/)** - Utilizada para a introdução de ruídos (`skimage.util.random_noise`).
- **[Matplotlib](https://matplotlib.org/)** - Visualização lado a lado das imagens, gráficos e resultados estatísticos.

## 📁 Estrutura do Diretório

```text
Sexto Semestre/PDI/
├── Codigo.ipynb       # Jupyter Notebook principal contendo o código e os resultados
├── image1.png         # Imagem de teste 1
├── imagem2.jpeg       # Imagem de teste 2
├── imagem3.png        # Imagem de teste 3
└── resultados/        # Diretório gerado automaticamente para salvar as saídas do processamento
```

## ⚙️ Como Executar

1. Certifique-se de ter o Python 3.x instalado em sua máquina.
2. Instale as dependências necessárias executando o comando abaixo:
   ```bash
   pip install opencv-python numpy scikit-image matplotlib jupyter
   ```
3. Navegue até o diretório do projeto:
   ```bash
   cd "Sexto Semestre/PDI"
   ```
4. Inicie o servidor do Jupyter Notebook:
   ```bash
   jupyter notebook Codigo.ipynb
   ```
5. Execute as células do notebook sequencialmente para reproduzir a análise inicial e observar a inserção do ruído.

## 📝 Notas de Implementação

- O *seed* de aleatoriedade (`RUIDO_SEED = 42`) é fixado no código de modo que todas as configurações de testes recebam exatamente o mesmo padrão de ruído, garantindo assim a **reprodutibilidade** do experimento.
- As imagens analisadas apresentam inicialmente um baixo contraste intrínseco (desvio padrão baixo + faixa estreita entre os percentis 1 e 99), o que pode exigir etapas de realce nas próximas fases do processamento.
