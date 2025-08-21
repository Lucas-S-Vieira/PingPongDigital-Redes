# cliente.py
import socket
import threading
import json
import pygame

SERVER_HOST = '127.0.0.1' 
SERVER_PORTA = 2004
LARGURA_TELA, ALTURA_TELA = 800, 600
COR_BRANCA, COR_PRETA = (255, 255, 255), (0, 0, 0)

cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((SERVER_HOST, SERVER_PORTA))

game_state = {}
meu_player_id = None

# Função para receber mensagens do servidor
def receber_mensagens():
    global game_state, meu_player_id
    buffer = ""
    while True:
        try:
            dados_recebidos = cliente.recv(2048).decode('utf-8')
            if not dados_recebidos:
                break
            buffer += dados_recebidos
            while '\n' in buffer:
                mensagem_completa, buffer = buffer.split('\n', 1)
                dados = json.loads(mensagem_completa)
                if dados['tipo'] == 'GAME_STATE':
                    game_state = dados['payload']
                elif dados['tipo'] == 'PLAYER_ID':
                    meu_player_id = dados['payload']
                    print(f"Você é o {meu_player_id}")
        except:
            break
    print("Desconectado do servidor.")
    cliente.close()

# Inicialização do pygame
pygame.init()
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption(f"Ping Pong - Cliente")
fonte = pygame.font.Font(None, 74)

# Thread para receber mensagens
thread_recebimento = threading.Thread(target=receber_mensagens, daemon=True)
thread_recebimento.start()

rodando = True
while rodando:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            rodando = False

    keys = pygame.key.get_pressed()
    if meu_player_id == 'P1':
        if keys[pygame.K_w]: 
            cliente.send((json.dumps({'tipo': 'MOVE', 'payload': 'UP'}) + '\n').encode('utf-8'))
        if keys[pygame.K_s]: 
            cliente.send((json.dumps({'tipo': 'MOVE', 'payload': 'DOWN'}) + '\n').encode('utf-8'))
    elif meu_player_id == 'P2':
        if keys[pygame.K_UP]: 
            cliente.send((json.dumps({'tipo': 'MOVE', 'payload': 'UP'}) + '\n').encode('utf-8'))
        if keys[pygame.K_DOWN]: 
            cliente.send((json.dumps({'tipo': 'MOVE', 'payload': 'DOWN'}) + '\n').encode('utf-8'))

    # menu para iniciar game
    tela.fill(COR_PRETA)
    if not game_state:
        texto_espera = fonte.render("Aguardando outro jogador...", True, COR_BRANCA)
        tela.blit(texto_espera, (
            LARGURA_TELA // 2 - texto_espera.get_width() // 2, 
            ALTURA_TELA // 2 - texto_espera.get_height() // 2
        ))
    else:
        # Desenha o jogo normalmente
        p1, p2 = game_state['paddle1'], game_state['paddle2']
        pygame.draw.rect(tela, COR_BRANCA, (p1['x'], p1['y'], 10, 100))
        pygame.draw.rect(tela, COR_BRANCA, (p2['x'], p2['y'], 10, 100))
        bola = game_state['bola']
        pygame.draw.ellipse(tela, COR_BRANCA, (bola['x'], bola['y'], 10, 10))
        placar = game_state['placar']
        texto_placar = fonte.render(f"{placar['p1']}    {placar['p2']}", True, COR_BRANCA)
        tela.blit(texto_placar, (LARGURA_TELA // 2 - texto_placar.get_width() // 2, 20))
    # ------------------------------------------------

    pygame.display.flip()

pygame.quit()
cliente.close()