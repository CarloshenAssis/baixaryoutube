# baixaryoutube

Programa local (Windows) para baixar em lote o áudio (MP3) de vídeos do YouTube usando `yt-dlp` e `ffmpeg`.

## Requisitos

- Windows
- Python 3.9+ instalado (com `python` disponível no PATH)
- `yt-dlp.exe`, `ffmpeg.exe`, `ffprobe.exe` e `ffplay.exe` já presentes em:
  `C:\Users\carlo\OneDrive\Área de Trabalho\yt-dlp`

Se o caminho do yt-dlp for diferente no seu computador, edite a variável `YTDLP_DIR` no início do arquivo `app.py`.

## Como usar

1. Dê duplo clique em `run.bat`.
   - Na primeira execução ele cria um ambiente virtual Python (`venv`) e instala o Flask automaticamente.
   - Em seguida abre o navegador em `http://127.0.0.1:5000`.
2. Cole até 10 links do YouTube na caixa de texto (um por linha).
3. Deixe marcada a opção "Ignorar playlist/rádio automática" para baixar só o vídeo do link, mesmo que ele tenha `&list=...` na URL. Desmarque apenas se quiser baixar a playlist inteira.
4. Clique em "Adicionar à fila" e depois em "Iniciar downloads".
5. Acompanhe o status de cada item (pendente / baixando / concluído / erro) — a lista atualiza sozinha a cada 2 segundos.
6. Para interromper, clique em "Cancelar" — o download atual é interrompido, os pendentes não são iniciados, mas os arquivos já concluídos permanecem na pasta.
7. Ao final, clique em "Abrir pasta" para ver os MP3s no Explorador de Arquivos.

## Onde os arquivos são salvos

Os MP3s são salvos em:
`C:\Users\carlo\OneDrive\Área de Trabalho\yt-dlp\downloads`

Essa pasta é criada automaticamente se não existir.

## Problemas comuns

- **"Arquivos não encontrados na pasta configurada"**: confira se `yt-dlp.exe`, `ffmpeg.exe` e `ffprobe.exe` realmente estão na pasta indicada.
- **"Link inválido"**: o texto colado não é uma URL do YouTube.
- **"Vídeo indisponível/privado/removido"**: o yt-dlp não conseguiu acessar o vídeo (removido, privado, restrito por idade, etc).

## Estrutura do projeto

```
app.py               # servidor Flask + lógica de download
templates/index.html # página única
static/style.css     # estilos
static/app.js        # lógica do frontend (polling, fila, botões)
run.bat               # cria venv, instala dependências e roda o app
requirements.txt      # dependências Python (Flask)
```

Uso pessoal, 100% local — sem banco de dados, sem hospedagem externa, sem autenticação.
