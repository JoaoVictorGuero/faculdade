# Resolução: Estudo Dirigido — Camada de Transporte
## Livro: *Redes de Computadores e a Internet* (Kurose & Ross)
### Problema P1 — Streaming de Vídeo, Jitter e Buffer de Reprodução (*Playout Buffer*)

---

## Enunciado do Problema P1

Considere a figura a seguir. De modo semelhante à nossa discussão da Figura 7.1, suponha que o vídeo seja codificado a uma taxa de bits fixa, e assim cada bloco de vídeo contenha quadros de vídeo que devem ser reproduzidos por algum período de tempo fixo, $\Delta$. O servidor transmite o primeiro bloco de vídeo em $t_0$, o segundo bloco em $t_0 + \Delta$, o terceiro bloco em $t_0 + 2\Delta$, e assim por diante. Quando o cliente inicia a reprodução, cada bloco deve ser reproduzido $\Delta$ unidades de tempo após o bloco anterior.

```text
                  Transmissão de               Recepção
           9      vídeo com taxa               de vídeo
Número do  8      de bits constante            no cliente
bloco de   7      pelo servidor                 ___   |
vídeo      6             _                      | |   |
           5           _|                   ____| |   |
           4         _|                  ___|     |   |
           3       _|                 ___|        |   |
           2     _|                ___|           |   |
           1   _|               ___|              |   |
           0---|---|---|--------|---|---|---|---|---|---|---|---|---|---> Tempo
              t0   Δ   Δ       t1   Δ   Δ   Δ   Δ   Δ   Δ   Δ   Δ   Δ
```

---

## Mapeamento dos Dados da Figura

No lado do cliente, a chegada dos blocos sofre atraso variável de rede (*jitter*). Inspecionando os instantes em que a curva em degraus da recepção sobe para cada bloco $k$ em relação à grade de tempo (marcas de intervalo $\Delta$ a partir de $t_1$):

| Bloco ($k$) | Instante de Chegada no Cliente ($t_{\text{chegada}}$) | Localização Relativa na Grade |
| :---: | :---: | :--- |
| **Bloco 1** | $t_1$ | Exatamente no início da grade ($t_1$) |
| **Bloco 2** | Entre $t_1 + \Delta$ e $t_1 + 2\Delta$ ($\approx t_1 + 1{,}7\Delta$) | Chega após a 1ª marca $\Delta$ |
| **Bloco 3** | Entre $t_1 + 2\Delta$ e $t_1 + 3\Delta$ ($\approx t_1 + 2{,}3\Delta$) | Chega logo após a 2ª marca $\Delta$ |
| **Bloco 4** | Entre $t_1 + 2\Delta$ e $t_1 + 3\Delta$ ($\approx t_1 + 2{,}8\Delta$) | Chega antes da 3ª marca $\Delta$ |
| **Bloco 5** | Entre $t_1 + 3\Delta$ e $t_1 + 4\Delta$ ($\approx t_1 + 3{,}2\Delta$) | Chega logo após a 3ª marca $\Delta$ |
| **Bloco 6** | Entre $t_1 + 4\Delta$ e $t_1 + 5\Delta$ ($\approx t_1 + 4{,}7\Delta$) | Chega antes da 5ª marca $\Delta$ |
| **Bloco 7** | Entre $t_1 + 8\Delta$ e $t_1 + 9\Delta$ ($\approx t_1 + 8{,}3\Delta$) | Sofre longo atraso de rede (após a 8ª marca) |

---

## Questões e Resoluções

### Item (a)
> **Suponha que o cliente inicie a reprodução assim que o primeiro bloco chega em $t_1$. Na figura a seguir, quantos blocos de vídeo (incluindo o primeiro) terão chegado ao cliente em tempo para sua reprodução? Explique como você chegou a essa resposta.**

#### **Resposta:**
**4 blocos** (os blocos **1, 4, 5 e 6**).

