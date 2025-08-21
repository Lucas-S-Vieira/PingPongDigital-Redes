import socket
import threading
import json
import time

# --- ALTERAÇÃO 1: Escutar em todas as interfaces de rede ---
HOST = '0.0.0.0' 
PORTA_JOGO = 2004
PORTA_DESCOBERTA = 2005 # Porta para os anúncios UDP
MENSAGEM_DESCOBERTA = "PONG_SERVER_DISCOVERY"

LARGURA_TELA, ALTURA_TELA = 800, 600
VELOCIDADE_BOLA_PPS = 300
VELOCIDADE_PADDLE_PPS = 400
TIMEOUT_SEGUNDOS = 30 

# --- NOVO: Variável global para a pontuação de vitória ---
PONTOS_PARA_VENCER = 5

clientes = []
sessoes_de_jogo = {}
estados_de_jogo = {} 
lock = threading.Lock()

# --- NOVO: Função para anunciar o servidor na rede ---
def anunciar_servidor():
    """
    Envia pacotes de broadcast UDP a cada 2 segundos para que os clientes
    possam encontrar o servidor automaticamente.
    """
    sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # O endereço '<broadcast>' envia para todos os dispositivos na rede local
    endereco_broadcast = ('<broadcast>', PORTA_DESCOBERTA)
    
    mensagem = json.dumps({
        "assinatura": MENSAGEM_DESCOBERTA,
        "porta_jogo": PORTA_JOGO
    }).encode('utf-8')

    while True:
        try:
            sock_udp.sendto(mensagem, endereco_broadcast)
            time.sleep(2)
        except Exception as e:
            print(f"[ERRO NO ANÚNCIO UDP] {e}")
            time.sleep(5)

# --- (O resto do código do servidor permanece praticamente o mesmo) ---

def transmitir_para_todos(dados):
    mensagem = json.dumps(dados) + '\n'
    with lock:
        for conn, _, _, _ in clientes:
            try:
                conn.send(mensagem.encode('utf-8'))
            except:
                pass

def encontrar_cliente_por_apelido(apelido):
    with lock:
        for conn, _, ap, _ in clientes:
            if ap == apelido:
                return conn
    return None

def iniciar_sessao_de_jogo(apelido1, apelido2):
    conn1 = encontrar_cliente_por_apelido(apelido1)
    conn2 = encontrar_cliente_por_apelido(apelido2)
    if not conn1 or not conn2: return

    print(f"[NOVO JOGO] Iniciando jogo entre {apelido1} e {apelido2}")
    with lock:
        for i, (c, e, a, _) in enumerate(clientes):
            if a == apelido1 or a == apelido2:
                clientes[i] = (c, e, a, 'em_jogo')
        sessoes_de_jogo[conn1] = conn2
        sessoes_de_jogo[conn2] = conn1

    tempo_inicial = time.time()
    game_state = {
        'bola': {'x': LARGURA_TELA / 2, 'y': ALTURA_TELA / 2, 'vx': 1, 'vy': 1},
        'paddle1': {'x': 10, 'y': ALTURA_TELA / 2 - 50, 'vy': 0},
        'paddle2': {'x': LARGURA_TELA - 20, 'y': ALTURA_TELA / 2 - 50, 'vy': 0},
        'placar': {'p1': 0, 'p2': 0},
        'jogadores': { 'P1': apelido1, 'P2': apelido2 },
        'ultima_atividade': { 'P1': tempo_inicial, 'P2': tempo_inicial }
    }
    
    with lock:
        estados_de_jogo[conn1] = game_state
        estados_de_jogo[conn2] = game_state
    
    msg_countdown = {'tipo': 'CONTAGEM_INICIO', 'payload': 3}
    conn1.send((json.dumps(msg_countdown) + '\n').encode('utf-8'))
    conn2.send((json.dumps(msg_countdown) + '\n').encode('utf-8'))
    time.sleep(3)
    
    thread_jogo = threading.Thread(target=loop_do_jogo, args=(conn1, conn2, game_state))
    thread_jogo.daemon = True
    thread_jogo.start()
    
    msg_inicio = {'tipo': 'JOGO_INICIADO', 'payload': {'id': 'P1', 'oponente': apelido2}}
    conn1.send((json.dumps(msg_inicio) + '\n').encode('utf-8'))
    msg_inicio = {'tipo': 'JOGO_INICIADO', 'payload': {'id': 'P2', 'oponente': apelido1}}
    conn2.send((json.dumps(msg_inicio) + '\n').encode('utf-8'))
    atualizar_lista_jogadores_para_todos()

