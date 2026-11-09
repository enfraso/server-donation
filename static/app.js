let currentConfig = null;
const brl = n => Number(n || 0).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
function crc16(str){let crc=0xFFFF;for(let i=0;i<str.length;i++){crc^=str.charCodeAt(i)<<8;for(let j=0;j<8;j++)crc=(crc&0x8000)?((crc<<1)^0x1021):(crc<<1);crc&=0xFFFF;}return crc.toString(16).toUpperCase().padStart(4,'0');}
function field(id,value){return id+String(value.length).padStart(2,'0')+value;}
function pixPayload(amount){
 const c=currentConfig, key=c.pix_key, name=(c.pix_receiver||'DOACAO SERVIDOR').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase().slice(0,25), city=(c.pix_city||'BRASILIA').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase().slice(0,15);
 const mai=field('00','br.gov.bcb.pix')+field('01',key);
 let payload=field('00','01')+field('26',mai)+field('52','0000')+field('53','986')+field('54',Number(amount).toFixed(2))+field('58','BR')+field('59',name)+field('60',city)+field('62',field('05','***'))+'6304';
 return payload+crc16(payload);
}
function renderQr(){if(!currentConfig)return;const amount=Math.max(1,Number(document.getElementById('amount').value)||1);const el=document.getElementById('qrcode');el.innerHTML='';new QRCode(el,{text:pixPayload(amount),width:180,height:180,correctLevel:QRCode.CorrectLevel.M});}
function setMeter(id,bar,val){document.getElementById(id).textContent=val.toFixed(1)+'%';document.getElementById(bar).style.width=Math.min(100,Math.max(0,val))+'%';}
function duration(s){let d=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60);return `${d}d ${h}h ${m}min`;}
async function refresh(){
 try{
  const r=await fetch('/api/status',{cache:'no-store'});if(!r.ok)throw new Error('API indisponível');const d=await r.json();currentConfig=d.config;
  document.getElementById('serverName').textContent=d.server_name;
  document.getElementById('total').textContent=brl(d.total_cost);
  document.getElementById('energy').textContent=brl(d.energy_cost);document.getElementById('kwh').textContent=d.energy_kwh+' kWh';
  document.getElementById('trafficCost').textContent=brl(d.traffic_cost);document.getElementById('traffic').textContent=d.traffic_gb+' GB';
  document.getElementById('depreciation').textContent=brl(d.depreciation_cost);
  setMeter('cpu','cpuBar',d.cpu_percent);setMeter('ram','ramBar',d.memory_percent);setMeter('disk','diskBar',d.disk_percent);
  document.getElementById('ramDetail').textContent=`${d.memory_used_gb} / ${d.memory_total_gb} GB`;
  document.getElementById('diskDetail').textContent=`${d.disk_used_gb} / ${d.disk_total_gb} GB`;
  document.getElementById('uptime').textContent='Tempo ligado: '+duration(d.uptime_seconds);
  document.getElementById('updated').textContent=new Date(d.timestamp).toLocaleString('pt-BR');
  document.getElementById('pixKey').textContent=d.config.pix_key;
  const amounts=document.getElementById('amounts');if(!amounts.dataset.ready){amounts.innerHTML='';(d.config.donation_suggestions||[5,10,20,50]).forEach(v=>{let b=document.createElement('button');b.textContent=brl(v);b.onclick=()=>{document.getElementById('amount').value=v;renderQr();};amounts.appendChild(b)});amounts.dataset.ready='1';}
  renderQr();
 }catch(e){document.getElementById('updated').textContent='Erro ao atualizar';}
}
document.getElementById('amount').addEventListener('input',renderQr);
document.getElementById('copyPix').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(pixPayload(Math.max(1,Number(document.getElementById('amount').value)||1)));document.getElementById('copyStatus').textContent='Código Pix copiado.';}catch(e){document.getElementById('copyStatus').textContent='Não foi possível copiar automaticamente.';}});
refresh();setInterval(refresh,15000);