#### **Explicação Detalhada:**
Se a reprodução é iniciada imediatamente em $t_1$, não há tempo de pré-carregamento no buffer. O instante programado de reprodução para o $k$-ésimo bloco é:
$$t_{\text{reprodução}}(k) = t_1 + (k - 1)\Delta$$

Um bloco chega em tempo se, e somente se:
$$t_{\text{chegada}}(k) \le t_{\text{reprodução}}(k)$$

Avaliando bloco a bloco:
1. **Bloco 1:** Deve ser reproduzido em $t_1$. Chega em $t_1$.  
   $\implies t_1 \le t_1$ $\rightarrow$ **A tempo** $\checkmark$
2. **Bloco 2:** Deve ser reproduzido em $t_1 + \Delta$. Chega em $\approx t_1 + 1{,}7\Delta$.  
   $\implies t_1 + 1{,}7\Delta > t_1 + \Delta$ $\rightarrow$ **Atrasado** $\times$
3. **Bloco 3:** Deve ser reproduzido em $t_1 + 2\Delta$. Chega em $\approx t_1 + 2{,}3\Delta$.  
   $\implies t_1 + 2{,}3\Delta > t_1 + 2\Delta$ $\rightarrow$ **Atrasado** $\times$
4. **Bloco 4:** Deve ser reproduzido em $t_1 + 3\Delta$. Chega em $\approx t_1 + 2{,}8\Delta$.  
   $\implies t_1 + 2{,}8\Delta \le t_1 + 3\Delta$ $\rightarrow$ **A tempo** $\checkmark$
5. **Bloco 5:** Deve ser reproduzido em $t_1 + 4\Delta$. Chega em $\approx t_1 + 3{,}2\Delta$.  
   $\implies t_1 + 3{,}2\Delta \le t_1 + 4\Delta$ $\rightarrow$ **A tempo** $\checkmark$
6. **Bloco 6:** Deve ser reproduzido em $t_1 + 5\Delta$. Chega em $\approx t_1 + 4{,}7\Delta$.  
   $\implies t_1 + 4{,}7\Delta \le t_1 + 5\Delta$ $\rightarrow$ **A tempo** $\checkmark$
7. **Bloco 7:** Deve ser reproduzido em $t_1 + 6\Delta$. Chega em $\approx t_1 + 8{,}3\Delta$.  
   $\implies t_1 + 8{,}3\Delta > t_1 + 6\Delta$ $\rightarrow$ **Atrasado** $\times$

Conclusão: Apenas os blocos **1, 4, 5 e 6** chegam antes do respectivo prazo, totalizando **4 blocos**.

---

### Item (b)
> **Suponha que o cliente inicie a reprodução agora em $t_1 + \Delta$. Quantos blocos de vídeo (incluindo o primeiro) terão chegado ao cliente em tempo para sua reprodução? Explique como você chegou a essa resposta.**

#### **Resposta:**
**6 blocos** (os blocos **1, 2, 3, 4, 5 e 6**).

#### **Explicação Detalhada:**
Ao adiar o início da reprodução para $t_1 + \Delta$, cria-se uma folga temporal (*delay safety cushion*) de $\Delta$ unidades de tempo. O cronograma de reprodução é deslocado para a frente:
$$t_{\text{reprodução}}(k) = (t_1 + \Delta) + (k - 1)\Delta = t_1 + k\Delta$$

Reavaliando a condição $t_{\text{chegada}}(k) \le t_{\text{reprodução}}(k)$:
1. **Bloco 1:** Prazo $= t_1 + \Delta$. Chegada $= t_1$.  
   $\implies t_1 \le t_1 + \Delta$ $\rightarrow$ **A tempo** $\checkmark$
2. **Bloco 2:** Prazo $= t_1 + 2\Delta$. Chegada $\approx t_1 + 1{,}7\Delta$.  
   $\implies t_1 + 1{,}7\Delta \le t_1 + 2\Delta$ $\rightarrow$ **A tempo** $\checkmark$
