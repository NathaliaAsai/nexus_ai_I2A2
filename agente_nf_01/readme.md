# Documentação do Agente de Análise de Notas Fiscais

Este documento detalha o script Python que implementa um agente de IA especializado em análise de dados de notas fiscais. O agente é construído utilizando a biblioteca `langchain` e o modelo `ChatGoogleGenerativeAI` para processar consultas em linguagem natural e fornecer insights sobre os dados carregados de arquivos CSV.

------

## Visão Geral do Projeto

O objetivo principal deste script é criar um **Agente de IA** interativo capaz de responder a perguntas sobre dados de notas fiscais (cabeçalho e itens). Ele utiliza ferramentas predefinidas para analisar informações como fornecedores, valores e quantidades de itens. Além disso, o script inclui um sistema de log e tratamento de erros para garantir a estabilidade e rastreabilidade das operações.

### Funcionalidades Principais

- **Carga de Dados Flexível**: Suporta o carregamento de arquivos CSV de cabeçalho (`_NFs_Cabecalho.csv`) e itens (`_NFs_Itens.csv`) de notas fiscais, seja por arquivo individual ou diretório.

- **Tratamento de Erros Abrangente**: Implementa um decorador de erro (`@handle_errors`) para gerenciar exceções comuns, como `FileNotFoundError`, `PermissionError` e `ValueError`, garantindo um desligamento gracioso.

- **Logging Detalhado**: Configura um sistema de log para registrar eventos, informações e erros tanto em arquivo quanto no console, auxiliando na depuração e monitoramento.

- **Agente de IA com Ferramentas**: Utiliza `langchain` para criar um agente que pode invocar ferramentas específicas para responder a perguntas sobre os dados.

- Ferramentas de Análise de Dados

  Oferece ferramentas para identificar:

  - O maior e o menor fornecedor em valor.
  - Top X maiores e menores fornecedores em valor.
  - Fornecedores agrupados por UF.
  - Itens com maior e menor volume entregue (quantidade).
  - Itens com maior e menor valor total (custo).

- **Interação com o Usuário**: Permite que o usuário faça perguntas em linguagem natural e recebe respostas geradas pelo agente.

---

### Descrição do Script de Extração de Arquivos ZIP

Este script Python foi projetado para **extrair o conteúdo de arquivos ZIP** para um diretório especificado. Ele é construído para ser robusto, incorporando um sistema de log detalhado e tratamento de erros para garantir uma operação confiável.

As principais características e componentes do script incluem:

- **Configuração de Log**: Utiliza a biblioteca `logging` para configurar um sistema de log que registra mensagens informativas e de erro tanto em um arquivo de log (`.log`) quanto no console (stdout). Isso facilita a depuração e o monitoramento das operações do script.

- **Tratamento de Erros**: Possui um decorador `@handle_errors` que encapsula métodos da classe `Extractor`, capturando e gerenciando exceções comuns como `FileNotFoundError`, `PermissionError`, e `ValueError`, além de outras exceções genéricas. Em caso de erro, uma mensagem é logada e o script é encerrado graciosamente.

- Classe `Extractor`

  :

  - **Inicialização (`__init__`)**: Configura o logger específico para a classe e define o diretório de saída. Se o diretório de saída não existir, um aviso é logado e um caminho padrão é sugerido.
  - **Verificação de Arquivo (`_check_file`)**: Um método interno que valida se o caminho de arquivo fornecido existe e se o arquivo tem a extensão `.zip`.
  - **Carregamento e Extração (`load_file`)**: Este é o método principal que recebe o caminho de um arquivo ZIP. Ele primeiro verifica a validade do arquivo usando `_check_file` e, se válido, utiliza a biblioteca `zipfile` para extrair todo o conteúdo do arquivo ZIP para o `output_dir` configurado.

