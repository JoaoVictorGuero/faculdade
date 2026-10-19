# UNIVERSIDADE DO VALE DO ITAJAÍ — UNIVALI
## Curso de Ciência da Computação
### Disciplina: Redes de Computadores II
### Professor: Ewerton Alonso

---

# RELATÓRIO PRÁTICO: ATIVIDADE 03
## Análise da Camada de Transporte: TCP x UDP

**Integrantes:**
- [Nome do Aluno / Integrantes]

**Professor:** Prof. Ewerton Alonso  
**Data de Entrega:** [Inserir Data]

---

## 1. Introdução

Na arquitetura de redes em camadas (Modelos OSI e TCP/IP), a camada de transporte ocupa uma posição estratégica fundamental entre as aplicações de usuário (camada de aplicação) e a infraestrutura de encaminhamento de pacotes (camadas de rede, enlace e física). Enquanto a camada de rede é encarregada de rotear pacotes entre diferentes nós da rede (comunicação hospedeiro a hospedeiro), a camada de transporte provê a comunicação lógica direta entre os processos de software em execução nesses nós (comunicação processo a processo).

Para atender às variadas demandas dos serviços de rede, a camada de transporte disponibiliza dois protocolos de transporte basilares na Internet:
- **TCP (Transmission Control Protocol):** Protocolo orientado à conexão, com entrega garantida e ordenada dos dados. Utiliza o procedimento de *three-way handshake* para sincronização de parâmetros, números de sequência e confirmação (*Sequence* e *Acknowledgment*), controle de fluxo baseado em janela deslizante e controle de congestionamento.
- **UDP (User Datagram Protocol):** Protocolo não orientado à conexão (*connectionless*) e sem confirmações nativas (*best-effort*). Dispensa o handshake, não mantém estado de sessão e possui um cabeçalho fixo e enxuto de 8 bytes, viabilizando transmissões com mínima latência e sem a sobrecarga de controle presente no TCP.

---

## 2. Objetivo

Analisar empiricamente o comportamento dos protocolos TCP e UDP mediante a execução de aplicações cliente-servidor implementadas em Python, avaliando o ciclo de vida da comunicação, os filtros de captura, o papel dos identificadores de portas lógicas e a estrutura dos pacotes capturados no Wireshark.

---

## 3. Metodologia

1. **Ambiente e Ferramentas:**
   - **Sistema Operacional:** Windows 10 / Windows 11 (ou macOS / Linux adaptado).
   - **Linguagem de Programação:** Python 3 (módulo de baixo nível `socket`).
   - **Analisador de Protocolos de Rede:** Wireshark.
   - **Rede de Teste:** Interface de Loopback Local (`127.0.0.1` / `localhost`).

2. **Programas Executados:**
   - `servidor_tcp.py`: Cria socket TCP com `socket.SOCK_STREAM`, associa à porta `5000` via `bind()`, aguarda solicitações via `listen(1)` e `accept()`, recebe a mensagem do cliente, transmite resposta e finaliza a conexão.
   - `cliente_tcp.py`: Instancia socket TCP, solicita conexão ao servidor (`127.0.0.1:5000`) via `connect()`, envia a string `"Olá, servidor TCP!"`, recebe a confirmação e encerra a conexão.
   - `servidor_udp.py`: Cria socket UDP com `socket.SOCK_DGRAM`, associa à porta `5001` via `bind()`, aguarda datagramas com `recvfrom()`, extrai dados e endereço de origem do remetente, envia resposta `"Mensagem recebida via UDP."` com `sendto()` e fecha o socket.
   - `cliente_udp.py`: Cria socket UDP, envia diretamente `"Olá, servidor UDP!"` para `(127.0.0.1, 5001)` usando `sendto()`, aguarda o retorno com `recvfrom()` e encerra o socket.

3. **Captura no Wireshark:**
   - Interface selecionada: `Adapter for loopback traffic capture` ou `Npcap Loopback Adapter` (ou `lo0` no macOS).
   - Filtros de exibição aplicados:
     - Para teste TCP: `tcp.port == 5000`
     - Para teste UDP: `udp.port == 5001`
   - Inicialização do servidor em um terminal, execução do cliente em outro terminal e inspeção detalhada dos pacotes.

---

## 4. Resultados

### 4.1 Execução do Teste TCP
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

