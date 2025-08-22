document.addEventListener('DOMContentLoaded', () => {
    let socket = null; // Variável para armazenar a instância do Socket.IO

    // Referências aos elementos do DOM
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    // const sendButton = document.getElementById('send-button'); // REMOVIDO: Botão de enviar não existe mais
    const connectionStatus = document.getElementById('connection-status');
    const iniciarBtn = document.getElementById('iniciarBtn');
    const encerrarBtn = document.getElementById('encerrarBtn');
    const suggestionCards = document.querySelectorAll('.suggestion-card');
    const toggleSuggestionsBtn = document.getElementById('toggleSuggestionsBtn');
    const suggestionsContainer = document.querySelector('.suggestions-container');

    // --- Verificação de elementos DOM (importante para evitar erros) ---
    // Ajustado para não incluir o sendButton
    if (!chatBox || !messageInput || !connectionStatus || !iniciarBtn || !encerrarBtn || !toggleSuggestionsBtn || !suggestionsContainer) {
        console.error('Um ou mais elementos HTML essenciais não foram encontrados. Verifique os IDs/Classes no seu index.html.');
        return; // Abortar a execução se os elementos essenciais não estiverem presentes
    }

    let userSessionId = null; // ID da sessão do usuário, se aplicável

    // Função para adicionar mensagens no chat
    function addMessageToChat(sender, text, type = 'normal') {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');

        if (sender.toLowerCase() === 'user') {
            messageElement.classList.add('user-message');
            sender = 'Você';
        } else if (sender.toLowerCase() === 'bot') {
            messageElement.classList.add('bot-message');
            sender = 'Lumi';
            text = processBotMessage(text); // Processa a mensagem do bot para formatação
        } else {
            messageElement.classList.add('status-message');
        }

        if (type === 'error') {
            messageElement.classList.add('error-text');
            sender = 'Erro';
        } else if (type === 'status') {
            messageElement.classList.add('status-text');
            sender = 'Status';
        }

        const senderSpan = document.createElement('strong');
        senderSpan.textContent = `${sender}: `;
        messageElement.appendChild(senderSpan);

        const textSpan = document.createElement('span');
        textSpan.innerHTML = text;
        messageElement.appendChild(textSpan);

        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Função para processar a mensagem do bot (negrito e listas)
    function processBotMessage(text) {
        let processedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        const lines = processedText.split('\n');
        let inList = false;
        let outputHtml = '';

        lines.forEach(line => {
            if (line.trim().startsWith('* ')) {
                if (!inList) {
                    outputHtml += '<ul>';
                    inList = true;
                }
                outputHtml += `<li>${line.trim().substring(2)}</li>`;
            } else {
                if (inList) {
                    outputHtml += '</ul>';
                    inList = false;
                }
                if (line.trim() !== '') {
                    outputHtml += `<p>${line}</p>`;
                }
            }
        });

        if (inList) {
            outputHtml += '</ul>';
        }

        return outputHtml;
    }

    // Função para habilitar/desabilitar o chat (APENAS o input agora)
    function setChatEnabled(enabled) {
        messageInput.disabled = !enabled;
        messageInput.style.cursor = enabled ? 'text' : 'not-allowed';
    }

    // --- Estado inicial do chat ---
    setChatEnabled(false);
    connectionStatus.textContent = 'Desconectado';
    connectionStatus.className = 'status-offline';
    addMessageToChat('Status', 'Clique em "Iniciar conversa" para começar.', 'status');

    // Função para conectar ao servidor Socket.IO
    function iniciarConversa() {
        if (socket && socket.connected) {
            console.log('Cliente: Já conectado ao servidor. Ignorando novo pedido de conexão.');
            addMessageToChat('Status', 'Você já está conectado.', 'status');
            return;
        }

        try {
            socket = io('http://localhost:5000'); // Garanta que a URL está correta

            socket.on('connect', () => {
                console.log('Cliente: Conectado ao servidor Socket.IO! SID:', socket.id);
                connectionStatus.textContent = 'Conectado';
                connectionStatus.className = 'status-online';
                addMessageToChat('Status', 'Conectado ao servidor de chat.', 'status');
                setChatEnabled(true); // Habilita o input
                iniciarBtn.disabled = true;
                encerrarBtn.disabled = false;
            });

            socket.on('disconnect', (reason) => {
                console.log('Cliente: Desconectado do servidor Socket.IO. Razão:', reason);
                connectionStatus.textContent = 'Desconectado';
                connectionStatus.className = 'status-offline';
                addMessageToChat('Status', `Você foi desconectado. Razão: ${reason}`, 'status');
                setChatEnabled(false); // Desabilita o input
                iniciarBtn.disabled = false;
                encerrarBtn.disabled = true;
            });

            socket.on('connect_error', (error) => {
                console.error('Cliente: Erro de conexão Socket.IO:', error);
                addMessageToChat('Erro', `Falha ao conectar ao servidor: ${error.message}. Verifique se o servidor está rodando.`, 'error');
                connectionStatus.textContent = 'Erro na Conexão';
                connectionStatus.className = 'status-offline';
                setChatEnabled(false);
                iniciarBtn.disabled = false;
                encerrarBtn.disabled = true;
            });

            socket.on('status_conexao', (data) => {
                if (data.session_id) {
                    userSessionId = data.session_id;
                    console.log('Cliente: ID de sessão recebido:', userSessionId);
                }
            });

            socket.on('nova_mensagem', (data) => {
                addMessageToChat(data.remetente, data.texto);
            });

            socket.on('erro', (data) => {
                addMessageToChat('Erro', data.erro, 'error');
            });

        } catch (e) {
            console.error('Erro ao tentar inicializar Socket.IO:', e);
            addMessageToChat('Erro', 'Ocorreu um erro ao tentar iniciar a conversa.', 'error');
            setChatEnabled(false);
        }
    }

    // Função para encerrar a conversa
    function encerrarConversa() {
        if (socket && socket.connected) {
            console.log('Cliente: Solicitando desconexão...');
            socket.disconnect();
            setChatEnabled(false);
            addMessageToChat('Status', 'Conversa encerrada pelo usuário.', 'status');
            iniciarBtn.disabled = false;
            encerrarBtn.disabled = true;
        } else {
            addMessageToChat('Status', 'Nenhuma conversa ativa para encerrar.', 'status');
            console.log('Cliente: Tentativa de encerrar conversa, mas não estava conectado.');
        }
    }

    // Enviar mensagem para o servidor (APENAS via Enter agora)
    function sendMessageToServer() {
        const messageText = messageInput.value.trim();
        if (messageText === '') {
            console.log('Cliente: Mensagem vazia. Não enviando.');
            return;
        }

        if (socket && socket.connected) {
            addMessageToChat('user', messageText);
            socket.emit('enviar_mensagem', { mensagem: messageText });
            messageInput.value = '';
            messageInput.focus();
            console.log('Cliente: Mensagem enviada:', messageText);
        } else {
            addMessageToChat('Erro', 'Não conectado ao servidor. Clique em "Iniciar conversa".', 'error');
            console.warn('Cliente: Tentativa de enviar mensagem sem conexão.');
        }
    }

    // --- Event Listeners ---
    iniciarBtn.addEventListener('click', iniciarConversa);
    encerrarBtn.addEventListener('click', encerrarConversa);
    // REMOVIDO: sendButton.addEventListener('click', sendMessageToServer); // Não precisamos mais do clique do botão

    messageInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessageToServer(); // Agora, enviar só via Enter
        }
    });

    // Adiciona event listener para os cards de sugestão
    suggestionCards.forEach(card => {
    card.addEventListener('click', () => {
        const topic = card.dataset.topic;
        const message = card.dataset.message;

        if (topic) {
            // Abrir sub-sugestão
            showSuggestionScreen(`subSuggestions-${topic}`);
        } else if (message) {
            // Enviar sugestão direta
            if (socket && socket.connected) {
                messageInput.value = message;
                sendMessageToServer();
                suggestionsContainer.classList.remove('expanded');
                suggestionsContainer.classList.add('hidden');
                showSuggestionScreen('mainSuggestions'); // volta para principal
            } else {
                addMessageToChat('Erro', 'Não conectado ao servidor. Clique em "Iniciar conversa".', 'error');
            }
        }
    });
});


    // Lógica para mostrar/esconder as sugestões
    toggleSuggestionsBtn.addEventListener('click', () => {
        suggestionsContainer.classList.toggle('expanded');
        suggestionsContainer.classList.toggle('hidden');
    });

    // --- Sub-sugestões: lógica de exibição ---
