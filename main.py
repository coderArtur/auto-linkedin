# pyrefly: ignore [missing-import]
import os
import random
import time
import schedule
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Para ocultar o navegador
NAVEGADOR_INVISIVEL = False

# Carrega as credenciais do .env
load_dotenv()
EMAIL = os.getenv("LINKEDIN_EMAIL")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")

def random_sleep(min_seconds=3, max_seconds=10):
    time.sleep(random.uniform(min_seconds, max_seconds))

def login(page):
    print("Iniciando login...")
    page.goto("https://www.linkedin.com/login/pt/?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin")
    random_sleep()
    
    # Preenche email e senha usando seletores que focam apenas nos campos visíveis na tela
    page.fill('input[type="email"]:visible', EMAIL)
    random_sleep(2, 4)
    page.fill('input[type="password"]:visible', PASSWORD)
    random_sleep(2, 4)
    
    # Desmarca "manter acesso" usando JavaScript para contornar o fato do checkbox ser invisível
    # page.evaluate("document.querySelectorAll('input[type=\"checkbox\"]').forEach(cb => cb.checked = false)")
    
    # random_sleep(1, 3)
    # Clica no botão de Entrar garantindo o texto exato e verificando em Python qual está visível
    btn_entrar = page.get_by_role("button", name="Entrar", exact=True)
    btn_entrar.first.wait_for(state="attached") # Espera o botão existir na página
    for i in range(btn_entrar.count()):
        if btn_entrar.nth(i).is_visible():
            btn_entrar.nth(i).click()
            break
    print("Login concluído. Aguardando carregamento da página inicial...")
    page.wait_for_url("https://www.linkedin.com/feed/", timeout=20000)
    random_sleep(5, 10)

def search_and_connect(page, keyword, max_connections=10):
    print(f"Pesquisando por: {keyword}")
    url = f"https://www.linkedin.com/search/results/people/?keywords={keyword}&origin=FACETED_SEARCH&geoUrn=%5B%22106057199%22%5D"
    page.goto(url)
    random_sleep(5, 10)
    
    connections_sent = 0
    
    while connections_sent < max_connections:
        # O card do perfil engloba o botão. Usar aria-label garante 
        # que ele clique EXATAMENTE no botão isolado e não no card inteiro.
        connect_buttons = page.locator('button:text-is("Conectar"), [aria-label*="para se conectar"]')
        # Como o seletor é "ao vivo", quando enviamos o convite o botão some da lista (pois vira Pendente).
        # Por isso não podemos usar um "for" normal, senão ele pula um a cada rodada.
        failed_buttons = 0
        while failed_buttons < connect_buttons.count():
            if connections_sent >= max_connections:
                break
                
            # O alvo é sempre o primeiro botão válido (descontando os que falharam)
            button = connect_buttons.nth(failed_buttons)
            
            if button.is_visible():
                button.click()
                print(f"[{connections_sent+1}] Clicou em Conectar. Aguardando modal...")
                random_sleep(3, 6)
                
                # Verifica se o LinkedIn está pedindo e-mail para este usuário (caso raro)
                email_input = page.locator('div[role="dialog"] input[type="email"]')
                if email_input.count() > 0:
                    print("LinkedIn pediu e-mail para este usuário. Pulando sem contabilizar...")
                    close_btn = page.get_by_role("button", name="Fechar", exact=True)
                    if close_btn.count() > 0:
                        close_btn.first.click()
                    random_sleep(2, 4)
                    failed_buttons += 1
                    continue
                send_button = page.get_by_role("button", name="Enviar sem nota")
                if send_button.count() > 0:
                    send_button.first.click()
                    print("Convite enviado.")
                    connections_sent += 1
                    
                    print("Aguardando um tempo aleatório antes da próxima conexão...")
                    # random_sleep(300, 1200) 
                    random_sleep(3, 7) 
                    
                    # SUCESSO: o botão virou Pendente e vai sair do radar do locator.
                    # Por causa disso NÃO avançamos o 'failed_buttons'. O próximo cara válido vai "escorregar" para esse índice!
                else:
                    print("Botão 'Enviar sem nota' não encontrado, pulando...")
                    close_btn = page.get_by_role("button", name="Fechar", exact=True)
                    if close_btn.count() > 0:
                        close_btn.first.click()
                    random_sleep(2, 4)
                    # FALHA: O botão vai continuar sendo detectado como "Conectar", então avançamos o índice para não ficar num loop infinito.
                    failed_buttons += 1
            else:
                failed_buttons += 1

        # Se não enviou o suficiente, passa para a próxima página
        if connections_sent < max_connections:
            # Usa o data-testid exato além do texto, pega o primeiro caso achem dois
            next_button = page.locator('button[data-testid="pagination-controls-next-button-visible"], button:has-text("Próxima")').first
            if next_button.is_visible() and not next_button.is_disabled():
                print("Indo para a próxima página...")
                # Rola até o botão para evitar que elementos flutuantes do LinkedIn (como chat) o cubram
                next_button.scroll_into_view_if_needed()
                random_sleep(1, 3)
                # Usa force=True para clicar mesmo que o Playwright ache que ele está obstruído
                next_button.click(force=True)
                random_sleep(8, 15)
            else:
                print("Não há mais páginas ou botão 'Próxima' indisponível.")
                break

