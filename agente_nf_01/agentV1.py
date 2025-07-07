import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent # Importe create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder # Importe prompts de chat
from langchain.tools import tool
from datetime import datetime
import sys
from typing import Dict, NewType
from functools import wraps
import pandas as pd
import argparse
from tabulate import tabulate
import logging

from xml_parser import parse_nfe_xml
import config

# --- 1. Definição de variaveis globais ---
# Commentáro de teste
DataFrameType = NewType('DataFrameType', pd.DataFrame)


# --- 2. Definição das funcoes de handle errors e log format ---
def configure_log(file_prefix,log_dir="logs",timestamp=datetime.today().strftime('%y%m%d')):
    """Configures logging to file and stdout."""
    global logger
    os.makedirs(log_dir, exist_ok=True)
    log_file_name = os.path.join(log_dir, f"{file_prefix}_{timestamp}.log")
    log_format = '[%(asctime)s] [%(name)s] %(levelname)s: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    logging.basicConfig(
        filename=log_file_name,
        filemode='w',
        datefmt=date_format,
        format=log_format,
        level=logging.INFO,
        force=True # Garante que a configuração é aplicada, útil em ambientes que rodam várias vezes
    )

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))
    logging.getLogger().addHandler(stdout_handler)
    logger = logging.getLogger(__name__) # Atribuir o logger configurado à variável global
    logger.info(f"Logging configured to: {log_file_name}")

