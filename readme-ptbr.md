# Local Translator Studio

**Tradução de textos com privacidade, executada no seu próprio computador.**

[English](README.md) · [Instalação](#instalação) · [Gerenciar-idiomas](#gerenciar-idiomas) · [Capturas](#capturas-de-tela) · [API](#api-local)

O Local Translator Studio é um aplicativo Python com interface web em inglês, tradução automática, temas claro/escuro e API HTTP local. A inferência usa diretamente modelos CTranslate2 na CPU, com tokenizadores SentencePiece ou BPE. Após a instalação dos modelos, a tradução funciona offline.

**Versão 2.2.0** · Python 3.10–3.12 x64 · Windows / Linux · AGPL-3.0

![Página de tradução no tema claro](docs/screenshots/translate-light.png)

## Funcionalidades

- Tradução automática após 600 ms de pausa na digitação, incluindo colagem, troca de idioma e composição de caracteres por IME.
- Detecção do idioma de origem e inglês como destino padrão, com possibilidade de alteração.
- Inglês como ponte entre dois outros idiomas e exibição opcional do texto intermediário.
- Gerenciamento pela web: pesquisa, instalação, reparo, remoção, progresso e registro da operação.
- Comandos equivalentes para Windows CMD e terminal Linux.
- Temas claro/escuro persistentes e páginas responsivas em inglês.
- Processamento local, sem chave de API e sem cota diária de tradução.
- Endpoint de textos compatível com o [Hybrid Translator](https://github.com/marcusbsilva/Hybrid-web-translator).

## Instalação

Instale **Python 3.10, 3.11 ou 3.12 de 64 bits**. Não é necessário Docker, GPU ou PowerShell.

### Windows — CMD

Abra o CMD na pasta do aplicativo e execute:

```bat
start.bat
```

### Linux — terminal

Instale Python e o pacote `venv` correspondente. Na pasta do aplicativo, execute:

```sh
bash start.sh
```

Acesse **http://localhost:5000**. A primeira inicialização cria a `.venv`, instala as dependências e baixa os modelos ausentes. Mantenha o terminal aberto; Ctrl+C encerra o servidor. A instalação e novos downloads exigem internet; os idiomas instalados funcionam offline.

No ZIP da versão Tools, a pasta do aplicativo é `Tools/LocalTranslator`. Em um repositório independente, é a raiz do projeto.

Se a porta estiver ocupada, use `start.bat --port 5001` ou `bash start.sh --port 5001` e abra http://localhost:5001.

## Gerenciar idiomas

### Pela página web

Acesse **[Models](http://localhost:5000/models)**:

1. Pesquise pelo nome ou código do idioma.
2. Clique em **Install** para baixar e validar os dois sentidos de tradução, ou em **Repair** para reparar modelos ausentes de um idioma configurado.
3. Acompanhe o progresso, os bytes transferidos e o registro da operação. Mantenha o servidor funcionando até a conclusão.
4. Clique em **Remove** e confirme no diálogo para excluir os dois modelos e os arquivos de download daquele idioma. **Cancel** preserva a coleção.

Após a conclusão, o servidor reconhece a alteração imediatamente. Reabra ou atualize uma aba Translate já aberta para renovar os seletores de idioma. A página Models se atualiza automaticamente, sem reiniciar o servidor. Idiomas padrão removidos não são reinstalados na próxima inicialização. **O inglês é obrigatório**, pois conecta os demais idiomas.

Apenas uma operação de modelos funciona por vez. A remoção aguarda traduções em andamento antes de descarregar os modelos. Um par adicional com falha não é habilitado; instalações bem-sucedidas são preservadas. **Refresh catalogue** consulta a lista oficial mais recente.

### Windows — CMD

Encerre o servidor antes de gerenciar os modelos por outro terminal. Na pasta do aplicativo:

```bat
start.bat --list-languages
start.bat --install-languages de it ko
start.bat --remove-languages de it
start.bat --install-all-languages
start.bat --list-languages --refresh-catalog
start.bat --setup-only
start.bat
```

### Linux — terminal

```sh
bash start.sh --list-languages
bash start.sh --install-languages de it ko
bash start.sh --remove-languages de it
bash start.sh --install-all-languages
bash start.sh --list-languages --refresh-catalog
bash start.sh --setup-only
bash start.sh
```

`de it ko` adiciona alemão, italiano e coreano. Substitua pelos códigos listados e separe vários códigos por espaços. Os comandos de gerenciamento encerram após a conclusão. `--setup-only` repara a coleção configurada sem iniciar o servidor e respeita exclusões intencionais. `--skip-install` inicia um ambiente já configurado. As mesmas opções estão disponíveis com `python run.py`.

Instalar todo o catálogo pode consumir vários GB e bastante tempo. A compatibilidade de cada arquivo é validada durante a instalação; nem todos os idiomas adicionais foram testados neste projeto. Repita uma operação interrompida para aproveitar downloads concluídos. A instalação preserva outros idiomas; a remoção exclui também os downloads armazenados do idioma selecionado.

## Cobertura de idiomas

A instalação padrão possui **18 modelos / 10 idiomas incluindo inglês**:

| Idioma | Código da API | Idioma | Código da API |
|---|---|---|---|
| Inglês | `en` | Russo | `ru` |
| Chinês simplificado | `zh-Hans` | Português | `pt` |
| Chinês tradicional | `zh-Hant` | Espanhol | `es` |
| Vietnamita | `vi` | Francês | `fr` |
| Tailandês | `th` | Japonês | `ja` |

O catálogo oficial incluído, consultado em 04/10/2026, lista **49 pares bidirecionais de idiomas com inglês**. São oferecidos apenas idiomas com modelos nos dois sentidos. Há opções como alemão, italiano, coreano, árabe, hindi, ucraniano e português brasileiro separado (`pb`). Consulte Models ou o comando de listagem para ver o catálogo atual.

Os aliases `zh`, `zt`, `zh-CN`, `zh-TW`, `pt-BR` e `ptbr` mantêm compatibilidade com os modelos originais. `pt-BR` continua apontando para o modelo genérico `pt`; selecione `pb` explicitamente para o modelo brasileiro adicional. A detecção automática pode ser ambígua em textos curtos ou idiomas que compartilham caracteres; escolha a origem manualmente quando necessário.

A qualidade varia entre modelos. A passagem pelo inglês pode acumular erros, e um teste de carregamento bem-sucedido não comprova a precisão linguística.

## Capturas de tela

Capturas reais do aplicativo em execução. Todas as páginas permanecem em inglês; os dois temas estão incluídos.

| Página | Finalidade | Claro | Escuro |
|---|---|---|---|
| Translate | Tradução automática | [Ver](docs/screenshots/translate-light.png) | [Ver](docs/screenshots/translate-dark.png) |
| Models | Instalar, reparar e remover idiomas | [Ver](docs/screenshots/models-light.png) | [Ver](docs/screenshots/models-dark.png) |
| API Guide | Documentação e teste de requisições | [Ver](docs/screenshots/api-guide-light.png) | [Ver](docs/screenshots/api-guide-dark.png) |
| About | Motor, privacidade e integração | [Ver](docs/screenshots/about-light.png) | [Ver](docs/screenshots/about-dark.png) |
| Licenses | Créditos de terceiros | [Ver](docs/screenshots/licenses-light.png) | [Ver](docs/screenshots/licenses-dark.png) |
| Página de erro | Mensagens de erro em inglês | [Ver](docs/screenshots/error-light.png) | [Ver](docs/screenshots/error-dark.png) |

<details>
<summary>Ver todas as páginas</summary>

### Models
![Gerenciador de idiomas](docs/screenshots/models-light.png)

### API Guide
![Documentação e teste da API](docs/screenshots/api-guide-light.png)

### About
![Sobre o aplicativo](docs/screenshots/about-light.png)

### Licenses
![Créditos e licenças](docs/screenshots/licenses-light.png)

### Página de erro
![Página de erro em inglês](docs/screenshots/error-light.png)

### Tradução no tema escuro
![Tradução no tema escuro](docs/screenshots/translate-dark.png)

</details>

## API local

O servidor escuta em `127.0.0.1`. A tradução não exige chave de API.

| Endpoint | Método | Finalidade |
|---|---|---|
| `/translate` | POST | Traduzir um texto ou uma lista JSON |
| `/detect` | POST | Detectar um idioma de origem configurado |
| `/languages` | GET | Listar idiomas configurados e destinos |
| `/health` | GET | Verificar servidor e disponibilidade dos modelos |
| `/studio/status` | GET | Consultar modelos instalados/ausentes e limites |
| `/frontend/settings` | GET | Consultar padrões e limites por requisição |

```python
import json
from urllib.request import Request, urlopen

request = Request(
    "http://localhost:5000/translate",
    data=json.dumps({"q": "Bonjour tout le monde", "source": "auto", "target": "en"}).encode(),
    headers={"Content-Type": "application/json"},
)
with urlopen(request) as response:
    print(json.load(response)["translatedText"])
```

A API aceita texto simples, até 30 itens e 64.000 caracteres somados por requisição, com corpo máximo de 1 MiB. Listas JSON retornam listas de traduções; campos de formulário também são aceitos. Tradução de HTML/arquivos não está implementada. Consulte `/docs` para exemplos e o testador local.

No [Hybrid Translator](https://github.com/marcusbsilva/Hybrid-web-translator), configure um provedor que aceite um endpoint local `/translate` com endereço `http://localhost:5000`. Ative o fallback manualmente na extensão quando quiser usá-lo. Este aplicativo não altera dicionários nem preferências da extensão.

Os endpoints de gerenciamento foram feitos para a página local Models. Alterações exigem o token atual da página e requisições da mesma origem; o CORS da API de tradução não autoriza essas operações.

## Arquitetura e dependências

| Camada | Implementação |
|---|---|
| Inicialização | Python, venv isolada, BAT / shell |
| Serviço HTTP | Flask e Waitress, somente localhost |
| Tradução neural | CTranslate2 na CPU; cache de até três modelos |
| Tokenização | SentencePiece ou BPE com subword-nmt e sacremoses |
| Detecção de idioma | langdetect com pistas por caracteres |
| Interface | Templates Jinja, CSS local e JavaScript puro |
| Operações de modelos | Worker em segundo plano, bloqueio entre processos e gravação atômica |

As versões estão fixadas em `requirements.txt`. Fontes e arquivos locais dispensam CDNs externos. O texto é processado localmente e não é salvo pelo aplicativo. Instalações e atualizações explícitas do catálogo usam a internet.

Os downloads padrão usam hashes SHA-256 incluídos. Modelos adicionais sem hash incluído registram o hash do primeiro download HTTPS oficial para conferir cópias posteriores; esse registro local não é uma verificação independente do publicador. As licenças dos modelos/tokenizadores são preservadas. Origem do catálogo: [índice de modelos Argos](https://github.com/argosopentech/argospm-index).

Reserve vários GB para modelos, arquivos baixados e dependências; idiomas adicionais exigem mais espaço. 8 GB de RAM são um ponto de partida prático, não um mínimo universal. GPU não é necessária.

## Licença e créditos

Código e interface: [AGPL-3.0](LICENSE). Modelos, dependências e fontes mantêm suas próprias licenças; consulte [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md), `model-notices` e `web/fonts`. O rodapé oferece um ZIP do código sem modelos locais nem ambientes.

Preparado para o portfólio de desenvolvimento de Marcus Silva. Projeto relacionado: [Hybrid Translator](https://github.com/marcusbsilva/Hybrid-web-translator).
