# UNIVERSIDADE DO VALE DO ITAJAÍ — UNIVALI
## Curso de Ciência da Computação
### Disciplina: Redes de Computadores II
### Professor: Ewerton Alonso

---

# RELATÓRIO PRÁTICO: ATIVIDADE 02
## Análise da Camada de Transporte: TCP x UDP

**Integrantes:**
- [Nome do Aluno / Integrantes]

**Professor:** Prof. Ewerton Alonso  
**Data de Entrega:** [Inserir Data]

---

## 1. Introdução

A camada de transporte desempenha um papel central na arquitetura de redes TCP/IP e no modelo de referência OSI, sendo a responsável por fornecer canais de comunicação lógica fim a fim (*process-to-process*) entre aplicações executadas em diferentes dispositivos de rede. Para permitir que múltiplas aplicações compartilhem simultaneamente a mesma interface de rede, a camada de transporte introduz o conceito de portas lógicas (endereçamento de 16 bits), além de prover serviços de segmentação, verificação de erros e controle de transmissão.

Na pilha de protocolos da Internet, dois protocolos destacam-se como fundamentais:
- **TCP (Transmission Control Protocol):** Protocolo orientado à conexão, com entrega confiável e ordenada, dotado de mecanismos de sincronização prévia (*three-way handshake*), números de sequência, controle de fluxo por janela deslizante, controle de congestionamento e confirmações de recebimento (ACK).
- **UDP (User Datagram Protocol):** Protocolo não orientado à conexão e sem estado (*stateless*), que opera sob o paradigma de melhor esforço (*best-effort*). Possui cabeçalho mínimo de 8 bytes e não estabelece negociação prévia nem oferece garantias nativas de entrega ou ordenação, priorizando velocidade e mínima latência.

---

## 2. Objetivo

Analisar de maneira prática e aprofundada o comportamento dos protocolos TCP e UDP por meio da execução de aplicações cliente-servidor em linguagem Python, inspecionando detalhadamente a troca de mensagens, o uso dos métodos de sockets da biblioteca padrão e os pacotes capturados no analisador de tráfego Wireshark.

---

## 3. Metodologia

1. **Recursos de Software e Ambiente:**
   - **Sistema Operacional:** Windows 10 / Windows 11 (ou macOS / Linux adaptado).
   - **Linguagem de Programação:** Python 3 (utilizando o módulo nativo `socket`).
   - **Ferramenta de Captura:** Wireshark.
   - **Ambiente de Rede:** Interface de Loopback Local (`127.0.0.1` / `localhost`).

2. **Aplicações Implementadas:**
   - `servidor_tcp.py`: Configura um socket do tipo `SOCK_STREAM`, associa à porta `5000` via `bind()`, passa a escutar via `listen(1)` e aceita conexões ativas com `accept()`. Recebe a mensagem enviada pelo cliente, transmite a resposta e encerra o socket.
   - `cliente_tcp.py`: Cria um socket TCP, conecta-se ao servidor na porta `5000` via `connect()`, envia a mensagem `"Olá, servidor TCP!"`, aguarda a resposta e fecha a conexão.
   - `servidor_udp.py`: Configura um socket do tipo `SOCK_DGRAM`, associa à porta `5001` via `bind()`, aguarda datagramas com `recvfrom()`, responde com `"Mensagem recebida via UDP."` para a tupla de endereço do cliente e encerra o socket.
   - `cliente_udp.py`: Cria um socket UDP e envia o datagrama diretamente para `(127.0.0.1, 5001)` utilizando `sendto()`, aguarda a resposta através de `recvfrom()` e fecha o socket.

3. **Procedimentos de Captura no Wireshark:**
   - Seleção da interface correspondente ao loopback (`Npcap Loopback Adapter` ou `Adapter for loopback traffic capture` no Windows / `lo0` no macOS).
   - Aplicação dos filtros de captura:
     - Tráfego TCP: `tcp.port == 5000`
     - Tráfego UDP: `udp.port == 5001`
   - Inicialização do processo servidor em um terminal, execução do cliente em um segundo terminal e gravação do tráfego.

---

## 4. Resultados

