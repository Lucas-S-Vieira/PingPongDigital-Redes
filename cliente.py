# cliente.py (VERSÃO FINAL COM BOTÃO DE ATUALIZAR)
import socket
import threading
import json
import pygame

PORTA_DESCOBERTA = 2005
MENSAGEM_DESCOBERTA = "PONG_SERVER_DISCOVERY"
servidor_encontrado = None
LARGURA_TELA, ALTURA_TELA = 800, 600
COR_BRANCA, COR_PRETA, COR_CINZA, COR_VERDE, COR_VERMELHO, COR_AZUL = (255, 255, 255), (0, 0, 0), (100, 100, 100), (0, 255, 0), (255, 0, 0), (0, 100, 255)

estado_ecra = 'PROCURANDO_SERVIDOR' 
lista_jogadores = []
meu_apelido = ""
meu_player_id = None
oponente_apelido = ""
game_state = {}
convite_de = None
mensagem_fim_de_jogo = ""

# --- ALTERAÇÃO 1: Variáveis para a contagem regressiva dinâmica ---
contagem_tempo_inicio = 0
contagem_duracao = 0

pygame.init()
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Ping Pong")
fonte_grande = pygame.font.Font(None, 74)
fonte_media = pygame.font.Font(None, 50)
fonte_pequena = pygame.font.Font(None, 36)

def desenhar_texto(texto, fonte, cor, x, y, centro=True):
    obj_texto = fonte.render(texto, True, cor)
    rect_texto = obj_texto.get_rect()
    if centro: rect_texto.center = (x, y)
    else: rect_texto.topleft = (x, y)
    tela.blit(obj_texto, rect_texto)
    return rect_texto