- **Captura no Wireshark (`tcp.port == 5000`):**
  - **Estabelecimento de Conexão (*Handshake* em 3 vias):**
    1. Pacote 1: `[SYN]` emitido pelo cliente (`porta efêmera -> 5000`).
    2. Pacote 2: `[SYN, ACK]` emitido pelo servidor (`5000 -> porta efêmera`).
    3. Pacote 3: `[ACK]` emitido pelo cliente, concluindo o estabelecimento.
  - **Troca de Mensagens de Aplicação:**
    4. Pacote 4: `[PSH, ACK]` do cliente com `"Olá, servidor TCP!"`.
    5. Pacote 5: `[ACK]` do servidor confirmando os bytes recebidos.
    6. Pacote 6: `[PSH, ACK]` do servidor com `"Mensagem recebida via TCP."`.
    7. Pacote 7: `[ACK]` do cliente confirmando a resposta.
  - **Encerramento da Conexão:**
    8. Pacotes contendo as flags `[FIN, ACK]` e `[ACK]` finalizando graciosamente a transmissão em ambos os sentidos.
  *(Inserir print do Wireshark evidenciando a sequência de pacotes TCP e suas flags)*

---

### 4.2 Execução do Teste UDP
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

- **Captura no Wireshark (`udp.port == 5001`):**
  - Foram gerados e observados estritamente **2 datagramas**:
    1. Datagrama 1: `<PORTA_EFEMERA> -> 5001` contendo `"Olá, servidor UDP!"`.
    2. Datagrama 2: `5001 -> <PORTA_EFEMERA>` contendo `"Mensagem recebida via UDP."`.
  - Ausência completa de pacotes de sincronização (*handshake*), pacotes de confirmação (`ACK`) ou controle de encerramento na camada de transporte.
  *(Inserir print do Wireshark exibindo os datagramas UDP capturados)*

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

A comparação empírica permitiu contrastar diretamente os princípios operacionais de TCP e UDP:

1. **Eficiência de Protocolo versus Confiabilidade:**
   - O UDP executou a transferência em apenas 2 pacotes e com cabeçalho de 8 bytes, demonstrando eficiência máxima em termos de ocupação de canal e ausência de atraso prévio. Contudo, em cenários de perda na rede, os dados simplesmente desaparecem sem notificação para a aplicação.
   - O TCP demandou mais de 10 pacotes para entregar a mesma informação, mas garantiu contratualmente que nenhuma informação foi corrompida ou perdida e que os processos concordaram mutuamente na abertura e no término do canal.
2. **Multiplexação e Portas Lógicas:**
   - Em ambos os testes, a identificação dos processos foi assegurada pelo par de portas (porta de serviço fixa no servidor e porta efêmera alocada pelo sistema operacional no cliente), evidenciando como a camada de transporte atua de forma transparente e independente da camada de rede IP.

---

## 6. Conclusão

A atividade prática consolidou a compreensão do funcionamento da camada de transporte e de seus dois principais protocolos. Ficou evidenciado que o TCP é essencial em aplicações que demandam confiabilidade estrita, ordenação e integridade dos dados (como transferência de arquivos, páginas web e bancos de dados), enquanto o UDP é a escolha ideal para aplicações em que a baixa latência e a agilidade de transmissão são cruciais (como streaming multimídia em tempo real, jogos online e consultas rápidas de DNS).

---

## 7. Respostas às Perguntas Avaliativas (Item 9 do Roteiro da Atividade 03)

### 7.1 Questões Conceituais

#### 1. Explique por que a camada de transporte é necessária, mesmo já existindo a camada de rede.
**Resposta:** A camada de rede (protocolo IP) é responsável apenas pelo roteamento e pela entrega dos pacotes de uma máquina física/lógica até outra máquina (*comunicação host-a-host*). No entanto, um único computador executa dezenas de aplicações concorrentes. A camada de rede não tem conhecimento sobre processos, portas ou sessões de software. A camada de transporte é estritamente necessária porque:
- Fornece **comunicação lógica processo a processo**, garantindo que os dados sejam entregues ao processo específico correto por meio dos números de portas;
- Oferece serviços essenciais que a camada de rede IP (que é *best-effort*) não provê, tais como controle de fluxo, controle de congestionamento, verificação de integridade aprimorada e recuperação de pacotes perdidos por meio de retransmissões no caso do TCP.

