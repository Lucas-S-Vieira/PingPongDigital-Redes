# Pong Multiplayer com Sockets em Python

![Imagem de uma partida de Pong](https://i.imgur.com/Eddt61a.png)

## 📖 Sobre o Projeto

Este projeto é uma implementação de um jogo clássico de Pong com funcionalidades multiplayer, desenvolvido como parte do trabalho prático da disciplina de Redes de Computadores 1. O jogo utiliza uma arquitetura cliente-servidor com sockets TCP para a comunicação principal e sockets UDP para a descoberta automática de servidores na rede local.

O projeto foi desenvolvido em Python, utilizando a biblioteca Pygame para a interface gráfica e a renderização do jogo.

---

## ✨ Funcionalidades

- **Multiplayer em Rede Local (LAN):** Jogue com um amigo que esteja conectado na mesma rede.
- **Descoberta Automática de Servidor:** Não é necessário configurar IPs! O cliente encontra o servidor na rede local automaticamente.
- **Lobby e Sistema de Convites:** Os jogadores entram num lobby, podem ver quem está online e enviar convites para jogar.
- **Interface Gráfrica Completa:** Todas as interações, desde inserir o apelido até jogar, acontecem dentro de uma janela gráfica criada com Pygame.
- **Contagem Regressiva Dinâmica:** Antes de cada partida, uma contagem regressiva de 3 segundos é exibida na tela.
- **Lógica de Jogo no Servidor:** O servidor atua como autoridade central, garantindo uma experiência de jogo consistente e prevenindo trapaças.
- **Timeout por Inatividade:** Se um jogador ficar inativo por 30 segundos, ele perde a partida automaticamente.
- **Pontuação para Vitória Configurável:** A pontuação necessária para vencer pode ser facilmente ajustada no código do servidor.

---

## 🚀 Como Executar

### Pré-requisitos

Antes de começar, certifique-se de que tem o Python e a biblioteca Pygame instalados no seu sistema.

- **Python 3:** [python.org](https://www.python.org/downloads/)
- **Pygame:** Pode ser instalado via pip:
  ```bash
  pip install pygame
  ```

### Instruções de Execução

O jogo requer que uma instância do servidor e duas instâncias do cliente estejam a ser executadas.

**1. Iniciar o Servidor:**

No computador que irá hospedar a partida, execute o ficheiro `servidor.py`:

```bash
python servidor.py
```

O terminal deverá exibir uma mensagem a confirmar que o servidor está a escutar por conexões. Se a sua firewall solicitar permissão, permita o acesso à rede.

**2. Iniciar os Clientes:**

Em dois computadores na mesma rede (pode ser o mesmo computador do servidor para testes), execute o ficheiro `cliente.py`:

```bash
python cliente.py
```

- Uma janela do Pygame será aberta, exibindo "Procurando servidor na rede...".
- Assim que o servidor for encontrado, a tela mudará para pedir que você digite um apelido.
- Após inserir o apelido e pressionar `ENTER`, você entrará no menu principal.

---

## 🎮 Como Jogar

1.  **Menu Principal:** Clique em "Jogar" para ver a lista de jogadores disponíveis.
2.  **Lobby:** Na lista de jogadores, clique no apelido de um jogador para lhe enviar um convite. Você pode clicar em "Atualizar Lista" para recarregar a lista de jogadores.
3.  **Convite:** O jogador convidado receberá uma notificação no ecrã com as opções "Aceitar" ou "Recusar".
4.  **Controles no Jogo:**
    - **Mover para Cima:** Tecla `W` ou `Seta para Cima` (↑)
    - **Mover para Baixo:** Tecla `S` ou `Seta para Baixo` (↓)
5.  **Fim de Jogo:** O primeiro jogador a atingir 5 pontos vence. Após o fim da partida, pressione `ENTER` para voltar ao menu principal.

---

## 🛠️ Estrutura do Projeto

- **`servidor.py`**: O coração do jogo. Responsável por:
    - Anunciar a sua presença na rede (UDP Broadcast).
    - Gerir conexões de clientes (TCP).
    - Manter o estado dos jogadores (no lobby, em jogo).
    - Encaminhar convites.
    - Executar a lógica de cada partida (movimento da bola, colisões, pontuação, timeouts).

- **`cliente.py`**: A interface para o jogador. Responsável por:
    - Procurar e encontrar o servidor na rede (UDP).
    - Conectar-se ao servidor (TCP).
    - Renderizar a interface gráfica para todos os estados do jogo (menu, lobby, jogo, etc.).
    - Capturar os inputs do jogador (teclado e rato) e enviá-los para o servidor.
    - Exibir o estado do jogo recebido do servidor.

---

## 💻 Tecnologias Utilizadas

- **Linguagem:** Python 3
- **Interface Gráfica:** Pygame
- **Comunicação em Rede:** Sockets (TCP e UDP)
- **Formato de Dados:** JSON
- **Concorrência:** Módulos `threading`

---

## 👥 Autores

- [Insira seu Nome Aqui]
- [Insira o Nome do Colega Aqui, se aplicável]
