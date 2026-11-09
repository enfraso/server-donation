# Server Donation Dashboard

Painel simples para exibir custos estimados do servidor, utilização de recursos e doação via Pix.

## O que mostra
- CPU, RAM, disco e tempo ligado.
- Energia estimada: potência média configurada × tempo ligado × tarifa por kWh.
- Tráfego acumulado recebido + enviado. O contador é persistido em SQLite e continua após reinicializações.
- Custo estimado de tráfego: GB acumulados × (mensalidade da internet ÷ franquia configurada).
- Depreciação linear: valor de reposição do hardware ÷ vida útil em meses, proporcional ao tempo ligado.
- QR Code Pix com valor editável e botão para copiar o código Pix.

## Instalação no Debian 13

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
sudo mkdir -p /opt/server-donation
sudo cp -a . /opt/server-donation/
sudo useradd --system --home /opt/server-donation --shell /usr/sbin/nologin serverdonation
sudo chown -R serverdonation:serverdonation /opt/server-donation
cd /opt/server-donation
sudo -u serverdonation python3 -m venv venv
sudo -u serverdonation ./venv/bin/pip install -r requirements.txt
sudo cp systemd/server-donation.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now server-donation
```

A aplicação escuta em `127.0.0.1:8787`? Por padrão escuta em `0.0.0.0:8787`; mantenha a porta bloqueada externamente e publique via Caddy.

## Caddy

Adicione o conteúdo de `Caddyfile.example` ao seu Caddyfile, trocando o domínio. Depois:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

## Ajustar os valores

Edite `/opt/server-donation/config.json`:

- `electricity_brl_kwh`: tarifa total de energia em R$/kWh (consulte sua conta).
- `average_power_watts`: potência média real/estimada do servidor em watts. Idealmente meça com wattímetro.
- `internet_monthly_brl`: valor mensal do plano.
- `internet_allowance_gb`: franquia mensal usada para rateio. Se o plano for ilimitado, defina uma franquia de referência e deixe claro que é rateio estimado, não cobrança marginal da operadora.
- `hardware_value_brl`: valor de reposição/compra do conjunto de hardware.
- `hardware_lifetime_months`: vida útil estimada em meses.
- `pix_key`: chave Pix.
- `pix_receiver` e `pix_city`: nome e cidade exibidos no payload Pix. Ajuste para os dados corretos do titular/conta antes de divulgar o QR Code.

Reinicie após editar: `sudo systemctl restart server-donation`.

## Importante sobre os números

Os valores não são uma medição fiscal ou de concessionária. O consumo elétrico é estimado por potência média configurada; para precisão, use wattímetro. O custo de internet é uma alocação proporcional da mensalidade pelo tráfego acumulado, não necessariamente um custo adicional cobrado pelo provedor. A depreciação é uma estimativa linear de desgaste/desvalorização, não uma avaliação contábil. O contador de tráfego começa em zero quando o banco SQLite é criado; tráfego anterior não é recuperado.

## Segurança e privacidade

Não exponha a porta 8787 diretamente à internet. Use HTTPS no Caddy. O painel não tem autenticação porque foi pensado como página pública de transparência; não inclua informações privadas nem métricas sensíveis adicionais.