### 4.1 Execução do Teste TCP
- **Saída no Terminal do Servidor TCP:**
  ```text
  Servidor TCP aguardando conexão em 127.0.0.1:5000...
  Cliente conectado: ('127.0.0.1', <PORTA_EFEMERA_CLIENTE>)
  Mensagem recebida: Olá, servidor TCP!
  ```
  *(Inserir print da tela do terminal com a execução do servidor TCP)*

- **Saída no Terminal do Cliente TCP:**
  ```text
  Resposta do servidor: Mensagem recebida via TCP.
  ```
  *(Inserir print da tela do terminal com a execução do cliente TCP)*

- **Captura no Wireshark (`tcp.port == 5000`):**
  - **Fase de Estabelecimento (Handshake em 3 vias):**
    1. Pacote 1: Cliente $\to$ Servidor `[SYN] Seq=0`
    2. Pacote 2: Servidor $\to$ Cliente `[SYN, ACK] Seq=0 Ack=1`
    3. Pacote 3: Cliente $\to$ Servidor `[ACK] Seq=1 Ack=1`
  - **Fase de Transferência de Dados:**
    4. Pacote 4: Cliente $\to$ Servidor `[PSH, ACK]` com carga útil `"Olá, servidor TCP!"`
    5. Pacote 5: Servidor $\to$ Cliente `[ACK]` confirmando recebimento dos bytes
    6. Pacote 6: Servidor $\to$ Cliente `[PSH, ACK]` com carga útil `"Mensagem recebida via TCP."`
    7. Pacote 7: Cliente $\to$ Servidor `[ACK]` confirmando recebimento da resposta
  - **Fase de Encerramento da Conexão:**
    8. Pacotes com flags `[FIN, ACK]` e `[ACK]` trocados mutuamente para fechamento gracioso das duas direções do canal.
  *(Inserir print do Wireshark evidenciando a sequência de flags e números de sequência/confirmação)*

---

### 4.2 Execução do Teste UDP
- **Saída no Terminal do Servidor UDP:**
  ```text
  Servidor UDP aguardando datagrama em 127.0.0.1:5001...
  Mensagem recebida de ('127.0.0.1', <PORTA_EFEMERA_CLIENTE>): Olá, servidor UDP!
  ```
  *(Inserir print da tela do terminal com a execução do servidor UDP)*

- **Saída no Terminal do Cliente UDP:**
  ```text
  Resposta do servidor: Mensagem recebida via UDP.
  ```
  *(Inserir print da tela do terminal com a execução do cliente UDP)*

- **Captura no Wireshark (`udp.port == 5001`):**
  - Foram registrados estritamente **2 pacotes (datagramas)**:
    1. Datagrama do cliente para o servidor (`Origem: <PORTA_EFEMERA>`, `Destino: 5001`): Dados `"Olá, servidor UDP!"`.
    2. Datagrama do servidor para o cliente (`Origem: 5001`, `Destino: <PORTA_EFEMERA>`): Dados `"Mensagem recebida via UDP."`.
  - Ausência total de pacotes de controle, handshake, números de sequência ou pacotes de confirmação (ACK).
  *(Inserir print do Wireshark exibindo a lista e o cabeçalho dos datagramas UDP)*

---

### 4.3 Tabela Comparativa (Item 7.1 do Roteiro)

| Critério | TCP | UDP |
| :--- | :--- | :--- |
| **Estabelece conexão antes do envio?** | Sim (*Three-way handshake*) | Não |
| **Utiliza portas?** | Sim | Sim |
| **Possui handshake?** | Sim (`SYN`, `SYN-ACK`, `ACK`) | Não |
| **Garante entrega dos dados?** | Sim (confirmações e retransmissões) | Não (*Best-effort*) |
| **Garante ordem dos dados?** | Sim (via números de sequência) | Não |
| **Possui confirmação de recebimento?** | Sim (pacotes `ACK`) | Não |
| **Realiza retransmissão automática?** | Sim | Não |
| **Possui menor overhead?** | Não (cabeçalho de 20 a 60 bytes) | Sim (cabeçalho fixo de 8 bytes) |
| **Unidade de dados comum** | Segmento | Datagrama |
| **Porta usada no experimento** | `5000` | `5001` |

