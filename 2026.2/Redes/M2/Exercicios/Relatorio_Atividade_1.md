# UNIVERSIDADE DO VALE DO ITAJAÍ — UNIVALI
## Curso de Ciência da Computação
### Disciplina: Redes de Computadores II
### Professor: Ewerton Alonso

---

# RELATÓRIO PRÁTICO: ATIVIDADE 01
## Análise da Camada de Transporte: TCP x UDP

**Integrantes:**
- [Nome do Aluno / Integrantes]

**Professor:** Prof. Ewerton Alonso  
**Data de Entrega:** [Inserir Data]

---

## 1. Introdução

A camada de transporte do Modelo OSI (Open Systems Interconnection) e da arquitetura TCP/IP é responsável pela comunicação lógica fim a fim (processo a processo) entre aplicações executando em hospedeiros diferentes ou no mesmo hospedeiro. Para desempenhar esse papel, a camada de transporte faz uso de portas lógicas (endereçamento de 16 bits), segmentação, controle de fluxo e verificação de integridade.

Dentre os protocolos fundamentais dessa camada, destacam-se o **TCP (Transmission Control Protocol)** e o **UDP (User Datagram Protocol)**:
- O **TCP** é orientado à conexão, confiável e garante tanto a integridade quanto a ordem sequencial dos dados transmitidos, utilizando mecanismos de *three-way handshake*, confirmações numéricas (ACK) e retransmissões automáticas.
- O **UDP**, por sua vez, é um protocolo não orientado à conexão e do tipo *best-effort*, priorizando baixa latência e baixo *overhead* estrutural (cabeçalho de apenas 8 bytes), sem implementar garantias de entrega ou controle de fluxo nativos.

---

## 2. Objetivo

Analisar de forma prática e comparativa o comportamento dos protocolos TCP e UDP por meio da implementação e execução de aplicações cliente-servidor em linguagem Python, inspecionando o tráfego gerado através do analisador de pacotes Wireshark na interface de loopback local (`127.0.0.1`).

---

## 3. Metodologia

1. **Ambiente e Ferramentas:**
   - **Sistema Operacional:** Windows 10/11 (ou macOS / Linux adaptado).
   - **Linguagem de Programação:** Python 3 (módulo nativo `socket`).
   - **Analisador de Pacotes:** Wireshark.
   - **Ambiente de Rede:** Interface de Loopback Local (`127.0.0.1` / `localhost`).

2. **Códigos Desenvolvidos:**
   - `servidor_tcp.py`: Configura um socket TCP (`SOCK_STREAM`), faz o *bind* na porta `5000`, aguarda conexões via `listen()` e `accept()`, recebe a mensagem do cliente, envia confirmação em texto e fecha a conexão.
   - `cliente_tcp.py`: Inicia conexão com `127.0.0.1:5000`, envia a mensagem `"Olá, servidor TCP!"`, aguarda a resposta do servidor e fecha o socket.
   - `servidor_udp.py`: Cria um socket UDP (`SOCK_DGRAM`), associa-se à porta `5001`, recebe datagrama com `recvfrom()`, responde com `"Mensagem recebida via UDP."` para o endereço de origem e fecha o socket.
   - `cliente_udp.py`: Envia o datagrama `"Olá, servidor UDP!"` diretamente para `127.0.0.1:5001` sem estabelecimento prévio de conexão e aguarda resposta via `recvfrom()`.

3. **Captura no Wireshark:**
   - Seleção da interface `Npcap Loopback Adapter` (ou `Adapter for loopback traffic capture` no Windows / `lo0` no macOS).
   - Aplicação dos filtros:
     - Para TCP: `tcp.port == 5000`
     - Para UDP: `udp.port == 5001`
   - Inicialização do servidor, seguida da execução do cliente em terminais distintos, gravando o fluxo completo de pacotes.

---

## 4. Resultados

