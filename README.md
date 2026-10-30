# Matheus Kokoro TTS

Servidor de síntese de voz do **Matheus AI**, baseado no [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI) e preparado para execução em CPU no Render.

## Configuração

| Item | Valor |
|---|---|
| Host | `0.0.0.0` |
| Porta | `10000` |
| Dispositivo | CPU |
| Modelo | `kokoro` |
| Voz padrão | `pm_alex` |
| Player web | Desativado |

## Deploy no Render

1. Crie um **Web Service** usando este repositório.
2. Selecione **Docker** como ambiente de execução.
3. Use a porta interna `10000` (o Dockerfile já define `EXPOSE 10000`).
4. Faça o deploy e aguarde o carregamento inicial do modelo.

O serviço usa a imagem CPU oficial do Kokoro-FastAPI indicada no Dockerfile. Não é necessário configurar GPU.

## API

### Gerar áudio

`POST /v1/audio/speech`

Exemplo de corpo JSON:

```json
{
  "model": "kokoro",
  "input": "Olá! Esta é a voz do Matheus AI.",
  "voice": "pm_alex",
  "response_format": "mp3"
}
```

Exemplo com cURL:

```bash
curl -X POST "https://SEU-SERVICO.onrender.com/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -d '{"model":"kokoro","input":"Olá! Esta é a voz do Matheus AI.","voice":"pm_alex","response_format":"mp3"}' \
  --output matheus-ai.mp3
```

### Documentação interativa

Após o deploy, acesse:

`https://SEU-SERVICO.onrender.com/docs`

Substitua `SEU-SERVICO` pelo nome real do serviço no Render.

## Integração com o Matheus AI

Configure o backend do Matheus AI para enviar requisições HTTP ao serviço:

- Base URL: `https://SEU-SERVICO.onrender.com/v1`
- Endpoint: `/audio/speech`
- Model: `kokoro`
- Voice: `pm_alex`
- Formato recomendado: `mp3`

A URL do serviço deve ficar em uma variável de ambiente no backend, por exemplo `KOKORO_TTS_URL`. Não coloque segredos ou credenciais no frontend.

## Observações

- Este repositório contém a configuração do servidor; a integração no chat do Matheus AI é uma etapa separada.
- Em hospedagem gratuita, o primeiro pedido após um período sem uso pode demorar devido ao cold start e ao carregamento do modelo.
- A disponibilidade de vozes depende da imagem e da versão do Kokoro-FastAPI utilizadas.