def desenhar_tela_apelido(apelido_atual):
    tela.fill(COR_PRETA)
    desenhar_texto("Digite seu Apelido", fonte_media, COR_BRANCA, LARGURA_TELA // 2, 150)
    caixa_rect = pygame.Rect(LARGURA_TELA // 2 - 200, ALTURA_TELA // 2 - 25, 400, 50)
    pygame.draw.rect(tela, COR_BRANCA, caixa_rect, 2)
    desenhar_texto(apelido_atual, fonte_media, COR_BRANCA, LARGURA_TELA // 2, ALTURA_TELA // 2)
    desenhar_texto("Pressione ENTER para continuar", fonte_pequena, COR_CINZA, LARGURA_TELA // 2, ALTURA_TELA // 2 + 100)

def desenhar_menu():
    tela.fill(COR_PRETA)
    desenhar_texto("PONG Multiplayer", fonte_grande, COR_BRANCA, LARGURA_TELA // 2, 150)
    return desenhar_texto("Jogar", fonte_media, COR_BRANCA, LARGURA_TELA // 2, 350)

def desenhar_lista_jogadores():
    tela.fill(COR_PRETA)
    desenhar_texto("Escolha um Oponente", fonte_media, COR_BRANCA, LARGURA_TELA // 2, 50)
    botoes_jogadores = {}
    y_pos = 150
    jogadores_disponiveis = [j for j in lista_jogadores if j['apelido'] != meu_apelido and j['estado'] == 'lobby']
    if not jogadores_disponiveis:
        desenhar_texto("Nenhum jogador disponível no momento.", fonte_pequena, COR_CINZA, LARGURA_TELA // 2, 250)
    else:
        for jogador in jogadores_disponiveis:
            rect = desenhar_texto(jogador['apelido'], fonte_pequena, COR_BRANCA, LARGURA_TELA // 2, y_pos)
            botoes_jogadores[jogador['apelido']] = rect
            y_pos += 50
    
    btn_atualizar = desenhar_texto("Atualizar Lista", fonte_pequena, COR_AZUL, LARGURA_TELA // 2, ALTURA_TELA - 50)
    
    return botoes_jogadores, btn_atualizar

def desenhar_tela_espera(mensagem):
    tela.fill(COR_PRETA)
    desenhar_texto(mensagem, fonte_media, COR_BRANCA, LARGURA_TELA // 2, ALTURA_TELA // 2)

def desenhar_convite():
    tela.fill(COR_PRETA)
    desenhar_texto(f"Convite de {convite_de}", fonte_media, COR_BRANCA, LARGURA_TELA // 2, 200)
    btn_aceitar = desenhar_texto("Aceitar", fonte_media, COR_VERDE, LARGURA_TELA // 2 - 100, 400)
    btn_recusar = desenhar_texto("Recusar", fonte_media, COR_VERMELHO, LARGURA_TELA // 2 + 100, 400)
    return btn_aceitar, btn_recusar

def desenhar_jogo():
    tela.fill(COR_PRETA)
    if not game_state: return
    p1, p2 = game_state['paddle1'], game_state['paddle2']
    pygame.draw.rect(tela, COR_BRANCA, (p1['x'], p1['y'], 10, 100))
    pygame.draw.rect(tela, COR_BRANCA, (p2['x'], p2['y'], 10, 100))
    bola = game_state['bola']
    pygame.draw.ellipse(tela, COR_BRANCA, (bola['x'], bola['y'], 10, 10))
    placar = game_state['placar']
    nome_p1 = game_state['jogadores']['P1']
    nome_p2 = game_state['jogadores']['P2']
    texto_placar = f"{nome_p1}   {placar['p1']} X {placar['p2']}   {nome_p2}"
    desenhar_texto(texto_placar, fonte_media, COR_BRANCA, LARGURA_TELA // 2, 40)

cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
conectado_ao_servidor = False

def procurar_servidor_udp():
    global servidor_encontrado, estado_ecra
    sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock_udp.bind(('', PORTA_DESCOBERTA))
    except Exception as e:
        print(f"Erro ao bindar porta de descoberta: {e}")
        return
    print(f"[DESCOBERTA] Escutando por servidores na porta {PORTA_DESCOBERTA}")
    while not servidor_encontrado:
        try:
            dados, addr = sock_udp.recvfrom(1024)
            mensagem = json.loads(dados.decode('utf-8'))
            if mensagem.get("assinatura") == MENSAGEM_DESCOBERTA:
                ip_servidor = addr[0]
                porta_jogo = mensagem.get("porta_jogo")
                servidor_encontrado = (ip_servidor, porta_jogo)
                print(f"[DESCOBERTA] Servidor encontrado em {ip_servidor}:{porta_jogo}")
                estado_ecra = 'DIGITANDO_NOME'
                break
        except:
            pass
    sock_udp.close()

def enviar_mensagem(dados):
    if not conectado_ao_servidor: return
    try:
        cliente.send((json.dumps(dados) + '\n').encode('utf-8'))
    except (ConnectionResetError, BrokenPipeError):
        print("Erro de conexão ao enviar.")

def receber_mensagens():
    global estado_ecra, lista_jogadores, convite_de, game_state, meu_player_id, oponente_apelido, mensagem_fim_de_jogo, contagem_tempo_inicio, contagem_duracao, conectado_ao_servidor
    buffer = ""
    while conectado_ao_servidor:
        try:
            dados_recebidos = cliente.recv(2048).decode('utf-8')
            if not dados_recebidos: break
            buffer += dados_recebidos
            while '\n' in buffer:
                mensagem_completa, buffer = buffer.split('\n', 1)
                dados = json.loads(mensagem_completa)
                if dados['tipo'] == 'LISTA_JOGADORES': lista_jogadores = dados['payload']
                elif dados['tipo'] == 'CONVITE_RECEBIDO':
                    convite_de = dados['payload']
                    estado_ecra = 'CONVITE_RECEBIDO'
                elif dados['tipo'] == 'RESPOSTA_CONVITE':
                    if not dados['payload']['aceito']:
                        print(f"{dados['payload']['remetente']} recusou o seu convite.")
                        estado_ecra = 'ESCOLHENDO_JOGADOR'
                # --- ALTERAÇÃO 2: Inicia o temporizador da contagem ---
                elif dados['tipo'] == 'CONTAGEM_INICIO':
                    contagem_duracao = dados['payload']
                    contagem_tempo_inicio = pygame.time.get_ticks()
                    estado_ecra = 'CONTAGEM'
                elif dados['tipo'] == 'JOGO_INICIADO':
                    meu_player_id = dados['payload']['id']
                    oponente_apelido = dados['payload']['oponente']
                    estado_ecra = 'EM_JOGO'
                elif dados['tipo'] == 'GAME_STATE': game_state = dados['payload']
                elif dados['tipo'] == 'FIM_DE_JOGO':
                    mensagem_fim_de_jogo = f"Vencedor: {dados['payload']}"
                    estado_ecra = 'FIM_DE_JOGO'
        except (ConnectionResetError, json.JSONDecodeError): break
    print("Desconectado do servidor.")
    conectado_ao_servidor = False
    try: cliente.close()
    except: pass

def main():
    global estado_ecra, meu_apelido, conectado_ao_servidor, game_state, mensagem_fim_de_jogo
    thread_descoberta = threading.Thread(target=procurar_servidor_udp, daemon=True)
    thread_descoberta.start()
    rodando = True
    clock = pygame.time.Clock()
    btn_jogar, botoes_jogadores, btn_aceitar, btn_recusar, btn_atualizar = None, {}, None, None, None

    while rodando:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                rodando = False
            
            if estado_ecra == 'EM_JOGO':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                        enviar_mensagem({'tipo': 'START_MOVE', 'payload': {'id': meu_player_id, 'direction': 'UP'}})
                    elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        enviar_mensagem({'tipo': 'START_MOVE', 'payload': {'id': meu_player_id, 'direction': 'DOWN'}})
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                        enviar_mensagem({'tipo': 'STOP_MOVE', 'payload': {'id': meu_player_id, 'direction': 'UP'}})
                    elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        enviar_mensagem({'tipo': 'STOP_MOVE', 'payload': {'id': meu_player_id, 'direction': 'DOWN'}})

            elif estado_ecra == 'DIGITANDO_NOME':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if len(meu_apelido) > 0 and servidor_encontrado:
                            try:
                                print(f"Conectando a {servidor_encontrado[0]}:{servidor_encontrado[1]}...")
                                cliente.connect(servidor_encontrado)
                                conectado_ao_servidor = True
                                enviar_mensagem({'tipo': 'REGISTER', 'payload': meu_apelido})
                                thread_recebimento = threading.Thread(target=receber_mensagens, daemon=True)
                                thread_recebimento.start()
                                pygame.display.set_caption(f"Ping Pong - {meu_apelido}")
                                estado_ecra = 'MENU'
                            except Exception as e:
                                print(f"Não foi possível conectar ao servidor: {e}")
                                estado_ecra = 'PROCURANDO_SERVIDOR'
                                thread_descoberta = threading.Thread(target=procurar_servidor_udp, daemon=True)
                                thread_descoberta.start()
                    elif event.key == pygame.K_BACKSPACE: meu_apelido = meu_apelido[:-1]
                    else:
                        if len(meu_apelido) < 15: meu_apelido += event.unicode
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if estado_ecra == 'MENU' and btn_jogar and btn_jogar.collidepoint(event.pos): estado_ecra = 'ESCOLHENDO_JOGADOR'
                elif estado_ecra == 'ESCOLHENDO_JOGADOR':
                    if btn_atualizar and btn_atualizar.collidepoint(event.pos):
                        enviar_mensagem({'tipo': 'PEDIR_LISTA_JOGADORES'})
                    for apelido, rect in botoes_jogadores.items():
                        if rect.collidepoint(event.pos):
                            enviar_mensagem({'tipo': 'CONVIDAR_JOGADOR', 'payload': apelido})
                            estado_ecra = 'AGUARDANDO_RESPOSTA'
                elif estado_ecra == 'CONVITE_RECEBIDO':
                    if btn_aceitar and btn_aceitar.collidepoint(event.pos):
                        enviar_mensagem({'tipo': 'RESPONDER_CONVITE', 'payload': {'remetente': convite_de, 'aceito': True}})
                    elif btn_recusar and btn_recusar.collidepoint(event.pos):
                        enviar_mensagem({'tipo': 'RESPONDER_CONVITE', 'payload': {'remetente': convite_de, 'aceito': False}})
                        estado_ecra = 'MENU'
            
            elif event.type == pygame.KEYDOWN:
                if estado_ecra == 'FIM_DE_JOGO' and event.key == pygame.K_RETURN:
                    game_state = {}
                    mensagem_fim_de_jogo = ""
                    estado_ecra = 'MENU'

        if estado_ecra == 'PROCURANDO_SERVIDOR':
            desenhar_tela_espera("Procurando servidor na rede...")
        elif estado_ecra == 'DIGITANDO_NOME': desenhar_tela_apelido(meu_apelido)
        elif estado_ecra == 'MENU': btn_jogar = desenhar_menu()
        elif estado_ecra == 'ESCOLHENDO_JOGADOR':
            botoes_jogadores, btn_atualizar = desenhar_lista_jogadores()
        elif estado_ecra == 'AGUARDANDO_RESPOSTA': desenhar_tela_espera("Aguardando resposta do oponente...")
        elif estado_ecra == 'CONVITE_RECEBIDO': btn_aceitar, btn_recusar = desenhar_convite()
        # --- ALTERAÇÃO 3: Lógica de desenho da contagem regressiva ---
        elif estado_ecra == 'CONTAGEM':
            if contagem_tempo_inicio > 0:
                tempo_passado = (pygame.time.get_ticks() - contagem_tempo_inicio) / 1000
                tempo_restante = contagem_duracao - tempo_passado
                if tempo_restante > 0:
                    texto_a_mostrar = str(int(tempo_restante) + 1)
                    desenhar_tela_espera(texto_a_mostrar)
                else:
                    desenhar_tela_espera("Começando!")
        elif estado_ecra == 'EM_JOGO': desenhar_jogo()
        elif estado_ecra == 'FIM_DE_JOGO':
            desenhar_tela_espera(mensagem_fim_de_jogo)
            desenhar_texto("Pressione ENTER para voltar ao menu", fonte_pequena, COR_CINZA, LARGURA_TELA // 2, ALTURA_TELA // 2 + 100)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    if conectado_ao_servidor:
        cliente.close()

if __name__ == '__main__':
    main()
