# servidor.py
import socket
import threading
import json
import time

# (Nenhuma mudança nas configurações e variáveis globais)
HOST = '127.0.0.1'
PORTA = 2004
LARGURA_TELA, ALTURA_TELA = 800, 600
VELOCIDADE_BOLA = 5
VELOCIDADE_PADDLE = 1
clientes = []
game_state = {}
jogo_rodando = threading.Event()
game_state_lock = threading.Lock()

def transmitir_para_jogadores(dados):
    mensagem = json.dumps(dados) + '\n' # Adiciona o delimitador
    for cliente_socket, _, _ in clientes[:2]:
        try:
            cliente_socket.send(mensagem.encode('utf-8'))
        except:
            pass

def resetar_jogo():
    global game_state
    with game_state_lock:
        game_state = {
            'bola': {'x': LARGURA_TELA // 2, 'y': ALTURA_TELA // 2, 'vx': VELOCIDADE_BOLA, 'vy': VELOCIDADE_BOLA},
            'paddle1': {'x': 10, 'y': ALTURA_TELA // 2 - 50},
            'paddle2': {'x': LARGURA_TELA - 20, 'y': ALTURA_TELA // 2 - 50},
            'placar': {'p1': 0, 'p2': 0}
        }
    jogo_rodando.set()

# (Nenhuma mudança no loop_do_jogo)
def loop_do_jogo():
    while True:
        jogo_rodando.wait()
        with game_state_lock:
            if not game_state: continue
            game_state['bola']['x'] += game_state['bola']['vx']
            game_state['bola']['y'] += game_state['bola']['vy']
            bola, p1, p2 = game_state['bola'], game_state['paddle1'], game_state['paddle2']
            if bola['y'] <= 0 or bola['y'] >= ALTURA_TELA - 10: bola['vy'] *= -1
            if (p1['x'] < bola['x'] < p1['x'] + 10 and p1['y'] < bola['y'] < p1['y'] + 100) or \
               (p2['x'] < bola['x'] < p2['x'] + 10 and p2['y'] < bola['y'] < p2['y'] + 100):
                bola['vx'] *= -1
            if bola['x'] <= 0:
                game_state['placar']['p2'] += 1
                bola['x'], bola['y'] = LARGURA_TELA // 2, ALTURA_TELA // 2
            elif bola['x'] >= LARGURA_TELA:
                game_state['placar']['p1'] += 1
                bola['x'], bola['y'] = LARGURA_TELA // 2, ALTURA_TELA // 2
            dados = {"tipo": "GAME_STATE", "payload": game_state}
            transmitir_para_jogadores(dados)
        time.sleep(1/60)

def gerenciar_cliente(conexao, endereco, player_id):
    apelido = f"Jogador{player_id}"
    print(f"[NOVA CONEXÃO] {endereco} como {apelido}.")
    clientes.append((conexao, endereco, apelido))
    
    dados_id = {"tipo": "PLAYER_ID", "payload": f"P{player_id}"}
    mensagem_id = json.dumps(dados_id) + '\n'
    conexao.send(mensagem_id.encode('utf-8'))

    if len(clientes) == 2:
        print("[INÍCIO DE JOGO] Dois jogadores conectados. Iniciando a partida.")
        resetar_jogo()

    # CORREÇÃO: Usa um buffer para receber dados do cliente
    buffer = ""
    while True:
        try:
            # Recebe dados e adiciona ao buffer
            dados_recebidos = conexao.recv(1024).decode('utf-8')
            if not dados_recebidos:
                break
            
            buffer += dados_recebidos
            
            # Processa todas as mensagens completas (delimitadas por '\n') no buffer
            while '\n' in buffer:
                mensagem_completa, buffer = buffer.split('\n', 1)
                dados = json.loads(mensagem_completa)

                if dados['tipo'] == 'MOVE':
                    with game_state_lock:
                        if not game_state:
                            continue
                        
                        paddle_key = f"paddle{player_id}"
                        paddle = game_state[paddle_key]

                        if dados['payload'] == 'UP':
                            paddle['y'] = max(0, paddle['y'] - VELOCIDADE_PADDLE)
                        elif dados['payload'] == 'DOWN':
                            paddle['y'] = min(ALTURA_TELA - 100, paddle['y'] + VELOCIDADE_PADDLE)
        except:
            break
    
    # O resto da função de desconexão permanece o mesmo
    print(f"[DESCONEXÃO] {apelido} se desconectou.")
    for i, (c, _, a) in enumerate(clientes):
        if c == conexao:
            del clientes[i]
            break
    conexao.close()
    
    if len(clientes) < 2:
        jogo_rodando.clear()
        print("[JOGO PAUSADO] Aguardando jogadores...")

# (Nenhuma mudança em iniciar_servidor)
def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((HOST, PORTA))
    servidor.listen()
    print(f"[ESCUTANDO] Servidor está escutando em {HOST}:{PORTA}")
    threading.Thread(target=loop_do_jogo, daemon=True).start()
    player_count = 0
    while True:
        conexao, endereco = servidor.accept()
        player_count += 1
        thread = threading.Thread(target=gerenciar_cliente, args=(conexao, endereco, player_count))
        thread.start()

print("[INICIANDO] O servidor do jogo está iniciando...")
iniciar_servidor()