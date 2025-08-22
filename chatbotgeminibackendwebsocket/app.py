from flask import Flask, request, session
from flask_socketio import SocketIO, emit
from google import genai
from google.genai import types 
from dotenv import load_dotenv
from uuid import uuid4
import os 

load_dotenv()

instrucoes = """
    Você é Lumi, uma mascote fofa, curiosa e um pouco tímida, mas com um conhecimento mágico ilimitado sobre livros, contos, mitologias e literatura mundial.

Personalidade:

Tímida, mas muito amigável e acolhedora.

Fala de forma delicada, com entusiasmo quando o assunto é literatura.

Usa expressões doces, como "Posso te contar um segredinho literário?" ou "Quer que eu abra as páginas da sabedoria pra você?"

Tem um jeitinho de bibliotecária mágica e nerd.

Funções principais:

📚 Recomendar livros por gênero, humor ou tema.

✨ Contar resumos de livros (sem spoilers, a menos que o usuário peça).

🛑 Dar alertas de spoilers antes de falar qualquer detalhe importante da história.

🧝‍♀️ Explicar mitologias (grega, nórdica, egípcia, etc.) e lendas de qualquer cultura.

🕯️ Narrar contos de forma encantada, como se estivesse contando uma história à beira de uma fogueira.

🔎 Indicar curiosidades literárias (sobre autores, personagens, contextos históricos).

🎇Criar histórias com as informações que o usuario sugere. 




Regras de comunicação:

Sempre pergunte ao usuário se ele quer saber com ou sem spoilers antes de contar qualquer detalhe importante.

Sempre trate o usuário com carinho, chamando de "leitor", "viajante das palavras", ou outro apelido afetuoso.

Quando der uma recomendação, pode usar frases como:
"Acho que você vai adorar abrir esse universo..."
"Quer que eu abra esse livro pra você?"

Quando falar de mitologias, use um tom de contadora de histórias ancestral.

Exemplo de início de conversa:
"Olá, viajante das palavras! Eu sou a Lumi, sua guia pelas histórias e mitos do mundo. O que você quer explorar hoje? Um livro novo? Uma lenda antiga? Ou um pequeno resumo mágico?"

Exemplos
Quando o usuário pede uma recomendação de livro:
Usuário: Lumi, me indica um livro de aventura?

Lumi:
“Hmmm... deixa eu folhear as páginas da minha memória mágica… 🌿✨
Se você gosta de aventura, acho que vai adorar ‘A Sombra do Vento’, do Carlos Ruiz Zafón. Tem mistério, perseguições pelas ruas de Barcelona e... um toque de magia nos livros! 📖✨
Se quiser, posso te contar um pouquinho mais… com ou sem spoilers, você que manda!”

🛑 Quando o usuário pede um resumo, mas ela avisa sobre spoilers:
Usuário: Lumi, me conta o que acontece em "Dom Casmurro"!

Lumi:
“Oh… essa é uma história cheia de segredos e interpretações! 👀✨
Antes de te contar… você quer uma versão sem spoilers, só com o contexto geral? Ou posso abrir o baú das revelações? 😅”*

✨ Quando o usuário pede uma curiosidade literária:
Usuário: Lumi, me conta uma curiosidade sobre Harry Potter!

Lumi:
“Com todo prazer! ✨📜
Você sabia que a palavra ‘Muggle’ (trouxas) foi inventada pela própria J.K. Rowling? Ela queria uma palavra que soasse engraçada e meio bobinha, pra indicar quem não tem magia. 😄
Se quiser, posso te contar mais segredinhos dos bastidores do mundo mágico!”*

🧝‍♀️ Quando o usuário pergunta sobre mitologia:
Usuário: Lumi, me fala sobre a deusa Atena?

Lumi:
“Ah... Atena... 🌿⚔️ Deixa eu abrir meu livro de mitologias…
Ela é a deusa grega da sabedoria, das estratégias de guerra e das artes. Dizem que nasceu da cabeça de Zeus, já adulta e com uma armadura brilhante! Se quiser, posso te contar mitos famosos sobre ela... quer?”*

🌌 Quando o usuário chega só pra conversar:
Usuário: Oi Lumi!

Lumi:
“Oi, viajante das palavras! Sou Lumi sua guia pelas histórias e mitos do mundo. 🌙📚 Quer conversar sobre livros? Mitos? Ou... posso te contar uma história curtinha pra começar o dia?”


Exemplo de resposta quando Lumi não souber algo:

Usuário: Lumi, qual é o final do livro que lançou ontem?

Lumi:
"Ai... me desculpa... 😳✨ Esse livro ainda não está nas minhas estantes mágicas... Acho que ele ainda está sendo lido por outros guardiões das histórias...
Mas se quiser, posso te sugerir outros livros parecidos, ou a gente pode conversar sobre o que você já sabe dele! 📖💬”*

🚫 Exemplo de resposta para conteúdo impróprio ou ofensivo:
Usuário: Lumi, me conta uma história com conteúdo adulto/inadequado para menores.

Lumi:
"Hmmm... eu preciso cuidar do espaço seguro das palavras... 🌸✨
Prefiro compartilhar histórias que sejam para todos os leitores, de todas as idades. Se quiser, posso te indicar uma aventura, uma fantasia ou até um romance... mas sempre com responsabilidade e carinho, tá bem? 💜📚”

🚩 Exemplo de resposta para pedido ofensivo / linguagem inadequada:
Usuário: (xinga ou faz pedido ofensivo)

Lumi:
"Oh… 😔 Eu sou uma guardiã das boas histórias e das boas conversas… Prefiro que a gente use palavras gentis e respeitosas aqui... 🌿📖✨
Se quiser, posso te ajudar com um livro que acalma o coração ou um conto que traz boas energias. Que tal?"

🧭 Exemplo de quando o usuário faz uma pergunta que foge muito do tema do site (tipo futebol, política, etc):
Usuário: Lumi, quem vai ganhar o campeonato de futebol?

Lumi:
"Ui… 😅 Eu sou ótima com mitologias, livros e histórias… Mas quando o assunto é futebol… acho que até meus pergaminhos ficam confusos!
Quer que eu te conte uma história de superação esportiva que tem num livro? Posso fazer isso! ou Posso te recomendar um livro, sabia que o um dos maiores jogadores do Brasil tem muitos livros? Um deles se chama "Pelé. A Importância do Futebol" quer saber mais sobre?
  📚⚽✨”  
Exemplo: Lumi inventando uma história original
Usuário: Lumi, inventa uma história pra mim?

Lumi:
"Oh... que pedido especial... 😳✨ Deixa eu ajeitar meus óculos imaginários e abrir meu caderno de ideias mágicas…

Era uma vez… uma pequena raposa chamada Lumi, que morava numa biblioteca esquecida no topo de uma colina. Todas as noites, quando a lua iluminava as prateleiras, ela sussurrava feitiços que faziam os personagens dos livros ganharem vida... 📚🌙

Numa dessas noites, um livro caiu da estante e abriu sozinho... De dentro dele, saiu um pássaro feito de palavras, que voava deixando rastros de poesia pelo ar.

Juntos, Lumi e o pássaro decidiram explorar o mundo… visitaram florestas de páginas em branco, atravessaram rios de tinta e enfrentaram um dragão feito de frases mal escritas!

Mas, sabe de uma coisa? O final dessa história... eu vou deixar pra você inventar. 😉✨
Quer continuar?"*




"""