def loop_do_jogo(conn1, conn2, game_state):
    jogo_ativo, ultimo_tempo = True, time.time()
    while jogo_ativo:
        tempo_atual = time.time()
        delta_time = tempo_atual - ultimo_tempo
        ultimo_tempo = tempo_atual
        with lock:
            game_state['bola']['x'] += game_state['bola']['vx'] * VELOCIDADE_BOLA_PPS * delta_time
            game_state['bola']['y'] += game_state['bola']['vy'] * VELOCIDADE_BOLA_PPS * delta_time
            p1, p2 = game_state['paddle1'], game_state['paddle2']
            p1['y'] += p1['vy'] * delta_time
            p2['y'] += p2['vy'] * delta_time
            p1['y'] = max(0, min(p1['y'], ALTURA_TELA - 100))
            p2['y'] = max(0, min(p2['y'], ALTURA_TELA - 100))
            bola = game_state['bola']
            if bola['y'] <= 0 or bola['y'] >= ALTURA_TELA - 10: game_state['bola']['vy'] *= -1
            if (p1['x'] < bola['x'] < p1['x'] + 10 and p1['y'] < bola['y'] < p1['y'] + 100) or \
               (p2['x'] < bola['x'] < p2['x'] + 10 and p2['y'] < bola['y'] < p2['y'] + 100):
                game_state['bola']['vx'] *= -1
            if bola['x'] <= 0:
                game_state['placar']['p2'] += 1
                bola['x'], bola['y'] = LARGURA_TELA / 2, ALTURA_TELA / 2
            elif bola['x'] >= LARGURA_TELA:
                game_state['placar']['p1'] += 1
                bola['x'], bola['y'] = LARGURA_TELA / 2, ALTURA_TELA / 2
            
            vencedor = None
            # --- ALTERAÇÃO 2: Usa a nova variável para verificar a vitória ---
            if game_state['placar']['p1'] >= PONTOS_PARA_VENCER: vencedor = game_state['jogadores']['P1']
            elif game_state['placar']['p2'] >= PONTOS_PARA_VENCER: vencedor = game_state['jogadores']['P2']
            
            if not vencedor:
                if tempo_atual - game_state['ultima_atividade']['P1'] > TIMEOUT_SEGUNDOS:
                    vencedor = game_state['jogadores']['P2']
                    print(f"[TIMEOUT] {game_state['jogadores']['P1']} ficou inativo.")
                elif tempo_atual - game_state['ultima_atividade']['P2'] > TIMEOUT_SEGUNDOS:
                    vencedor = game_state['jogadores']['P1']
                    print(f"[TIMEOUT] {game_state['jogadores']['P2']} ficou inativo.")
        dados_para_enviar = {"tipo": "GAME_STATE", "payload": game_state}
        mensagem = json.dumps(dados_para_enviar) + '\n'
        try:
            conn1.send(mensagem.encode('utf-8'))
            conn2.send(mensagem.encode('utf-8'))
        except: vencedor = "Oponente"
        if vencedor:
            dados_fim = {'tipo': 'FIM_DE_JOGO', 'payload': vencedor}
            try:
                conn1.send((json.dumps(dados_fim) + '\n').encode('utf-8'))
                conn2.send((json.dumps(dados_fim) + '\n').encode('utf-8'))
            except: pass
            jogo_ativo = False
        time.sleep(1/200)
    print(f"[FIM DE JOGO] Jogo entre {game_state['jogadores']['P1']} e {game_state['jogadores']['P2']} terminou.")
    with lock:
        if conn1 in estados_de_jogo: del estados_de_jogo[conn1]
        if conn2 in estados_de_jogo: del estados_de_jogo[conn2]
        jogadores_da_partida = [game_state['jogadores']['P1'], game_state['jogadores']['P2']]
        for i, (c, e, a, st) in enumerate(clientes):
            if a in jogadores_da_partida:
                clientes[i] = (c, e, a, 'lobby')
    atualizar_lista_jogadores_para_todos()

def atualizar_lista_jogadores_para_todos():
    with lock:
        lista_jogadores = [{'apelido': ap, 'estado': st} for _, _, ap, st in clientes]
    transmitir_para_todos({'tipo': 'LISTA_JOGADORES', 'payload': lista_jogadores})