---

## 5. Discussão

A análise comparativa entre as capturas do Wireshark evidencia o contraste arquitetural entre o modelo de circuito virtual estabelecido pelo TCP e o modelo de envio sem conexão do UDP:

1. **Complexidade e Métodos de Socket:**
   - No TCP, o ciclo de vida da conexão exige métodos especializados de controle de estado (`listen()`, `accept()`, `connect()`). O servidor cria um socket dedicado para cada conexão aceita, separando o socket de escuta do socket de troca de dados.
   - No UDP, a ausência de estado reflete-se na simplicidade dos métodos: o socket apenas envia (`sendto()`) e recebe (`recvfrom()`), necessitando que o endereço e porta do destinatário acompanhem explicitamente cada datagrama.
2. **Sobrecarga de Rede e Eficiência:**
   - O TCP gera múltiplos pacotes de controle para gerenciar conexão e confirmação. Essa sobrecarga em pacotes e tamanho de cabeçalho (mínimo de 20 bytes versus 8 bytes do UDP) garante total confiabilidade, mas adiciona latência e consumo de banda.
   - O UDP descarta todo mecanismo de controle na camada de transporte, oferecendo envio imediato e direto, ideal para situações em que a velocidade imediata supera a relevância de eventuais perdas.

---

## 6. Conclusão

Os experimentos práticos executados demonstraram com clareza as características operacionais de TCP e UDP na camada de transporte. Foi possível compreender a importância dos métodos de socket na programação em redes e visualizar como o sistema operacional lida com conexões ativas versus mensagens avulsas. Conclui-se que a escolha entre TCP e UDP é uma decisão de compromisso (*trade-off*) entre confiabilidade e desempenho: o TCP é indispensável quando a perda de um único byte inviabiliza a aplicação, enquanto o UDP é a solução adequada quando a agilidade e a baixa latência são prioritárias.

---

## 7. Respostas às Perguntas Avaliativas (Item 9 do Roteiro da Atividade 02)

### 7.1 Questões Conceituais

#### 1. Qual é a diferença entre um segmento TCP e um datagrama UDP?
**Resposta:** A diferença fundamental reside na estrutura do cabeçalho e na semântica de transporte de cada unidade de dados:
- O **segmento TCP** é a unidade de dados do protocolo TCP. Possui um cabeçalho mais complexo (de 20 a 60 bytes) que contém campos para números de sequência (*Sequence Number*), números de confirmação (*Acknowledgment Number*), tamanho da janela deslizante (*Window Size*), flags de controle (`SYN`, `ACK`, `FIN`, `RST`, `PSH`, `URG`) e opções. O segmento faz parte de um fluxo de bytes contínuo, ordenado e confiável.
- O **datagrama UDP** é a unidade de dados do protocolo UDP. Possui um cabeçalho simples e fixo de apenas 8 bytes (contendo apenas Porta de Origem, Porta de Destino, Comprimento total e Checksum). Cada datagrama é uma mensagem delimitada, autônoma e independente (*message-oriented*), sem garantias de entrega, ordenação ou controle de estado.

#### 2. Explique o conceito de comunicação fim a fim na camada de transporte.
**Resposta:** Comunicação fim a fim (*end-to-end* ou *process-to-process*) significa que os protocolos da camada de transporte operam e mantêm estado exclusivamente nos dispositivos finais (origem e destino da comunicação — nós terminais). Os roteadores e comutadores intermediários da rede (que operam na camada de rede/enlace) apenas repassam os pacotes com base no cabeçalho IP, sem inspecionar, alterar ou manter informações sobre a sessão de transporte. A camada de transporte é a primeira camada que enxerga a aplicação e garante que a comunicação ocorra diretamente entre o processo cliente e o processo servidor.