#### 2. Qual é a função da multiplexação e da demultiplexação na camada de transporte?
**Resposta:**
- **Multiplexação (no transmissor):** É a capacidade de coletar blocos de dados provenientes de diferentes sockets e processos de aplicação em execução na máquina, encapsular cada um com o respectivo cabeçalho da camada de transporte (inserindo as portas de origem e destino) e encaminhar esses segmentos/datagramas unificados à camada de rede para transmissão pelo mesmo meio físico.
- **Demultiplexação (no receptor):** É o processo inverso, realizado no hospedeiro de destino, que inspeciona os campos do cabeçalho da camada de transporte (em especial a porta de destino e, no TCP, também IP e porta de origem) para direcionar os dados recebidos ao socket exato do processo destinatário correto.

#### 3. Explique a diferença entre endereço IP e número de porta.
**Resposta:**
- **Endereço IP (Camada de Rede - 32 bits no IPv4 / 128 bits no IPv6):** Identifica a interface de rede do hospedeiro (*host*) conectado à rede global ou local. Funciona analogamente ao endereço de um prédio residencial (localiza a edificação na cidade).
- **Número de Porta (Camada de Transporte - 16 bits, de 0 a 65535):** Identifica um ponto terminal lógico de comunicação (socket) associado a um processo ou aplicação específica dentro daquele hospedeiro. Funciona analogamente ao número do apartamento dentro do prédio, garantindo que a encomenda chegue ao morador exato.

#### 4. Por que duas aplicações diferentes podem usar a rede ao mesmo tempo no mesmo computador?
**Resposta:** Porque a camada de transporte gerencia o tráfego de rede associando cada aplicação a um **número de porta lógica exclusivo e distinto** (ou a uma tupla única de identificação de socket: IP Origem, Porta Origem, IP Destino, Porta Destino, Protocolo). Assim, embora compartilhem a mesma placa de rede e o mesmo endereço IP, os dados de cada aplicação possuem identificadores de porta diferentes, permitindo que o sistema operacional entregue os pacotes de cada fluxo ao respectivo processo de forma totalmente isolada e concorrente.

---

### 7.2 Questões sobre TCP

#### 5. No experimento TCP, qual lado iniciou a conexão: cliente ou servidor? Justifique.
**Resposta:** A conexão foi iniciada pelo **cliente** (`cliente_tcp.py`). A justificativa é que o servidor colocou-se em modo passivo de escuta através do método `listen()`, enquanto o cliente executou ativamente o método `connect()`, enviando o primeiro pacote da comunicação: o segmento TCP com a flag **`[SYN]`** direcionado ao servidor (`127.0.0.1:5000`), iniciando formalmente o *Three-Way Handshake*.

#### 6. Qual é a finalidade da flag SYN no início de uma conexão TCP?
**Resposta:** A finalidade da flag `SYN` (*Synchronize*) é sincronizar os números de sequência iniciais (*Initial Sequence Number* - ISN) entre o cliente e o servidor. Ela indica o início de uma nova conexão e permite que ambos os nós acordem a numeração que será usada para rastrear, ordenar e confirmar cada byte subsequente que for transmitido ao longo da sessão.

#### 7. Qual é a finalidade da flag ACK em uma comunicação TCP?
**Resposta:** A finalidade da flag `ACK` (*Acknowledgment*) é confirmar explicitamente o recebimento bem-sucedido de segmentos de dados ou pacotes de controle. Quando um host envia um pacote com a flag `ACK`, o campo *Acknowledgment Number* indica o número de sequência do próximo byte que o remetente espera receber, confirmando cumulativamente que todos os bytes anteriores foram recebidos de forma íntegra.

#### 8. Por que o TCP precisa de mais pacotes do que o UDP para transmitir uma mensagem simples?
**Resposta:** Porque o TCP implementa uma conexão orientada e confiável, o que exige a troca de pacotes de controle de protocolo adicionais além da mensagem útil da aplicação:
1. **Fase de Abertura:** 3 pacotes dedicados ao *three-way handshake* (`SYN`, `SYN-ACK`, `ACK`);
2. **Fase de Dados:** segmentos contendo a mensagem (`PSH, ACK`) acompanhados de seus respectivos pacotes de confirmação (`ACK`);
3. **Fase de Fechamento:** 3 a 4 pacotes para o encerramento gracioso bidirecional da conexão (`FIN, ACK` e `ACK`).
O UDP, por outro lado, transmite estritamente os datagramas de dados de aplicação sem qualquer pacote de controle prévio ou posterior.