- Interface de Linha de Comando

  : O script pode ser executado diretamente do terminal, aceitando dois argumentos obrigatórios:

  - `-f` ou `--file`: O caminho para o arquivo ZIP a ser extraído.
  - `-o` ou `--output`: O caminho para o diretório onde os arquivos serão extraídos.

------

## Estrutura do Código

O script é organizado em seções lógicas para facilitar a compreensão e manutenção.

### 1. Definição de Variáveis Globais

- `DataFrameType = NewType('DataFrameType', pd.DataFrame)`: Define um tipo personalizado para `pd.DataFrame` para anotação de tipo, melhorando a legibilidade e a verificação de tipo.

### 2. Definição das Funções de Tratamento de Erros e Formato de Log

- ```
  configure_log(file_prefix, log_dir="logs", timestamp=datetime.today().strftime('%y%m%d'))
  ```

  - **Propósito**: Configura o sistema de log para escrever logs em um arquivo e no console (stdout).
  - Detalhes
    - Cria um diretório `logs` se ele não existir.
    - Define o nome do arquivo de log com um prefixo e timestamp.
    - Configura o formato da mensagem de log e a formatação da data.
    - Adiciona um `StreamHandler` para exibir logs no console.
    - Define um `logger` global para uso em todo o script.

- ```
  handle_errors(func)
  ```

  - **Propósito**: Um decorador Python para capturar e lidar com exceções comuns que podem ocorrer dentro de métodos ou funções.
  - Detalhes
    - Envolve a função original (`func`) em um bloco `try-except`.
    - Captura `FileNotFoundError`, `PermissionError`, `ValueError` e `Exception` genéricas.
    - Registra a mensagem de erro usando o logger e encerra o programa (`sys.exit(1)`) em caso de erro.
    - É crucial que o primeiro argumento da função decorada seja `self` (a instância da classe), pois o decorador tenta acessar `instance.logger`.

### 3. Definição das Ferramentas (Tools)

As ferramentas são funções decoradas com `@tool` da `langchain.tools`, permitindo que o agente as invoque com base nas perguntas do usuário. Cada ferramenta tem uma docstring detalhada que descreve seu propósito, argumentos e valor de retorno.

- ```
  test_ai_agent() -> str
  ```

  - **Propósito**: Retorna uma string simples confirmando que o agente está operacional.
  - **Uso**: Útil para testar a funcionalidade básica do agente ("Executar teste", "Testar agente").

- ```
  obtain_bigger_supplier() -> str
  ```

  - **Propósito**: Identifica o fornecedor com o maior montante total de notas fiscais.
  - **Uso**: Responde a perguntas como "Qual fornecedor teve o maior montante?".
  - **Dependência**: Requer que os dados do cabeçalho (`data['header']`) estejam carregados.

- ```
  obtain_smaller_supplier() -> str
  ```

  - **Propósito**: Identifica o fornecedor com o menor montante total de notas fiscais.
  - **Uso**: Responde a perguntas como "Qual fornecedor teve o menor montante?".
  - **Dependência**: Requer que os dados do cabeçalho (`data['header']`) estejam carregados.

- ```
  top_x_bigger_suppliers(num_input: int) -> str
  ```

  - **Propósito**: Lista os `X` fornecedores com o maior montante total.
  - **Uso**: Responde a perguntas como "Quais foram os 5 maiores fornecedores?".
  - Argumentos
    - `num_input (int)`: O número de fornecedores a serem listados.
  - **Dependência**: Requer que os dados do cabeçalho (`data['header']`) estejam carregados.

- ```
  top_x_smaller_suppliers(num_input: int) -> str
  ```

  - **Propósito**: Lista os `X` fornecedores com o menor montante total.
  - **Uso**: Responde a perguntas como "Quais foram os 5 menores fornecedores?".
  - Argumentos
    - `num_input (int)`: O número de fornecedores a serem listados.
  - **Dependência**: Requer que os dados do cabeçalho (`data['header']`) estejam carregados.