#### 3. Por que a camada de transporte utiliza números de porta em vez de apenas endereços IP?
**Resposta:** Porque um mesmo computador (hospedeiro) com um único endereço IP executa simultaneamente dezenas de aplicações e processos de rede diferentes (por exemplo, um navegador web, um cliente de e-mail, um jogo online e um servidor de banco de dados). O endereço IP é responsável por localizar o host na rede global (*comunicação host-a-host*), mas é incapaz de distinguir qual programa interno deve receber a informação. Os números de porta (16 bits, variando de 0 a 65535) são necessários para permitir a **multiplexação** (combinar o tráfego de várias aplicações em um único fluxo de rede) e a **demultiplexação** (entregar os dados recebidos ao socket do processo correto).

#### 4. Explique o que significa dizer que o TCP mantém estado de conexão.
**Resposta:** Significa que os dois lados da comunicação (cliente e servidor) alocam e mantêm ativamente na memória do sistema operacional estruturas de controle que registram o status contínuo da sessão durante toda a sua existência. Esse estado engloba:
- A fase atual da conexão (ex.: `LISTEN`, `SYN_SENT`, `ESTABLISHED`, `FIN_WAIT`, `TIME_WAIT`).
- O número de sequência do próximo byte esperado e do próximo byte a enviar.
- O tamanho dos buffers de envio e recepção e a janela deslizante de controle de fluxo (*Receive Window*).
- Parâmetros dinâmicos de rede, como a estimativa do tempo de ida e volta (*Round-Trip Time* - RTT) e o controle de congestionamento (*Congestion Window*).

---

### 7.2 Questões sobre TCP

#### 5. No código do servidor TCP, qual é a função do método bind()?
**Resposta:** O método `bind((HOST, PORTA))` associa o socket recém-criado a um endereço IP específico e a um número de porta local específico do sistema operacional (no experimento, `127.0.0.1:5000`). Sem o `bind()`, o sistema operacional não saberia em qual porta o servidor pretende escutar para receber conexões direcionadas a ele.

#### 6. No código do servidor TCP, qual é a função do método listen()?
**Resposta:** O método `listen(backlog)` coloca o socket no estado passivo de escuta (`LISTEN`), indicando ao núcleo do sistema operacional que aquele socket está pronto para aceitar solicitações de conexão entrantes de clientes. O parâmetro passado (no código, `listen(1)`) define o tamanho máximo da fila de conexões pendentes aguardando para serem aceitas.

#### 7. No código do servidor TCP, qual é a função do método accept()?
**Resposta:** O método `accept()` é uma chamada bloqueante que aguarda a chegada de uma solicitação de conexão de um cliente na fila. Quando um cliente completa o *three-way handshake*, o `accept()` desbloqueia e retorna uma tupla contendo dois elementos: um **novo objeto de socket** dedicado exclusivamente à comunicação com aquele cliente conectado e o **endereço** (IP e porta efêmera) desse cliente. O socket original do servidor permanece livre e escutando na porta original.

#### 8. Por que o cliente TCP usa o método connect() antes de enviar a mensagem?
**Resposta:** Porque o TCP é um protocolo estritamente orientado à conexão. Antes que qualquer byte de mensagem da aplicação possa ser transmitido, é obrigatório negociar e estabelecer o circuito virtual com o servidor por meio do *three-way handshake* (troca de pacotes `SYN`, `SYN-ACK` e `ACK`), sincronizando os números de sequência iniciais e alocando recursos em ambas as pontas. O método `connect()` é justamente a chamada que dispara esse handshake no nível de rede.

#### 9. Explique por que o TCP é mais adequado quando a ordem correta dos dados é importante.
**Resposta:** O TCP atribui a cada byte transmitido um número de sequência numérico crescente (*Sequence Number*). Em uma rede real, diferentes pacotes IP podem percorrer rotas distintas e chegar fora de ordem ao destinatário. O receptor TCP utiliza esses números de sequência para reordenar os segmentos recebidos em um buffer de reorganização antes de entregá-los à aplicação consumidora, garantindo que o fluxo de bytes lido pelo processo de destino seja perfeitamente idêntico e sequencial ao emitido pela origem.

---

### 7.3 Questões sobre UDP

#### 10. No código do servidor UDP, qual é a função do método bind()?
**Resposta:** Assim como no TCP, o método `bind((HOST, PORTA))` associa o socket UDP ao endereço IP e à porta local definida (`127.0.0.1:5001`), de modo que o sistema operacional saiba para qual processo encaminhar qualquer datagrama UDP que chegue com destino à porta 5001.