document.querySelectorAll('.suggestion-card.main-card').forEach(mainCard => {
    mainCard.addEventListener('click', () => {
        // Ativa apenas este card
        document.querySelectorAll('.suggestion-card.main-card').forEach(c => c.classList.remove('active'));
        mainCard.classList.add('active');
    });

    const backButton = mainCard.querySelector('.back-button');
    if (backButton) {
        backButton.addEventListener('click', (e) => {
            e.stopPropagation();
            mainCard.classList.remove('active');
        });
    }
});

// Sub-sugestões enviam mensagem
document.querySelectorAll('.sub-suggestion-card').forEach(subCard => {
    subCard.addEventListener('click', () => {
        if (socket && socket.connected) {
            const message = subCard.dataset.message;
            messageInput.value = message;
            sendMessageToServer();
            suggestionsContainer.classList.remove('expanded');
            suggestionsContainer.classList.add('hidden');
            document.querySelectorAll('.main-card').forEach(c => c.classList.remove('active')); // Fecha sub-sugestões
        } else {
            addMessageToChat('Erro', 'Não conectado ao servidor. Clique em "Iniciar conversa".', 'error');
        }
    });
});

    // Início: Garantir que os botões de controle estejam no estado correto
    iniciarBtn.disabled = false;
    encerrarBtn.disabled = true;


});

// Função para trocar entre telas
function showSuggestionScreen(screenId) {
    document.querySelectorAll('.suggestions-screen').forEach(screen => {
        screen.classList.remove('active-screen');
    });
    const target = document.getElementById(screenId);
    if (target) target.classList.add('active-screen');
}

// Clique nos cards principais com sub-sugestões
document.querySelectorAll('.suggestion-card[data-topic]').forEach(card => {
    card.addEventListener('click', () => {
        const topic = card.dataset.topic;
        showSuggestionScreen(`subSuggestions-${topic}`);
    });
});

// Clique no botão voltar
document.querySelectorAll('.back-button').forEach(btn => {
    btn.addEventListener('click', () => {
        showSuggestionScreen('mainSuggestions');
    });
});

// Clique nas sub-sugestões
document.querySelectorAll('.sub-suggestion-card').forEach(sub => {
    sub.addEventListener('click', () => {
        if (socket && socket.connected) {
            const message = sub.dataset.message;
            messageInput.value = message;
            sendMessageToServer();
            suggestionsContainer.classList.remove('expanded');
            suggestionsContainer.classList.add('hidden');
            showSuggestionScreen('mainSuggestions'); // volta para a tela principal
        } else {
            addMessageToChat('Erro', 'Não conectado ao servidor. Clique em "Iniciar conversa".', 'error');
        }
    });
});