- ```
  suppliers_by_state() -> str
  ```

  - **Propósito**: Agrupa os fornecedores por Unidade Federativa (UF) e retorna a contagem de notas fiscais por estado.
  - **Uso**: Responde a perguntas como "Liste os fornecedores por UF".
  - **Dependência**: Requer que os dados do cabeçalho (`data['header']`) estejam carregados.

- ```
  delivery_item(num_input: int, type_consult:str) -> str
  ```

  - **Propósito**: Identifica itens com base na quantidade entregue (maior ou menor).
  - **Uso**: Responde a perguntas como "Qual o item mais vendido?" ou "Quais foram os 3 itens menos entregues?".
  - Argumentos
    - `num_input (int)`: (Opcional) O número de itens a serem considerados (padrão é 1 se `num_input <= 0`).
    - `type_consult (str)`: (Obrigatório) Define o tipo de consulta ('top', 'maior', 'menor', 'mais', 'menos').
  - **Dependência**: Requer que os dados dos itens (`data['items']`) estejam carregados.

- ```
  delivery_item_value(num_input: int, type_consult:str) -> str
  ```

  - **Propósito**: Identifica itens com base no valor total vendido (maior ou menor).
  - **Uso**: Responde a perguntas como "Qual o item mais caro vendido?" ou "Quais foram os 2 itens com menor valor vendido?".
  - Argumentos
    - `num_input (int)`: (Opcional) O número de itens a serem considerados (padrão é 1 se `num_input <= 0`).
    - `type_consult (str)`: (Obrigatório) Define o tipo de consulta ('top', 'maior', 'menor', 'mais', 'menos').
  - **Dependência**: Requer que os dados dos itens (`data['items']`) estejam carregados.

### 4. Definição da Classe Principal (`AgentAI`)

- ```
  class AgentAI
  ```

  - **Propósito**: Encapsula a lógica principal do agente de IA.

  - ```
    __init__(self)
    ```

    - Inicializa o logger para a classe.
    - Define uma função lambda `tabulateAgent` para formatar DataFrames para exibição.
    - Configura o modelo de linguagem (`self.llm_brain`) usando `ChatGoogleGenerativeAI` com base nas configurações em `config.py`.

  - ```
    agent_tolive(self) -> None
    ```

    - **Propósito**: Método principal que define, configura e executa o loop de interação do agente.
    - Detalhes
      - Cria uma lista de todas as ferramentas disponíveis.
      - Define o `agent_prompt` usando `ChatPromptTemplate` para instruir o modelo e incluir placeholders para histórico de chat (`chat_history`) e rascunho do agente (`agent_scratchpad`).
      - Cria o `agent` usando `create_tool_calling_agent`, que é adequado para modelos que suportam "tool calling".
      - Cria o `AgentExecutor` para gerenciar a execução do agente, ferramentas e histórico.
      - Inicia um loop infinito para interação com o usuário, onde as perguntas são processadas e as respostas são fornecidas.
      - Permite que o usuário digite 'sair' para encerrar.

  - ```
    check(self) -> None
    ```

    - **Propósito**: Um método auxiliar para verificar as configurações do agente.

### 5. Definição de Funções Globais

- ```
  _parser_user_input(arguments: list) -> list
  ```

  - **Propósito**: Analisa os argumentos da linha de comando, identificando arquivos CSV em caminhos fornecidos (arquivos individuais ou diretórios).
  - Detalhes
    - Usa `@handle_errors` para tratamento de exceções.
    - Verifica se o argumento é um arquivo ou diretório.
    - Se for um diretório, percorre-o em busca de arquivos `.csv`.
    - Retorna uma lista de caminhos absolutos para os arquivos CSV encontrados.

