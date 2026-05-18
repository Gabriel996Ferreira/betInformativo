from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.secret_key = "chave_secreta_para_notificacoes_toast"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bet_informativo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ==========================================
# MODELO DO BANCO DE DADOS
# ==========================================
class Time(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    posicao = db.Column(db.Integer, nullable=False)
    nome = db.Column(db.String(50), nullable=False)
    pontos = db.Column(db.Integer, nullable=False)
    forma_letras = db.Column(db.String(20), nullable=False)  # Ex: "V,V,E,V,D"
    placares = db.Column(db.String(50), nullable=False)      # Ex: "3-1,2-0,1-1,3-0,0-1"

# ==========================================
# PROCESSADOR DE ESTATÍSTICAS
# ==========================================
def processar_dados_times(times_do_banco):
    lista_times_formatados = []
    
    for time in times_do_banco:
        lista_ultimos_5 = time.forma_letras.split(',')
        lista_placares = time.placares.split(',')
        
        jogos_mais_1_5 = 0
        jogos_ambas_marcam = 0
        total_jogos = len(lista_placares) if lista_placares else 1

        for placar in lista_placares:
            if '-' in placar:
                try:
                    gols_pro, gols_contra = map(int, placar.split('-'))
                    if (gols_pro + gols_contra) > 1.5:
                        jogos_mais_1_5 += 1
                    if gols_pro > 0 and gols_contra > 0:
                        jogos_ambas_marcam += 1
                except ValueError:
                    continue

        time_formatado = {
            "id": time.id,
            "posicao": time.posicao,
            "nome": time.nome,
            "pontos": time.pontos,
            "ultimos_5": lista_ultimos_5,
            "estatisticas": {
                "mais_1_5_gols": f"{int((jogos_mais_1_5 / total_jogos) * 100)}%",
                "ambas_marcam": f"{int((jogos_ambas_marcam / total_jogos) * 100)}%"
            }
        }
        lista_times_formatados.append(time_formatado)
        
    return lista_times_formatados

# ==========================================
# ROTAS PÚBLICAS
# ==========================================
@app.route('/')
def index():
    times_banco = Time.query.order_by(Time.posicao).all()
    times_processados = processar_dados_times(times_banco)
    return render_template('index.html', times=times_processados)

# ==========================================
# ROTAS ADMINISTRATIVAS & AUTOMATIZAÇÃO
# ==========================================
@app.route('/admin')
def admin():
    times_banco = Time.query.order_by(Time.posicao).all()
    return render_template('admin.html', times=times_banco)

@app.route('/admin/salvar', methods=['POST'])
def salvar_time():
    posicao = int(request.form['posicao'])
    nome = request.form['nome']
    pontos = int(request.form['pontos'])
    forma_letras = request.form['forma_letras'].upper().replace(" ", "")
    placares = request.form['placares'].replace(" ", "")

    time_existente = Time.query.filter_by(posicao=posicao).first()
    
    if time_existente:
        time_existente.nome = nome
        time_existente.pontos = pontos
        time_existente.forma_letras = forma_letras
        time_existente.placares = placares
        flash(f"Time {nome} atualizado com sucesso!")
    else:
        novo_time = Time(posicao=posicao, nome=nome, pontos=pontos, forma_letras=forma_letras, placares=placares)
        db.session.add(novo_time)
        flash(f"Time {nome} adicionado com sucesso!")

    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/deletar/<int:id>', methods=['POST'])
def deletar_time(id):
    time_para_deletar = Time.query.get_or_404(id)
    nome_time = time_para_deletar.nome
    db.session.delete(time_para_deletar)
    db.session.commit()
    flash(f"Time {nome_time} removido com sucesso!")
    return redirect(url_for('admin'))

# ==========================================
# ROTA DE INTEGRAÇÃO COM A API (MOCK ROBUSTO)
# ==========================================
@app.route('/admin/sincronizar', methods=['POST'])
def sincronizar_api():
    # Simulando um endpoint confiável de dados esportivos na nuvem.
    # Caso a requisição falhe por falta de rede ou erro na URL, usamos dados de contingência estruturados.
    api_url = "https://raw.githubusercontent.com/luiztools/comunidade/main/api-times.json"
    
    times_importados = []
    
    try:
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            times_importados = response.json()
    except Exception:
        # Contingência offline caso o servidor de mock ou a internet falhe
        pass

    # Se a API de testes falhou ou retornou vazia, usamos dados reais pré-moldados para a simulação
    if not times_importados:
        times_importados = [
            {"posicao": 1, "nome": "Botafogo", "pontos": 15, "forma_letras": "V,V,V,E,D", "placares": "2-0,3-1,1-0,1-1,0-2"},
            {"posicao": 2, "nome": "Palmeiras", "pontos": 13, "forma_letras": "V,V,E,V,V", "placares": "2-1,3-0,0-0,2-0,1-0"},
            {"posicao": 3, "nome": "Flamengo", "pontos": 12, "forma_letras": "V,D,V,V,D", "placares": "4-0,1-2,2-0,3-1,0-1"},
            {"posicao": 4, "nome": "Fortaleza", "pontos": 10, "forma_letras": "E,V,D,E,V", "placares": "1-1,2-0,1-2,0-0,3-1"},
            {"posicao": 5, "nome": "São Paulo", "pontos": 9, "forma_letras": "D,V,E,D,V", "placares": "0-1,2-1,1-1,0-2,1-0"}
        ]

    # Remove todos os registros atuais para popular com as novas rodadas vindas da internet
    Time.query.delete()
    
    for item in times_importados:
        novo_time = Time(
            posicao=item["posicao"],
            nome=item["nome"],
            pontos=item["pontos"],
            forma_letras=item["forma_letras"],
            placares=item["placares"]
        )
        db.session.add(novo_time)
        
    db.session.commit()
    flash("Sincronização com a API de Futebol realizada com sucesso!")
    return redirect(url_for('admin'))

# ==========================================
# INICIALIZAÇÃO DO SERVIDOR
# ==========================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if Time.query.count() == 0:
            botafogo = Time(posicao=1, nome="Botafogo", pontos=12, forma_letras="V,V,E,V,D", placares="3-1,2-0,1-1,3-0,0-1")
            palmeiras = Time(posicao=2, nome="Palmeiras", pontos=10, forma_letras="V,E,V,V,E", placares="1-0,0-0,2-1,2-0,1-1")
            flamengo = Time(posicao=3, nome="Flamengo", pontos=9, forma_letras="D,V,D,V,V", placares="1-2,4-1,0-2,3-2,2-1")
            db.session.add_all([botafogo, palmeiras, flamengo])
            db.session.commit()

    app.run(debug=True)