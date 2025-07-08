from flask import Flask, render_template_string, request
import random

app = Flask(__name__)

cores_disponiveis = ['Azul', 'Verde', 'Amarela', 'Laranja', 'Vermelha']
misturas_cores = {
    frozenset(['Azul', 'Vermelha']): 'Roxa',
    frozenset(['Azul', 'Amarela']): 'Verde-limão',
    frozenset(['Vermelha', 'Amarela']): 'Laranja-avermelhada',
    frozenset(['Azul', 'Verde']): 'Ciano',
    frozenset(['Verde', 'Amarela']): 'Amarelo-esverdeado',
}
regioes_disponiveis = ['Norte', 'Sul', 'Leste', 'Oeste']

HTML_FORM = """
<!doctype html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Simulação de Populações</title>
    <style>
        body { font-family: sans-serif; margin: 2em; background-color: #f9f9f9; }
        form { background-color: #fff; padding: 2em; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        fieldset { border: 1px solid #ccc; border-radius: 5px; margin-bottom: 1em; padding: 1em; }
        legend { font-weight: bold; color: #0056b3; }
        label { display: inline-block; margin-bottom: 0.5em;}
        small { color: #666; margin-left: 10px; }
        input[type=number], select { width: 100px; margin-bottom: 0.5em; padding: 5px; }
        input[type=submit] { padding: 10px 20px; font-size: 1.1em; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; margin-top: 10px;}
        input[type=submit]:hover { background-color: #0056b3; }
        .error { color: red; font-weight: bold; margin-top: 1em; }
    </style>
</head>
<body>
    <h2>Simulação de Populações - Configuração</h2>
    <form method=post>

    <fieldset>
        <legend>Etapa 1: Selecione as Populações</legend>
        <p>Marque as populações que deseja simular e configure seus parâmetros iniciais.</p>
        {% for pop in todas_as_pops %}
        <div>
            <input type="checkbox" name="simular_{{ pop }}" {% if pop in populacoes_escolhidas %}checked{% endif %}>
            <label><b>{{ pop }}</b></label> 
            Número inicial: <input type=number name="{{ pop }}_n" min=1 max=1000 placeholder="1000" value="{{ request.form.get(pop+'_n', '') }}"> <small>(valor de 1 a 1000)</small>
            Taxa de reprodução: <input type=number step=0.01 name="{{ pop }}_taxa" min=0 max=1 placeholder="0.1" value="{{ request.form.get(pop+'_taxa', '') }}"> <small>(valor de 0 a 1)</small> 
            Região:
            <select name="{{ pop }}_regiao">
                {% for r in regioes %}
                <option value="{{ r }}" {% if request.form.get(pop+'_regiao') == r %}selected{% endif %}>{{ r }}</option>
                {% endfor %}
            </select>
        </div>
        {% endfor %}
    </fieldset>

    {% if not populacoes_escolhidas %}
        <input type=submit name="action" value="Configurar Interações e Parâmetros">
    {% endif %}

    {% if populacoes_escolhidas %}
    <fieldset>
        <legend>Etapa 2: Interações entre Populações Selecionadas</legend>
        <label>Defina a chance (0 a 1) de uma população eliminar a outra na mesma região:</label><br>
        {% for atacante in populacoes_escolhidas %}
            {% for vitima in populacoes_escolhidas %}
                {% if atacante != vitima %}
                {{ atacante }} elimina {{ vitima }}: <input type=number step=0.01 name="int_{{ atacante }}_{{ vitima }}" min=0 max=1 placeholder="0" value="{{ request.form.get('int_'+atacante+'_'+vitima, '') }}"><br>
                {% endif %}
            {% endfor %}
        {% endfor %}
    </fieldset>

    <fieldset>
        <legend>Etapa 3: Parâmetros Gerais da Simulação</legend>
        Chance de combinação na mesma região: <input type=number step=0.01 name=chance_combinacao min=0 max=1 required> <small>(valor de 0 a 1)</small><br>
        Chance de combinação entre regiões: <input type=number step=0.01 name=chance_combinacao2 min=0 max=1 required> <small>(valor de 0 a 1)</small><br>
        Chance de mutação aleatória: <input type=number step=0.01 name=chance_mutacao min=0 max=1 required> <small>(valor de 0 a 1)</small><br><br>
        Gerações para simular: <input type=number name=geracoes min=1 max=50 required> <small>(máximo 50)</small><br><br>
    </fieldset>

    <input type=submit name="action" value="Rodar Simulação">
    {% endif %}

    {% if error %}
        <p class="error">{{ error }}</p>
    {% endif %}
    </form>
</body>
</html>
"""

HTML_RESULT = """
<!doctype html>
<title>Resultado da Simulação</title>
<h2>Resultado da Simulação</h2>
<pre style="background-color:#f4f4f4; border: 1px solid #ccc; padding: 1em; white-space: pre-wrap; word-wrap: break-word;">{{ resultado }}</pre>
<a href="/">Voltar para a Configuração</a>
"""


def parse_float(valor, minimo, maximo, default=0.0):
    try:
        v = float(valor)
        if minimo <= v <= maximo:
            return v
        return default
    except (ValueError, TypeError):
        return default