### 4.1 Execução TCP
- **Terminal do Servidor TCP:**
  ```text
  Servidor TCP aguardando conexão em 127.0.0.1:5000...
  Cliente conectado: ('127.0.0.1', <PORTA_EFEMERA_CLIENTE>)
  Mensagem recebida: Olá, servidor TCP!
  ```
  *(Inserir print da janela do terminal do servidor TCP)*

- **Terminal do Cliente TCP:**
  ```text
  Resposta do servidor: Mensagem recebida via TCP.
  ```
  *(Inserir print da janela do terminal do cliente TCP)*

- **Captura no Wireshark (Filtro: `tcp.port == 5000`):**
  - Sequência de estabelecimento de conexão (*Three-Way Handshake*): `[SYN]`, `[SYN, ACK]`, `[ACK]`.
  - Envio de dados do cliente para servidor: `[PSH, ACK]` contendo `"Olá, servidor TCP!"`.
  - Confirmação recebida do servidor: `[ACK]`.
  - Envio de dados de resposta do servidor: `[PSH, ACK]` contendo `"Mensagem recebida via TCP."`.
  - Confirmação do cliente: `[ACK]`.
  - Procedimento de finalização de conexão: `[FIN, ACK]`, `[ACK]`, `[FIN, ACK]`, `[ACK]`.
  *(Inserir print do Wireshark evidenciando as flags e portas do tráfego TCP)*

---

### 4.2 Execução UDP
- **Terminal do Servidor UDP:**
  ```text
  Servidor UDP aguardando datagrama em 127.0.0.1:5001...
  Mensagem recebida de ('127.0.0.1', <PORTA_EFEMERA_CLIENTE>): Olá, servidor UDP!
  ```
  *(Inserir print da janela do terminal do servidor UDP)*

- **Terminal do Cliente UDP:**
  ```text
  Resposta do servidor: Mensagem recebida via UDP.
  ```
  *(Inserir print da janela do terminal do cliente UDP)*

- **Captura no Wireshark (Filtro: `udp.port == 5001`):**
  - Foram observados apenas **2 pacotes (datagramas)**:
    1. Pacote do cliente (`127.0.0.1:<PORTA_EFEMERA> -> 127.0.0.1:5001`): Datagrama com `"Olá, servidor UDP!"`.
    2. Pacote de resposta do servidor (`127.0.0.1:5001 -> 127.0.0.1:<PORTA_EFEMERA>`): Datagrama com `"Mensagem recebida via UDP."`.
  - Ausência total de handshake prévio ou pacotes de confirmação (ACK) na camada de transporte.
  *(Inserir print do Wireshark com a captura dos datagramas UDP)*

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

A comparação prática entre as capturas no Wireshark revelou de forma inequívoca as filosofias de projeto distintas de cada protocolo:

1. **Volume de Tráfego e Sobrecarga (*Overhead*):** Enquanto o UDP exigiu estritamente 2 pacotes para realizar a troca completa das mensagens (um para ida e um para volta), o TCP exigiu entre 10 e 11 pacotes para transmitir a mesma carga útil de aplicação. O volume adicional do TCP decorre da necessidade de estabelecer o canal (*handshake* triplo), confirmar cada segmento de dados (`ACK`) e encerrar a sessão de forma ordenada (`FIN`).
2. **Conexão e Estado:** O TCP mantém controle rigoroso de estado nos dois hospedeiros, com números de sequência e reconhecimento contínuos. O UDP opera de modo completamente *stateless* e desacoplado na camada de transporte.
3. **Complexidade vs. Desempenho:** A simplicidade do UDP proporciona latência mínima e processamento trivial, tornando-o ideal para aplicações sensíveis a atrasos, como chamadas VoIP, transmissões ao vivo e jogos online. Já a robustez do TCP o torna insubstituível em cenários onde a integridade do dado é prioritária, como navegação web (HTTP/HTTPS), transferência de arquivos (FTP/SFTP) e correio eletrônico (SMTP/IMAP).