#### 11. No código UDP, por que o cliente usa sendto() em vez de connect()?
**Resposta:** Porque o UDP não estabelece conexão prévia nem realiza handshake (*connectionless*). O método `sendto(mensagem, (HOST, PORTA))` permite empacotar e despachar imediatamente um datagrama avulso especificando explicitamente a tupla de destino `(IP, Porta)` a cada envio, sem a necessidade de criar uma sessão ou um canal contínuo com o destinatário.

#### 12. No servidor UDP, qual é a função do método recvfrom()?
**Resposta:** O método `recvfrom(buffer_size)` bloqueia o processo servidor até que um datagrama UDP chegue na porta associada. Ao receber o dado, o método lê o conteúdo do datagrama (até o limite de bytes especificado no buffer) e retorna simultaneamente os **dados brutos recebidos** e uma **tupla contendo o endereço de origem** `(IP, porta)` de quem enviou o datagrama.

#### 13. Por que o servidor UDP precisa conhecer o endereço do cliente para enviar a resposta?
**Resposta:** Porque o socket UDP não mantém uma conexão ativa ou persistente com o cliente; ele não possui um canal dedicado associado ao cliente após a leitura dos dados. Portanto, para responder, o servidor deve extrair a tupla `(IP, porta efêmera)` fornecida pelo retorno do `recvfrom()` e fornecê-la explicitamente como parâmetro de destino no método `sendto()`.

#### 14. Explique uma possível desvantagem do UDP em uma rede congestionada ou instável.
**Resposta:** A principal desvantagem é a **perda silenciosa de dados e a ausência de mecanismos de controle**. Em uma rede congestionada ou com alto índice de descarte, o UDP:
- Não possui confirmação de recebimento nem retransmissão automática; portanto, se um datagrama for descartado por um roteador sobrecarregado, a informação é perdida sem que a camada de transporte notifique a origem ou o destino.
- Não possui controle de congestionamento; logo, continuará injetando pacotes na taxa que a aplicação mandar, podendo agravar o colapso da rede e gerando alta taxa de perda sem qualquer autorregulação.

---

### 7.4 Questões Comparativas

#### 15. Ao observar o Wireshark, como é possível diferenciar visualmente uma comunicação TCP de uma comunicação UDP?
**Resposta:** É possível diferenciar visualmente por múltiplos aspectos evidentes na tela de captura:
1. **Pela coluna Protocol:** O Wireshark rotula claramente cada linha com `TCP` ou `UDP`.
2. **Pela presença de Flags:** As linhas TCP mostram flags no campo Info, como `[SYN]`, `[SYN, ACK]`, `[ACK]`, `[PSH, ACK]`, `[FIN, ACK]`, e números de sequência e confirmação (`Seq=... Ack=...`), enquanto as linhas UDP exibem apenas o comprimento do pacote e informações diretas da aplicação.
3. **Pela quantidade de pacotes:** O UDP exibe um fluxo direto de apenas 2 linhas (ida e volta da mensagem), enquanto o TCP apresenta uma sequência muito mais longa (10 a 11 linhas) contemplando a abertura da conexão, a troca de confirmações e o encerramento.
4. **Pelo esquema de cores padrão:** O Wireshark utiliza esquemas de coloração distintos para tráfego TCP (linhas acinzentadas/azuladas com destaque de flags) e tráfego UDP (tipicamente azul-claro).

#### 16. Qual protocolo apresentou menor complexidade na troca de mensagens capturada? Justifique.
**Resposta:** O **UDP apresentou menor complexidade**. Enquanto o TCP exigiu 10 a 11 pacotes com múltiplas transições de estado (negociação de 3 vias, envio com flag PSH, confirmações ACK para cada sentido e troca mútua de flags FIN para desconexão), o UDP realizou toda a comunicação em apenas **2 datagramas diretos** (um envio do cliente e uma resposta do servidor), com cabeçalho elementar de apenas 8 bytes e sem nenhum pacote de controle adicional.