def parse_int(valor, minimo, maximo, default=1):
    try:
        v = int(valor)
        if minimo <= v <= maximo:
            return v
        return default
    except (ValueError, TypeError):
        return default


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")

        populacoes_escolhidas = [
            cor for cor in cores_disponiveis
            if f"simular_{cor}" in request.form
        ]

        if action == "Configurar Interações e Parâmetros":
            if not populacoes_escolhidas:
                return render_template_string(
                    HTML_FORM,
                    todas_as_pops=cores_disponiveis,
                    populacoes_escolhidas=[],
                    regioes=regioes_disponiveis,
                    request=request,
                    error=
                    "ERRO: Você deve selecionar pelo menos uma população para continuar."
                )

            ### INÍCIO DA ALTERAÇÃO ###
            # Validação para garantir que os campos das populações selecionadas foram preenchidos
            for pop in populacoes_escolhidas:
                n_inicial = request.form.get(f"{pop}_n")
                taxa_reproducao = request.form.get(f"{pop}_taxa")
                # Se um dos campos obrigatórios estiver vazio
                if not n_inicial or not taxa_reproducao:
                    return render_template_string(
                        HTML_FORM,
                        todas_as_pops=cores_disponiveis,
                        # Passamos uma lista vazia para forçar a renderização apenas da Etapa 1
                        populacoes_escolhidas=[],
                        regioes=regioes_disponiveis,
                        request=request,
                        error=f"ERRO: Por favor, preencha o número inicial e a taxa de reprodução para a população '{pop}' antes de prosseguir."
                    )
            ### FIM DA ALTERAÇÃO ###


            return render_template_string(
                HTML_FORM,
                todas_as_pops=cores_disponiveis,
                populacoes_escolhidas=populacoes_escolhidas,
                regioes=regioes_disponiveis,
                request=request)

        elif action == "Rodar Simulação":
            populacoes = {}
            for pop in populacoes_escolhidas:
                n = parse_int(request.form.get(f"{pop}_n"), 1, 1000, 100)
                taxa = parse_float(request.form.get(f"{pop}_taxa"), 0, 1, 0.1)
                regiao = request.form.get(f"{pop}_regiao",
                                        regioes_disponiveis[0])
                populacoes[pop] = {
                    'quantidade': n,
                    'taxa': taxa,
                    'regiao': regiao
                }

            interacoes = {}
            for atacante in populacoes_escolhidas:
                for vitima in populacoes_escolhidas:
                    if atacante != vitima:
                        chave = f"int_{atacante}_{vitima}"
                        chance = parse_float(request.form.get(chave), 0, 1, 0)
                        if chance > 0:
                            interacoes[(atacante, vitima)] = chance

            chance_combinacao = parse_float(
                request.form.get("chance_combinacao"), 0, 1, 0)
            chance_combinacao2 = parse_float(
                request.form.get("chance_combinacao2"), 0, 1, 0)
            chance_mutacao = parse_float(request.form.get("chance_mutacao"), 0,
                                         1, 0)
            geracoes = parse_int(request.form.get("geracoes"), 1, 50, 10)

            output = []

            def p(text):
                output.append(str(text))

            p(f"SIMULAÇÃO INICIADA COM AS POPULAÇÕES: {', '.join(populacoes.keys())}"
              )
            for g in range(geracoes):
                p(f"\nGeração {g+1}")

                for (atacante, vitima), chance in interacoes.items():
                    if populacoes.get(atacante) and populacoes.get(vitima):
                        if populacoes[atacante]['regiao'] == populacoes[
                                vitima]['regiao']:
                            mortos = int(populacoes[vitima]['quantidade'] *
                                         chance)
                            if mortos > 0:
                                populacoes[vitima]['quantidade'] -= mortos
                                p(f"{atacante} eliminou {mortos} de {vitima} no {populacoes[atacante]['regiao']}"
                                  )

                for pop in list(populacoes.keys()):
                    novos = int(populacoes[pop]['quantidade'] *
                                populacoes[pop]['taxa'])
                    populacoes[pop]['quantidade'] += novos

                if random.random() < chance_mutacao:
                    cor_mut = "Mutante " + str(random.randint(1, 100))
                    regiao_mut = random.choice(regioes_disponiveis)
                    populacoes[cor_mut] = {
                        'quantidade': 10,
                        'taxa': 0.05,
                        'regiao': regiao_mut
                    }
                    p(f"MUTAÇÃO: Surgiu uma nova população '{cor_mut}' na região {regiao_mut}"
                      )

                for pop in list(populacoes.keys()):
                    if populacoes[pop]['quantidade'] <= 0:
                        p(f"EXTINÇÃO: {pop} foi extinta")
                        del populacoes[pop]

                p("\nPopulações atuais:")
                if populacoes:
                    for pop, dados in sorted(populacoes.items()):
                        p(f"{pop}: {dados['quantidade']} indivíduos | Região: {dados['regiao']}"
                          )
                else:
                    p("Nenhuma população sobreviveu.")

                if not populacoes:
                    p("\nTodas as populações foram extintas.")
                    break

            p("\nFIM")
            resultado = "\n".join(output)
            return render_template_string(HTML_RESULT, resultado=resultado)

    return render_template_string(HTML_FORM,
                                  todas_as_pops=cores_disponiveis,
                                  populacoes_escolhidas=[],
                                  regioes=regioes_disponiveis,
                                  request=request)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