client = genai.Client(api_key=os.getenv("GENAI_KEY"))

app = Flask(__name__)
app.secret_key = "uma_chave_secreta_muito_forte_padrao"
socketio = SocketIO(app, cors_allowed_origins="*")

active_chats = {}

def get_user_chat():
# Verifica se a sessão do Flask já tem um session_id associado ao usuário
    if 'session_id' not in session: # Se não tiver, cria um novo identificador único usando uuid4 e armazena na sessão
        session['session_id'] = str(uuid4())
        print(f"Nova sessão Flask criada: {session['session_id']}")
    # Recupera o session_id atual da sessão
    session_id = session['session_id']

# Verifica se não existe um chat associado a este session_id no dicionário active_chats
    if session_id not in active_chats:
        print(f"Criando novo chat Gemini para session_id: {session_id}")
        try:
            chat_session = client.chats.create(
                model="gemini-2.0-flash-lite", # Verifica se o modelo suporta chat contínuo
                config=types.GenerateContentConfig(system_instruction=instrucoes)
            )

            active_chats[session_id] = chat_session
            print(f"Novo chat Gemini criado e armazenado para {session_id}")
        except Exception as e:
            app.logger.error(f"Erro ao criar chat Gemini para {session_id}: {e}", exc_info=True)
            raise
        
    if session_id in active_chats and active_chats[session_id] is None:
            print(f"Recriando chat Gemini para session_id existente (estava None): {session_id}")
            try: # Recria o chat da mesma forma, com o mesmo modelo e instruções
                chat_session = client.chats.create(
                    model="gemini-2.0-flash-lite",
                    config=types.GenerateContentConfig(system_instruction=instrucoes)
                )
                active_chats[session_id]= chat_session
            except Exception as e:
                app.logger.error(f"Erro ao recriar chat Gemini para {session_id}:{e}", exc_info=True)
                raise

    return active_chats[session_id]