---

## 6. Conclusão

A atividade permitiu constatar experimentalmente os conceitos teóricos fundamentais da camada de transporte. Foi possível visualizar o papel essencial das portas na multiplexação e demultiplexação de processos em um mesmo dispositivo e verificar com precisão o funcionamento do *three-way handshake* e do fechamento de conexão no TCP, contrapondo-os à agilidade e descomplicação dos datagramas UDP. Conclui-se que nenhum dos protocolos é estritamente superior ao outro em termos absolutos: o TCP é a escolha mandatória quando a confiabilidade é indispensável, ao passo que o UDP é preferível quando a velocidade e a baixa latência se sobrepõem à eventual perda de pacotes.

---

## 7. Respostas às Perguntas Avaliativas (Item 9 do Roteiro)

### 7.1 Questões Conceituais

#### 1. Qual é a principal função da camada de transporte no modelo OSI?
**Resposta:** Fornecer comunicação lógica fim a fim (*process-to-process*) entre aplicações executadas em hospedeiros diferentes. Ela realiza a multiplexação e demultiplexação de tráfego por meio de portas lógicas, controla a segmentação e remontagem dos dados e, dependendo do protocolo empregado, fornece serviços de confiabilidade, controle de fluxo e controle de congestionamento.

#### 2. Explique a diferença entre comunicação host-a-host e comunicação processo-a-processo.
**Resposta:** A comunicação **host-a-host** (camada de rede / IP) é responsável por entregar pacotes de uma máquina física/lógica (endereço IP de origem) até outra máquina (endereço IP de destino), sem saber qual programa ou serviço receberá os dados. Já a comunicação **processo-a-processo** (camada de transporte / TCP/UDP) identifica e entrega a mensagem diretamente ao processo/aplicação correto em execução dentro do host, utilizando o número da porta lógica (*port number*).

#### 3. O que são portas TCP e UDP e qual sua importância na comunicação entre aplicações?
**Resposta:** São identificadores numéricos de 16 bits (valores de 0 a 65535) que funcionam como endereços lógicos dos pontos terminais de comunicação nos sistemas operacionais. Sua importância reside em possibilitar a multiplexação (várias aplicações transmitindo simultaneamente pela mesma placa de rede) e a demultiplexação (o sistema operacional saber exatamente qual processo deve receber cada dado recebido).

#### 4. O que é uma porta efêmera? Ela apareceu nos testes realizados? Explique.
**Resposta:** Uma porta efêmera (ou temporária) é uma porta alocada dinamicamente pelo sistema operacional para o processo cliente quando este inicia uma comunicação de rede. Ela possui vida útil curta, durando apenas enquanto a conexão/sessão estiver ativa, e pertence tipicamente à faixa de portas dinâmicas (49152 a 65535). **Sim, ela apareceu claramente nos testes realizados**: nos scripts clientes (`cliente_tcp.py` e `cliente_udp.py`), não foi definida nenhuma porta fixa de saída; logo, o sistema operacional atribuiu automaticamente uma porta efêmera (ex.: 54321, 62956, etc.) exibida tanto nas mensagens do servidor (`Cliente conectado: ('127.0.0.1', porta)`) quanto nas capturas do Wireshark na coluna de porta de origem do cliente.

---

### 7.2 Questões sobre TCP

#### 5. Qual porta foi utilizada pelo servidor TCP nesta atividade?
**Resposta:** Foi utilizada a porta **5000** (`HOST = "127.0.0.1"`, `PORTA = 5000`).

#### 6. Quais pacotes formam o processo de estabelecimento de conexão TCP?
**Resposta:** Os pacotes que formam o processo conhecido como *Three-Way Handshake* (Aperto de Mão em Três Vias):
1. **SYN**: O cliente envia uma flag SYN com seu número de sequência inicial (*ISN*).
2. **SYN-ACK**: O servidor responde com as flags SYN e ACK, confirmando o número de sequência do cliente e informando o seu próprio.
3. **ACK**: O cliente responde com a flag ACK, finalizando a sincronização e estabelecendo a conexão.