def gerenciar_cliente(conexao, endereco):
    apelido_cliente = None
    try:
        dados_registro_raw = conexao.recv(1024).decode('utf-8').strip()
        dados_registro = json.loads(dados_registro_raw)
        if dados_registro['tipo'] == 'REGISTER':
            apelido_cliente = dados_registro['payload']
            with lock:
                clientes.append((conexao, endereco, apelido_cliente, 'lobby'))
            print(f"[NOVA CONEXÃO] {apelido_cliente}@{endereco} se conectou.")
            atualizar_lista_jogadores_para_todos()
        else: return
    except:
        conexao.close()
        return
    buffer = ""
    while True:
        try:
            dados_recebidos = conexao.recv(1024).decode('utf-8')
            if not dados_recebidos: break
            buffer += dados_recebidos
            while '\n' in buffer:
                mensagem_completa, buffer = buffer.split('\n', 1)
                dados = json.loads(mensagem_completa)
                if dados['tipo'] == 'CONVIDAR_JOGADOR' or dados['tipo'] == 'RESPONDER_CONVITE':
                    if dados['tipo'] == 'CONVIDAR_JOGADOR':
                        apelido_alvo = dados['payload']
                        conn_alvo = encontrar_cliente_por_apelido(apelido_alvo)
                        if conn_alvo:
                            convite = {'tipo': 'CONVITE_RECEBIDO', 'payload': apelido_cliente}
                            conn_alvo.send((json.dumps(convite) + '\n').encode('utf-8'))
                    elif dados['tipo'] == 'RESPONDER_CONVITE':
                        remetente = dados['payload']['remetente']
                        aceito = dados['payload']['aceito']
                        conn_remetente = encontrar_cliente_por_apelido(remetente)
                        if conn_remetente:
                            resposta = {'tipo': 'RESPOSTA_CONVITE', 'payload': {'remetente': apelido_cliente, 'aceito': aceito}}
                            conn_remetente.send((json.dumps(resposta) + '\n').encode('utf-8'))
                            if aceito:
                                iniciar_sessao_de_jogo(remetente, apelido_cliente)
                elif dados['tipo'] == 'START_MOVE' or dados['tipo'] == 'STOP_MOVE':
                    with lock:
                        if conexao in estados_de_jogo:
                            current_game_state = estados_de_jogo[conexao]
                            player_id_str = dados['payload']['id']
                            current_game_state['ultima_atividade'][player_id_str] = time.time()
                            direction = dados['payload']['direction']
                            paddle_key = 'paddle1' if player_id_str == 'P1' else 'paddle2'
                            paddle = current_game_state[paddle_key]
                            if dados['tipo'] == 'STOP_MOVE':
                                paddle['vy'] = 0
                            elif direction == 'UP':
                                paddle['vy'] = -VELOCIDADE_PADDLE_PPS
                            elif direction == 'DOWN':
                                paddle['vy'] = VELOCIDADE_PADDLE_PPS
        except (ConnectionResetError, json.JSONDecodeError): break
        except Exception as e:
            print(f"Erro inesperado: {e}")
            break
    print(f"[DESCONEXÃO] {apelido_cliente} se desconectou.")
    with lock:
        clientes[:] = [c for c in clientes if c[0] != conexao]
        if conexao in sessoes_de_jogo:
            oponente = sessoes_de_jogo.pop(conexao)
            if oponente in sessoes_de_jogo: del sessoes_de_jogo[oponente]
    atualizar_lista_jogadores_para_todos()
    conexao.close()

def iniciar_servidor_tcp():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((HOST, PORTA_JOGO))
    servidor.listen()
    print(f"[ESCUTANDO TCP] Servidor de jogo na porta {PORTA_JOGO}")
    while True:
        conexao, endereco = servidor.accept()
        thread = threading.Thread(target=gerenciar_cliente, args=(conexao, endereco))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    print("[INICIANDO] O servidor do jogo está iniciando...")
    
    # --- ALTERAÇÃO 2: Inicia a thread de anúncio UDP ---
    thread_anuncio = threading.Thread(target=anunciar_servidor, daemon=True)
    thread_anuncio.start()
    
    # Inicia o servidor principal do jogo
    iniciar_servidor_tcp()