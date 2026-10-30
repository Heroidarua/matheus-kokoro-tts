# ADA-M Original Voice — Qwen3-TTS

Serviço separado para a identidade vocal original da ADA-M. A branch `main` (Piper) e a branch `test/kokoro-pm-alex` permanecem preservadas.

## Perfil vocal

- Nome interno: `ada-m-original-ptbr`
- Voz masculina adulta, registro médio-grave natural
- Estilo humano, conversacional, acolhedor e claro
- Idioma: português brasileiro
- Perfil definido por instrução fixa em `app.py`
- Sem gravação ou clonagem de uma pessoa real

## Como a identidade é mantida

1. Qwen3-TTS VoiceDesign cria uma amostra de referência a partir da descrição vocal e de um texto fixo.
2. O modelo VoiceDesign é descarregado da GPU.
3. Qwen3-TTS Base 0.6B cria um prompt de voz reutilizável a partir da amostra.
4. Todas as frases seguintes usam esse mesmo prompt, mantendo a identidade vocal consistente.

Esse fluxo segue o método oficial “Voice Design then Clone” do projeto Qwen3-TTS. É uma identidade sintética desenhada para a ADA-M, não uma voz humana exclusiva treinada do zero.

## Requisitos de implantação

**Não implantar no Render Free.** Este serviço exige GPU NVIDIA com CUDA e memória suficiente para carregar os modelos durante a inicialização. Use um host GPU e mantenha um volume persistente em `/data` para o cache Hugging Face.

Runtime: Docker com acesso à GPU NVIDIA.

Variáveis:
- `TTS_API_KEY`: chave Bearer opcional (recomendada em produção).
- `TTS_DEVICE`: padrão `cuda:0`.
- `VOICE_DESIGN_MODEL`: padrão `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign`.
- `VOICE_CLONE_MODEL`: padrão `Qwen/Qwen3-TTS-12Hz-0.6B-Base`.
- `HF_HOME`: padrão `/data/huggingface`.

A primeira inicialização baixa os pesos dos modelos e cria a referência vocal; pode demorar vários minutos.

## Endpoints

- `GET /health`
- `GET /`
- `POST /v1/audio/speech` — WAV
- `POST /v1/audio/speech/stream` — SSE com WAV em base64

O endpoint SSE mantém compatibilidade com o cliente ADA-M atual. Nesta primeira versão, cada evento contém o áudio da frase depois que a síntese daquela frase termina. O chat pode continuar gerando enquanto as frases são sintetizadas em sequência, mas a API Python de alto nível não entrega pacotes WAV decodificados em tempo real. Não considerar 97 ms como latência garantida do serviço completo.

## Teste

```bash
curl https://SEU-SERVICO/health
curl -X POST https://SEU-SERVICO/v1/audio/speech \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SUA_CHAVE" \
  -d '{"model":"ada-m-original","input":"Olá! Eu sou a ADA-M. Como posso ajudar?","voice":"ada-m-original-ptbr","response_format":"wav"}' \
  --output ada-m-voice.wav
```

## Licença e origem

O modelo Qwen3-TTS VoiceDesign é publicado no Hugging Face com licença Apache-2.0. Consulte o repositório oficial QwenLM/Qwen3-TTS para instruções, versões e condições dos artefatos de modelo.