#### 7. O que significa o three-way handshake no TCP? Explique com base na captura do Wireshark.
**Resposta:** Significa o procedimento de três etapas pelo qual cliente e servidor entram em acordo mútuo para sincronizar números de sequência, parâmetros de transmissão (como tamanho máximo de segmento - MSS e fator de escala de janela) e alocar buffers de memória antes que qualquer byte de dado de aplicação seja transmitido. No Wireshark, isso é observado logo no início da captura nas 3 primeiras linhas filtradas por `tcp.port == 5000`: primeiro um pacote do cliente para o servidor com a flag `[SYN]`, em seguida a resposta do servidor com `[SYN, ACK]`, e finalmente a confirmação do cliente com `[ACK]`, ficando o socket pronto para troca de dados.

#### 8. O TCP apresentou pacotes de confirmação de recebimento? Como isso foi observado no Wireshark?
**Resposta:** **Sim.** Foi observado no Wireshark pela presença de segmentos com a flag **ACK** (`Acknowledgement`). Imediatamente após o envio do segmento contendo os dados da mensagem (flag `[PSH, ACK]`), o receptor devolve um pacote `[ACK]` cujo campo *Acknowledgment Number* corresponde ao número de sequência recebido acrescido do tamanho em bytes dos dados entregues, confirmando explicitamente que os bytes foram recebidos com sucesso.

#### 9. O TCP é considerado um protocolo confiável? Justifique.
**Resposta:** **Sim.** O TCP é classificado como confiável porque implementa um conjunto rigoroso de garantias: confirmações de recebimento (ACKs), temporizadores de retransmissão para pacotes perdidos (ARQ), ordenação sequencial dos segmentos via *Sequence Numbers* (evitando entrega fora de ordem), controle de integridade através de *checksum* e controle de fluxo e congestionamento (evitando que o receptor ou a rede fiquem sobrecarregados).

---

### 7.3 Questões sobre UDP

#### 10. Qual porta foi utilizada pelo servidor UDP nesta atividade?
**Resposta:** Foi utilizada a porta **5001** (`HOST = "127.0.0.1"`, `PORTA = 5001`).

#### 11. O UDP realizou handshake antes do envio da mensagem? Explique.
**Resposta:** **Não.** O UDP é um protocolo não orientado à conexão (*connectionless*). Ele simplesmente encapsula a carga útil da aplicação com seu cabeçalho de 8 bytes e a entrega à camada de rede imediatamente através da chamada de envio (`sendto`), sem qualquer negociação prévia ou sincronização de estado com o destinatário.

#### 12. O UDP apresentou confirmações de recebimento no nível da camada de transporte? Justifique com base na captura.
**Resposta:** **Não.** Na captura do Wireshark filtrada por `udp.port == 5001`, verificam-se unicamente os dois datagramas contendo dados de aplicação (o enviado pelo cliente e a resposta enviada pelo servidor). Não há nenhum pacote intermediário ou campo de flag de confirmação (ACK) gerado pelo protocolo UDP; a camada de transporte apenas encaminha os datagramas sem verificar se chegaram.

#### 13. Por que o UDP é considerado mais simples que o TCP?
**Resposta:** Porque o UDP possui uma estrutura enxuta e estática: seu cabeçalho tem apenas 8 bytes (contendo somente Porta de Origem, Porta de Destino, Comprimento e Checksum) e ele não mantém controle de estado da conexão, dispense o *handshake*, não possui números de sequência, não controla fluxo, não realiza retransmissões e não efetua controle de congestionamento.

