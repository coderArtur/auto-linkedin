# Auto LinkedIn Bot - Guia de Execução Local (Windows)

Este guia contém o passo a passo para configurar e executar o robô automaticamente no seu próprio computador utilizando o Agendador de Tarefas do Windows. 

Rodar localmente é a forma mais inteligente e segura de executar o bot, pois utiliza o seu IP residencial e um ambiente/navegador que o sistema de segurança do LinkedIn já confia.

## ⚠️ Pré-requisitos
Certifique-se de que o seu arquivo `main.py` está configurado da maneira que você deseja visualizar o bot.
Se quiser que o robô rode de forma totalmente invisível enquanto você usa o PC, certifique-se de manter o modo headless ativado:
```python
browser = p.firefox.launch(headless=True)
```
Se quiser acompanhar o robô abrindo o navegador e trabalhando visualmente na sua tela, mude para `headless=False`.

---

## Passo a Passo de Configuração Inicial

### 1. Preparar o Ambiente Virtual (.venv)
Você já deve ter o ambiente virtual criado na pasta do projeto. Caso precise instalar do zero em um novo computador:
```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install --with-deps firefox
```

### 2. Configurar Variáveis de Ambiente (.env)
Certifique-se de que existe um arquivo oculto `.env` na raiz do projeto contendo as suas credenciais de login do LinkedIn:
```env
LINKEDIN_EMAIL=seu_email@exemplo.com
LINKEDIN_PASSWORD=sua_senha
```

### 3. Primeira Execução e Autenticação
Antes de agendar qualquer coisa, é obrigatório rodar o script manualmente pelo menos uma vez para que ele faça o primeiro login e gere o arquivo `sessao.json`. Assim, as próximas execuções automáticas não precisarão preencher e-mail e senha.
```cmd
python main.py
```

---

## Como Automatizar Execuções Diárias no Windows

Nós criamos um arquivo chamado `run_bot.bat` que é o responsável por iniciar o seu ambiente virtual e dar a partida no código em Python. Para que o Windows chame esse arquivo todos os dias no mesmo horário de forma religiosa, siga estes passos no **Agendador de Tarefas**:

1. Aperte a tecla **Windows** no teclado, digite **Agendador de Tarefas** (ou *Task Scheduler*) e aperte `Enter`.
2. No menu "Ações" localizado à direita, clique em **"Criar Tarefa Básica..."**
3. **Nome:** Digite `Robô LinkedIn` (ou o nome que preferir) e clique em Avançar.
4. **Disparador:** Escolha **Diariamente** e avance.
5. **Horário:** Configure para começar a partir da data de hoje e defina o horário de execução diário (ex: `10:30:00`). Avance.
6. **Ação:** Escolha **"Iniciar um programa"** e avance.
7. **Programa/Script:** Clique no botão **"Procurar..."**, navegue até a pasta do seu projeto (`C:\Users\artur\Documents\auto_linkedin\`) e selecione o executável **`run_bot.bat`**. Avance.
8. **Resumo:** Clique em **Concluir**.

### Observação sobre a Tela de Salvamento (Aba Geral)
Se o Windows pedir alguma senha e der erro na hora de salvar, dê dois cliques na tarefa criada para abrir as Propriedades (Aba Geral) e certifique-se de que a opção **"Executar somente quando o usuário estiver conectado"** está marcada. Isso evita conflitos com contas vinculadas a e-mail Outlook/PIN.

---

### E agora?
Missão cumprida! Todos os dias, no horário agendado, o Windows abrirá um terminal automaticamente, acionará o seu robô, fará as conexões com profissionais estratégicos aguardando os devidos tempos de segurança, e se encerrará sozinho. Tudo no piloto automático!