3. **Bloco 3:** Prazo $= t_1 + 3\Delta$. Chegada $\approx t_1 + 2{,}3\Delta$.  
   $\implies t_1 + 2{,}3\Delta \le t_1 + 3\Delta$ $\rightarrow$ **A tempo** $\checkmark$
4. **Bloco 4:** Prazo $= t_1 + 4\Delta$. Chegada $\approx t_1 + 2{,}8\Delta$.  
   $\implies t_1 + 2{,}8\Delta \le t_1 + 4\Delta$ $\rightarrow$ **A tempo** $\checkmark$
5. **Bloco 5:** Prazo $= t_1 + 5\Delta$. Chegada $\approx t_1 + 3{,}2\Delta$.  
   $\implies t_1 + 3{,}2\Delta \le t_1 + 5\Delta$ $\rightarrow$ **A tempo** $\checkmark$
6. **Bloco 6:** Prazo $= t_1 + 6\Delta$. Chegada $\approx t_1 + 4{,}7\Delta$.  
   $\implies t_1 + 4{,}7\Delta \le t_1 + 6\Delta$ $\rightarrow$ **A tempo** $\checkmark$
7. **Bloco 7:** Prazo $= t_1 + 7\Delta$. Chegada $\approx t_1 + 8{,}3\Delta$.  
   $\implies t_1 + 8{,}3\Delta > t_1 + 7\Delta$ $\rightarrow$ **Atrasado** $\times$

Conclusão: Com a inclusão da margem $\Delta$, os blocos 2 e 3 deixam de atrasar. Dos 7 blocos ilustrados, os blocos **1, 2, 3, 4, 5 e 6** chegam a tempo, totalizando **6 blocos**.

---

### Item (c)
> **No mesmo cenário do item "b", qual é o maior número de blocos que chega a ser armazenado no buffer do cliente, aguardando a reprodução? Explique como você chegou a essa resposta.**

#### **Resposta:**
**2 blocos**.

#### **Explicação Detalhada:**
A ocupação do buffer no instante $t$ é a diferença entre a contagem cumulativa de blocos recebidos e a contagem cumulativa de blocos consumidos para reprodução:
$$\text{Buffer}(t) = \text{Recebidos}(t) - \text{Reproduzidos}(t)$$

Rastreando a evolução do buffer no tempo sob o cenário (b):
- **$t = t_1$:** Chega o bloco 1.  
  Recebidos = 1, Reproduzidos = 0 $\implies$ **Buffer = 1** (bloco 1).
- **$t_1 \le t < t_1 + \Delta$:** Nenhum bloco chega.  
  $\implies$ **Buffer = 1**.
- **$t = t_1 + \Delta$:** Inicia a reprodução do bloco 1 (é retirado do buffer).  
  Recebidos = 1, Reproduzidos = 1 $\implies$ **Buffer = 0**.
- **$t \approx t_1 + 1{,}7\Delta$:** Chega o bloco 2.  
  Recebidos = 2, Reproduzidos = 1 $\implies$ **Buffer = 1** (bloco 2).
- **$t = t_1 + 2\Delta$:** O bloco 2 é consumido para reprodução.  
  Recebidos = 2, Reproduzidos = 2 $\implies$ **Buffer = 0**.
- **$t \approx t_1 + 2{,}3\Delta$:** Chega o bloco 3.  
  Recebidos = 3, Reproduzidos = 2 $\implies$ **Buffer = 1** (bloco 3).
- **$t \approx t_1 + 2{,}8\Delta$:** Chega o bloco 4 (antes de o bloco 3 ser consumido).  
  Recebidos = 4, Reproduzidos = 2 $\implies$ **Buffer = 2** (blocos 3 e 4 no buffer).
- **$t = t_1 + 3\Delta$:** O bloco 3 é consumido.  
  Recebidos = 4, Reproduzidos = 3 $\implies$ **Buffer = 1** (bloco 4).
- **$t \approx t_1 + 3{,}2\Delta$:** Chega o bloco 5.  
  Recebidos = 5, Reproduzidos = 3 $\implies$ **Buffer = 2** (blocos 4 e 5 no buffer).