#### 14. Cite dois exemplos de aplicações em que o uso de UDP pode ser adequado.
**Resposta:**
1. **Transmissões de áudio e vídeo em tempo real (VoIP / Streaming ao vivo / Videoconferências como Zoom/Discord):** onde a baixa latência é crucial e a retransmissão de um pacote de voz atrasado não traria utilidade prática.
2. **Consultas DNS (Domain Name System) e Jogos Online Multiplayer:** onde mensagens curtas de requisição/resposta se beneficiam da ausência de latência de conexão, e jogos em tempo real necessitam da menor latência possível para sincronização de posição de jogadores.

---

### 7.4 Questões Comparativas

#### 15. Preencha a tabela comparativa entre TCP e UDP apresentada na Parte III.
**Resposta:** *(A tabela encontra-se preenchida na Seção 4.3 deste relatório).*

#### 16. Comparando as capturas TCP e UDP, qual protocolo gerou mais pacotes para realizar a comunicação? Explique o motivo.
**Resposta:** O **TCP gerou significativamente mais pacotes** (em média 10 a 11 pacotes) em comparação ao UDP (que gerou apenas 2 pacotes). O motivo é que o TCP necessita de 3 pacotes para estabelecer a conexão (*three-way handshake*), pacotes de confirmação (`ACK`) para cada segmento de dados enviado, e de 3 a 4 pacotes para finalizar a conexão de modo ordenado (*FIN-ACK handshake*), enquanto o UDP realiza estritamente o envio dos datagramas de dados solicitados pela aplicação.

#### 17. Em quais situações o TCP é mais indicado? Justifique.
**Resposta:** O TCP é mais indicado em qualquer situação onde a integridade, a exatidão e a completude dos dados são essenciais e onde perdas ou desordenação de bytes corromperiam o resultado. Exemplos incluem transferência de arquivos (FTP, SFTP), páginas web (HTTP/HTTPS), envio e recebimento de e-mails (SMTP, IMAP, POP3), acesso remoto seguro (SSH) e transações em bancos de dados. Nesses casos, o custo adicional de processamento e latência do TCP é plenamente justificado pela garantia de que nenhuma informação se perderá.

#### 18. Em quais situações o UDP é mais indicado? Justifique.
**Resposta:** O UDP é mais indicado em aplicações de tempo real (*real-time*) e baixa latência, em que a velocidade de entrega é mais importante do que a confiabilidade absoluta de cada pacote individual, ou em comunicações atômicas de pergunta-e-resposta curta. Exemplos: jogos em rede competitivos, chamadas de voz e vídeo (VoIP), broadcast/multicast em redes locais e consultas leves de resolução de nomes (DNS) e atribuição de endereços (DHCP). Nesses cenários, reenviar um pacote perdido chegaria tarde demais para ser útil.

#### 19. Qual foi a principal diferença observada entre TCP e UDP durante a atividade prática?
**Resposta:** A principal diferença observada foi a presença visível de uma **sessão formal de conexão** no TCP em contraste com o envio imediato e independente no UDP. No TCP, o cliente precisou negociar a conexão antes de poder enviar sua mensagem e precisou encerrá-la explicitamente, gerando múltiplos pacotes de controle observados no Wireshark; no UDP, o tráfego resumiu-se estritamente aos dados da aplicação, sem qualquer fase de abertura, confirmação de recebimento ou encerramento no nível de transporte.

#### 20. Explique como o Wireshark ajudou na compreensão da camada de transporte.
**Resposta:** O Wireshark permitiu tornar visual e tangível aquilo que antes era puramente teórico na especificação dos protocolos. Através dele, foi possível inspecionar os cabeçalhos reais, visualizar a alternância de portas de origem e destino na comunicação de ida e volta, acompanhar a evolução das flags (`SYN`, `ACK`, `FIN`, `PSH`), verificar os números de sequência e confirmação do TCP e constatar, de forma prática e imediata, a ausência de sobrecarga e a concisão dos datagramas UDP.