#### 17. Por que a porta do servidor permanece fixa enquanto a porta do cliente pode variar a cada execução?
**Resposta:** A porta do servidor precisa ser **fixa e conhecida (*well-known / advertised port*)** para que qualquer cliente saiba exatamente para qual endereço e porta deve direcionar suas requisições — da mesma forma que um serviço de atendimento precisa de um número de telefone fixo e público. Já o cliente não precisa ter uma porta previamente fixada: o sistema operacional aloca dinamicamente uma **porta efêmera (temporária)** livre no momento em que o socket do cliente é aberto. Essa porta serve exclusivamente para identificar o processo daquela sessão específica e permitir que a resposta do servidor retorne ao programa correto. Ao fechar a aplicação e executá-la novamente, uma nova porta livre é alocada.

#### 18. Explique o que aconteceria se o cliente TCP tentasse se conectar à porta errada do servidor.
**Resposta:** Se o cliente TCP tentar conectar-se a uma porta onde não há nenhum processo escutando (por exemplo, porta 5555):
- No nível de rede, o cliente envia um pacote `[SYN]`. O sistema operacional do hospedeiro de destino recebe o pacote, verifica que não existe nenhum socket com `listen()` naquela porta e responde imediatamente com um pacote TCP com a flag **`[RST, ACK]` (Reset)**, rejeitando a tentativa de conexão.
- Na aplicação Python, a chamada `cliente.connect((HOST, PORTA))` falha e levanta uma exceção de sistema: `ConnectionRefusedError: [Errno 111 / Errno 61] Connection refused`.

#### 19. Explique o que aconteceria se o cliente UDP enviasse um datagrama para uma porta onde não há servidor aguardando.
**Resposta:** Como o UDP é *connectionless*, a chamada `cliente.sendto()` executa com sucesso imediatamente e o datagrama é transmitido pela rede, pois o cliente não espera nem verifica a disponibilidade do destinatário antes do envio. No entanto:
- Ao chegar no destino, como não há nenhum processo vinculado àquela porta UDP, a pilha IP do sistema operacional receptor descarta o datagrama e devolve para a origem uma mensagem de controle ICMP do tipo 3, código 3: **`ICMP Destination Unreachable (Port Unreachable)`**.
- Na captura do Wireshark, ver-se-á o pacote UDP de envio seguido imediatamente por um pacote `ICMP (Port unreachable)`.
- No lado do cliente, a chamada subsequente `cliente.recvfrom()` ficará bloqueada indefinidamente aguardando uma resposta que nunca virá (ou, em alguns sistemas operacionais que repassam o erro ICMP ao socket na leitura seguinte, levantará `ConnectionResetError`).

#### 20. Com base na atividade, explique como a escolha entre TCP e UDP pode afetar o desempenho e a confiabilidade de uma aplicação.
**Resposta:** A escolha entre TCP e UDP define o compromisso estrutural entre **confiabilidade total** e **máximo desempenho/menor latência**:
- **Escolhendo o TCP:** A aplicação ganha entrega garantida, dados livres de corrupção, sem duplicações e estritamente na ordem correta, além de proteção contra congestionamento da rede. Por outro lado, há um custo de **desempenho**: maior sobrecarga de cabeçalho (overhead de 20 a 60 bytes por pacote), latência adicional introduzida pelo *handshake* inicial de ida e volta (RTT), pausas para aguardar confirmações (*Stop-and-Wait* ou janelas) e atrasos causados pelo bloqueio de cabeça de fila (*head-of-line blocking*) quando um pacote perdido precisa ser retransmitido antes dos seguintes.
- **Escolhendo o UDP:** A aplicação obtém **desempenho máximo**: envio imediato sem atraso de conexão, menor consumo de largura de banda (cabeçalho de apenas 8 bytes) e processamento simplificado. Porém, a aplicação abdica de qualquer garantia da camada de transporte; se a rede falhar, oscilar ou descartar pacotes, dados serão perdidos ou chegarão fora de ordem. Caso a aplicação precise de confiabilidade seletiva, esses mecanismos precisarão ser implementados manualmente na camada de aplicação.