- **$t = t_1 + 4\Delta$:** O bloco 4 é consumido.  
  Recebidos = 5, Reproduzidos = 4 $\implies$ **Buffer = 1** (bloco 5).
- **$t \approx t_1 + 4{,}7\Delta$:** Chega o bloco 6.  
  Recebidos = 6, Reproduzidos = 4 $\implies$ **Buffer = 2** (blocos 5 e 6 no buffer).
- **$t = t_1 + 5\Delta$:** O bloco 5 é consumido.  
  Recebidos = 6, Reproduzidos = 5 $\implies$ **Buffer = 1** (bloco 6).
- **$t = t_1 + 6\Delta$:** O bloco 6 é consumido.  
  Recebidos = 6, Reproduzidos = 6 $\implies$ **Buffer = 0**.

Conclusão: Em nenhum instante o buffer acumula 3 ou mais blocos. O pico de armazenamento ocorre em momentos de rajada de chegada de pacotes (como entre $t_1 + 2{,}8\Delta$ e $t_1 + 3\Delta$), atingindo no máximo **2 blocos**.

---

### Item (d)
> **Qual é o menor atraso de reprodução no cliente, tal que cada bloco de vídeo tenha chegado em tempo para sua reprodução? Explique como você chegou a essa resposta.**

#### **Resposta:**
**Iniciar a reprodução em $t_1 + 3\Delta$** (atraso de inicialização de **$3\Delta$** a partir da chegada do primeiro bloco; ou $\approx \mathbf{2{,}3\Delta}$ em tempo contínuo exato).

#### **Explicação Detalhada:**
Seja $p$ o tempo de atraso adicional a partir de $t_1$ para o início da reprodução. Assim, o instante de reprodução do bloco $k$ é:
$$t_{\text{reprodução}}(k) = t_1 + p + (k - 1)\Delta$$

Para que nenhum bloco atrase, a condição $t_{\text{chegada}}(k) \le t_{\text{reprodução}}(k)$ deve ser satisfeita para todos os blocos:
$$p \ge t_{\text{chegada}}(k) - t_1 - (k - 1)\Delta, \quad \forall k \in \{1, 2, \dots, 7\}$$

Calculando o atraso mínimo exigido por cada bloco:
- Bloco 1: $p \ge t_1 - t_1 - 0 = 0$
- Bloco 2: $p \ge 1{,}7\Delta - \Delta = 0{,}7\Delta$
- Bloco 3: $p \ge 2{,}3\Delta - 2\Delta = 0{,}3\Delta$
- Bloco 4: $p \ge 2{,}8\Delta - 3\Delta = -0{,}2\Delta$ (chega adiantado)
- Bloco 5: $p \ge 3{,}2\Delta - 4\Delta = -0{,}8\Delta$ (chega adiantado)
- Bloco 6: $p \ge 4{,}7\Delta - 5\Delta = -0{,}3\Delta$ (chega adiantado)
- **Bloco 7 (Gargalo / Caso Crítico):**
  O bloco 7 é o 7º bloco ($k=7$), mas devido ao jitter de rede só chega após a 8ª marca de intervalo ($\approx t_1 + 8{,}3\Delta$):
  $$p \ge 8{,}3\Delta - (7 - 1)\Delta = 8{,}3\Delta - 6\Delta = 2{,}3\Delta$$

Como sistemas de streaming e as questões padronizadas do livro operam com atrasos discretizados em múltiplos inteiros do intervalo de bloco $\Delta$:
- Se escolhermos $p = 2\Delta$, o bloco 7 seria reproduzido em $t_1 + 2\Delta + 6\Delta = t_1 + 8\Delta$, perdendo o prazo por uma fração de $\approx 0{,}3\Delta$ e causando congelamento (*freezing*).
- Logo, o menor atraso inteiro necessário para garantir que absolutamente todos os blocos estejam disponíveis a tempo é **$p = 3\Delta$**, ou seja, iniciar a reprodução em **$t_1 + 3\Delta$**.
