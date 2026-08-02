# baixaryoutube

Programa local (Windows) para baixar em lote o áudio (MP3) de vídeos do YouTube usando `yt-dlp` e `ffmpeg`.

## Requisitos

- Windows 10 ou 11 com acesso à internet.

Nada mais precisa ser instalado manualmente: o `run.bat` cuida de tudo (Python, yt-dlp e ffmpeg) na primeira execução.

## Como instalar e usar

1. No GitHub, clique em **Code → Download ZIP** e extraia o arquivo em qualquer pasta do seu computador.
2. Dentro da pasta extraída, dê duplo clique em **`run.bat`**.
   - Se o Python não estiver instalado, o script baixa e instala automaticamente. Nesse caso, ao final ele vai pedir para você **fechar a janela e rodar `run.bat` de novo** (necessário para o Windows reconhecer o Python recém-instalado).
   - Na execução seguinte, o script baixa `yt-dlp.exe`, `ffmpeg.exe` e `ffprobe.exe` sozinho para uma pasta `bin` dentro do programa (isso pode demorar alguns minutos, só na primeira vez).
   - Depois cria um ambiente virtual Python (`venv`), instala o Flask e abre o navegador em `http://127.0.0.1:5000`.
3. Cole até 10 links do YouTube na caixa de texto (um por linha).
4. Deixe marcada a opção "Ignorar playlist/rádio automática" para baixar só o vídeo do link, mesmo que ele tenha `&list=...` na URL. Desmarque apenas se quiser baixar a playlist inteira.
5. Clique em "Adicionar à fila" e depois em "Iniciar downloads".
6. Acompanhe o status de cada item (pendente / baixando / concluído / erro) — a lista atualiza sozinha a cada 2 segundos.
7. Para interromper, clique em "Cancelar" — o download atual é interrompido, os pendentes não são iniciados, mas os arquivos já concluídos permanecem na pasta.
8. Ao final, clique em "Abrir pasta" para ver os MP3s no Explorador de Arquivos.

Nas próximas vezes, basta dar duplo clique em `run.bat` — nada precisa ser baixado de novo.

## Usando uma instalação própria do yt-dlp/ffmpeg (opcional)

Se preferir usar uma instalação sua (ex: já tem `yt-dlp.exe` e `ffmpeg.exe` em outra pasta), abra a página, clique em **"Selecionar pasta..."** no topo, escolha essa pasta e clique em **"Salvar"**. Esse caminho substitui a pasta `bin` baixada automaticamente e fica lembrado nas próximas execuções (salvo em `config.json`).

## Onde os arquivos são salvos

Os MP3s são salvos em uma subpasta `downloads` dentro da pasta do yt-dlp em uso (por padrão, `bin\downloads`, dentro da pasta do programa). Essa pasta é criada automaticamente se não existir.

## Problemas comuns

- **"ERRO: não foi possível baixar..."** (Python, yt-dlp ou ffmpeg): verifique sua conexão com a internet e rode `run.bat` novamente.
- **"Configure a pasta do yt-dlp antes de iniciar"**: normalmente não acontece com a instalação automática; se aparecer, use "Selecionar pasta..." e "Salvar".
- **"Arquivos não encontrados na pasta configurada"**: confira se `yt-dlp.exe`, `ffmpeg.exe` e `ffprobe.exe` realmente estão na pasta indicada.
- **"Link inválido"**: o texto colado não é uma URL do YouTube.
- **"Vídeo indisponível/privado/removido"**: o yt-dlp não conseguiu acessar o vídeo (removido, privado, restrito por idade, etc).

## Estrutura do projeto

```
app.py               # servidor Flask + lógica de download
templates/index.html # página única
static/style.css     # estilos
static/app.js        # lógica do frontend (polling, fila, botões)
run.bat               # baixa Python/yt-dlp/ffmpeg se faltarem, cria venv e roda o app
requirements.txt      # dependências Python (Flask)
bin/                  # yt-dlp.exe, ffmpeg.exe, ffprobe.exe baixados automaticamente (criado no primeiro uso)
```

Uso pessoal, 100% local — sem banco de dados, sem hospedagem externa, sem autenticação.