#### 9. O que pode acontecer em uma comunicação TCP caso um segmento seja perdido durante a transmissão?
**Resposta:** O TCP detectará a perda e realizará a **retransmissão automática** do segmento perdido. Isso ocorre por dois mecanismos:
- **Estouro de Temporizador (*Retransmission Timeout* - RTO):** Se o transmissor não receber o `ACK` correspondente antes de expirar o temporizador de retransmissão, ele reenviará o segmento.
- **Confirmações Duplicadas (*Fast Retransmit*):** Se o receptor receber segmentos posteriores fora de ordem, ele continuará enviando ACKs duplicados com o número do segmento faltante; ao receber três ACKs duplicados, o transmissor reenvia o pacote imediatamente sem aguardar o timeout.
Durante a recuperação, o receptor retém os segmentos posteriores em seu buffer e não os entrega à aplicação até que o segmento faltante chegue, garantindo entrega completa e estritamente ordenada (*evitando corrupção do fluxo*).

---

### 7.3 Questões sobre UDP

#### 10. No experimento UDP, o cliente precisou estabelecer conexão antes de enviar a mensagem? Explique.
**Resposta:** **Não.** O cliente UDP simplesmente invocou o método `sendto(mensagem.encode(), (HOST, PORTA))` e despachou o datagrama de forma imediata. O UDP não possui conceito de estado de circuito virtual ou aperto de mão; o cliente assume que o destinatário pode estar ouvindo e envia os dados diretamente à rede.

#### 11. Por que se diz que o UDP é um protocolo não orientado à conexão?
**Resposta:** Porque ele não estabelece nem finaliza uma sessão lógica prévia entre os pontos terminais antes de transmitir dados. Não existe troca de mensagens de controle (*handshake*), não há criação de circuitos virtuais, nenhum dos hosts aloca recursos coordenados de controle de estado e cada datagrama é tratado pela rede como uma entidade completamente independente dos anteriores ou posteriores.

#### 12. O UDP garante que a mensagem chegará ao destino? Justifique.
**Resposta:** **Não.** O UDP opera sob o princípio de melhor esforço (*best-effort delivery*). Ele encapsula o dado e o entrega à camada IP; se o datagrama for descartado por um roteador congestionado, se corromper por ruído físico ou se o receptor estiver desligado, a camada de transporte UDP não é notificada, não envia avisos de erro e não realiza retransmissão.

#### 13. O que a aplicação teria que implementar caso precisasse de confiabilidade usando UDP?
**Resposta:** Caso uma aplicação utilize UDP e necessite de confiabilidade, ela própria (na camada de aplicação) deverá implementar todas as funcionalidades típicas de controle de transporte:
- Números de sequência para cada mensagem ou bloco de dados;
- Mensagens de confirmação de recebimento (ACKs de aplicação);
- Temporizadores (*timers*) e rotinas de retransmissão automática de mensagens não confirmadas;
- Mecanismos de reordenação e descarte de duplicatas em buffers na aplicação;
*(Um exemplo prático e moderno desse modelo é o protocolo QUIC / HTTP/3, que roda sobre UDP mas implementa confiabilidade e controle na camada de aplicação).*

#### 14. Por que o UDP pode ser vantajoso em aplicações sensíveis a atraso?
**Resposta:** Porque o UDP oferece **latência mínima (atraso mínimo de entrega)** e previsibilidade temporal:
- **Zero RTT de inicialização:** O envio de dados começa no primeiro instante, sem a necessidade de esperar pelo handshake do TCP;
- **Ausência de bloqueio de cabeça de fila (*Head-of-Line Blocking*):** Se um pacote for perdido, os pacotes subsequentes são entregues imediatamente à aplicação, sem que ela fique travada esperando retransmissões;
- **Sem congelamentos de retransmissão:** Em aplicações como chamadas de voz (VoIP), videoconferências e jogos competitivos em tempo real, um pacote com áudio ou coordenadas de posição atrasado 500ms é inútil; é preferível tolerar uma perda quase imperceptível de um milissegundo de som do que travar a chamada inteira para retransmitir o frame antigo.

