# Classificação sugerida (Aplicação > Linha/Sistema > Função) a partir do código, descrição e catálogo de origem
import re, unicodedata
def _n(s): return unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode().lower()
TAB={'CT':'Cantoneiras','BC':'Barras chatas','TR':'Tubos redondos','TQ':'Tubos quadrados','TG':'Tubos retangulares','VR':'Vergalhões redondos','VQ':'Vergalhões quadrados','PU':'Perfis U','PT':'Perfis T','U':'Perfis U','34':'Perfis U'}
LINHA_PREF={'SU':'Suprema','LG':'Gold','25':'Linha 25','30':'Linha 30','42':'Linha 42','MB':'Linha MB (correr)','ST':'SP20','MN':'Suprema Integrada (persiana)','80':'MG32','ES':'Euroshow Giro-Oscilo','SI':'Linha SI','PMO':'Linha 30 (ASA)','E':'Linha 30 (ASA)','Y':'Linha 25 (ASA)','A':'Linha 25 (ASA)','Z':'Linha 25 (ASA)'}
def linha_atual(cod, desc, cat):
    p=re.match(r'^([A-Z]+|\d+)',cod).group(1)
    if p in TAB: return 'Tabelados'
    if p in LINHA_PREF: return LINHA_PREF[p]
    return cat or '—'
def funcao(desc):
    d=_n(desc)
    for k,v in [('contra marco','Contramarco'),('contramarco','Contramarco'),('marco','Marco'),('trilho','Trilho'),('baguete','Baguete'),('arremate','Arremate'),('montante','Montante'),('travessa','Travessa'),('coluna','Coluna'),('complemento','Complemento'),('batedeira','Batedeira'),('mata junta','Mata-junta'),('guia','Guia'),('tampa','Tampa'),('clic','Clic'),('corrimao','Corrimão'),('calha','Calha'),('lambri','Lambri'),('veneziana','Veneziana'),('acoplador','Acoplador'),('tubo','Tubo'),('cantoneira','Cantoneira'),('barra chata','Barra chata'),('vergalhao','Vergalhão'),('perfil "u"','Perfil U'),('perfil "t"','Perfil T'),('transpace','Transpace'),('capa','Capa'),('chapeu','Chapéu'),('cadeirinha','Cadeirinha'),('forro','Forro'),('rodape','Rodapé'),('brise','Brise'),('suporte','Suporte'),('folha','Folha'),('requadro','Requadro'),('pingadeira','Pingadeira'),('ripado','Ripado'),('caixa','Caixa'),('soleira','Soleira')]:
        if k in d: return v
    return 'Outros'
def sugerido(cod, equiv, desc, cat):
    p=re.match(r'^([A-Z]+|\d+)',cod).group(1); d=_n(desc); e=str(equiv or '').upper(); c=_n(cat)
    f=funcao(desc)
    if p in TAB: return ('Perfis estruturais e tabelados', TAB[p], f)
    if re.match(r'AP-12[3-5]\d$',cod): return ('Sistemas modulares','Sistema Modular', f)
    if 'muxarabi' in d or 'ripado' in d or cod in ('AP-6509','AP-6510','AP-056','AP-057') or e.startswith('MUX'): return ('Lambris, ripados e muxarabi','Muxarabi', f)
    if 'lambri' in d or p=='LB' or cod=='AP-050': return ('Lambris, ripados e muxarabi','Lambris', f)
    if 'corrimao' in d or p in ('CG','AL') or 'guarda' in d: return ('Guarda-corpo e corrimão','Guarda-corpo e corrimão', f)
    if 'brise' in d or e.startswith('FA') or 'atlanta' in c or p=='DC': return ('Fachadas e pele de vidro','Atlanta (pele de vidro)', f)
    if p in ('BX','CL','37','50','2936','2937','39') or 'box' in d or 'temperado' in d or 'transpace' in d or 'cadeirinha' in d: return ('Box e vidro temperado','Box e temperado', f)
    if p=='TSL' or 'sala limpa' in c: return ('Divisórias e forros','Sala limpa', f)
    if p in ('DV','DS') or 'forro' in d or 'sanitar' in d: return ('Divisórias e forros','Divisórias', f)
    if p in ('PV','LM') or 'vitrine' in c or 'luminoso' in d: return ('Vitrines e comunicação visual','Vitrines e luminosos', f)
    if p=='PC' or 'portao' in c or 'gradil' in c: return ('Portões e gradis','Portão / Gradil', f)
    if 'mosquiteiro' in d: return ('Janelas e portas','Tela mosquiteira', f)
    if p in ('CA','ME','T','PP') or (p=='CM' and 'arremate' in d): return ('Arremates e acabamentos','Arremates', f)
    if p=='CM' or 'contra marco' in d: return ('Janelas e portas','Contramarcos', f)
    if p in LINHA_PREF: return ('Janelas e portas', LINHA_PREF[p], f)
    if p=='FC': return ('Janelas e portas','Linha FC', f)
    if p in ('BG','VZ'): return ('Janelas e portas','Uso geral (baguetes e venezianas)', f)
    if 'stelman' in c or e.startswith('STL'): return ('Janelas e portas','Stelman', f)
    if e.startswith('DP-') or 'portoes' in c: return ('Portões e gradis','Decamp Portões', f)
    if 'chapeu' in d or 'capa para chapeu' in d: return ('Box e vidro temperado','Box e temperado', f)
    if 'corrimao' in c: return ('Guarda-corpo e corrimão','Guarda-corpo e corrimão', f)
    if 'persiana' in d: return ('Janelas e portas','Persiana integrada', f)
    if f in ('Marco','Montante','Travessa','Trilho','Complemento','Folha','Coluna','Guia','Caixa','Tampa','Batedeira','Mata-junta','Contramarco','Suporte') or 'basculante' in d:
        nome={'geral asa':'ASA (diversas)','geral decamp':'Decamp (diversas)','novaxx luxxor 2.5':'Luxxor 2.5','geral novaxx (ocr)':'Novaxx (diversas)','geral imperio':'Império (diversas)','geral alumil':'Alumil (diversas)','geral tera':'Tera (diversas)','geral hyspex':'Hyspex (diversas)'}.get(c,'Outras linhas')
        return ('Janelas e portas', nome, f)
    return ('A revisar', cat or '—', f)