def handle_errors(func):
    """Decorator to handle exceptions within methods."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        instance = args[0]
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            instance.logger.error(f"Arquivo não encontrado: {e}")
            sys.exit(1)
        except PermissionError as e:
            instance.logger.error(f"Erro de permissão: {e}")
            sys.exit(1)
        except ValueError as e:
            instance.logger.error(f"Erro de valor: {e}")
            sys.exit(1)
        except Exception as e:
            instance.logger.error(f"Erro inesperado em {func.__name__}: {e}")
            sys.exit(1)
    return wrapper


# --- 3. Definição das ferramentas ---

# Ferramenta de teste
@tool
def test_ai_agent() -> str:
    """
        Retorna uma string com a descrição do agente.
        
        Ela retorna uma string com a descrição do agente. Para que o usuário saiba que o agente está operacional
        Ela é particularmente útil para responder perguntas do tipo: "Executar teste", "Testar agente", "Verificar agente", etc.
        
        Args:
            #Não são necessários argumentos para esta ferramenta.
        
        Returns:
            str: Uma string com a descrição do agente e um status de operação.
    """
    return "O agente está operacional e pronto para realizar tarefas!"

# Ferramenta de maior forncedor
@tool
def obtain_bigger_supplier() -> str:
    """
        Retorna o fornecedor que teve o maior montante total recebido em notas fiscais,
        Baseado nos dados carregados retorna a informação de qual foi o maior fornecedor considerando o montante.
        Útil para perguntas como: "Qual fornecedor teve o maior montante?", "Quem foi o fornecedor com o maior valor total de notas fiscais?"
        
        Args:
            #Não são necessários argumentos para esta ferramenta.
        
        Returns:
            str: Uma string com a informação de qual foi o maior fornecedor.
    """
    
    if 'header' not in data or data['header'].empty:
        response = "Dados do cabeçalho das notas fiscais não carregados ou vazios. Não foi possível analisar fornecedores."
        return response

    amount_suppliers = data['header'].groupby('RAZÃO SOCIAL EMITENTE')['VALOR NOTA FISCAL'].sum()
    
    if amount_suppliers.empty:
        response = "Não foi possível encontrar dados de montante para fornecedores."
        return response

    top_supplier = amount_suppliers.idxmax()
    largest_amount = amount_suppliers.max()
    
    response = f"O fornecedor com o maior montante recebido é '{top_supplier}' com um total de R$ {largest_amount:.2f}."
    return response

# Ferramenta de menor fornecedor
@tool
def obtain_smaller_supplier() -> str:
    """
    Retorna o fornecedor que teve o menor montante total recebido em notas fisca
    Baseado nos dados carregados retorna a informação de qual foi o menor fornecedor considerando o montante.
    Útil para perguntas como: "Qual fornecedor teve o menor montante?", "Qual o fornecedor com menor valor total de notas fiscais?"
    
    Args:
        #Não são necessários argumentos para esta ferramenta.
    
    Returns:
        str: Uma string com a informação de qual foi o menor fornecedor.
    """
    if 'header' not in data or data['header'].empty:
        response = "Dados do cabeçalho das notas fiscais não carregados ou vazios. Não foi possível analisar fornecedores."
        return response

    amount_suppliers = data['header'].groupby('RAZÃO SOCIAL EMITENTE')['VALOR NOTA FISCAL'].sum()
    
    if amount_suppliers.empty:
        response = "Não foi possível encontrar dados de montante para fornecedores."
        return response

    smaller_supplier = amount_suppliers.idxmin()
    amount = amount_suppliers.min()
    
    response = f"O fornecedor com o menor montante recebido é '{smaller_supplier}' com um total de R$ {amount:.2f}."
    return response
        
# Ferramenta top X fornecedores por valor total recebido.
@tool
def top_x_bigger_suppliers(num_input: int) -> str:
    """
    Retorna os X fornecedores com o maior montante total recebido em notas fiscais.
    Baseado nos dados carregados retorna a informação de quais foram os X maiores fornecedores considerando o montante, sendo X um valor definido pelo usuário.
    Útil para perguntas como: "Quais foram os 5 maiores fornecedores?", "Liste os maiores 3 fornecedores"
    
    Args:
        num_input (int): O número de fornecedores a serem listados.
    
    Returns:
        str: Uma string contendo todos os fornecedores com o maior montante total recebido.
    
    """
    if 'header' not in data or data['header'].empty:
        response = "Dados do cabeçalho das notas fiscais não carregados ou vazios. Não foi possível analisar fornecedores."
    if num_input <= 0:
        response = "O valor de X deve ser um número positivo."
    amount_suppliers = data['header'].groupby('RAZÃO SOCIAL EMITENTE')['VALOR NOTA FISCAL'].sum()
    
    if amount_suppliers.empty:
        response = "Não foi possível encontrar dados de montante para fornecedores."
    else:
        top_suppliers = amount_suppliers.nlargest(num_input)
        response = f"Os {num_input} maiores fornecedores foram:"
        for supplier, amount in top_suppliers.items():
            
            response += f"\n{supplier}: R$ {amount:.2f}"
        
    return response

# Ferramenta top X fornecedores com menor valor recebido
@tool
def top_x_smaller_suppliers(num_input: int) -> str:
    """
    Retorna os X fornecedores com o menor montante total recebido em notas fiscais.
    Baseado nos dados carregados retorna a informação de quais foram os X menores fornecedores considerando o montante, sendo X um valor definido pelo usuário.
    Útil para perguntas como: "Quais foram os 5 menores fornecedores?", "Liste os menores 3 fornecedores"
    
    Args:
        num_input (int): O número de fornecedores a serem listados.
    
    Returns:
        str: Uma string contendo todos os fornecedores com o maior montante total recebido.
    
    """
    if 'header' not in data or data['header'].empty:
        response = "Dados do cabeçalho das notas fiscais não carregados ou vazios. Não foi possível analisar fornecedores."
    if num_input <= 0:
        response = "O valor de X deve ser um número positivo."
    amount_suppliers = data['header'].groupby('RAZÃO SOCIAL EMITENTE')['VALOR NOTA FISCAL'].sum()
    
    if amount_suppliers.empty:
        response = "Não foi possível encontrar dados de montante para fornecedores."
    else:
        top_suppliers = amount_suppliers.nsmallest(num_input)
        response = f"Os {num_input} menores fornecedores foram:"
        for supplier, amount in top_suppliers.items():
            
            response += f"\n{supplier}: R$ {amount:.2f}"
        
    return response
    
# Ferramenta de fornecedores por UF
@tool
def suppliers_by_state() -> str:
    """
        Retorna uma string com os fornecedores agrupados por UF.
        Baseado nos dados carregados retorna a informação de quais foram os fornecedores considerando a UF, sendo útil para perguntas como:\
            "Qual o montante de fornecedores por estado?", "Liste os fornecedores por UF", "Quais foram os fornecedores por UF?"
        
        Args: 
            #Não são necessários argumentos para esta ferramenta.
        
        Returns:
            str: Uma string contendo todos os fornecedores agrupados por UF.
    """
    if 'header' not in data or data['header'].empty:
        response = "Dados do cabeçalho das notas fiscais não carregados ou vazios. Não foi possível analisar fornecedores."
    amount_suppliers = data['header'].groupby('UF EMITENTE')['CHAVE DE ACESSO'].nunique()
    
    amount_suppliers =  pd.Series(amount_suppliers).sort_values(ascending=False)
    response = "Os fornecedores agrupados por UF foram:"
    for estado, quantidade in amount_suppliers.items():
        response += f"\n- {estado}: {quantidade} notas"

    return response
    
# Qual item teve o maior volume entregue (em quantidade)?
@tool
def delivery_item(num_input: int, type_consult:str) -> str:
    """
    Retorna uma string com os items entregues (em quantidade).
    Baseado nos dados carregados retorna a informação de quais foram os itens considerando o montante.
    Útil para perguntas como: "Qual o item mais vendido?", "Quais foram os itens mais vendidos?",
    "Quais foram os itens mais entregues?", "Quais foram os items menos vendidos?",
    "Quais foram os items menos entregues?"

    Args:
        num_input (int): (opicional) O número de itens a serem considerados.
        type_consult (str): (obrigatório) O tipo de consulta a ser realizada. opções: 'top','maior', 'menor', 'mais', 'menos'.
    
    Returns:
        Uma string com o(s) items mais vendidos
    """
    if 'header' not in data or data['header'].empty:
        response: str = "Dados do cabeçalho das notas fiscais não carregados ou vazios. Não foi possível analisar fornecedores."
    
    if num_input <= 0:
        qtd_query: int = 1
    else:
        qtd_query: int = num_input
    
    
    amount = data['items'].groupby('DESCRIÇÃO DO PRODUTO/SERVIÇO')['QUANTIDADE'].sum()
    if type_consult in [ 'maior', 'mais', 'top']:
        produts = amount.nlargest(qtd_query)
        str_complement = "maior(es)" 
    elif type_consult in ['menor', 'menos']:
        produts = amount.nsmallest(qtd_query)
        str_complement = "menor(es)"
    
    response = f"Os produtos {str_complement} foram:"
    for supplier, amount in produts.items():
        response += f"\n- {supplier}: {amount} unidades"
    
    return response    

# Relaçoes itens e valores entregues (em valor)?
@tool
def delivery_item_value(num_input: int, type_consult:str) -> str:
    """
    Retorna uma string com os items entregues (em valor).
    Baseado nos dados carregados retorna a informação de quais foram os itens considerando o valor.
    Útil para perguntas como: "Qual o item mais caro vendido?", "Quais foram os itens mais caros vendidos?",
    "Quais foram os items mais baratos vendidos?", "Quais foram os items com o maior valor vendido?",
    "Quais foram os items com o menor valor vendido?"
    
    Args:
        num_input (int): (opcional) O número de itens a serem considerados.
        type_consult (str): (obrigatório) O tipo de consulta a ser realizada. opções: 'top','maior', 'menor', 'mais', 'menos
    
    Returns:
        Retorna uma string com a relação de itens entregues e seu valor.
    """
    
    if 'items' not in data or data['items'].empty:
        response = "Dados do cabeçalho das notas fiscais não carregados ou vazios. Não foi possível analisar fornecedores."
    
    qtd_query: int = num_input
    if num_input <= 0:
        qtd_query: int = 1
        
    amount = data['items'].groupby('DESCRIÇÃO DO PRODUTO/SERVIÇO')['VALOR TOTAL'].sum()
    if type_consult in [ 'maior', 'mais', 'top']:
        produts = amount.nlargest(qtd_query)
        str_complement = "maior(es)"
    elif type_consult in ['menor', 'menos']:
        produts = amount.nsmallest(qtd_query)
        str_complement = "menor(es)"
        
    response: str = f"Os produtos {str_complement} em valor foram:"
    for supplier, amount in produts.items():
        response += f"\n- {supplier}: Total de vendas: R${amount:.2f}"
    
    return response
    

# --- 4. Definição da classe principal ---
class AgentAI:
    def __init__(self):
        self.logger = logging.getLogger(__class__.__name__)
        self.tabulateAgent = lambda x: tabulate(x, headers='keys', tablefmt='psql')
        
        # --- Configuração do LLM (Gemini) ---
        self.llm_brain = ChatGoogleGenerativeAI(model=config.LLM_MODEL, temperature=config.LLM_TEMPERATURE, google_api_key=config.GOOGLE_API_KEY)
        
    
    def agent_tolive(self) -> None:
        """Método principal do agente."""
        self.logger.info("Agent Tolive started")
        
        # ---  Lista de Ferramentas ---
        tools_list = [test_ai_agent,obtain_bigger_supplier,obtain_smaller_supplier, 
                      top_x_bigger_suppliers, top_x_smaller_suppliers,
                      suppliers_by_state,delivery_item, delivery_item_value]

        # --- Prompt para o Agente (Usando ChatPromptTemplate) ---
        # Para tool_calling_agent, o prompt é geralmente mais simples, baseado em mensagens.
        # MessagesPlaceholder é crucial para o agent_scratchpad, onde o histórico de ferramentas fica.
        agent_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "Você é um assistente útil e experiente em análise de dados de notas fiscais.\
                    Sua tarefa é responder a perguntas sobre os dados de notas fiscais usando as ferramentas disponíveis.\
                        Se precisar de mais informações para usar uma ferramenta, peça ao usuário."),
                
                MessagesPlaceholder("chat_history"), # Para manter o histórico da conversa
                ("user", "{input}"),
                MessagesPlaceholder("agent_scratchpad"), # Onde o agente coloca seus pensamentos e chamadas de ferramenta
            ]
        )

        # --- Criação e Execução do Agente ---
        agent = create_tool_calling_agent(self.llm_brain, tools_list, agent_prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools_list,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=10,
        )
        
        # --- 6. Interação com o Usuário ---
        print("--- Agente de IA de Consulta de Notas Fiscais ---")
        print("Olá! Sou o ZeroUm, agente especializado em notas fiscais.\nEstou pronto para responder perguntas sobre seus dados de notas fiscais.")
        print("Pergunte-me, por exemplo: 'Qual fornecedor teve o maior montante recebido?'")
        print("Digite 'sair' para encerrar.")

        while True:
            user_input = input("\nSua pergunta: ")
            if user_input.lower() == 'sair':
                print("Até logo!")
                break
            
            try:
                response = agent_executor.invoke({"input": user_input, "chat_history": []})
                print(f"\nAgente: {response['output']}")
                
            except Exception as e:
                print(f"Ocorreu um erro ao processar sua pergunta: {e}")
                print("Por favor, tente novamente.")
        

    def check(self) -> None:
        """Método de verificação do agente."""
        self.logger.info("Agent Tolive check started")
        self.logger.info(config.LLM_MODEL)
        self.logger.info(config.LLM_TEMPERATURE)
        
            
# --- 5. Definição de funcoes globais        
@handle_errors 
def _parser_user_input(arguments: list) -> list:
    """Parses arguments from command line."""
    all_files = []
    path_maker = lambda file: os.path.abspath(file)
    for intent in arguments:
        if os.path.isfile(intent):
            logger.info("Considering file: %s", intent)
            all_files.append(path_maker(intent))
        elif os.path.isdir(intent): # Usar 'elif' para garantir que não processe como arquivo E diretório
            logger.warning("Considering directory: %s", intent)
            for root, _, files in os.walk(intent): # _ para ignorar dirs, que não precisamos
                for file in files:
                    if file.endswith(".csv"):
                        all_files.append(path_maker(os.path.join(root, file)))
        else:
            logger.warning(f"Argumento ignorado (não é arquivo nem diretório): {intent}")
    return all_files

@handle_errors
def _load_files_nf(files) -> Dict[str, DataFrameType]: # Use DataFrameType
    """Loads files from the list of files provided, returning a dict of DataFrames."""
    dataframes: Dict[str, DataFrameType] = {}
    load_df = lambda file: pd.read_csv(file, header=0, index_col=None, sep=',', decimal='.',dtype=str)
    
    for file in files:
        if file.endswith("_NFs_Cabecalho.csv"):
            logger.info(f"Detected NFs Cabeçalho file: {file}")
            data = load_df(file)
                            
            # Conversão de tipos: use errors='coerce' para lidar com valores não numéricos
            data['VALOR NOTA FISCAL'] = pd.to_numeric(data['VALOR NOTA FISCAL'], errors='coerce')
            
            dataframes["header"] = data
            
        elif file.endswith("_NFs_Itens.csv"):
            logger.info(f"Detected NFs Itens file: {file}")
            data = load_df(file)
            
            # Conversão de tipos para Itens
            data['VALOR TOTAL'] = pd.to_numeric(data['VALOR TOTAL'], errors='coerce')
            data['VALOR UNITÁRIO'] = pd.to_numeric(data['VALOR UNITÁRIO'], errors='coerce')
            data['QUANTIDADE'] = pd.to_numeric(data['QUANTIDADE'], errors='coerce')
            
            # Preencher NaNs após conversão para numérico (se aplicável)
            data['VALOR TOTAL'] = data['VALOR TOTAL'].fillna(0)
            data['VALOR UNITÁRIO'] = data['VALOR UNITÁRIO'].fillna(0)
            data['QUANTIDADE'] = data['QUANTIDADE'].fillna(0) # Quantidade pode ser float se tiver decimal
            
            # Garanta que a CHAVE DE ACESSO seja string para merge/lookup
            data['CHAVE DE ACESSO'] = data['CHAVE DE ACESSO'].astype(str)
            
            dataframes["items"] = data
    return dataframes


if __name__ == "__main__":
    #configure_log("my_agent")
    configure_log("my_agent")
    
    #Caminho padrão da pasta onde estão os arquivos de notas fiscais
    default_folder = "NotasFiscais"

    logger.info("Starting agent application using default folder: NotasFiscais")
    
    #Carrega os arquivos de notas fiscais do diretório padrão
    files = _parser_user_input([default_folder])

    if not files:
        logger.error("Nenhum arquivo válido foi encontrado para processar. Encerrando.")
        sys.exit(1)

    logger.info(f"Using files: {files}")
   
    # Verifica se há XMLs e carrega usando o parse_nfe_xml
    xml_files = [f for f in files if f.lower().endswith(".xml")]
    csv_files = [f for f in files if f.lower().endswith(".csv")]

    if xml_files:
        logger.info(f"Lendo arquivo XML: {xml_files[0]}")
        header_df, items_df = parse_nfe_xml(xml_files[0])
        data = {"header": header_df, "items": items_df}

    elif csv_files:
        data = _load_files_nf(csv_files)

    else:
        logger.error("Nenhum arquivo XML ou CSV válido encontrado.")
        sys.exit(1)
    
    # --- Importação dos arquivos ---
    logger.info("Data loaded successfully.")
    logger.info("Running statistics...")
    for key, df in data.items():
        logger.info(f"--- Statistics for {key} ---")
        logger.info(df.info(verbose=True, show_counts=True, buf=sys.stdout))
        logger.info("--- df.describe numeric ---")
        logger.info("\n"+tabulate(df.describe().transpose(), headers='keys', tablefmt='psql'))
        logger.info("--- df.describe object ---")
        logger.info("\n"+tabulate(df.describe(include='object').transpose(), headers='keys', tablefmt='psql'))
        
    # Criar a instância do Agent
    agent_instance = AgentAI()
    logger.info(f"Agent instance created and data loaded.")
    agent_instance.agent_tolive()
    
    # ZONA DE TESTE DE FERRAMENTA
    # logger.info("Running agent tool tests...")
    # logger.info(suppliers_by_state())