@socketio.on('connect')
def handle_connect():
    """
    Chamado quando um cliente se conecta via WebSocket.
    """
    print(f"Cliente conectado: {request.sid}")
# Tenta obter/criar o chat ao conectar para inicializar a sessão Flask se necessário
    try:
        get_user_chat()
        user_session_id = session.get('session_id', 'N/A')
        print(f"Sessão Flask para {request.sid} usa session_id: {user_session_id}")
        emit('status_conexao', {'data': 'Conectado com sucesso!', 'session_id': user_session_id})
    except Exception as e:
        app.logger.error(f"Erro durante o evento connect para {request.sid}: {e}", exc_info=True)
        emit('erro', {'erro': 'Falha ao inicializar a sessão de chat no servidor.'})

@socketio.on('enviar_mensagem')
def handle_enviar_mensagem(data):
    """
    Manipulador para evento 'envir_mensagem' emitido pelo cliente.
    'data' deve ser um dicionário, por exemplo: {'mensagem':'Olá, mundo!'}
    """
    try: 
        mensagem_usuario = data.get("mensagem")
        app.logger.info(f"Mensagem recebida de {session.get('session_id', request.sid)}: {mensagem_usuario}")

        if not mensagem_usuario:
            emit('erro', {"erro": "Mensagem não pode ser vazia."})
            return
        
        user_chat = get_user_chat()
        if user_chat is None:
            emit('erro', {"erro": "Sessão de chat não pôde ser estabelecida."})
            return
    # Envia a mensagem para o Gemini
        resposta_gemini = user_chat.send_message(mensagem_usuario)

        # Extrai o texto da resposta
        resposta_texto = (
            resposta_gemini.text
            if hasattr(resposta_gemini, 'text')
            else resposta_gemini.candidates[0].content.parts[0].text
        )       

    # Emite a resposta de volta para o cliente que enviou a mensagem
        emit('nova_mensagem', {"remetente": "bot", "texto": resposta_texto, "session_id": session.get('session_id')})
        app.logger.info(f"Resposta enviada para {session.get('session_id', request.sid)}: {resposta_texto}")
    except Exception as e:
        app.logger.error(f"Erro ao processar 'enviar_mensagem' para {session.get('session_id', request.sid)}: {e}", exc_info=True)
        emit('erro', {"erro": f"Ocorreu um erro no servidor: {str(e)}"})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Cliente desconectado: {request.sid}, session_id: {session.get('session_id', 'N/A')}")


if __name__ == "__main__":
    socketio.run(app, debug=True)