def run_daily_automation():
    print("Iniciando rotina diária...")
    with sync_playwright() as p:
        # Rodamos apenas o firefox
        browser = p.firefox.launch(headless=NAVEGADOR_INVISIVEL) # Em uma VM, geralmente headless=True
        # Tenta reaproveitar a sessão anterior se ela existir
        state_file = "sessao.json"
        if os.path.exists(state_file):
            print("Carregando sessão salva do arquivo...")
            context = browser.new_context(storage_state=state_file)
        else:
            context = browser.new_context()
            
        page = context.new_page()
        
        try:
            # Tenta acessar o feed direto para ver se a sessão atual ainda é válida
            print("Verificando status da sessão...")
            page.goto("https://www.linkedin.com/feed/")
            random_sleep(3, 6)
            
            # Lógica Inversa Infalível: se o LinkedIn nos deslogar, ele SEMPRE mostra campos de email/senha.
            # Se não houver campo de email na tela, é porque estamos logados com sucesso no Feed!
            # O ":visible" dentro do seletor + "count() > 0" impede o robô de travar caso o LinkedIn esconda 2 inputs na tela.
            tem_email = page.locator('input[type="email"]:visible').count() > 0
            tem_senha = page.locator('input[type="password"]:visible').count() > 0
            
            if tem_email or tem_senha or "login" in page.url or "authwall" in page.url:
                print("Sessão expirada ou página de bloqueio detectada. Refazendo login...")
                login(page)
                # Salva o arquivo sessao.json com os cookies atualizados
                context.storage_state(path=state_file)
                print("Sessão guardada com sucesso para o próximo uso!")
            else:
                print("Perfeito! Já estamos logados. Pulando tela de login...")
            
###################################################################################################################
            # Define as estratégias disponíveis e seus parâmetros de busca
            estrategias = {
                "engenheiro_dados": [
                    {"keyword": "engenheiro%20de%20dados", "min_conn": 8, "max_conn": 12},
                    {"keyword": "engenheira%20de%20dados", "min_conn": 8, "max_conn": 12}
                ],
                # "tech_recruiter": [
                #     {"keyword": "tech%20recruiter", "min_conn": 18, "max_conn": 22}
                # ],
                # "data_engineer": [
                #     {"keyword": "data%20engineer", "min_conn": 18, "max_conn": 22}
                # ],
                # "ai_engineer": [
                #     {"keyword": "ai%20engineer", "min_conn": 18, "max_conn": 22}
                # ],
                # "engenheiro_ia": [
                #     {"keyword": "engenheiro%20de%20ia", "min_conn": 8, "max_conn": 12},
                #     {"keyword": "engenheira%20de%20ia", "min_conn": 8, "max_conn": 12}
                # ]
            }
###################################################################################################################
            
            # Escolhe aleatoriamente a estratégia do dia com base nas chaves do dicionário
            strategy_name = random.choice(list(estrategias.keys()))
            print(f"Estratégia selecionada para hoje: {strategy_name}")
            
            # Executa as buscas da estratégia selecionada de forma dinâmica
            for busca in estrategias[strategy_name]:
                max_conn = random.randint(busca["min_conn"], busca["max_conn"])
                try:
                    search_and_connect(page, busca["keyword"], max_connections=max_conn)
                except Exception as e:
                    print(f"Erro na busca por '{busca['keyword']}': {e}")
                
            print("Rotina diária finalizada com sucesso. Limite de 20 conexões atingido.")
            
        except Exception as e:
            print(f"Erro durante a execução: {e}")
        finally:
            context.close()
            browser.close()

def job():
    # Podemos colocar mais uma aleatoriedade para não rodar exatamente na hora agendada sempre
    delay_minutes = random.randint(0, 90)
    print(f"Agendado para rodar. Aguardando um delay aleatório de {delay_minutes} minutos antes de iniciar...")
    time.sleep(delay_minutes * 60)
    run_daily_automation()

if __name__ == "__main__":
    print("Iniciando bot...")
    run_daily_automation()

    # APENAS SE FUNCIONASSE EM UMA VPS, MAS O LINKEDIN BLOQUEIA MESMO COM USO DE VPN

    # print("Iniciando bot...")
    # print("Escolha o modo de execução:")
    # print("1 - Rodar uma vez agora mesmo")
    # print("2 - Rodar modo 24/7 (Agendamento diário)")
    
    # escolha = input("Digite 1 ou 2: ").strip()
    
    # if escolha == "1":
    #     print("Execução imediata selecionada. O bot vai iniciar em instantes...")
    #     run_daily_automation()
    # elif escolha == "2":
    #     print("Modo 24/7 ativado. O script fará uma execução diária a partir das 08:00.")
    #     schedule.every().day.at("08:00").do(job)
        
    #     while True:
    #         schedule.run_pending()
    #         time.sleep(60)
    # else:
    #     print("Opção inválida! Por favor, rode o script novamente e digite 1 ou 2.")

    # print("Iniciando bot em nuvem...")
    
    # # Executa uma vez AGORA MESMO para já garantir o envio do dia de hoje (Opcional)
    # print("Fazendo a execução de inicialização...")
    # run_daily_automation()
    
    # # Em seguida, ativa o agendador eterno para os próximos dias
    # print("Modo 24/7 ativado. O script fará a próxima execução amanhã a partir das 08:00.")
    # schedule.every().day.at("08:00").do(job)
    
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)