- ```
  _load_files_nf(files) -> Dict[str, DataFrameType]
  ```

  - **Propósito**: Carrega os arquivos CSV identificados em DataFrames pandas, realizando conversões de tipo necessárias.
  - Detalhes
    - Usa `@handle_errors` para tratamento de exceções.
    - Identifica arquivos de cabeçalho (`_NFs_Cabecalho.csv`) e de itens (`_NFs_Itens.csv`).
    - Carrega os dados usando `pd.read_csv`.
    - Converte colunas numéricas para o tipo apropriado, usando `errors='coerce'` para lidar com valores inválidos e `fillna(0)` para preencher NaNs.
    - Armazena os DataFrames em um dicionário (`dataframes`) com chaves "header" e "items".

### 6. Bloco de Execução Principal (`if __name__ == "__main__":`)

- **Propósito**: Ponto de entrada do script quando executado diretamente.
- Detalhes
  - Chama `configure_log` para iniciar o sistema de log.
  - Configura o `ArgumentParser` para aceitar argumentos de linha de comando, especificamente o `-f` ou `--files` para fornecer os caminhos dos arquivos/diretórios.
  - Analisa os argumentos do usuário com `_parser_user_input`.
  - Carrega os dados das notas fiscais com `_load_files_nf`.
  - Registra estatísticas básicas dos DataFrames carregados (info, describe).
  - Cria uma instância de `AgentAI`.
  - Chama `agent_instance.agent_tolive()` para iniciar a interação com o agente.

------

## Como Implementar e Executar

Siga os passos abaixo para configurar e executar o agente de IA:

### 1. Pré-requisitos

Certifique-se de ter o Python 3.x instalado. Você precisará instalar as seguintes bibliotecas:

```
pip install -r requirements.txt
```

### 2. Configuração da Chave API

Crie um arquivo chamado `config.py` no mesmo diretório do script principal. Este arquivo deve conter sua chave de API do Google Gemini e as configurações do modelo:

Python

```
# config.py

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LLM_MODEL = "gemini-1.5-flash" # Ou outro modelo compatível
LLM_TEMPERATURE = 0.2
```

### 3. Preparação dos Dados

O script espera arquivos CSV com os seguintes padrões de nome:

- **Cabeçalho das Notas Fiscais**: O nome do arquivo deve terminar com `_NFs_Cabecalho.csv`. As colunas esperadas incluem `'RAZÃO SOCIAL EMITENTE'`, `'VALOR NOTA FISCAL'`, `'UF EMITENTE'`, e `'CHAVE DE ACESSO'`.
- **Itens das Notas Fiscais**: O nome do arquivo deve terminar com `_NFs_Itens.csv`. As colunas esperadas incluem `'DESCRIÇÃO DO PRODUTO/SERVIÇO'`, `'QUANTIDADE'`, `'VALOR TOTAL'`, `'VALOR UNITÁRIO'`, e `'CHAVE DE ACESSO'`.

**Exemplo de estrutura de diretório:**

```
seu_projeto/
├── agentV1.py
├── config.py
├── logs/
└── data/
    ├── minhas_nfs_Cabecalho.csv
    └── minhas_nfs_Itens.csv
```

### 4. Execução do Script

Execute o script a partir da linha de comando, fornecendo os caminhos para seus arquivos CSV:

```
python agentV1.py -f data/minhas_nfs_Cabecalho.csv data/minhas_nfs_Itens.csv
```

Ou, se seus arquivos estiverem em um diretório, você pode fornecer o caminho do diretório:

```
python agentV1.py.py -f data/
```

O script irá carregar os dados, exibir algumas estatísticas e iniciar a interação com o agente.

### 5. Interagindo com o Agente

Uma vez que o agente inicia, você verá um prompt. Digite suas perguntas e o agente tentará responder usando as ferramentas disponíveis.

**Exemplos de perguntas:**

- `Qual fornecedor teve o maior montante recebido?`
- `Liste os 3 maiores fornecedores.`
- `Quais foram os fornecedores por UF?`
- `Qual o item mais vendido?`
- `Quais foram os 5 itens mais caros vendidos?`
- `Testar agente`
- `Sair` (para encerrar a conversa)

------