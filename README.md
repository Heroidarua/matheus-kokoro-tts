# Matheus Piper TTS

Serviço independente de síntese de voz para o **Matheus AI**, usando Piper TTS em CPU e a voz brasileira `pt_BR-faber-medium`.

Este repositório substitui a implementação anterior baseada em Kokoro-FastAPI. A integração com o backend principal do Matheus AI é uma etapa separada.

## Stack

- Python 3.11
- Piper TTS 1.8.0
- ONNX Runtime em CPU
- FastAPI + Uvicorn
- Voz: `pt_BR-faber-medium`
- Saída: WAV

## Deploy no Render

1. Crie um Web Service conectado a este repositório.
2. Selecione **Docker** como runtime.
3. Use a branch `main`.
4. Escolha inicialmente o plano Free.
5. Adicione a variável de ambiente `PIPER_API_KEY` com uma chave longa e aleatória.
6. Faça o deploy.

O Dockerfile baixa o modelo e o arquivo de configuração correspondente durante o build. O serviço escuta na porta definida pela variável `PORT` (Render fornece essa variável automaticamente).

### Limites do plano gratuito

O Render Free possui 512 MB de RAM e pode suspender serviços sem tráfego. Piper é uma alternativa mais leve que Kokoro, mas o consumo real desta imagem precisa ser confirmado nos logs e métricas do próprio Render. Se ocorrer encerramento por memória, não tente aumentar concorrência: será necessário reduzir dependências/modelo ou usar outro plano/host.

## Endpoints

### Health check

`GET /health`

Resposta esperada:

```json
{
  "status": "ok",
  "engine": "piper",
  "voice": "pt_BR-faber-medium"
}
```

### Gerar áudio

`POST /v1/audio/speech`

Cabeçalhos:

```
Content-Type: application/json
Authorization: Bearer SUA_CHAVE
```

Corpo:

```json
{
  "model": "piper",
  "input": "Olá! Esta é a voz do Matheus AI.",
  "voice": "pt_BR-faber-medium",
  "response_format": "wav"
}
```

Exemplo cURL:

```bash
curl -X POST "https://SEU-SERVICO.onrender.com/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SUA_CHAVE" \
  -d '{"model":"piper","input":"Olá! Esta é a voz do Matheus AI.","voice":"pt_BR-faber-medium","response_format":"wav"}' \
  --output teste.wav
```

A documentação interativa fica em `/docs`.

## Variáveis de ambiente

| Nome | Obrigatória | Descrição |
|---|---|---|
| `PORT` | Não | Porta HTTP; padrão 10000 |
| `PIPER_API_KEY` | Recomendada | Token Bearer para proteger a geração |
| `PIPER_MODEL_PATH` | Não | Caminho do arquivo ONNX |

Não coloque a chave no frontend nem no GitHub. Guarde-a somente nas variáveis de ambiente do Render e do backend do Matheus AI.

## Observações

- O endpoint aceita textos de até 4.000 caracteres por solicitação.
- Por segurança de memória e estabilidade, a síntese é serializada (uma requisição de áudio por vez).
- A implementação retorna WAV; MP3 ainda não está habilitado.
- O modelo ONNX e seu arquivo `.onnx.json` correspondente são necessários.
- O motor Piper é distribuído sob GPL-3.0-or-later. Verifique as obrigações da licença antes de distribuir uma versão modificada ou incorporá-la a uma oferta comercial.