---

### 7.4 Questões Comparativas

#### 15. Qual filtro foi utilizado no Wireshark para visualizar apenas o tráfego TCP da atividade?
**Resposta:** Foi utilizado o filtro de exibição:
```text
tcp.port == 5000
```
*(Filtra exclusivamente os pacotes cujo protocolo seja TCP e cuja porta de origem ou porta de destino seja igual a 5000).*

#### 16. Qual filtro foi utilizado no Wireshark para visualizar apenas o tráfego UDP da atividade?
**Resposta:** Foi utilizado o filtro de exibição:
```text
udp.port == 5001
```
*(Filtra exclusivamente os datagramas cujo protocolo seja UDP e cuja porta de origem ou porta de destino seja igual a 5001).*

#### 17. Ao analisar a captura TCP, quais campos ou informações permitem identificar as portas de origem e destino?
**Resposta:**
- No **painel da lista de pacotes (*Packet List*)**: As colunas *Source Port* e *Destination Port* (ou a coluna de resumo *Info*, que exibe a relação `porta_origem -> porta_destino`, como `54321 -> 5000`).
- No **painel de detalhes do pacote (*Packet Details*)**: Ao expandir o cabeçalho **Transmission Control Protocol (TCP)**, encontram-se explicitamente os campos:
  - `Source Port: <número_da_porta_de_origem>`
  - `Destination Port: <número_da_porta_de_destino>`

#### 18. Ao analisar a captura UDP, o que comprova que não houve handshake antes do envio da mensagem?
**Resposta:** O fato de que a captura com o filtro `udp.port == 5001` começa **diretamente com o primeiro pacote contendo os dados da aplicação** (`"Olá, servidor UDP!"`), com tamanho de payload preenchido e sem nenhum pacote preliminar de sincronização. Não há pacotes com flags de controle de sincronização (`SYN` ou similar) e o número total de pacotes de toda a sessão de envio e resposta resume-se estritamente a 2 datagramas de dados.

#### 19. Compare o comportamento do servidor TCP e do servidor UDP quanto ao modo de recebimento das mensagens.
**Resposta:**
- **Servidor TCP:** Opera orientado à conexão e a fluxo de bytes contínuo (*stream*). O servidor precisa primeiro aceitar a conexão através de `accept()`, que cria um **segundo socket exclusivo** para aquele cliente específico. As mensagens são lidas desse socket dedicado por meio de `recv(1024)`, sem necessidade de especificar o remetente a cada leitura, pois o canal já está atrelado àquele cliente.
- **Servidor UDP:** Opera orientado a datagramas discretos (*datagram*). O servidor utiliza o mesmo e único socket associado à porta 5001 e invoca o método `recvfrom(1024)`. Esse método retorna não apenas os dados da mensagem, mas também a tupla com o endereço de origem `(IP, porta)` de quem enviou aquele pacote específico, permitindo ao servidor responder datagramas de múltiplos clientes distintos usando o mesmo socket.

#### 20. Com base nos testes realizados, explique qual protocolo seria mais adequado para uma aplicação de transferência de arquivos e qual seria mais adequado para uma chamada de vídeo ao vivo.
**Resposta:**
- **Transferência de arquivos:** O protocolo mais adequado é o **TCP**. Em um arquivo (como um executável, documento PDF ou imagem ISO), a perda ou corrupção de um único byte pode invalidar o arquivo por completo ou corromper a instalação. O TCP garante 100% de confiabilidade, integridade, remontagem estritamente ordenada e retransmissão de qualquer fragmento perdido, sendo o atraso adicional perfeitamente aceitável em troca da garantia de integridade.
- **Chamada de vídeo ao vivo (Streaming em tempo real / VoIP):** O protocolo mais adequado é o **UDP**. Em comunicações síncronas de áudio e vídeo em tempo real, a latência mínima e a fluidez temporal são prioritárias. Se alguns pacotes de vídeo forem descartados pela rede, o decodificador simplesmente interpola o quadro ou causa uma leve e imperceptível perda de nitidez momentânea. Se fosse utilizado o TCP, a perda de um único pacote faria a transmissão congelar completamente aguardando a retransmissão, tornando a experiência de conversação ao vivo inviável.
